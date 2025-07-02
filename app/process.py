import pdfplumber
import pandas as pd
from io import BytesIO
from copy import deepcopy

FINAL_HEADER = [
    "PABN No.", "Series No.", "Member PIN", "Patient Name", "Health Care Professional",
    "Confinement Period",
    "Caserate1_Code", "Caserate1_Gross",
    "Caserate2_Code", "Caserate2_Gross",
    "Others_Code", "Others_Gross",
    "Total_Gross", "Total_WTax", "Total_HCI", "Total_PF"
]

def is_header_row(row):
    header_keywords = ["PABN No.", "Series No.", "Member PIN", "Patient Name", "Confinement Period"]
    subheader_keywords = ["Code", "Gross", "WTax", "HCI", "PF"]
    if any(cell and any(k in cell for k in header_keywords) for cell in row[:6]):
        return True
    if all(cell and any(k in cell for k in subheader_keywords) for cell in row if cell):
        return True
    return False

def process_pdf(file_bytes: bytes) -> tuple:
    data_rows = []

    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            table = page.extract_table()
            if not table:
                continue
            rows = table[1:] if i == 0 else table
            j = 0
            while j < len(rows):
                base_row = rows[j]
                if is_header_row(base_row):
                    j += 1
                    continue
                if j + 1 < len(rows) and "Health Care Professional/s:" in (rows[j + 1][0] or ""):
                    physician_line = rows[j + 1][0]
                    raw_text = physician_line.split("Health Care Professional/s:")[-1].strip()
                    physicians = [p.strip() for p in raw_text.split(";") if p.strip()]
                    for p in physicians:
                        new_row = deepcopy(base_row)
                        new_row.insert(4, p)
                        data_rows.append(new_row)
                    j += 2
                else:
                    new_row = deepcopy(base_row)
                    new_row.insert(4, "")
                    data_rows.append(new_row)
                    j += 1

    clean_data = [r for r in data_rows if len(r) == len(FINAL_HEADER)]
    if not clean_data:
        raise ValueError("No valid rows extracted.")
    df = pd.DataFrame(clean_data, columns=FINAL_HEADER)
    df = df.ffill(axis=0)

    excel_output = BytesIO()
    with pd.ExcelWriter(excel_output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    excel_output.seek(0)

    json_data = df.to_dict(orient="records")
    return json_data, excel_output