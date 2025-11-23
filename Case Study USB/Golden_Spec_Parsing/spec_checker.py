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

os.environ["OPENAI_API_KEY"] = ""
class Module_GPT_Response:
    def __init__(self, module_name):
        self.module_name = module_name
        self.verilog_code = []
        self.summary_text = []  # Sequential text summaries (just text)
        self.long_description = []
        self.control_flow_text = []
        self.data_flow_text = []
        self.input_output_list = []
        self.FSM = []
        self.cfg = []
        self.dfg = []
        self.CSR = []
        self.submodule_GPT_Response = {}

class Spec_GPT_Response:
    def __init__(self, spec_text, fsm_json, csr_json, others_json):
        # self.module_name = module_name
        self.spec_text = spec_text
        self.fsm_json = fsm_json
        self.csr_json = csr_json
        self.others_json = others_json

def create_module_prompt (module_response, spec_text):

    prompt = (
        f'You are analyzing a Verilog module and its submodules''s description to determine whether a :\n'
        f'particular information (extracted from it"s specification document so it is ground truth) is described in it \n SPECIFICATION INFO: "{spec_text}" '
        f'For this module, various description is given'
        f'For its submodule, only high-level summary is given\n'
        f'### MODULE: {module_response.module_name}\n'
        f'long description: {module_response.long_description}\n'
        f'FSM: {module_response.FSM}\n'
        f'CFG: {module_response.cfg}\n'
        f'DFG: {module_response.dfg}\n'
        f'CSR: {module_response.CSR}\n'
        # f'Dataflow: {module_response.data_flow_text}\n'
        # f'Controlflow: {module_response.control_flow_text}\n' 
        f'### SUMMARIES OF SUBMODULES\n'
    )

    for submodule_response in module_response.submodule_GPT_Response.values():
        temp = (
            f'### SUBMODULE: {submodule_response.module_name}\n'
            f'Summary: {submodule_response.summary_text}\n'
        )

        prompt = prompt + temp

    task = (
        f'### TASK\n'
        f'Step-by-step, reason and take notes about whether the current module describes the SPECIFICATION INFO.\n'
        f'- Step 1: Does `{module_response.module_name}` directly describes the SPECIFICATION INFO?\n'
        f'- Step 2: If not, does it delegate to any submodules?\n'
        f'- Step 3: Based on the summaries of the submodules, do any of them fully or partially describes tSPECIFICATION INFO?\n'
        f'- Step 4: Should any submodule be analyzed in more detail before a final decision can be made?(Note: only the instantiated submodule within this module can be analyzed)\n'
        f'Dont try to improvise or be efficient, I need you to respond ONLY in this JSON format, it is an absolute must:\n'
        f'{{\n '
        f'    "final_answer": "Yes | No | Needs more analysis",\n'
        f'    "needs_analysis": ["SubModuleA", "SubModuleB"],\n'
        f'    "reasoning_and_notes": [\n'
        f'        "Step 1...",\n'
        f'        "Step 2..."\n'
        f'    ]\n'
        f'}}\n'
    )

    prompt = prompt + task

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


