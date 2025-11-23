import pickle
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


import sys
import sys
import os
import json
import time
import pickle
from langchain.schema import SystemMessage
from langchain_openai import ChatOpenAI
import time
from openai import APIConnectionError, RateLimitError



from class_def import*
os.environ["OPENAI_API_KEY"] = ""
top = 0 # Global Variable for pointing to top module of the HSG

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



def safe_llm_invoke(llm, chat_history, retries=5, delay=5):
    """
    Safely invoke the LLM with automatic retry on connection errors or rate limits.
    """
    for attempt in range(1, retries + 1):
        try:
            response = llm.invoke(chat_history)
            return response  # This is a ChatResult object in LangChain
        except (APIConnectionError, RateLimitError) as e:
            print(f"⚠️ Attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                print(f"⏳ Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("❌ All retry attempts failed.")
                raise


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


def build_contextual_description_tree(module_response, up_levels=0, down_levels=1):
    """
    Builds a contextual hierarchical tree centered on a given module.
    Includes its parents (with descendants depth adjusted per level) 
    and descendants (children) up to specified depths.

    For all modules (both up and down directions), include:
      - long_description
      - cfg
      - dfg

    Args:
        module_response (Module_GPT_Response): Starting module.
        up_levels (int): Number of parent levels to include.
        down_levels (int): Maximum descendant depth for each module.
    Returns:
        dict: Nested dictionary representing the contextual module tree.
    """

    def build_descendant_tree(module, level, relation, max_level):
        """Recursively builds descendant (child) tree up to max_level depth."""
        if level > max_level or max_level <= 0:
            return None

        node = {
            "module_name": getattr(module, "module_name", "Unknown"),
            "relation": relation,
            "long_description": getattr(module, "long_description", []),
            # "FSM": getattr(module, "FSM", []),
            # "cfg": getattr(module, "cfg", []),
            # "dfg": getattr(module, "dfg", []),
            "submodules": []
        }

        if hasattr(module, "submodule_GPT_Response") and module.submodule_GPT_Response:
            for sub in module.submodule_GPT_Response.values():
                child = build_descendant_tree(sub, level + 1, relation="child", max_level=max_level)
                if child:
                    node["submodules"].append(child)

        return node

    # Build tree for the current module (self + descendants)
    current_tree = build_descendant_tree(module_response, level=0, relation="self", max_level=down_levels)

    # Traverse upward and wrap the tree within each parent level
    parent = getattr(module_response, "parent", None)
    current_root = current_tree
    up_level_index = 1

    while up_level_index <= up_levels and parent:
        # Determine descendant depth for this parent
        parent_descendant_depth = max(down_levels - up_level_index, 0)

        parent_node = {
            "module_name": getattr(parent, "module_name", "Unknown"),
            "relation": "parent",
            "long_description": getattr(parent, "long_description", []),
            # "cfg": getattr(parent, "cfg", []),
            # "dfg": getattr(parent, "dfg", []),
            "submodules": []
        }

        # Include submodules of this parent (siblings + current subtree)
        for sub in parent.submodule_GPT_Response.values():
            if sub == module_response:
                parent_node["submodules"].append(current_root)
            else:
                sibling_tree = build_descendant_tree(
                    sub,
                    level=1,
                    relation="sibling",
                    max_level=parent_descendant_depth
                )
                if sibling_tree:
                    parent_node["submodules"].append(sibling_tree)

        current_root = parent_node
        module_response = parent
        parent = getattr(parent, "parent", None)
        up_level_index += 1

    return current_root


def gen_spec_recursive (module_response, llm, chat_history, spec_text, visited = None, prev_analysis = None):

    up_level = 0
    down_level = 1
    window_length = 5

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

    def create_module_spec_prompt (module_response, spec_text, prev_analysis):

        prompt = (
            f'You are analyzing a Verilog module named `{module_response.module_name}`' 
            f'which is part of top level module: `{top.module_name}`, to generate content for its specification document'
            f'Current subsection needs to be generated: SPECIFICATION FIELD: "{spec_text}" '
            f'From this module: `{module_response.module_name}`, a window of functional descriptions and control & data flow graph'
            f' of its child and parent modules are given'
            f'For its parents and child module?s, a contextual long description tree is given\n'
            # f'### MODULE: {module_response.module_name}\n'
            # # f'verilog code: {module_response.verilog_code}\n'
            # f'verilog code: {module_response.long_description}\n'
            # f'FSM: {module_response.FSM}\n'
            # f'CSR: {module_response.CSR}\n\n'             
        )

        prompt += f'### Contextual Tree of child and parent modules\n'
        prompt += json.dumps(build_contextual_description_tree(module_response, up_levels=up_level, down_levels=down_level) ,indent=2)

        # prompt += "Hierarchy of the system: "+ get_hierarchy_str(top)

        if hasattr(module_response, "protocols"):
            prompt += f'Analysis on standard protocols found in this system'
            for protocol in module_response.protocols:
                prompt += protocol

        if prev_analysis:
            prompt += f'Past reasoning upto this point: {"".join(prev_analysis[-window_length:])}'

        task = (
            f'### TASK\n'
            f'From the current contextual tree along with the past reasoning generate content for this SPECIFICATION FIELD: "{spec_text}" \n'
            f'The whole hierarchy of the system will be traversed so generate partial descriptions and notes'
            f'In the end, all these descriptions and notes will be combined to generate the complete description for this SPECIFICATION FIELD'
            f'If current tree has no relevance to current SPECIFICATION FIELD, you can just keep the SPEC_DESCRIPTION field empty'
            f'The purpose of notes to keep contexts which will help forward analysis'
            f'Be comprehensive but not verbose'
            f'Respond ONLY in this JSON format. Do not add any extra explanation or commentary.:\n'
            f'{{\n '
            # f'    "ANSWER": "SUFFICIENT | NOT_SUFFICIENT",\n'
            f'    "SPEC_DESCRIPTION": "",\n'
            f'    "NOTES": ""\n'
            f'}}\n'
        )

        prompt = prompt + task

        return prompt

    def extract_llm_response_fields_spec_json(response_text):
        try:
            response_start = response_text.find('{')
            response_end = response_text.rfind('}') + 1

            if response_start == -1 or response_end == -1:
                return None, None, None, "JSON object not found in response."

            json_text = response_text[response_start:response_end]
            parsed = json.loads(json_text)

            required_keys = {"ANSWER", "NEEDS_ANALYSIS", "DESCRIPTION", "REASONING"}
            if not required_keys.issubset(parsed):
                return None, None, None, "Missing one or more required fields in LLM response."

            return parsed["ANSWER"], parsed["NEEDS_ANALYSIS"], parsed["DESCRIPTION"], parsed["REASONING"], None

        except json.JSONDecodeError as e:
            return None, None, None, None, f"Invalid JSON format: {e}"
        except Exception as e:
            return None, None, None, None, f"Unexpected error: {e}"

    global top

    if visited is None:
        visited = set()
    
    if prev_analysis is None:
        prev_analysis = []

    module_name = getattr(module_response, "module_name", None)
    if module_name in visited:
        print(f"🌀 Skipping {module_name} — already visited to prevent livelock.")
        return f"Skipped {module_name} (already analyzed)", chat_history
    visited.add(module_name)

    prompt = create_module_spec_prompt(module_response=module_response, spec_text=spec_text)
    # print('Prompt:', prompt)
    chat_history.append(HumanMessage(content=prompt))
    chat_history = trim_chat_history(chat_history=chat_history)
    response = safe_llm_invoke(llm, chat_history)
    chat_history.append(AIMessage(content=response.content))

    prev_analysis.append(response.content)

    print('Response:', response.content)
    final_answer, needs_analysis, description, reasoning, error = extract_llm_response_fields_spec_json(response.content)
    # print(error)
    if error:
        print(error)
        return None
    
    if final_answer == 'Yes':
        return f'Final Answer: {final_answer}\n Needs more analysis: {needs_analysis}\n DESCRIPTION: {description} REASONING: {reasoning}', chat_history
    else:
        temp = ''

        for submod_name in needs_analysis:
            submod_resp = get_submodule_response(module_response.submodule_GPT_Response, submod_name)
            if submod_resp is None:
                print(f"⚠️ {submod_name} not found under {module_name}, checking top-level.")
                submod_resp = get_submodule_response(top.submodule_GPT_Response, submod_name)
            if submod_resp is None:
                print(f"🚫 {submod_name} not found anywhere, skipping.")
                continue

            subdmod_response, chat_history = gen_spec_recursive(module_response.submodule_GPT_Response[submod_name], llm, chat_history, spec_text, visited, prev_analysis)
            # submod_final_answer, submod_needs_analysis, submod_reasoning, submod_error = extract_llm_response_fields_json(subdmod_response.content)
            # while submod_error:
            #     print(submod_error)
            #     return None
            temp = temp + subdmod_response
    
        return f'Final Answer: {final_answer}\n Needs more analysis: {needs_analysis}\n DESCRIPTION: {description} REASONING: {reasoning}'+ temp, chat_history

def gen_spec(module_response, llm, chat_history, spec_text):

    def extract_llm_response_fields_simple(response_text):
        try:
            response_start = response_text.find('{')
            response_end = response_text.rfind('}') + 1

            if response_start == -1 or response_end == -1:
                return None, None, None, "JSON object not found in response."

            json_text = response_text[response_start:response_end]
            parsed = json.loads(json_text)

            required_keys = {"Description"}
            if not required_keys.issubset(parsed):
                return None, "Missing one or more required fields in LLM response."

            return (
                parsed["Description"],
                None
            )

        except json.JSONDecodeError as e:
            return None, None, None, f"Invalid JSON format: {e}"
        except Exception as e:
            return None, None, None, f"Unexpected error: {e}"


    response, chat_history = gen_spec_recursive(module_response, llm, chat_history, spec_text)
    
    prompt = (
        f'Based on reasoning so far. Following are the previous reasonings and analysis\n'
        f'{response}\n'
        f'Based on the response generate specification for the specificatio field: {spec_text} ?\n'
        f'Reply in following strict JSON format:'
        f'{{\n '
        f'    "Description": ""\n'
        f'}}\n'
    )

    
    print(prompt)

    chat_history.append(HumanMessage(content=prompt))
    chat_history = trim_chat_history(chat_history=chat_history)

    response = safe_llm_invoke(llm, chat_history)
    chat_history.append(AIMessage(content=response.content))

    spec, error = extract_llm_response_fields_simple(response.content)

    count = 0
    while error:
        print("Json error. Trying again")
        prompt = (
        'Previous response had json formatting error'
        f'Reply in following strict JSON format:'
        f'{{\n '
        f'    "Description": ""\n'
        f'}}\n'
        )
        chat_history.append(HumanMessage(content=prompt))
        response = safe_llm_invoke(llm, chat_history)
        chat_history.append(AIMessage(content=response.content))
        spec, error = extract_llm_response_fields_simple(response.content)
        count += 1
        if count == 5:
            break
    return spec, chat_history


# === CONFIG ===
STATE_FILE = "spec_generation_state.json"
PAUSE_FILE = "pause.flag"


# === STATE HANDLING ===
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


# === PARENT POINTER ASSIGNMENT ===
def assign_parent_pointers(module_obj, parent=None):
    """Recursively assign parent pointers for all submodules."""
    module_obj.parent = parent
    for submodule in module_obj.submodule_GPT_Response.values():
        assign_parent_pointers(submodule, module_obj)


# === MAIN EXECUTION ===
if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python script.py <top_module_name>")
        sys.exit(1)

    top_module_name = sys.argv[1]
    file_name = f"{top_module_name}.pkl"

    # --- Load module responses ---
    with open(file_name, "rb") as f:
        module_response = pickle.load(f)

    top = module_response
    assign_parent_pointers(top)

################################################################################
######### --- Load protocol responses Start---##################################
################################################################################

    # with open("USB_verification_response.pkl", "rb") as f:
    #     USB_verification_response = pickle.load(f)
    # with open("WB_verification_response.pkl", "rb") as f:
    #     wb_verification_response = pickle.load(f)

    # top.protocols = []
    # top.protocols.append(USB_verification_response.FINAL_RESPONSE)
    # top.protocols.append(wb_verification_response.FINAL_RESPONSE)

################################################################################
######### --- Load protocol responses End---##################################
################################################################################



    # --- Initialize LLM ---
    llm = ChatOpenAI(model="gpt-5")
    initial_msg = (
        "You are a helpful assistant that can generate a specification document "
        "from descriptions of Verilog code for a top module or instantiated modules."
    )

    chat_history = [SystemMessage(content=initial_msg)]

    # --- Load subsections file ---
    filename = f"{top_module_name}_subsections.json"
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            print("⚠️ File contains raw text, not JSON.")
            data = {}

    subsections = data.get("Subsections", {})
    spec_doc = {}

    # --- Load recovery state ---
    state = load_state()
    total_sections = len(subsections)
    section_count = 0

    # === MAIN LOOP ===
    for section, sub_list in subsections.items():
        section_count += 1
        print(f"\n📘 Section {section_count}/{total_sections}: {section}")
        spec_doc.setdefault(section, {})

        for idx, sub in enumerate(sub_list):
            check_pause()
            progress = f"[{idx + 1}/{len(sub_list)}] (Section {section_count}/{total_sections})"
            item_key = f"{section}_{sub}"

            # Skip completed subsections
            if state.get(item_key, {}).get("done"):
                print(f"✅ Skipping {progress} — already completed ({sub})")
                continue

            print(f"\n🔁 Processing {progress}: {sub}")
            start_time = time.time()
            try:
                # === Generate content for subsection ===
                spec_field_response, chat_history = gen_spec(module_response, llm, chat_history, sub)
                spec_doc[section][sub] = spec_field_response

                # Save progress
                state[item_key] = {"done": True, "section": section, "sub": sub}
                save_state(state)

                print(f"🧩 Completed {progress} in {time.time() - start_time:.1f}s")

            except Exception as e:
                print(f"⚠️ Error on {progress}: {e}")
                state[item_key] = {"error": str(e)}
                save_state(state)
                continue

    # === Final Save ===
    with open("generated_spec_doc.json", "w", encoding="utf-8") as f:
        json.dump(spec_doc, f, indent=4, ensure_ascii=False)

    print("\n✅ Specification document generation complete.")
    print("📄 Output: generated_spec_doc.json")
    print("💾 Progress saved in:", STATE_FILE)
