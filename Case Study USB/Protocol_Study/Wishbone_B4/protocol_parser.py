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
os.environ["OPENAI_API_KEY"] = ""
# ==========================
# CONFIG
# ==========================
# OPENAI_API_KEY = "your_api_key_here"
# client = OpenAI(api_key=OPENAI_API_KEY)

# Choose encoding for token counting
tokenizer = tiktoken.get_encoding("cl100k_base")

# ==========================
# STEP 1: EXTRACT TEXT
# ==========================

class Protocol_GPT_Response:
    def __init__(self, spec_text, others_json):
        # self.module_name = module_name
        self.spec_text = spec_text
        # self.fsm_json = fsm_json
        # self.csr_json = csr_json
        self.others_json = others_json

import os
from PIL import Image

def load_images_from_directory(directory="images"):
    image_files = []
    supported_exts = (".png", ".jpg", ".jpeg", ".bmp", ".gif")

    if not os.path.exists(directory):
        print(f"⚠️ Directory {directory} does not exist.")
        return []

    for file in os.listdir(directory):
        if file.lower().endswith(supported_exts):
            image_path = os.path.join(directory, file)
            image_files.append(image_path)

    return sorted(image_files)


import os
import re
import pdfplumber

# ==========================
# STEP 1: EXTRACT TEXT FROM PDF
# ==========================

def extract_text_pdf(path: str) -> str:
    text = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text()
            if txt:
                text.append(txt)
    return "\n".join(text)


# ==========================
# STEP 2: CLEAN & NORMALIZE
# ==========================

def clean_text(text: str) -> str:
    # Remove isolated page numbers and collapse whitespace
    text = re.sub(r"\n\d+\n", "\n", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


# ==========================
# STEP 3: PROCESS ALL PDF FILES IN FOLDER
# ==========================

def process_spec_files_in_folder(folder_path: str):
    cleaned_texts = []

    # Get all PDF files in folder and sort numerically
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
    pdf_files.sort(key=lambda x: int(os.path.splitext(x)[0]))  # numeric sort by filename like "1.pdf"

    for filename in pdf_files:
        file_path = os.path.join(folder_path, filename)
        print(f"📄 Processing: {filename}")

        try:
            raw_text = extract_text_pdf(file_path)
            cleaned = clean_text(raw_text)
            cleaned_texts.append(cleaned)
        except Exception as e:
            print(f"⚠️ Error processing {filename}: {e}")

    print(f"\n✅ Processed {len(cleaned_texts)} PDF files successfully.")
    return cleaned_texts


# # ==========================
# # Example Usage
# # ==========================
# if __name__ == "__main__":
#     folder_name = "specs"  # your folder name in current directory
#     folder_path = os.path.join(os.getcwd(), folder_name)
#     texts = process_spec_files_in_folder(folder_path)
#     print(f"\nTotal documents processed: {len(texts)}")

# ==========================
# USAGE
# ==========================

import argparse
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
import time
import json

def extract_major_points(cleaned_text: str, llm, chat_history) -> dict:

    def extract_final_answer_fields(text: str):
        try:
            response_start = text.find('{')
            response_end = text.rfind('}') + 1
            if response_start == -1 or response_end == -1:
                return None, "JSON object not found."

            json_text = text[response_start:response_end]
            parsed = json.loads(json_text)

            if "major_points" not in parsed:
                return None, "Missing 'major_points' field."

            return parsed["major_points"], None

        except json.JSONDecodeError as e:
            return None, f"Invalid JSON format: {e}"
        except Exception as e:
            return None, f"Unexpected error: {e}"


    major_prompt = f"""
        You are extracting relevant information from a standard protocol specification document.
        I have a natural language description of a RTL implementation.
        My ultimate target is to determine if the RTL implements the standard protocol.
        1. Does it fully comply to mandatory features of the protocol?
        2. Does it implement the optional features or which optional features does it implement.
        So Extract all major points and their descriptions from the protocol specification text so that you
        can later use them to answer the above two questions for an RTL implementation. 
        Return strictly in this JSON schema:
        {{
        "major_points": [
            {{"title": "...", "description": "..."}}
        ]
        }}

        I am providing the specification text in few chunks. Following is one chunk:
        PROTOCOL SPECIFICATION TEXT:
        \"\"\"{cleaned_text}\"\"\"
        """

    chat_history.append(HumanMessage(content=major_prompt))
    response = llm.invoke(chat_history)
    chat_history.append(AIMessage(content=response.content))

    # Try parsing JSON
    print(response.content)
    major_points, error = extract_final_answer_fields(response.content)

    return major_points, error


from PIL import Image
import io
import base64

def encode_image_base64(img_path, max_size=(512, 512), quality=70):
    """
    Compresses and encodes an image to base64.
    
    Args:
        img_path (str): Path to the image file.
        max_size (tuple): Maximum (width, height) for resizing.
        quality (int): JPEG quality (1–95). Lower = smaller file.
    """
    with Image.open(img_path) as img:
        # Convert to RGB (important if PNG has transparency)
        img = img.convert("RGB")

        # Resize while keeping aspect ratio
        img.thumbnail(max_size, Image.LANCZOS)

        # Save compressed version to memory
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)

        # Encode as base64
        return base64.b64encode(buffer.read()).decode("utf-8")

def build_message_with_text_and_images(cleaned_text: str, images: list):
    content = [{"type": "text", "text": f"Here is the specification text:\n{cleaned_text}"}]

    for img in images:
        img_b64 = encode_image_base64(img)
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
        })

    return HumanMessage(content=content)

class Protocol_GPT_Response:
    def __init__(self, protocol_name):
        self.protocol_name = protocol_name
        self.specs_json = []

if __name__ == "__main__":

    folder_name = "chapters"  # your folder name in current directory
    folder_path = os.path.join(os.getcwd(), folder_name)
    spec_texts = process_spec_files_in_folder(folder_path)
    print(f"\nTotal documents processed: {len(spec_texts)}")

    llm = ChatOpenAI(
            model="gpt-5"
            # response_format={"type": "json_object"}
        )
    
    protocol_name = 'WB_B_4'
    # Add a common system message (applies to all extractors)
    initial_msg = f'''
        You are extracting relevant information from a standard protocol specification document.
        PROTOCOL NAME = {protocol_name}.
        I have a natural language description of a RTL implementation.
        My ultimate target is to determine if the RTL implements the standard protocol.
        1. Does it fully comply to mandatory features of the protocol?
        2. Does it implement the optional features or which optional features does or does not it implements.
        So Extract all major points and their descriptions from the protocol specification text so that you
        can later use them to answer the above two questions for an RTL implementation.
        Only extracts information that can be mapped into RTL functionality (no electricl/mechanical information).
        I will provide the protocol spec texts in chunks. 
    '''
    system_msg = SystemMessage(content=initial_msg)
    protocol_gpt_response = Protocol_GPT_Response(protocol_name)

    for spec_text in spec_texts:
        chat_history = []
        chat_history.append(system_msg)
        major_points_json, error  = extract_major_points(spec_text, llm, chat_history)
        print(major_points_json)
        protocol_gpt_response.specs_json.append(major_points_json)

    
    # print(csr_json, major_points_json, fsm_json)
    file_name = f'protocol_gpt_response_{protocol_name}.pkl'
    with open(file_name, "wb") as f:
        pickle.dump(protocol_gpt_response, f)
