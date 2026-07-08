import pandas as pd

# Each entry maps a workbook sheet name to how its columns map onto the
# common normalized schema used by the rest of the pipeline (filterer.py,
# main.py). Add a new sheet here to onboard a new product/client list.
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
            "detail_value": "PC / SVR",
        },
        "detail_label": "PC / SVR",
    },
    "Sangfor": {
        "product": "VMware (Sangfor)",
        "columns": {
            "company": "COMPANY NAME",
            "contact": "PERSON IN CHARGE",
            "email": "EMAIL",
            "phone": "PHONE NO",
            "expired_date": "END DATE",
            "detail_value": "QUANTITY",
        },
        "detail_label": "Quantity",
    },
}

# Normalized columns every row in the combined DataFrame will have.
NORMALIZED_COLS = ["company", "contact", "email", "cust_email", "phone", "expired_date", "detail_value"]


def _find_header_row(raw: pd.DataFrame, marker: str) -> int:
    for i, row in raw.iterrows():
        values = [str(v).strip() for v in row.tolist()]
        if marker in values:
            return i
    raise ValueError(f"Could not find header row containing '{marker}'")


def _load_sheet(xls: pd.ExcelFile, sheet_name: str, config: dict) -> pd.DataFrame:
    columns = config["columns"]
    marker = next(iter(columns.values()))

    raw = pd.read_excel(xls, sheet_name=sheet_name, header=None)
    header_row = _find_header_row(raw, marker)

    df = pd.read_excel(xls, sheet_name=sheet_name, header=header_row)
    df = df.dropna(how="all")

    missing = [src for src in columns.values() if src not in df.columns]
    if missing:
        raise ValueError(f"Sheet '{sheet_name}' missing columns: {missing}")

    out = pd.DataFrame()
    for norm_name in NORMALIZED_COLS:
        src_name = columns.get(norm_name)
        out[norm_name] = df[src_name] if src_name else ""

    out["detail_label"] = config["detail_label"]
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
