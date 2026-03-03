from datetime import datetime, timedelta
import pandas as pd

def normalize_date(value):
    if pd.isna(value):
        return None
    try:
        dt = pd.to_datetime(value, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.to_pydatetime().date()
    except Exception:
        return None

def filter_expiring(df: pd.DataFrame, remind_days: int):
    today = datetime.now().date()
    end = today + timedelta(days=remind_days)

    records = []
    skipped = []

    for i, row in df.iterrows():
        email = str(row.get("EMAIL", "")).strip()
        exp = normalize_date(row.get("EXPIRED DATE"))

        if not email or email.lower() == "nan":
            skipped.append((i, "missing_email"))
            continue
        if exp is None:
            skipped.append((i, "invalid_or_missing_expired_date"))
            continue

        if today <= exp <= end:
            records.append((i, row, exp))
        else:
            skipped.append((i, "not_in_window"))

    return records, skipped