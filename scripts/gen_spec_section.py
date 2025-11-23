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
import pickle
from class_def import*
os.environ["OPENAI_API_KEY"] = ""

    

def gen_spec_subsection_recursive (module_response, llm, chat_history, section_text):

    def create_module_spec__subsection_prompt (module_response, section_text):

        prompt = (
            f'You are analyzing a Verilog module named `{module_response.module_name}` and its submodules to determine subsections list for a particular section for a specification document:\n'
            f'SPECIFICATION FIELD: "{section_text}" '
            f'For this module, long description is given'
            f'For its submodule, only high-level summary is given\n'
            f'### MODULE: {module_response.module_name}\n'
            f'long description: {module_response.long_description}\n'
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
            f'Step-by-step, reason and take notes for this module. We will traverse through its submodules and take notes for them as well\n'
            f'The target is to combine all the reasoning and notes to create the complete subsection list for the original top level\n'
            f'Respond ONLY in this JSON format. Do not add any extra explanation or commentary.:\n'
            f'{{\n '
            f'    "NOTES": ""'
            f'    "REASONING": [\n'
            f'        "Step 1...",\n'
            f'        "Step 2..."\n'
            f'    ]\n'
            f'}}\n'
        )

        prompt = prompt + task

        return prompt


    def extract_llm_response_fields_spec_section_json(response_text):
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

            required_keys = {"NOTES", "REASONING"}
            if not required_keys.issubset(parsed):
                return None, None, None, "Missing one or more required fields in LLM response."

            return parsed["NOTES"], parsed["REASONING"], None

        except json.JSONDecodeError as e:
            return None, None, f"Invalid JSON format: {e}"
        except Exception as e:
            return None, None, f"Unexpected error: {e}"
    
    prompt = create_module_spec__subsection_prompt(module_response=module_response, section_text=section_text)
    print('Prompt:', prompt)
    chat_history.append(HumanMessage(content=prompt))
    response = llm(chat_history)
    chat_history.append(AIMessage(content=response.content))
    print('Response:', response.content)
    Notes, reasoning, error = extract_llm_response_fields_spec_section_json(response.content)
    # print(error)
    while error:
        print(error)
        return None
    
    temp = ''
    for submod in module_response.submodule_GPT_Response.values():
        print(submod.module_name)
        subdmod_response, chat_history = gen_spec_subsection_recursive(submod, llm, chat_history, section_text)
        temp = temp + subdmod_response

    return f'NOTES: {Notes}\n REASONING: {reasoning}'+ temp, chat_history

def gen_spec_subsection(module_response, llm, chat_history, section_text):

    def extract_llm_response_fields_simple(response_text):
        try:
            response_start = response_text.find('{')
            response_end = response_text.rfind('}') + 1

            if response_start == -1 or response_end == -1:
                return None, None, None, "JSON object not found in response."

            json_text = response_text[response_start:response_end]
            parsed = json.loads(json_text)

            required_keys = {"Subsection_List"}
            if not required_keys.issubset(parsed):
                return None, "Missing one or more required fields in LLM response."

            return (
                parsed["Subsection_List"],
                None
            )

        except json.JSONDecodeError as e:
            return None, None, None, f"Invalid JSON format: {e}"
        except Exception as e:
            return None, None, None, f"Unexpected error: {e}"


    response, chat_history = gen_spec_subsection_recursive(module_response, llm, chat_history, section_text)
    

    prompt = (
        f"Based on the reasoning and analysis provided below, identify the most relevant subsections "
        f"that should appear under each specification section of an RTL IP core document.\n\n"
        f"Previous reasoning and analysis:\n{response}\n\n"
        f"Target sections:\n{section_text}\n\n"
        f"For each section, generate a concise and complete list of subsection titles that are typically "
        f"included in RTL IP core specifications (e.g., architecture, interfaces, timing, configuration registers, etc.). "
        f"Do not include explanations or numbering.\n\n"
        f"Reply strictly in the following JSON format (no markdown, no comments):\n"
        f"{{\n"
        f'    "Subsections": {{\n'
        f'        "SectionName1": ["SubsectionA", "SubsectionB", "SubsectionC"],\n'
        f'        "SectionName2": ["SubsectionA", "SubsectionB", "SubsectionC"]\n'
        f'    }}\n'
        f"}}"
    )


    
    print(prompt)

    chat_history.append(HumanMessage(content=prompt))
    response = llm(chat_history)
    chat_history.append(AIMessage(content=response.content))

    # Subsection_List, error = extract_llm_response_fields_simple(response.content)

    return response.content, chat_history



import sys
from class_def import*

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python script.py <top_module_name>")
        sys.exit(1)

    top_module_name = sys.argv[1]
    file_name = f'{top_module_name}.pkl'

    with open(file_name, "rb") as f:
        module_response = pickle.load(f)

    top = module_response

#####################################################################################################################################
#######################The following Lines needed to include results from protocol compliance study###################################
#####################################################################################################################################

    # with open("USB_verification_response.pkl", "rb") as f:
    #     USB_verification_response = pickle.load(f)
    # with open("WB_verification_response.pkl", "rb") as f:
    #     wb_verification_response = pickle.load(f)

    # top.protocols = []
    # top.protocols.append(USB_verification_response.FINAL_RESPONSE)
    # top.protocols.append(wb_verification_response.FINAL_RESPONSE)

#####################################################################################################################################
#######################Tprotocol compliance study Portion End                                    ###################################
#####################################################################################################################################


    llm = ChatOpenAI(model="gpt-5")
    initial_msg = 'You are a helpful assistant that can generate specification fields from summary of verilog code top module or instantiated modules.'

    chat_history = [
        SystemMessage(content = initial_msg),
    ]

 
 
#####################################################################################################################################
#######################Major Section List of the Specification Start###################################
#####################################################################################################################################
 
    feature  = '''
{
  "sections": [
    "Introduction",
    "Architecture",
    "Operation",
    "Register Map",
    "Interface Specifications",
    "Parameterization and Configuration",
    "Module Hierarchy and Integration Notes",
  ]
}
'''

#####################################################################################################################################
####################### Major Section List of the Specification End ###################################
#####################################################################################################################################

    Subsection_List, chat_history = gen_spec_subsection(module_response, llm, chat_history, feature)

    output_filename = f"{top_module_name}_subsections.json"

    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(Subsection_List, f, indent=4, ensure_ascii=False)