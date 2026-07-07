from datetime import datetime, timedelta
import pandas as pd

def normalize_date(value):
    if pd.isna(value):
        return None
    dt = pd.to_datetime(value, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.to_pydatetime().date()

def filter_expiring(df: pd.DataFrame, max_window_days: int):
    """
    Returns:
      records: list of (idx, row, exp_date, days_left)
      skipped: list of (idx, reason)
    """
    today = datetime.now().date()
    end = today + timedelta(days=max_window_days)

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
            days_left = (exp - today).days
            records.append((i, row, exp, days_left))
        else:
            skipped.append((i, "not_in_window"))

    return records, skipped