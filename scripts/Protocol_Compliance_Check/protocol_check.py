# from create_graph import *
# from helpers import *
# from parse_module_recursive import *
import pickle
from langchain.schema import HumanMessage, AIMessage
import re
import os
import pdfplumber
import docx
import re
from typing import List, Dict
from openai import OpenAI
import tiktoken
import os
import webbrowser
import pickle
import argparse
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
import time
import json
from class_def import*

os.environ["OPENAI_API_KEY"] = ""

# def trim_chat_history(chat_history, max_tokens=150000, model="gpt-5"):
#     """
#     Trims chat history so total tokens (approx.) stay within model limits.
#     Keeps the system message and most recent messages up to the limit.
#     """
#     try:
#         enc = tiktoken.encoding_for_model(model)
#     except KeyError:
#         enc = tiktoken.get_encoding("cl100k_base")

#     total_tokens = 0
#     trimmed = []

#     # Iterate from newest to oldest
#     for msg in reversed(chat_history):
#         msg_tokens = len(enc.encode(msg.content))
#         # Leave a 15–20% safety buffer for metadata + system overhead
#         if total_tokens + msg_tokens > max_tokens:
#             break
#         trimmed.insert(0, msg)
#         total_tokens += msg_tokens

#     # Always keep system message at index 0
#     if chat_history:
#         if chat_history[0] not in trimmed:
#             trimmed.insert(0, chat_history[0])

#     return trimmed


# def trim_chat_history(chat_history, max_tokens=250000, model="gpt-5"):
#     """
#     Trims chat history so total tokens stay within model limits.
#     Keeps the system message and the most recent messages up to the limit.
#     """
#     # import tiktoken

#     try:
#         enc = tiktoken.encoding_for_model(model)
#     except KeyError:
#         enc = tiktoken.get_encoding("cl100k_base")

#     total_tokens = 0
#     trimmed = []
#     effective_limit = int(max_tokens)  # leave 15% headroom

#     for msg in reversed(chat_history):
#         # handle string or structured message
#         if isinstance(msg.content, list):
#             text = " ".join([c["text"] for c in msg.content if c.get("type") == "text"])
#         else:
#             text = str(msg.content)

#         msg_tokens = len(enc.encode(text))

#         if total_tokens + msg_tokens > effective_limit:
#             break

#         trimmed.insert(0, msg)
#         total_tokens += msg_tokens

#     print("tokens = ", total_tokens)
#     # Always keep system message
#     if chat_history and chat_history[0] not in trimmed:
#         trimmed.insert(0, chat_history[0])

#     return trimmed


def trim_chat_history(chat_history, max_tokens=200000, model="gpt-5"):
    """
    Trims chat history to stay within token limits.
    Always keeps the system message and the last three messages,
    then adds older messages until the limit is reached.
    """
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model(model)
    except (ImportError, KeyError):
        enc = tiktoken.get_encoding("cl100k_base")

    # Nothing to trim if very short
    if len(chat_history) <= 4:
        return chat_history

    # Always keep system message (first) and latest three messages
    system_msg = chat_history[0]
    recent_msgs = chat_history[-3:]

    # Start counting tokens
    total_tokens = sum(len(enc.encode(str(m.content))) for m in recent_msgs)
    effective_limit = int(max_tokens)

    trimmed = [system_msg] + recent_msgs

    # Work backward from messages before the last three
    for msg in reversed(chat_history[1:-3]):  # skip system + last 3
        if isinstance(msg.content, list):
            text = " ".join([c["text"] for c in msg.content if c.get("type") == "text"])
        else:
            text = str(msg.content)

        msg_tokens = len(enc.encode(text))
        if total_tokens + msg_tokens > effective_limit:
            break

        trimmed.insert(1, msg)  # insert after system message
        total_tokens += msg_tokens

    print(f"Total tokens after trim: {total_tokens}")
    return trimmed


def build_long_description_tree(module_response):
    """
    Recursively builds a nested dictionary of module names and their long descriptions.
    This structure is ideal for LLMs to analyze module hierarchies and decide which
    module(s) to explore further.
    """
    node = {
        "module_name": getattr(module_response, "module_name", "Unknown"),
        "long_description": getattr(module_response, "long_description", ""),
        "submodules": []
    }

    # Recurse into submodules if any exist
    if hasattr(module_response, "submodule_GPT_Response") and module_response.submodule_GPT_Response:
        for submodule in module_response.submodule_GPT_Response.values():
            node["submodules"].append(build_long_description_tree(submodule))

    return node