def check_spec_recursive (module_response, llm, chat_history, spec_text):
    prompt = create_module_prompt(module_response=module_response, spec_text=spec_text)
    # print('Prompt:', prompt)
    # print("spec_text: ", spec_text)
    chat_history.append(HumanMessage(content=prompt))
    response = llm(chat_history)
    chat_history.append(AIMessage(content=response.content))
    # print('Prompt: ', prompt)
    # print('Response:', response.content)

    final_answer, needs_analysis, reasoning, error = extract_llm_response_fields_json(response.content)
    # print("\n module name: ", module_response.module_name, final_answer, needs_analysis, reasoning)
    if error:
        return response.content, chat_history
    # while error:
    #     input("Press Enter to continue to the next iteration (or Ctrl+C to stop)...")
    #     prompt = f'Respond ONLY in this JSON format. I will determine coverage and accuracy later so answer in following json. Do not add any extra explanation or commentary.:\n'
    #     f'{{\n '
    #     f'    "final_answer": "Yes | No | Needs more analysis",\n'
    #     f'    "needs_analysis": ["SubModuleA", "SubModuleB"],\n'
    #     f'    "reasoning_and_notes": [\n'
    #     f'        "Step 1...",\n'
    #     f'        "Step 2..."\n'
    #     f'    ]\n'
    #     f'}}\n'

    #     chat_history.append(HumanMessage(content=prompt))
    #     response = llm(chat_history)
    #     chat_history.append(AIMessage(content=response.content))
    #     print('Prompt: ', prompt)
    #     print('Response:', response.content)
    #     final_answer, needs_analysis, reasoning, error = extract_llm_response_fields_json(response.content)
    
    if final_answer == 'Yes' or final_answer == 'No':
        return f'Final Answer: {final_answer}\n Needs more analysis: {needs_analysis}\n Reasoning: {reasoning}', chat_history
    else:
        temp = ''
        # for submod in module_response.submodule_GPT_Response.values():
            # print("I am in else branch", submod.module_name)
        for submod_name in needs_analysis:
            # print(submod_name)
            submod_resp = get_submodule_response(module_response.submodule_GPT_Response, submod_name)
            if submod_resp is None:
                raise KeyError(f"{submod_name} not found in any nested submodule_GPT_Response")

            subdmod_response, chat_history = check_spec_recursive(submod_resp, llm, chat_history, spec_text)


            # subdmod_response, chat_history = check_spec_recursive(module_response.submodule_GPT_Response[submod_name], llm, chat_history, spec_text)
            # # submod_final_answer, submod_needs_analysis, submod_reasoning, submod_error = extract_llm_response_fields_json(subdmod_response.content)
            # # while submod_error:
            # #     print(submod_error)
            # #     return None
            temp = temp + subdmod_response
    
        return f'Final Answer: {final_answer}\n Needs more analysis: {needs_analysis}\n Reasoning: {reasoning}'+ temp, chat_history

def check_spec(module_response, llm, chat_history, spec_text):
        
    response, chat_history = check_spec_recursive(module_response, llm, chat_history, spec_text)
    prompt = (
        f'Based on reasoning so far. Following are the previous reasonings and analysis\n'
        f'{response}\n'
        f'Does the module :{module_response.module_name} or submodule as a system covers this specification information: {spec_text} ?\n'
        f'If this information is covered then how accurate is this between 0 to 10\n'
        f'Reply in following strict JSON format:'
        f'{{\n '
        f'    "Coverage": "Yes | No\n'
        f'    "Accuracy": ""\n'
        f'    "Explaination": ""\n'
        f'}}\n'
    )

    # print(prompt)

    chat_history.append(HumanMessage(content=prompt))
    response = llm(chat_history)
    chat_history.append(AIMessage(content=response.content))

    # print(response.content)
    return response.content, chat_history

class Spec_Verification_Response:
    def __init__(self):
        self.FSM = []
        self.CSR = []
        self.OTHERS = []

# class Property_Response:
#     def __init__(self, property, property_statisfied, explaination):
#         self.property = property
#         self.property_satisfied = property_statisfied
#         self.explaination = explaination

def check_feature(module_response, llm, chat_history, spec_text):

    def extract_llm_response_fields_simple(response_text):
        try:
            response_start = response_text.find('{')
            response_end = response_text.rfind('}') + 1

            if response_start == -1 or response_end == -1:
                return None, None, None, "JSON object not found in response."

            json_text = response_text[response_start:response_end]
            parsed = json.loads(json_text)

            required_keys = {"Coverage", "Accuracy","Explaination"}
            if not required_keys.issubset(parsed):
                return None, None, "Missing one or more required fields in LLM response."

            return (
                parsed["Coverage"],
                parsed["Accuracy"],
                parsed["Explaination"],
                None
            )

        except json.JSONDecodeError as e:
            return None, None, None, f"Invalid JSON format: {e}"
        except Exception as e:
            return None, None, None, f"Unexpected error: {e}"
              
    response, chat_history = check_spec(module_response, llm, chat_history, spec_text)    
    # print(response)
    coverage, accuracy, explaination, error = extract_llm_response_fields_simple(response)

    return coverage, accuracy, explaination, chat_history, error

import json

