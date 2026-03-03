import pandas as pd

REQUIRED_COLS = [
    "INDIVIDUAL/COMPANY",
    "OFFICER NAME/NAME",
    "EMAIL",
    "NO TEL",
    "EXPIRED DATE",
    "PC / SVR",
    "REMARK",
]

def load_clients(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, engine="openpyxl")
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in Excel: {missing}")
    return df