top = 0

def generate_submodule_summaries(module_response, level=1):
    """
    Recursively generates summaries of all submodules (and their nested submodules)
    for a given module_response object.
    """
    summaries = ""

    # Base case: if no submodules, return empty string
    if not hasattr(module_response, "submodule_GPT_Response") or not module_response.submodule_GPT_Response:
        return summaries

    # Iterate through each submodule
    for submodule_response in module_response.submodule_GPT_Response.values():
        indent = "#" * (level + 3)  # e.g. #### for level 1, ##### for level 2
        summaries += (
            f'{indent} SUBMODULE: {submodule_response.module_name}\n'
            f'Long description: {getattr(submodule_response, "long_description", "")}\n'
        )

        # Add summaries of submodules
        if hasattr(submodule_response, "submodule_GPT_Response") and submodule_response.submodule_GPT_Response:
            summaries += f'{"#" * (level + 4)} SUMMARIES OF SUBMODULES OF {submodule_response.module_name}\n'
            for nested_sub in submodule_response.submodule_GPT_Response.values():
                summaries += f'- {nested_sub.module_name}: {getattr(nested_sub, "summary_text", "")}\n'

            # Recursive call for deeper nesting
            summaries += generate_submodule_summaries(submodule_response, level + 1)

        summaries += "\n"

    return summaries


def build_contextual_description_tree(module_response, up_levels=0, down_levels=1, subdown_levels=2):
    """
    Builds a contextual hierarchical tree centered on a given module.
    Includes its parents (with all their submodules, i.e., siblings) and
    descendants (children) up to specified depths.

    Args:
        module_response (Module_GPT_Response): Starting module.
        up_levels (int): Levels to include above (parents + all their submodules).
        down_levels (int): Levels to include below with long descriptions.
        subdown_levels (int): Levels to include below (beyond down_levels) with summaries only.

    Returns:
        dict: Nested dictionary representing the contextual module tree.
    """

    def build_down_tree(module, level, relation, full_level):
        """
        Recursively build the descendant (child/sibling) tree up to full_level.
        - For levels ≤ down_levels: include long_description.
        - For levels > down_levels: include summary_text.
        """
        if level > full_level:
            return None

        if level <= down_levels:
            desc_field = "long_description"
            desc_value = getattr(module, "long_description", "")
        else:
            desc_field = "summary_text"
            desc_value = getattr(module, "summary_text", "")

        node = {
            "module_name": getattr(module, "module_name", "Unknown"),
            desc_field: desc_value,
            "relation": relation,
            "submodules": []
        }

        # Go deeper if allowed
        if level < full_level and hasattr(module, "submodule_GPT_Response"):
            for sub in module.submodule_GPT_Response.values():
                child = build_down_tree(sub, level + 1, relation="child", full_level=full_level)
                if child:
                    node["submodules"].append(child)

        return node

    # Start from the target module (self) and build downward
    current_tree = build_down_tree(module_response, level=0, relation="self", full_level=subdown_levels)

    # Move upward, wrapping the tree with each parent level
    parent = getattr(module_response, "parent", None)
    current_root = current_tree

    for _ in range(up_levels):
        if not parent:
            break

        parent_node = {
            "module_name": getattr(parent, "module_name", "Unknown"),
            "long_description": getattr(parent, "long_description", ""),
            "relation": "parent",
            "submodules": []
        }

        for sub in parent.submodule_GPT_Response.values():
            if sub == module_response:
                parent_node["submodules"].append(current_root)
            else:
                sibling_tree = build_down_tree(sub, level=1, relation="sibling", full_level=subdown_levels)
                if sibling_tree:
                    parent_node["submodules"].append(sibling_tree)

        # Move up one level
        current_root = parent_node
        module_response = parent
        parent = getattr(parent, "parent", None)

    return current_root


# def build_contextual_description_tree(module_response, up_levels=0, down_levels=1):
#     """
#     Builds a contextual hierarchical tree centered on a given module.
#     Includes its parents (with all their submodules, i.e., siblings) and
#     descendants (children) up to specified depths.

