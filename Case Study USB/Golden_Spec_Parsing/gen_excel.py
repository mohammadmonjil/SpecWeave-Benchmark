import pickle
import json
import pandas as pd

class Spec_Verification_Response:
    def __init__(self):
        self.FSM = []
        self.CSR = []
        self.OTHERS = []


def parse_json_entry(entry):
    """
    Safely parse JSON-formatted strings or dicts into a consistent dictionary structure.
    """
    if isinstance(entry, str):
        try:
            entry = json.loads(entry)
        except json.JSONDecodeError:
            return {"title": "", "description": "", "coverage": "", "accuracy": "", "explanation": ""}
    return {
        "title": entry.get("title", ""),
        "description": entry.get("description", ""),
        "coverage": entry.get("coverage", ""),
        "accuracy": entry.get("accuracy", ""),
        "explanation": entry.get("explanation", "")
    }


def create_excel_from_pickle(pickle_file, excel_file):
    """
    Loads the Spec_Verification_Response object from a pickle file and creates an Excel summary.
    """
    # Load pickle
    with open(pickle_file, "rb") as f:
        spec_verification_response = pickle.load(f)

    rows = []

    # CSR section
    if spec_verification_response.CSR:
        csr_entry = parse_json_entry(spec_verification_response.CSR)
        csr_entry["section"] = "CSR"
        rows.append(csr_entry)

    # FSM section
    if spec_verification_response.FSM:
        fsm_entry = parse_json_entry(spec_verification_response.FSM)
        fsm_entry["section"] = "FSM"
        rows.append(fsm_entry)

    # OTHERS section
    for item in spec_verification_response.OTHERS:
        item_entry = parse_json_entry(item)
        item_entry["section"] = "OTHERS"
        rows.append(item_entry)

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=["section", "title", "description", "coverage", "accuracy", "explanation"])

    # Save to Excel
    df.to_excel(excel_file, index=False)
    print(f"✅ Excel file created: {excel_file}")


def main():
    pickle_file = "spec_verification_response_0.pkl"
    excel_file = "spec_verification_summary_0.xlsx"
    create_excel_from_pickle(pickle_file, excel_file)

    pickle_file = "spec_verification_response_1.pkl"
    excel_file = "spec_verification_summary_1.xlsx"
    create_excel_from_pickle(pickle_file, excel_file)

    pickle_file = "spec_verification_response_2.pkl"
    excel_file = "spec_verification_summary_2.xlsx"
    create_excel_from_pickle(pickle_file, excel_file)



if __name__ == "__main__":
    main()
