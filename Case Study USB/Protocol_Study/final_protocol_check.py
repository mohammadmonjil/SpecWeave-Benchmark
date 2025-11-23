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

class Protocol_Verification_Response:
    def __init__(self):
        self.FSM = []
        self.CSR = []
        self.OTHERS = []
        self.FINAL_RESPONSE = []
        self.RESPONSE = []

if __name__ == "__main__":
    # Load module and protocol responses
    
    # p1 = 'WB_B_3'
    # p2 = 'WB_B_4'
    # p  = 'WB'

    p1 = 'USB_1_0'
    p2 = 'USB_2_0'
    p  = 'USB'

    # p1 = PCI_2.2
    # p2 = PCI_3.0
    # p3 = PCI_ex_1_0
    # p = PCI
    with open(f"protocol_verification_response_{p1}.pkl", "rb") as f:
        protocol_verification_response_PCI_2_2 = pickle.load(f)

    with open(f"protocol_verification_response_{p2}.pkl", "rb") as f:
        protocol_verification_response_PCI_3_0 = pickle.load(f)

    # with open(f"protocol_verification_response_{p3}.pkl", "rb") as f:
    #     protocol_verification_response_PCI_ex_1_0 = pickle.load(f)
    # top = module_response

    prompt = (
        f'ANALYSIS WITH {p1}:'
        f'{protocol_verification_response_PCI_2_2.FINAL_RESPONSE}'
        f'ANALYSIS WITH {p2}:'
        f'{protocol_verification_response_PCI_3_0.FINAL_RESPONSE}'
        # f'ANALYSIS WITH {p3}:'
        # f'{protocol_verification_response_PCI_ex_1_0.FINAL_RESPONSE}'
    )
    
    prompt += (
        f'Now make final judgement, which protocol matches the closest for this module. Provide detailed explaination'
        f'List the mandory and optional features implemented of the  protocol'
        f'Keep as much details as possible for previous analysis of the chosen protocols as I will use them later' 
    )

    initial_msg = (
        "You are a helpful assistant that checks information extracted from a protocol "
        "specification document. You will given analysis of a RTL againts specification"
        "document of various protocols."
        "Based on the analysis, final decision is to be made"
    )

    chat_history = [
        SystemMessage(content=initial_msg),
        HumanMessage(content=prompt)
    ]

    llm = ChatOpenAI(model="gpt-5")
    response = llm(chat_history)

    PCI_verification_response = Protocol_Verification_Response()
    PCI_verification_response.FINAL_RESPONSE = response.content
    print(response.content)

    with open(f"{p}_verification_response.pkl", "wb") as f:
        pickle.dump(PCI_verification_response, f)

    # print(protocol_verification_response_PCI_2_2.FINAL_RESPONSE)