# def build_metrics_json(coverage, accuracy, explanation):
#     result = {
#         "coverage": coverage,
#         "accuracy": accuracy,
#         "explanation": explanation
#     }
#     return json.dumps(result, indent=2)

def build_metrics_json_2(item, coverage, accuracy, explanation):
    """
    Builds a JSON entry combining spec item info and evaluation metrics.
    
    Args:
        item (dict): e.g., {'title': '...', 'description': '...'}
        coverage (float or str): Coverage metric.
        accuracy (float or str): Accuracy metric.
        explanation (str): Explanation text.
    
    Returns:
        str: JSON-formatted string with all fields.
    """
    result = {
        "title": item.get("title", ""),
        "description": item.get("description", ""),
        "coverage": coverage,
        "accuracy": accuracy,
        "explanation": explanation
    }
    return json.dumps(result, indent=2)

import json

def build_metrics_csr(item, coverage, accuracy, explanation):
    """
    Builds a JSON entry combining CSR info and evaluation metrics.
    """
    # Parse if string
    if isinstance(item, str):
        try:
            item = json.loads(item)
        except json.JSONDecodeError:
            item = {}

    result = {
        "CSR_FOUND": item.get("CSR_FOUND", ""),
        "Description": item.get("Description", ""),
        "coverage": coverage,
        "accuracy": accuracy,
        "explanation": explanation
    }
    return json.dumps(result, indent=2)


def build_metrics_fsm(item, coverage, accuracy, explanation):
    """
    Builds a JSON entry combining FSM info and evaluation metrics.
    """
    # Parse if string
    if isinstance(item, str):
        try:
            item = json.loads(item)
        except json.JSONDecodeError:
            item = {}

    result = {
        "FSM_FOUND": item.get("FSM_FOUND", ""),
        "Description": item.get("Description", ""),
        "coverage": coverage,
        "accuracy": accuracy,
        "explanation": explanation
    }
    return json.dumps(result, indent=2)


# def build_metrics_fsm(item, coverage, accuracy, explanation):
#     """
#     Builds a JSON entry combining spec item info and evaluation metrics.
    
#     Args:
#         item (dict): e.g., {'title': '...', 'description': '...'}
#         coverage (float or str): Coverage metric.
#         accuracy (float or str): Accuracy metric.
#         explanation (str): Explanation text.
    
#     Returns:
#         str: JSON-formatted string with all fields.
#     """
#     result = {
#         "title": item.get("FSM_FOUND", ""),
#         "description": item.get("Description", ""),
#         "coverage": coverage,
#         "accuracy": accuracy,
#         "explanation": explanation
#     }
#     return json.dumps(result, indent=2)

# def build_metrics_csr(item, coverage, accuracy, explanation):
#     """
#     Builds a JSON entry combining spec item info and evaluation metrics.
    
#     Args:
#         item (dict): e.g., {'title': '...', 'description': '...'}
#         coverage (float or str): Coverage metric.
#         accuracy (float or str): Accuracy metric.
#         explanation (str): Explanation text.
    
#     Returns:
#         str: JSON-formatted string with all fields.
#     """
#     result = {
#         "title": item.get("CSR_FOUND", ""),
#         "description": item.get("Description", ""),
#         "coverage": coverage,
#         "accuracy": accuracy,
#         "explanation": explanation
#     }
#     return json.dumps(result, indent=2)

