from datetime import datetime, timedelta
import pandas as pd
from dateutil.relativedelta import relativedelta

def normalize_date(value):
    if pd.isna(value):
        return None
    dt = pd.to_datetime(value, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.to_pydatetime().date()


def resolve_schedule(row, exp_date, default_schedule_days):
    """Return the list of day-offsets (days-before-expiry) on which this row
    should be reminded.

    A sheet can opt into a calendar "months before" reminder via the
    ``remind_months_before`` column (see SHEET_CONFIGS in loader.py). Because a
    calendar month is not a fixed number of days, the offset is computed from
    this row's own expiry date, so it lands on the exact date N months earlier
    (e.g. 3 months before 14/07/2027 -> 14/04/2027 -> 91 days).

    When ``remind_months_before`` is unset, the global day-offset schedule
    (default 30/7/1) is used unchanged.
    """
    months = row.get("remind_months_before")
    if months is not None and not pd.isna(months):
        months = int(months)
        trigger_date = exp_date - relativedelta(months=months)
        return [(exp_date - trigger_date).days]
    return list(default_schedule_days)


def filter_expiring(df: pd.DataFrame, default_schedule_days):
    """
    Returns:
      records: list of (idx, row, exp_date, days_left, schedule_days)
      skipped: list of (idx, reason)

    A row is kept when it is not yet expired and today has reached its widest
    reminder window (max of its resolved schedule). The exact stage match
    (days_left in schedule_days) is enforced later in main.py.
    """
    today = datetime.now().date()

    records = []
    skipped = []

    for i, row in df.iterrows():
        email = str(row.get("email", "")).strip()
        exp = normalize_date(row.get("expired_date"))

        if not email or email.lower() == "nan":
            skipped.append((i, "missing_email"))
            continue
        if exp is None:
            skipped.append((i, "invalid_or_missing_expired_date"))
            continue

        schedule_days = resolve_schedule(row, exp, default_schedule_days)
        window = max(schedule_days) if schedule_days else 0
        end = today + timedelta(days=window)

        if today <= exp <= end:
            days_left = (exp - today).days
            records.append((i, row, exp, days_left, schedule_days))
        else:
            skipped.append((i, "not_in_window"))

    return records, skipped
