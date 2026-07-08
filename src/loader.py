import pandas as pd

# Each entry maps a workbook sheet name to how its columns map onto the
# common normalized schema used by the rest of the pipeline (filterer.py,
# main.py). Add a new sheet here to onboard a new product/client list.
#
# "details" is an ordered list of (label, source_column) pairs rendered as
# extra info lines in the reminder email — sheets can have as many as they need.
#
# A sheet may contain multiple stacked mini-tables that each repeat the same
# header row (e.g. PSP-FORTI has separate blocks per site). The loader finds
# every occurrence of the header row and treats each as its own block.
SHEET_CONFIGS = {
    "clients": {
        "product": "Antivirus",
        "columns": {
            "company": "INDIVIDUAL/COMPANY",
            "contact": "OFFICER NAME/NAME",
            "email": "EMAIL",
            "cust_email": "CUST EMAIL",
            "phone": "NO TEL",
            "expired_date": "EXPIRED DATE",
        },
        "details": [("PC / SVR", "PC / SVR")],
    },
    "Sangfor": {
        "product": "VMware (Sangfor)",
        "columns": {
            "company": "COMPANY NAME",
            "contact": "PERSON IN CHARGE",
            "email": "EMAIL",
            "phone": "PHONE NO",
            "expired_date": "END DATE",
        },
        "details": [("Quantity", "QUANTITY")],
    },
    "PSP-FORTI": {
        "product": "Fortinet (PSP)",
        "columns": {
            "company": "COMPANY NAME",
            "contact": "PERSON IN CHARGE",
            "email": "EMAIL",
            "phone": "PHONE NO",
            "expired_date": "END DATE",
        },
        "details": [("Quantity", "QUANTITY"), ("S/N", "S/N"), ("Remarks", "REMARKS")],
    },
    "PLAN SELANGOR-FORTI": {
        "product": "Fortinet (PLAN Selangor)",
        "columns": {
            "company": "COMPANY NAME",
            "contact": "PERSON IN CHARGE",
            "email": "EMAIL",
            "phone": "PHONE NO",
            "expired_date": "END DATE",
        },
        "details": [("Quantity", "QUANTITY"), ("S/N", "S/N"), ("Remarks", "REMARKS")],
    },
    "MD MERSING-FORTI": {
        "product": "Fortinet (MD Mersing)",
        "columns": {
            "company": "COMPANY NAME",
            "contact": "PERSON IN CHARGE",
            "email": "EMAIL",
            "phone": "PHONE NO",
            "expired_date": "END DATE",
        },
        "details": [("Quantity", "QUANTITY"), ("S/N", "S/N"), ("Remarks", "REMARKS")],
    },
    "MP JASIN-FORTI": {
        "product": "Fortinet (MP Jasin)",
        "columns": {
            "company": "COMPANY NAME",
            "contact": "PERSON IN CHARGE",
            "email": "EMAIL",
            "phone": "PHONE NO",
            "expired_date": "END DATE",
        },
        "details": [("Quantity", "QUANTITY"), ("S/N", "S/N"), ("Remarks", "REMARKS")],
    },
}

# Normalized columns every row in the combined DataFrame will have.
NORMALIZED_COLS = ["company", "contact", "email", "cust_email", "phone", "expired_date"]


def _find_header_rows(raw: pd.DataFrame, marker: str) -> list:
    rows = []
    for i, row in raw.iterrows():
        values = [str(v).strip() for v in row.tolist()]
        if marker in values:
            rows.append(i)
    return rows


def _load_sheet(xls: pd.ExcelFile, sheet_name: str, config: dict) -> pd.DataFrame:
    columns = config["columns"]
    detail_specs = config.get("details", [])
    marker = next(iter(columns.values()))

    raw = pd.read_excel(xls, sheet_name=sheet_name, header=None)
    header_rows = _find_header_rows(raw, marker)
    if not header_rows:
        raise ValueError(f"Could not find header row containing '{marker}' in sheet '{sheet_name}'")

    blocks = []
    for i, header_row in enumerate(header_rows):
        end_row = header_rows[i + 1] if i + 1 < len(header_rows) else len(raw)
        block = raw.iloc[header_row:end_row].reset_index(drop=True)
        block.columns = block.iloc[0].tolist()
        block = block.iloc[1:].reset_index(drop=True)
        blocks.append(block)

    df = pd.concat(blocks, ignore_index=True)
    df = df.dropna(how="all")

    required_cols = list(columns.values()) + [src for _, src in detail_specs]
    missing = [src for src in required_cols if src not in df.columns]
    if missing:
        raise ValueError(f"Sheet '{sheet_name}' missing columns: {missing}")

    out = pd.DataFrame()
    for norm_name in NORMALIZED_COLS:
        src_name = columns.get(norm_name)
        out[norm_name] = df[src_name] if src_name else ""

    out["details"] = [
        [(label, row[src_col]) for label, src_col in detail_specs]
        for _, row in df.iterrows()
    ]
    out["product"] = config["product"]
    out["source_sheet"] = sheet_name
    return out


def load_clients(path: str) -> pd.DataFrame:
    xls = pd.ExcelFile(path, engine="openpyxl")

    frames = []
    for sheet_name, config in SHEET_CONFIGS.items():
        if sheet_name not in xls.sheet_names:
            continue
        frames.append(_load_sheet(xls, sheet_name, config))

    if not frames:
        raise ValueError(
            f"No configured sheets found in {path}. Expected one of: {list(SHEET_CONFIGS)}"
        )

    return pd.concat(frames, ignore_index=True)
