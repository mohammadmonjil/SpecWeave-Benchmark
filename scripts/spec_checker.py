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

def check_spec(generated_spec, llm, chat_history, spec_text):
        
    prompt = (
        f'Following is a generated spec of a RTl:\n'
        f'{generated_spec}\n'
        f'Does the generated spec covers this specification(ground truth) information: {spec_text} ?\n'
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




def check_feature(generated_spec, llm, chat_history, spec_text):

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
              
    response, chat_history = check_spec(generated_spec, llm, chat_history, spec_text)    
    # print(response)
    coverage, accuracy, explaination, error = extract_llm_response_fields_simple(response)

    return coverage, accuracy, explaination, chat_history, error

import json


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


def read_spec_text(file_path="generated_spec_doc.txt"):
    """
    Reads the generated specification text file and returns its content as a string.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"📖 Successfully read spec file: {file_path}\n")
        return content
    except FileNotFoundError:
        print(f"❌ Error: File '{file_path}' not found.")
        return ""
    except Exception as e:
        print(f"⚠️ Error reading file '{file_path}': {e}")
        return ""

if __name__ == "__main__":
    

    generated_spec = read_spec_text()

    with open("spec_gpt_response.pkl", "rb") as f:
        spec_response = pickle.load(f)

    llm = ChatOpenAI(
        model="gpt-5"
        # response_format={"type": "json_object"}
    )

    chat_history = []
    initial_msg = 'You are a helpful assistant that checks information extrated from specification document against specification generated from the RTL'

    chat_history = [
        SystemMessage(content = initial_msg),
    ]

    spec_verification_response = Spec_Verification_Response()

    # coverage, accuracy, explaination, chat_history, error  = check_feature(generated_spec, llm, chat_history, spec_response.csr_json)
    # spec_verification_response.CSR = build_metrics_csr(spec_response.csr_json, coverage, accuracy, explaination)

    chat_history = [
        SystemMessage(content = initial_msg),
    ]

    coverage, accuracy, explaination, chat_history, error  = check_feature(generated_spec, llm, chat_history, spec_response.fsm_json)
    spec_verification_response.FSM = build_metrics_fsm(spec_response.fsm_json, coverage, accuracy, explaination)

    for item in spec_response.others_json:
        print("Huh")
        chat_history = [
        SystemMessage(content = initial_msg),
        ]
        coverage, accuracy, explaination, chat_history, error  = check_feature(generated_spec, llm, chat_history, item)
        spec_verification_response.OTHERS.append( build_metrics_json_2(item, coverage, accuracy, explaination))


    file_name = f'spec_verification_response.pkl'
    with open(file_name, "wb") as f:
        pickle.dump(spec_verification_response, f)
