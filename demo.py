"""
demo.py — SAFE local demo runner for the presentation.

Runs the exact same logic as `src/main.py`, but forces a safe, isolated
configuration so it can NEVER email real clients or touch real data/state:

  * TEST_MODE=true        -> every email is redirected to your own inbox
  * a throwaway workbook  -> 3 fake demo clients (D-30, D-7, D-1), plus 2
                             "3 months before" license renewal demo rows
                             (License Pentest, License SOC), no real PII
  * a separate demo/ dir  -> its own sent-log, logs, and reports

These are set as environment variables, which take precedence over .env
(python-dotenv uses override=False), so your real .env is left untouched.

Usage:
    python demo.py
"""
import os
import sys
import json
from datetime import date, timedelta

import pandas as pd
from dateutil.relativedelta import relativedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
DEMO_DIR = os.path.join(ROOT, "demo")
DEMO_XLSX = os.path.join(DEMO_DIR, "demo_clients.xlsx")
DEMO_SENTLOG = os.path.join(DEMO_DIR, "demo_sent_log.json")

# >>> The inbox that will receive every demo email (change if you like) <<<
DEMO_INBOX = "arifdanial@gmail.com"


def build_demo_data():
    """Create a fresh demo workbook with 3 fake clients at the 30/7/1
    milestones, plus License Pentest / License SOC demo rows dated exactly
    3 calendar months out, so they fire today under the "3 Months before"
    schedule (see remind_months_before in src/loader.py)."""
    os.makedirs(DEMO_DIR, exist_ok=True)
    os.makedirs(os.path.join(DEMO_DIR, "logs"), exist_ok=True)
    os.makedirs(os.path.join(DEMO_DIR, "reports"), exist_ok=True)

    today = date.today()
    rows = [
        {"COMPANY NAME": "Demo Alpha Sdn. Bhd.", "PERSON IN CHARGE": "Encik Demo Alpha",
         "EMAIL": "demo.alpha@example.com", "PHONE NO": "03-0000 0001",
         "END DATE": today + timedelta(days=30), "QUANTITY": 1, "REMARKS": "satuduatiga"},
        {"COMPANY NAME": "Demo Beta Sdn. Bhd.", "PERSON IN CHARGE": "Encik Demo Beta",
         "EMAIL": "demo.beta@example.com", "PHONE NO": "03-0000 0002",
         "END DATE": today + timedelta(days=7), "QUANTITY": 1, "REMARKS": "satuduatiga"},
        {"COMPANY NAME": "Demo Gamma Sdn. Bhd.", "PERSON IN CHARGE": "Encik Demo Gamma",
         "EMAIL": "demo.gamma@example.com", "PHONE NO": "03-0000 0003",
         "END DATE": today + timedelta(days=1), "QUANTITY": 1, "REMARKS": "satuduatiga"},
    ]
    df = pd.DataFrame(rows, columns=[
        "COMPANY NAME", "PERSON IN CHARGE", "EMAIL", "PHONE NO", "END DATE", "QUANTITY", "REMARKS"])

    # expiry = exactly 3 calendar months from today -> trigger date = today,
    # matching the real License Pentest / License SOC "3 months before" logic.
    license_expiry = today + relativedelta(months=3)
    pentest_df = pd.DataFrame([{
        "COMPANY NAME": "Kyrol Security Labs",
        "EMAIL": "demo.pentest@example.com",
        "EXPIRY DATE": license_expiry,
        "REMARKS": "Penetration testing license renewal (demo)",
    }], columns=["COMPANY NAME", "EMAIL", "EXPIRY DATE", "REMARKS"])
    soc_df = pd.DataFrame([{
        "COMPANY NAME": "Kyrol Security Labs",
        "EMAIL": "demo.soc@example.com",
        "EXPIRY DATE": license_expiry,
        "REMARKS": "SOC license renewal (demo)",
    }], columns=["COMPANY NAME", "EMAIL", "EXPIRY DATE", "REMARKS"])

    # sheet names match SHEET_CONFIGS entries in src/loader.py
    with pd.ExcelWriter(DEMO_XLSX, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="M365", index=False)
        pentest_df.to_excel(writer, sheet_name="License Pentest", index=False)
        soc_df.to_excel(writer, sheet_name="License SOC", index=False)

    # fresh (empty) sent-log every run, so the demo always sends
    with open(DEMO_SENTLOG, "w") as f:
        json.dump({}, f)

    return df


def configure_env():
    """Force safe demo settings. These win over .env (load_dotenv override=False)."""
    os.environ["TEST_MODE"] = "true"                # <-- redirects all mail to DEMO_INBOX
    os.environ["TEST_TO_EMAIL"] = DEMO_INBOX
    os.environ["DATA_FILE"] = DEMO_XLSX
    os.environ["SENT_LOG_FILE"] = DEMO_SENTLOG
    os.environ["LOG_DIR"] = os.path.join(DEMO_DIR, "logs")
    os.environ["REPORT_DIR"] = os.path.join(DEMO_DIR, "reports")
    os.environ["MAX_EMAILS_PER_RUN"] = "10"
    os.environ["REMIND_SCHEDULE_DAYS"] = "30,7,1"


if __name__ == "__main__":
    os.chdir(ROOT)
    print("=" * 60)
    print(" SAFE DEMO MODE — no real clients will be emailed")
    print("=" * 60)
    print("Building demo workbook (3 fake clients: D-30, D-7, D-1;")
    print("plus 2 license renewals for Kyrol Security Labs at 3 Months before: Pentest, SOC)...")
    build_demo_data()
    configure_env()
    print(f"TEST_MODE = true  ->  ALL email redirected to: {DEMO_INBOX}")
    print("Running the real src/main.py logic...\n")

    sys.path.insert(0, os.path.join(ROOT, "src"))
    import main
    main.main()

    print("\n" + "=" * 60)
    print(f" Done. Open the inbox for {DEMO_INBOX} to show the emails.")
    print("=" * 60)
