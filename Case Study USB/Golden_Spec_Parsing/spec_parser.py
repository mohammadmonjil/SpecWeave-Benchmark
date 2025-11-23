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
# CONFIG
# ==========================
# OPENAI_API_KEY = "your_api_key_here"
# client = OpenAI(api_key=OPENAI_API_KEY)

# Choose encoding for token counting
tokenizer = tiktoken.get_encoding("cl100k_base")

# ==========================
# STEP 1: EXTRACT TEXT
# ==========================

class Spec_GPT_Response:
    def __init__(self, spec_text, fsm_json, csr_json, others_json):
        # self.module_name = module_name
        self.spec_text = spec_text
        self.fsm_json = fsm_json
        self.csr_json = csr_json
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


def extract_text_pdf(path: str) -> str:
    text = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text()
            if txt:
                text.append(txt)
    return "\n".join(text)

def extract_text_docx(path: str) -> str:
    doc = docx.Document(path)
    text = []
    for para in doc.paragraphs:
        if para.text.strip():
            text.append(para.text)
    return "\n".join(text)

# ==========================
# STEP 2: CLEAN & NORMALIZE
# ==========================

def clean_text(text: str) -> str:
    # Remove headers/footers/page numbers heuristically
    text = re.sub(r"\n\d+\n", "\n", text)  # remove isolated page numbers
    text = re.sub(r"(\s){2,}", " ", text)  # collapse whitespace
    return text.strip()

# ==========================
# STEP 3: CHUNKING
# ==========================

def chunk_text(text: str, max_tokens: int = 272000) -> List[str]:
    words = text.split()
    chunks = []
    current_chunk = []
    current_tokens = 0

    for word in words:
        token_count = len(tokenizer.encode(word))
        if current_tokens + token_count > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_tokens = token_count
        else:
            current_chunk.append(word)
            current_tokens += token_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

# ==========================
# STEP 4: OPTIONAL EMBEDDINGS
# ==========================

def embed_chunks(chunks: List[str]) -> List[Dict]:
    results = []
    for idx, chunk in enumerate(chunks):
        emb = client.embeddings.create(
            model="text-embedding-3-large",
            input=chunk
        )
        results.append({
            "id": f"chunk_{idx}",
            "text": chunk,
            "embedding": emb.data[0].embedding
        })
    return results

# ==========================
# MAIN
# ==========================

def process_spec_file(path: str, do_embedding: bool = False, extract_images: bool = True):
    if path.endswith(".pdf"):
        raw_text = extract_text_pdf(path)
        # images = extract_images_pdf(path) if extract_images else []
    elif path.endswith(".docx") or path.endswith(".doc"):
        raw_text = extract_text_docx(path)
        # images = extract_images_docx(path) if extract_images else []
    else:
        raise ValueError("Unsupported file type")
    # print(raw_text)
    cleaned = clean_text(raw_text)
    # print("\n ***********************************************Clean Text********************************************************", cleaned)
    chunks = chunk_text(cleaned)

    print(f"Extracted {len(chunks)} chunks from {path}")

    if do_embedding:
        return embed_chunks(chunks)
    else:
        return cleaned

# ==========================
# USAGE
# ==========================

import argparse
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
import time
import json


def extract_fsm(cleaned_text: str, llm, chat_history) -> dict:

    def extract_final_answer_fields(text):
        try:
            # Try to locate the JSON object inside the response text
            response_start = text.find('{')
            response_end = text.rfind('}') + 1

            if response_start == -1 or response_end == -1:
                return None, None, "JSON object not found in response."

            json_text = text[response_start:response_end]
            parsed = json.loads(json_text)

            required_keys = {"FSM_FOUND", "Description"}
            if not required_keys.issubset(parsed):
                return None, None, "Missing one or more required fields."

            final_answer = parsed["FSM_FOUND"]
            description = parsed["Description"]

            if not all(isinstance(field, str) for field in [final_answer, description]):
                return None, None, "All fields must be strings."

            return final_answer, description, None

        except json.JSONDecodeError as e:
            return None, None, f"Invalid JSON format: {e}"
        except Exception as e:
            return None, None, f"Unexpected error: {e}"

    """
    Extract FSM description from cleaned spec text.
    Uses the provided llm and chat_history.
    Returns the full JSON plus extracted fields.
    """
    fsm_prompt = f"""
        Detect FSM description in the following specification text.
        Return strictly this JSON schema:

        {{
        "FSM_FOUND": "yes" | "no",
        "Description": ""
        }}

        Rules:
        - If no FSM is described: "FSM_FOUND": "no", "Description": "".
        - If FSM(s) are described: "FSM_FOUND": "yes", "Description": detailed description.
        - No extra keys. No comments. No markdown.

        SPECIFICATION TEXT:
        \"\"\"{cleaned_text}\"\"\"
        """.strip()

    chat_history.append(HumanMessage(content=fsm_prompt))
    response = llm.invoke(chat_history)
    chat_history.append(AIMessage(content=response.content))

    # Try parsing JSON
    fsm_found, fsm_description, error = extract_final_answer_fields(response.content)

    return response.content, error