#     Args:
#         module_response (Module_GPT_Response): Starting module.
#         up_levels (int): Levels to include above (parents + all their submodules).
#         down_levels (int): Levels to include below (children depth).

#     Returns:
#         dict: Nested dictionary representing the contextual module tree.
#     """

#     def build_down_tree(module, level, relation):
#         """
#         Recursively build the descendant (child/sibling) tree up to the given level.
#         Includes long_description and relation info.
#         """
#         node = {
#             "module_name": getattr(module, "module_name", "Unknown"),
#             "long_description": getattr(module, "long_description", ""),
#             "relation": relation,
#             "submodules": []
#         }
#         if level > 0 and hasattr(module, "submodule_GPT_Response"):
#             for sub in module.submodule_GPT_Response.values():
#                 node["submodules"].append(build_down_tree(sub, level - 1, relation="child"))
#         return node

#     # Start from the target module (self) and build downward
#     current_tree = build_down_tree(module_response, down_levels, relation="self")

#     # Move upward, wrapping the tree with each parent level
#     parent = module_response.parent
#     current_root = current_tree
#     for _ in range(up_levels):
#         if not parent:
#             break

#         parent_node = {
#             "module_name": getattr(parent, "module_name", "Unknown"),
#             "long_description": getattr(parent, "long_description", ""),
#             "relation": "parent",
#             "submodules": []
#         }

#         # For each submodule of this parent, add:
#         # - our current subtree if it's the one we came from
#         # - full recursive sibling subtrees otherwise
#         for sub in parent.submodule_GPT_Response.values():
#             if sub == module_response:
#                 parent_node["submodules"].append(current_root)
#             else:
#                 parent_node["submodules"].append(
#                     build_down_tree(sub, down_levels, relation="sibling")
#                 )

#         # Move upward for next loop
#         current_root = parent_node
#         module_response = parent
#         parent = parent.parent

#     return current_root





