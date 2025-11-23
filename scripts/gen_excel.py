import pickle
import json
import pandas as pd
import numpy as np
from class_def import*


def parse_json_entry(entry):
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

def parse_json_entry_csr(entry):
    if isinstance(entry, str):
        try:
            entry = json.loads(entry)
        except json.JSONDecodeError:
            return {"title": "", "description": "", "coverage": "", "accuracy": "", "explanation": ""}
    return {
        "title": entry.get("CSR_FOUND", ""),
        "description": entry.get("Description", ""),
        "coverage": entry.get("coverage", ""),
        "accuracy": entry.get("accuracy", ""),
        "explanation": entry.get("explanation", "")
    }

def parse_json_entry_fsm(entry):
    if isinstance(entry, str):
        try:
            entry = json.loads(entry)
        except json.JSONDecodeError:
            return {"title": "", "description": "", "coverage": "", "accuracy": "", "explanation": ""}
    return {
        "title": entry.get("FSM_FOUND", ""),
        "description": entry.get("Description", ""),
        "coverage": entry.get("coverage", ""),
        "accuracy": entry.get("accuracy", ""),
        "explanation": entry.get("explanation", "")
    }


# def create_excel_from_pickle(pickle_file, excel_file):
#     # Load pickle
#     with open(pickle_file, "rb") as f:
#         spec_verification_response = pickle.load(f)

#     rows = []

#     # CSR
#     if spec_verification_response.CSR:
#         csr_entry = parse_json_entry_csr(spec_verification_response.CSR)
#         csr_entry["section"] = "CSR"
#         rows.append(csr_entry)

#     # FSM
#     if spec_verification_response.FSM:
#         fsm_entry = parse_json_entry_fsm(spec_verification_response.FSM)
#         fsm_entry["section"] = "FSM"
#         rows.append(fsm_entry)

#     # OTHERS
#     for item in spec_verification_response.OTHERS:
#         item_entry = parse_json_entry(item)
#         item_entry["section"] = "OTHERS"
#         rows.append(item_entry)

#     # DataFrame
#     df = pd.DataFrame(rows, columns=["section", "title", "description", "coverage", "accuracy", "explanation"])

#     # Convert numeric-like strings in accuracy to floats (if needed)
#     df["accuracy"] = pd.to_numeric(df["accuracy"], errors="coerce")

#     # --- Add coverage_2 ---
#     coverage_2_values = []
#     for _, row in df.iterrows():
#         section = row["section"]
#         title = str(row["title"]).strip()
#         coverage = str(row["coverage"]).strip()

#         if section in ["FSM", "CSR"]:
#             if title.lower() == "yes" and coverage.lower() == "yes":
#                 coverage_2_values.append(1)
#             elif title.lower() == "yes" and coverage.lower() == "no":
#                 coverage_2_values.append(0)
#             elif title.lower() == "no":
#                 coverage_2_values.append(-1)
#             else:
#                 coverage_2_values.append(0)
#         else:
#             coverage_2_values.append(1 if coverage.lower() == "yes" else 0)

#     df["coverage_2"] = coverage_2_values

#     # --- Add metric column (coverage_2 * accuracy) ---
#     df["metric"] = df["coverage_2"] * df["accuracy"]

#     # --- Compute summary row ---
#     avg_cov2 = df.loc[df["coverage_2"] > -1, "coverage_2"].mean()
#     avg_acc = df.loc[df["accuracy"] > 0, "accuracy"].mean()
#     avg_metric = df.loc[df["coverage_2"] > -1, "metric"].mean()

#     # --- Append summary row ---
#     summary_row = {
#         "section": "AVERAGE",
#         "title": "",
#         "description": "",
#         "coverage": "",
#         "coverage_2": avg_cov2,
#         "accuracy": avg_acc,
#         "metric": avg_metric,
#         "explanation": ""
#     }
#     df = pd.concat([df, pd.DataFrame([summary_row])], ignore_index=True)

#     # --- Reorder columns ---
#     df = df[["section", "title", "description", "coverage", "coverage_2", "accuracy", "metric", "explanation"]]

#     # --- Save to Excel ---
#     df.to_excel(excel_file, index=False)
#     print(f"✅ Excel file created: {excel_file}")

def create_excel_from_spec_verification_response(pickle_file, excel_file):
    # Load pickle
    with open(pickle_file, "rb") as f:
        spec_verification_response = pickle.load(f)

    rows = []

    # CSR
    if spec_verification_response.CSR:
        csr_entry = parse_json_entry_csr(spec_verification_response.CSR)
        csr_entry["section"] = "CSR"
        rows.append(csr_entry)

    # FSM
    if spec_verification_response.FSM:
        fsm_entry = parse_json_entry_fsm(spec_verification_response.FSM)
        fsm_entry["section"] = "FSM"
        rows.append(fsm_entry)

    # OTHERS
    for item in spec_verification_response.OTHERS:
        item_entry = parse_json_entry(item)
        item_entry["section"] = "OTHERS"
        rows.append(item_entry)

    # DataFrame
    df = pd.DataFrame(rows, columns=["section", "title", "description", "coverage", "accuracy", "explanation"])

    # Convert numeric-like strings in accuracy to floats (if needed)
    df["accuracy"] = pd.to_numeric(df["accuracy"], errors="coerce")

    # --- Add coverage_2 ---
    coverage_2_values = []
    for _, row in df.iterrows():
        section = row["section"]
        title = str(row["title"]).strip()
        coverage = str(row["coverage"]).strip()

        if section in ["FSM", "CSR"]:
            if title.lower() == "yes" and coverage.lower() == "yes":
                coverage_2_values.append(1)
            elif title.lower() == "yes" and coverage.lower() == "no":
                coverage_2_values.append(0)
            elif title.lower() == "no":
                coverage_2_values.append(-1)
            else:
                coverage_2_values.append(0)
        else:
            coverage_2_values.append(1 if coverage.lower() == "yes" else 0)

    df["coverage_2"] = coverage_2_values

    # --- Add metric column (coverage_2 * accuracy) ---
    df["metric"] = df["coverage_2"] * df["accuracy"]

    # --- Compute summary row ---
    avg_cov2 = df.loc[df["coverage_2"] > -1, "coverage_2"].mean()
    avg_acc = df.loc[df["accuracy"] > 0, "accuracy"].mean()
    avg_metric = df.loc[df["coverage_2"] > -1, "metric"].mean()

    # --- Append summary row ---
    summary_row = {
        "section": "AVERAGE",
        "title": "",
        "description": "",
        "coverage": "",
        "coverage_2": avg_cov2,
        "accuracy": avg_acc,
        "metric": avg_metric,
        "explanation": ""
    }
    df = pd.concat([df, pd.DataFrame([summary_row])], ignore_index=True)

    # --- Reorder columns ---
    df = df[["section", "title", "description", "coverage", "coverage_2", "accuracy", "metric", "explanation"]]

    # --- Save to Excel ---
    df.to_excel(excel_file, index=False)
    print(f"✅ Excel file created: {excel_file}")


def main():
    pickle_file = "spec_verification_response.pkl"
    excel_file = "spec_verification_summary.xlsx"
    create_excel_from_spec_verification_response(pickle_file, excel_file)


if __name__ == "__main__":
    main()