if __name__ == "__main__":
    
    with open("i2c_master_top_0.pkl", "rb") as f:
        module_response = pickle.load(f)

    with open("spec_gpt_response.pkl", "rb") as f:
        spec_response = pickle.load(f)

    llm = ChatOpenAI(
        model="gpt-5"
        # response_format={"type": "json_object"}
    )

    chat_history = []
    initial_msg = 'You are a helpful assistant that checks information extrated from spec againes natural language description of verilog modules'

    chat_history = [
        SystemMessage(content = initial_msg),
    ]

    spec_verification_response = Spec_Verification_Response()

    # print(spec_response.csr_json)
    # print(spec_response.fsm_json)
    coverage, accuracy, explaination, chat_history, error  = check_feature(module_response, llm, chat_history, spec_response.csr_json)
    spec_verification_response.CSR = build_metrics_csr(spec_response.csr_json, coverage, accuracy, explaination)

    # print(spec_verification_response.CSR )
    coverage, accuracy, explaination, chat_history, error  = check_feature(module_response, llm, chat_history, spec_response.fsm_json)
    spec_verification_response.FSM = build_metrics_fsm(spec_response.fsm_json, coverage, accuracy, explaination)
    # print(spec_verification_response.FSM )
    for item in spec_response.others_json:
        # print(item)
        coverage, accuracy, explaination, chat_history, error  = check_feature(module_response, llm, chat_history, item)
        spec_verification_response.OTHERS.append( build_metrics_json_2(item, coverage, accuracy, explaination))


    file_name = f'spec_verification_response_0.pkl'
    with open(file_name, "wb") as f:
        pickle.dump(spec_verification_response, f)



    ################################################################################
    with open("i2c_master_top_1.pkl", "rb") as f:
        module_response = pickle.load(f)

    with open("spec_gpt_response.pkl", "rb") as f:
        spec_response = pickle.load(f)

    llm = ChatOpenAI(
        model="gpt-5"
        # response_format={"type": "json_object"}
    )

    chat_history = []
    initial_msg = 'You are a helpful assistant that checks information extrated from spec againes natural language description of verilog modules'

    chat_history = [
        SystemMessage(content = initial_msg),
    ]

    spec_verification_response = Spec_Verification_Response()

    coverage, accuracy, explaination, chat_history, error  = check_feature(module_response, llm, chat_history, spec_response.csr_json)
    spec_verification_response.CSR = build_metrics_csr(spec_response.csr_json, coverage, accuracy, explaination)

    coverage, accuracy, explaination, chat_history, error  = check_feature(module_response, llm, chat_history, spec_response.fsm_json)
    spec_verification_response.FSM = build_metrics_fsm(spec_response.fsm_json, coverage, accuracy, explaination)

    for item in spec_response.others_json:
        coverage, accuracy, explaination, chat_history, error  = check_feature(module_response, llm, chat_history, item)
        spec_verification_response.OTHERS.append( build_metrics_json_2(item, coverage, accuracy, explaination))


    file_name = f'spec_verification_response_1.pkl'
    with open(file_name, "wb") as f:
        pickle.dump(spec_verification_response, f)

    

    with open("i2c_master_top_2.pkl", "rb") as f:
        module_response = pickle.load(f)

    with open("spec_gpt_response.pkl", "rb") as f:
        spec_response = pickle.load(f)

    llm = ChatOpenAI(
        model="gpt-5"
        # response_format={"type": "json_object"}
    )

    chat_history = []
    initial_msg = 'You are a helpful assistant that checks information extrated from spec against natural language description of verilog modules'

    chat_history = [
        SystemMessage(content = initial_msg),
    ]

    spec_verification_response = Spec_Verification_Response()

    coverage, accuracy, explaination, chat_history, error  = check_feature(module_response, llm, chat_history, spec_response.csr_json)
    spec_verification_response.CSR = build_metrics_csr(spec_response.csr_json, coverage, accuracy, explaination)

    coverage, accuracy, explaination, chat_history, error  = check_feature(module_response, llm, chat_history, spec_response.fsm_json)
    spec_verification_response.FSM = build_metrics_fsm(spec_response.fsm_json, coverage, accuracy, explaination)

    for item in spec_response.others_json:
        coverage, accuracy, explaination, chat_history, error  = check_feature(module_response, llm, chat_history, item)
        spec_verification_response.OTHERS.append( build_metrics_json_2(item, coverage, accuracy, explaination))


    file_name = f'spec_verification_response_2.pkl'
    with open(file_name, "wb") as f:
        pickle.dump(spec_verification_response, f)

    #     title = item.get("title", "")
    #     description = item.get("description", "")

    #     print(title,": ", description, "\n")
    # coverage, accuracy, explaination, error = check_feature(module_response, llm, chat_history, spec_text)
    # print(coverage, accuracy, explaination, error)
    # print(feature_response.feature,'\n', feature_response.feature_present, '\n', feature_response.description,'\n', feature_response.explainatian)