def check_spec_recursive(module_response, llm, chat_history, spec_text, visited=None, prev_response = None):

    def get_submodule_response(data, key):
        """
        Recursively search for a key in nested submodule_GPT_Response dicts.
        
        Args:
            data (dict): The dictionary (e.g., module_response.submodule_GPT_Response).
            key (str): The submodule name to search for.
        
        Returns:
            The value if found, else None.
        """
        if not isinstance(data, dict):
            return None
        
        # Direct hit
        if key in data:
            return data[key]
        
        # Recursive search in all children
        for v in data.values():
            # if isinstance(v, dict) and "submodule_GPT_Response" in v:
                result = get_submodule_response(v.submodule_GPT_Response, key)
                if result is not None:
                    return result
        
        return None

    def create_module_prompt(module_response, spec_text, prev_response):

        global top

        prompt = (
            f'You are analyzing a Verilog module to determine whether a:\n'
            f'particular information (extracted from a protocol specification document) is described in it.\n\n'
            f'SPECIFICATION INFO: "{spec_text}"\n\n'
            f'Essentially, you are determining if the protocol is implemented by the RTL or not.\n'
            f'For this module, various desription is given\n'
            f'I also provide a JSON-like dictionary tree containing only the module names and their long descriptions for nested submodules upto 5 levels are given.\n'
            
            f'### MODULE: {module_response.module_name}\n'
            f'Long description: {module_response.long_description}\n'
            # f'Verilog Code: {module_response.verilog_code}'
            f'FSM: {module_response.FSM}\n'
            f'CSR: {module_response.CSR}\n\n'
            f'### JSON tree:\n {build_contextual_description_tree(module_response, up_levels= 0, down_levels= 20, subdown_levels=21)}'
        )

        # Include submodule details
        # for submodule_response in module_response.submodule_GPT_Response.values():
        #     temp = (
        #         f'#### SUBMODULE: {submodule_response.module_name}\n'
        #         f'Long description: {submodule_response.long_description}\n'
        #         # f'Summary: {submodule_response.summary_text}\n'
        #     )

        #     # Add summaries of submodules of this submodule (nested level)
        #     if hasattr(submodule_response, "submodule_GPT_Response") and submodule_response.submodule_GPT_Response:
        #         temp += f'##### SUMMARIES OF SUBMODULES OF {submodule_response.module_name}\n'
        #         for nested_sub in submodule_response.submodule_GPT_Response.values():
        #             temp += (
        #                 f'- {nested_sub.module_name}: {nested_sub.summary_text}\n'
        #             )
        #     temp += "\n"
        #     prompt += temp

        # prompt += generate_submodule_summaries(module_response)

        # Final task section
        if prev_response:
            prompt += f"Previous Analysis: {" ".join(prev_response)}"
        task = (
            f'### TASK\n'
            f'Step-by-step, reason and take notes about whether the current module or any other module(evident from the long descriptions tree) implements/satisfies the protocol point.\n'
            f'- Step 1: Does this or any other module combinedly directly describe the protocol point?\n'
            f'- Step 2: Should any submodule be analyzed in more detail before a final decision can be made? \n'
            f'- Step 3: If you can not conclude definitely yes or no from this module or the contextual tree, the evidence might be in deeper nested submodules not shown in the contextual tree '
            f' In that case, you can analyze the lowest submodules from the contextual tree which will ultimately help you inspect the deeper nested submodules which you can not see right now from the tree'
            f' If you analyze the lowest submodules you might eventually inspect the submodule you need to conclude definitely'
            # f'And the nested submodule which might help in making final decisions'
            f'Respond ONLY in this JSON format:\n'
            f'{{\n'
            f'    "final_answer": "Yes | No | Needs more analysis",\n'
            f'    "needs_analysis": ["SubModuleA", "SubModuleB"],\n'
            f'    "reasoning_and_notes": [\n'
            f'        "Step 1...",\n'
            f'        "Step 2..."\n'
            f'        "Step 3..."\n'
            f'    ]\n'
            f'}}\n'
        )

        prompt += task
        return prompt

    def extract_llm_response_fields_json(response_text):
        """
        Extracts 'final_answer', 'needs_analysis', and 'reasoning' from an LLM JSON-formatted response.

        Parameters:
            response_text (str): LLM response as a JSON-formatted string.

        Returns:
            tuple: (final_answer, needs_analysis, reasoning, error)
                - final_answer (str or None)
                - needs_analysis (list or None)
                - reasoning (list or None)
                - error (str or None): Error message if failed, otherwise None
        """
        try:
            response_start = response_text.find('{')
            response_end = response_text.rfind('}') + 1

            if response_start == -1 or response_end == -1:
                return None, None, None, "JSON object not found in response."

            json_text = response_text[response_start:response_end]
            parsed = json.loads(json_text)

            required_keys = {"final_answer", "needs_analysis", "reasoning_and_notes"}
            if not required_keys.issubset(parsed):
                return None, None, None, "Missing one or more required fields in LLM response."

            return parsed["final_answer"], parsed["needs_analysis"], parsed["reasoning_and_notes"], None

        except json.JSONDecodeError as e:
            return None, None, None, f"Invalid JSON format: {e}"
        except Exception as e:
            return None, None, None, f"Unexpected error: {e}"
    
    if visited is None:
        visited = set()
    if prev_response is None:
        prev_response = []

    module_name = getattr(module_response, "module_name", None)
    if module_name in visited:
        print(f"🌀 Skipping {module_name} — already visited to prevent livelock.")
        return f"Skipped {module_name} (already analyzed)", chat_history
    visited.add(module_name)

    prompt = create_module_prompt(module_response=module_response, spec_text=spec_text, prev_response = prev_response)
    chat_history.append(HumanMessage(content=prompt))
    chat_history = trim_chat_history(chat_history=chat_history)

    response = llm(chat_history)
    chat_history.append(AIMessage(content=response.content))
    print(response.content)

    prev_response.append(response.content)
    final_answer, needs_analysis, reasoning, error = extract_llm_response_fields_json(response.content)
    if error:
        return response.content, chat_history

    global top
    if final_answer in ('Yes', 'No'):
        return f"Final Answer: {final_answer}\nNeeds more analysis: {needs_analysis}\nReasoning: {reasoning}", chat_history

    temp = ''
    for submod_name in needs_analysis:
        submod_resp = get_submodule_response(module_response.submodule_GPT_Response, submod_name)
        if submod_resp is None:
            print(f"⚠️ {submod_name} not found under {module_name}, checking top-level.")
            submod_resp = get_submodule_response(top.submodule_GPT_Response, submod_name)
        if submod_resp is None:
            print(f"🚫 {submod_name} not found anywhere, skipping.")
            continue
        
        # Recursive call with updated visited set
        sub_response, chat_history = check_spec_recursive(submod_resp, llm, chat_history, spec_text, visited, prev_response)
        sub_final, sub_needs, sub_reason, sub_err = extract_llm_response_fields_json(sub_response)

        temp += sub_response
        if sub_final == 'Yes':
            break
    
    return (
        f"Final Answer: {final_answer}\nNeeds more analysis: {needs_analysis}\nReasoning: {reasoning}\n{temp}",
        chat_history
    )