def extract_csr(cleaned_text: str, llm, chat_history) -> dict:

    def extract_final_answer_fields(text):
        try:
            # Try to locate the JSON object inside the response text
            response_start = text.find('{')
            response_end = text.rfind('}') + 1

            if response_start == -1 or response_end == -1:
                return None, None, "JSON object not found in response."

            json_text = text[response_start:response_end]
            parsed = json.loads(json_text)

            required_keys = {"CSR_FOUND", "Description"}
            if not required_keys.issubset(parsed):
                return None, None, "Missing one or more required fields."

            final_answer = parsed["CSR_FOUND"]
            description = parsed["Description"]

            if not all(isinstance(field, str) for field in [final_answer, description]):
                return None, None, "All fields must be strings."

            return final_answer, description, None

        except json.JSONDecodeError as e:
            return None, None, f"Invalid JSON format: {e}"
        except Exception as e:
            return None, None, f"Unexpected error: {e}"

    """
    Extract FSM description from cleaned spec text.
    Uses the provided llm and chat_history.
    Returns the full JSON plus extracted fields.
    """
    csr_prompt = f"""
        Detect Control and Status Registers or any other programmable register and their detailed description in the following specification text.
        Return strictly this JSON schema:

        {{
        "CSR_FOUND": "yes" | "no",
        "Description": ""
        }}

        Rules:
        - If no CSR is described: "CSR_FOUND": "no", "Description": "".
        - If CSR(s) are described: "CSR_FOUND": "yes", "Description": detailed description.
        - No extra keys. No comments. No markdown.

        SPECIFICATION TEXT:
        \"\"\"{cleaned_text}\"\"\"
        """.strip()

    chat_history.append(HumanMessage(content=csr_prompt))
    response = llm.invoke(chat_history)
    chat_history.append(AIMessage(content=response.content))

    # Try parsing JSON
    csr_found, csr_description, error = extract_final_answer_fields(response.content)

    return response.content, error

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
        Extract all major points and their detailed descriptions from the following specification text.  
        Exclude: input/output signals, FSMs, and CSRs.  
        Focus only on high-level functional or architectural points that would have a direct mapping to RTL functionality.  
        Exclude things like frequency requirement or features, synthesis results, testbenches etc which can not be mapped to module RTL functionality.
        Return strictly in this JSON schema:
        {{
        "major_points": [
            {{"title": "...", "description": "..."}}
        ]
        }}

        SPECIFICATION TEXT:
        \"\"\"{cleaned_text}\"\"\"
        """

    chat_history.append(HumanMessage(content=major_prompt))
    response = llm.invoke(chat_history)
    chat_history.append(AIMessage(content=response.content))

    # Try parsing JSON
    major_points, error = extract_final_answer_fields(response.content)

    return major_points, error


# import base64

# def encode_image_base64(image_path: str) -> str:
#     with open(image_path, "rb") as f:
#         return base64.b64encode(f.read()).decode("utf-8")


# def build_message_with_text_and_images(cleaned_text: str, images: list):
#     content = [{"type": "text", "text": f"Here is the specification text:\n{cleaned_text}"}]

#     for img in images:
#         img_b64 = encode_image_base64(img)
#         content.append({
#             "type": "image_url",
#             "image_url": {"url": f"data:image/png;base64,{img_b64}"}
#         })

#     return HumanMessage(content=content)


from PIL import Image
import io
import base64

def encode_image_base64(img_path, max_size=(256, 256), quality=70):
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



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a spec file (PDF/DOCX).")
    parser.add_argument("spec_path", help="Path to the spec file (PDF or DOCX)")
    parser.add_argument("--embed", action="store_true",
                        help="Generate embeddings for chunks")

    args = parser.parse_args()

    cleaned_text = process_spec_file(args.spec_path)
    images = load_images_from_directory("images")
    # for img in images:
    #     print(img)
    #     webbrowser.open(img)  
    # print(cleaned_text)

    llm = ChatOpenAI(
            model="gpt-5"
            # response_format={"type": "json_object"}
        )
    chat_history = []

    # Add a common system message (applies to all extractors)
    system_msg = SystemMessage(content=(
        "You are an information extraction engine. "
        "Verbosity: Low. Always respond with JSON that matches the schema provided. "
        "Do not add extra commentary, keys, or markdown. "
    ))
    
    chat_history.append(system_msg)
    combined_spec_text = build_message_with_text_and_images(cleaned_text, images)
    # chat_history.append(combined_msg)

    # fsm_json, error  = extract_fsm(combined_spec_text, llm, chat_history)
    # print(fsm_json)
    # chat_history = []
    # chat_history.append(system_msg)
    csr_json, error  = extract_csr(combined_spec_text, llm, chat_history)
    chat_history = []
    chat_history.append(system_msg)
    major_points_json, error  = extract_major_points(combined_spec_text, llm, chat_history)

    chat_history = []
    chat_history.append(system_msg)
    fsm_json, error  = extract_fsm(combined_spec_text, llm, chat_history)

    spec_gpt_response = Spec_GPT_Response(combined_spec_text, fsm_json, csr_json, major_points_json )
    print(csr_json, major_points_json, fsm_json)
    file_name = f'spec_gpt_response.pkl'
    with open(file_name, "wb") as f:
        pickle.dump(spec_gpt_response, f)
