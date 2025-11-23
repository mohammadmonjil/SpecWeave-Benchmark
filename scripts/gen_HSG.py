from pyverilog.vparser.parser import parse
from pyverilog.vparser.ast import ModuleDef, Decl, Always, InstanceList
import openai
import os
import sys
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
codegen = ASTCodeGenerator()

import re

import pickle
from cdfg import*
import os
os.environ["OPENAI_API_KEY"] = ""
from langchain_openai import ChatOpenAI
import time 

from langchain.schema import SystemMessage, HumanMessage, AIMessage

import time
from openai import RateLimitError
# from langchain.schema import HumanMessage, AIMessage
from class_def import*


def clean_encoding(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    # decode with fallback and re-encode to UTF-8
    cleaned = data.decode('utf-8', errors='ignore')
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(cleaned)


def parse_mod_2(file_path, module_name, llm, chat_history, config):
    filename = f"{module_name}.v"
    filename = os.path.join(file_path, filename)

    if not os.path.isfile(filename):
        print(f" File not found: {filename}")
        return None
    
    clean_encoding(filename)
    print(f" Parsing: {filename}")

    # Parse the file
    try:
        ast, _ = parse([filename], preprocess_include=[file_path],   # where include files live
                                 preprocess_define=[])
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
        return None

    # Read full verilog code
    with open(filename, "r") as f:
        verilog_code = f.read()
    
    verilog_code = resolve_verilog_includes(verilog_code = verilog_code, base_dir=file_path)
    # Track if this file has any module instantiations
    has_instantiations = False
    instantiated_modules = []

    def visit(node):
        nonlocal has_instantiations
        if isinstance(node, InstanceList):
            has_instantiations = True
            instantiated_modules.append(node.module)
        for c in node.children():
            visit(c)
    
    visit(ast)
    
   # print(instantiated_modules)
    # Initialize
    module_response = Module_GPT_Response(module_name)
    
    cfg, dfg = create_cdfg(filename, include= [file_path])
    module_response.cfg = cfg
    module_response.dfg = dfg

    #make recursive calls to submodules
    if has_instantiations:
        
        for sub_module_name in instantiated_modules:
            print(f"Going inside {sub_module_name} \n")
            response, _ , chat_history = parse_mod_2(file_path, sub_module_name, llm, chat_history, config)
            # module_response.submodule_GPT_Response.append(response)
            module_response.submodule_GPT_Response[sub_module_name] = response


    
    module_response, chat_history = get_summary(module_response, verilog_code, llm, chat_history, config)
    module_response.verilog_code = verilog_code
    # 1️⃣ Send system instruction first


    return module_response, llm, chat_history

def get_summary(module_response, verilog_code, llm, chat_history, config):

    def generate_submodule_summary(module: Module_GPT_Response, level=1):
        """
        Generate summaries for each submodule of a module, including:
        - summary_text
        - long_description
        - CFG and DFG
        - summaries of the instantiated submodules within each submodule (non-recursive)
        """
        result = []
        indent = "    " * (level - 1)

        for submod in module.submodule_GPT_Response.values():
            result.append(f"{indent}=== Level {level} Submodule: {submod.module_name} ===")

            # Summary
            # if submod.summary_text:
            #     result.append(f"{indent}Summary:")
            #     for line in submod.summary_text:
            #         result.append(f"{indent}- {line.strip()}")

            # Long Description
            if submod.long_description:
                result.append(f"{indent}Long Description:")
                for line in submod.long_description:
                    result.append(f"{indent}- {line.strip()}")

            # Control Flow Graph (CFG)
            if submod.cfg:
                result.append(f"{indent}Control Flow Graph (CFG):")
                for line in submod.cfg:
                    result.append(f"{indent}- {line.strip()}")

            # Data Flow Graph (DFG)
            if submod.dfg:
                result.append(f"{indent}Data Flow Graph (DFG):")
                for line in submod.dfg:
                    result.append(f"{indent}- {line.strip()}")

            # Summaries of directly instantiated submodules inside this submodule
            # if submod.submodule_GPT_Response:
            #     result.append(f"{indent}Instantiated Submodules inside {submod.module_name}:")
            #     for inner_submod in submod.submodule_GPT_Response.values():
            #         result.append(f"{indent}  - {inner_submod.module_name}:")
            #         if inner_submod.summary_text:
            #             for line in inner_submod.summary_text:
            #                 result.append(f"{indent}    • {line.strip()}")

        return result


    submodule_summaries = generate_submodule_summary(module_response)

    
    initial_msg = 'You are a helpful assistant that explains verilog code'

    chat_history = [
        SystemMessage(content = initial_msg),
    ]

    code_prompt = f'Following is a verilog module:\n {verilog_code}'
    if config == 'CDFG':
        code_prompt += f'Control-flow graph of the module: {module_response.cfg}\nData-flow graph of the module: {module_response.dfg}'
    
    code_prompt += f'\nFollowing are descriptions of its submodules:\n{submodule_summaries}\n'

    long_description_prompt = f'{code_prompt}\n Given the above desribe its functionality in details. Be comprehensive but dont be verbose'

    chat_history.append(HumanMessage(content=long_description_prompt))

    response = llm.invoke(chat_history)
    print(response.content)
    module_response.long_description = response.content
    chat_history.append(AIMessage(content=response.content))

    chat_history = [
        SystemMessage(content = initial_msg),
    ]

    highlevel_function_prompt = f'{code_prompt}\n Given the above desribe its high level functionality in few sentences only.'
    chat_history.append(HumanMessage(content=highlevel_function_prompt))
    response = llm.invoke(chat_history)
    print(response.content)
    module_response.summary_text = response.content
    chat_history.append(AIMessage(content=response.content))
    # time.sleep(60)


    chat_history = [
        SystemMessage(content = initial_msg),
    ]
    FSM_prompt = f'{code_prompt}\n Given the above desribe its Finite State Machines if there is any'
    chat_history.append(HumanMessage(content=FSM_prompt))
    response = llm.invoke(chat_history)
    print(response.content)
    module_response.FSM = response.content
    chat_history.append(AIMessage(content=response.content))
    # time.sleep(60)


    chat_history = [
        SystemMessage(content = initial_msg),
    ]
    CSR_prompt = f'{code_prompt}\n Given the above desribe its Control and Status Registers or any other programmable registers if there is any'
    chat_history.append(HumanMessage(content=CSR_prompt))
    response = llm.invoke(chat_history)
    print(response.content)
    module_response.CSR = response.content
    chat_history.append(AIMessage(content=response.content))

    return module_response, chat_history


def resolve_verilog_includes(verilog_code, base_dir="", include_dirs=None, visited=None):
    if include_dirs is None:
        include_dirs = []
    if visited is None:
        visited = set()

    def find_include_path(filename):
        paths_to_try = [os.path.join(base_dir, filename)] + [os.path.join(d, filename) for d in include_dirs]
        # print(f"[DEBUG] Looking for '{filename}' in:")
        for p in paths_to_try:
            # print("   ", os.path.abspath(p), "✅" if os.path.isfile(p) else "❌")
            if os.path.isfile(p):
                return p
        return None

    def replace_include(match):
        include_file = match.group(1)
        include_path = find_include_path(include_file)
        if not include_path or include_path in visited:
            return f"// Failed to include {include_file}\n"

        visited.add(include_path)
        with open(include_path, "r") as f:
            included_code = f.read()

        resolved_code = resolve_verilog_includes(included_code, os.path.dirname(include_path), include_dirs, visited)
        return resolved_code

    pattern = re.compile(r'`include\s+"([^"]+)"')
    return pattern.sub(replace_include, verilog_code)


if __name__ == "__main__":

 

    if len(sys.argv) != 2:
        print("Usage: python script.py <top_module_name>")
        sys.exit(1)

    top_module_name = sys.argv[1]
    # llm = ChatOpenAI(model="gpt-4o", temperature=0)

    x = 0
    
    llm = ChatOpenAI(model="gpt-5")
    initial_msg = 'You are a helpful assistant that explains verilog code'

    chat_history = [
        SystemMessage(content = initial_msg),
    ]
    
    config = 'CDFG'
    module_response ,_, chat_history = parse_mod_2(top_module_name, llm, chat_history,config)
    # print_module_contents(module_response)
    
    file_name = f'{top_module_name}.pkl'
    with open(file_name, "wb") as f:
        pickle.dump(module_response, f)



    
    # x = 2

    # # llm = ChatOpenAI(model="gpt-4o", temperature=0)
    # llm = ChatOpenAI(model="gpt-5")
    # initial_msg = 'You are a helpful assistant that explains verilog code'

    # chat_history = [
    #     SystemMessage(content = initial_msg),
    # ]
    
    # module_response ,_, chat_history = parse_mod_2(top_module_name, llm, chat_history)
    # print_module_contents(module_response)
    
    # file_name = f'{top_module_name}_{x}.pkl'
    # with open(file_name, "wb") as f:
    #     pickle.dump(module_response, f)


    # x = 1

    # # llm = ChatOpenAI(model="gpt-4o", temperature=0)
    # llm = ChatOpenAI(model="gpt-5")
    # initial_msg = 'You are a helpful assistant that explains verilog code'

    # chat_history = [
    #     SystemMessage(content = initial_msg),
    # ]
    
    # module_response ,_, chat_history = parse_mod_2(top_module_name, llm, chat_history)
    # print_module_contents(module_response)
    
    # file_name = f'{top_module_name}_{x}.pkl'
    # with open(file_name, "wb") as f:
    #     pickle.dump(module_response, f)