def check_spec(module_response, llm, chat_history, spec_text):
        
    response, chat_history = check_spec_recursive(module_response, llm, chat_history, spec_text)
    prompt = (
        f'Based on reasoning so far. Following are the previous reasonings and analysis\n'
        f'{response}\n'
        f'Does the module :{module_response.module_name} or submodule as a system covers this protocol specification information: {spec_text} ?\n'
        f'If a certain point can not be fully proven or inconclusive give it benefit of doubt. But in the explaination mention it.'
        f'Consider a point to be failed if you can disprove or get counter evidence.'
        f'Provide the module names that hold the evidence or counter-evidence'
        f'If this information is covered then provide confidence score between 0 to 10\n'
        f'Reply in following strict JSON format:'
        f'{{\n '
        f'    "Response": "Yes | No | Partially\n'
        f'    "Confidence": ""\n'
        f'    "Spec_Title": ""\n' 
        f'    "Explaination": ""\n'
        f'    "Key_Modules": ["SubModuleA", "SubModuleB"] \n '
        f'}}\n'
    )

    # print(prompt)

    chat_history.append(HumanMessage(content=prompt))
    response = llm(chat_history)
    chat_history.append(AIMessage(content=response.content))

    # print(response.content)
    return response.content, chat_history



def check_feature(module_response, llm, chat_history, spec_text):

    def extract_llm_response_fields_simple(response_text):
        try:
            response_start = response_text.find('{')
            response_end = response_text.rfind('}') + 1

            if response_start == -1 or response_end == -1:
                return None, None, None, "JSON object not found in response."

            json_text = response_text[response_start:response_end]
            parsed = json.loads(json_text)

            required_keys = {"Response", "Confidence","Spec_Title", "Explaination", "Key_Modules"}
            if not required_keys.issubset(parsed):
                return None, None, "Missing one or more required fields in LLM response."

            return (
                parsed["Response"],
                parsed["Confidence"],
                parsed["Spec_Title"],
                parsed["Explaination"],
                parsed["Key_Modules"],
                None
            )

        except json.JSONDecodeError as e:
            return None, None, None, None, None, f"Invalid JSON format: {e}"
        except Exception as e:
            return None, None, None, None,None, f"Unexpected error: {e}"
              
    gpt_text, chat_history = check_spec(module_response, llm, chat_history, spec_text)    

    response, confidence, spec_title, explaination, key_modules, error = extract_llm_response_fields_simple(gpt_text)
    
    return gpt_text, response, confidence, explaination, spec_title, key_modules, chat_history, error

import json


STATE_FILE = "protocol_progress_state.json"
PAUSE_FILE = "pause.flag"

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def check_pause():
    """Pauses execution if pause.flag exists."""
    while os.path.exists(PAUSE_FILE):
        print("⏸ Paused — remove 'pause.flag' to resume...")
        time.sleep(3)

# --------------- MAIN ---------------

def assign_parent_pointers(module_obj, parent=None):
    """
    Recursively assigns parent pointers for all submodules.
    
    Args:
        module_obj (Module_GPT_Response): The current module object.
        parent (Module_GPT_Response or None): The parent module object.
    """
    # Set this module's parent
    module_obj.parent = parent

    # Recurse into all submodules
    for submodule in module_obj.submodule_GPT_Response.values():
        assign_parent_pointers(submodule, module_obj)

import sys

if __name__ == "__main__":
    # Load module and protocol responses
    if len(sys.argv) != 3:
        print("Usage: python script.py <top_module_name> <protocol_name>")
        sys.exit(1)

    top_module_name = sys.argv[1]
    protocol_name = sys.argv[2]
    file_name = f'{top_module_name}_module_response_store.pkl'

    with open(file_name, "rb") as f:
        module_response_store = pickle.load(f)

    config = 'CDFG' 
    comment = 'Comment_Removed'
    module_response = module_response_store.get(key1=config, key2=comment)

    top = module_response

    assign_parent_pointers(top)
    
    

    with open(f"protocol_gpt_response_{protocol_name}.pkl", "rb") as f:
        protocol_response = pickle.load(f)

    llm = ChatOpenAI(model="gpt-5")

    initial_msg = (
        "You are a helpful assistant that checks information extracted from a protocol "
        "specification document against natural language description of Verilog modules "
        "to determine if the RTL module or its instantiated module implements the mandatory "
        "or optional features of the protocol, and ultimately decide if the RTL is protocol-compliant."
    )

    response_history = []
    state = load_state()

    total_groups = len(protocol_response.specs_json)
    group_counter = 0

    # Outer loop over spec groups
    for spec_jsons in protocol_response.specs_json:
        group_counter += 1
        print(f"\n📘 Processing group {group_counter}/{total_groups} ...")

        total_items = len(spec_jsons)
        for idx, item in enumerate(spec_jsons):
            check_pause()
            progress = f"[{idx + 1}/{total_items}] (Group {group_counter}/{total_groups})"
            item_key = f"group{group_counter}_item{idx}_{item.get('title', 'unknown')[:40]}"

            # Skip already processed
            if state.get(item_key, {}).get("done"):
                print(f"✅ Skipping {progress} — already done ({item.get('title', '')})")
                continue

            print(f"\n🔁 Running {progress}: {item.get('title', '')}")
            chat_history = [SystemMessage(content=initial_msg)]

            try:
                start_time = time.time()
                gpt_text, response, confidence, explanation, spec_title, key_modules, chat_history, error = check_feature(
                    module_response, llm, chat_history, item
                )
                end_time = time.time()

                print(f"🧩 Completed {progress} in {end_time - start_time:.1f}s")
                print("Result snippet:", gpt_text[:200].replace("\n", " "), "..." if len(gpt_text) > 200 else "")

                response_history.append(gpt_text)
                # Save per-item progress
                state[item_key] = {
                    "done": True,
                    "title": spec_title,
                    "confidence": confidence,
                    "explanation": explanation,
                    "key_modules": key_modules,
                }
                save_state(state)

            except Exception as e:
                print(f"⚠️ Error on {progress}: {e}")
                state[item_key] = {"error": str(e)}
                save_state(state)
                continue

    # --------- Final Compliance Judgment ---------

    combined_text = "\n".join(response_history)

    prompt = f"""
    Now based on all the analysis you will make the final judgment whether this module:
    {module_response.module_name}
    complies with the protocol: {protocol_response.protocol_name} in the context of the system-level functionality of this module.

    Previous responses:
    {combined_text}

    Does it implement all the mandatory features?
    Does it implement the optional features?
    Is it compliant/partially compliant for the purpose of this device's functionality?
    If a certain point cannot be fully proven or is inconclusive, give it the benefit of the doubt, but explain it.
    Consider a point failed only if it is disproven or has counter-evidence.
    Answer in the following JSON format:
    {{
        "Response": "Yes | No | Partially",
        "Confidence": "",
        "Detailed_Explaination": ""
    }}
    """
    

    chat_history = [
        SystemMessage(content=initial_msg),
        HumanMessage(content=prompt)
    ]

    print("\n⚙️ Generating final compliance report...")
    response = llm(chat_history)
    print("✅ Final verdict received.\n")
    print(response.content)

    response_history.append(prompt)
    response_history.append(response.content)

    # Save results
    protocol_verification_response = Protocol_Verification_Response()
    protocol_verification_response.FINAL_RESPONSE = response.content
    protocol_verification_response.RESPONSE = response_history

    with open(f"protocol_verification_response_{protocol_name}.pkl", "wb") as f:
        pickle.dump(protocol_verification_response, f)

    print(f"\n🎯 Protocol verification complete. Results saved to protocol_verification_response_{protocol_name}.pkl")
