import os
import logging
from datetime import datetime

from config import (
    REMIND_DAYS, TEST_MODE,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
    FROM_EMAIL, TEST_TO_EMAIL,
    DATA_FILE, LOG_DIR, REPORT_DIR,
    RETRY_MAX, RETRY_BACKOFF_SECONDS,
    SENT_LOG_FILE,
)
from loader import load_clients
from filterer import filter_expiring
from emailer import send_email
from report import write_summary
from sentlog import load_sent_log, save_sent_log, make_key, was_sent, mark_sent


def setup_logging() -> str:
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, "app.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    return log_path


def make_text_body(row, exp_date) -> str:
    return f"""Reminder: Client Renewal Expiring Soon

INDIVIDUAL/COMPANY: {row['INDIVIDUAL/COMPANY']}
OFFICER NAME/NAME: {row['OFFICER NAME/NAME']}
EMAIL: {row['EMAIL']}
NO TEL: {row['NO TEL']}
EXPIRED DATE: {exp_date}
PC / SVR: {row['PC / SVR']}
REMARK: {row['REMARK']}

Generated at: {datetime.now()}
"""


def make_html_body(row, exp_date) -> str:
    # Minimal escaping so user data doesn't break HTML
    def esc(x):
        s = "" if x is None else str(x)
        return (
            s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
        )

    return f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.4;">
    <h2 style="margin: 0 0 12px 0;">Renewal Reminder</h2>
    <p>Your client/service is expiring soon. Details below:</p>

    <table cellpadding="8" cellspacing="0" style="border-collapse: collapse; border: 1px solid #ddd;">
      <tr><td style="border:1px solid #ddd;"><b>INDIVIDUAL/COMPANY</b></td><td style="border:1px solid #ddd;">{esc(row.get('INDIVIDUAL/COMPANY'))}</td></tr>
      <tr><td style="border:1px solid #ddd;"><b>OFFICER NAME/NAME</b></td><td style="border:1px solid #ddd;">{esc(row.get('OFFICER NAME/NAME'))}</td></tr>
      <tr><td style="border:1px solid #ddd;"><b>EMAIL</b></td><td style="border:1px solid #ddd;">{esc(row.get('EMAIL'))}</td></tr>
      <tr><td style="border:1px solid #ddd;"><b>NO TEL</b></td><td style="border:1px solid #ddd;">{esc(row.get('NO TEL'))}</td></tr>
      <tr><td style="border:1px solid #ddd;"><b>EXPIRED DATE</b></td><td style="border:1px solid #ddd;">{esc(exp_date)}</td></tr>
      <tr><td style="border:1px solid #ddd;"><b>PC / SVR</b></td><td style="border:1px solid #ddd;">{esc(row.get('PC / SVR'))}</td></tr>
      <tr><td style="border:1px solid #ddd;"><b>REMARK</b></td><td style="border:1px solid #ddd;">{esc(row.get('REMARK'))}</td></tr>
    </table>

    <p style="color:#666; margin-top: 12px; font-size: 12px;">
      Generated at: {esc(datetime.now())}
    </p>
  </body>
</html>
""".strip()


def validate_env():
    if TEST_MODE and not TEST_TO_EMAIL:
        raise ValueError("TEST_MODE is true but TEST_TO_EMAIL is empty.")

    if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
        raise ValueError("SMTP settings missing. Set SMTP_HOST, SMTP_USER, SMTP_PASS (and port).")


def main():
    log_path = setup_logging()
    logging.info("Starting email reminder job...")
    logging.info(f"DATA_FILE={DATA_FILE} REMIND_DAYS={REMIND_DAYS} TEST_MODE={TEST_MODE}")
    logging.info(f"RETRY_MAX={RETRY_MAX} RETRY_BACKOFF_SECONDS={RETRY_BACKOFF_SECONDS}")
    logging.info(f"SENT_LOG_FILE={SENT_LOG_FILE}")

    validate_env()

    # Load input data
    df = load_clients(DATA_FILE)
    expiring, skipped = filter_expiring(df, REMIND_DAYS)

    # Load "already sent" state so we don't spam daily
    sent_log = load_sent_log(SENT_LOG_FILE)

    emailed = 0
    failed = 0
    already_sent = 0

    for idx, row, exp_date in expiring:
        # Determine who to email
        real_email = str(row["EMAIL"]).strip()
        to_email = TEST_TO_EMAIL if TEST_MODE else real_email

        # Unique key per email+expiry date (so same item won't be sent again)
        key = make_key(real_email, exp_date)
        if was_sent(sent_log, key):
            already_sent += 1
            logging.info(f"Skipping row={idx} (already sent) key={key}")
            continue

        subject = f"Renewal Reminder: Expires {exp_date}"
        text_body = make_text_body(row, exp_date)
        html_body = make_html_body(row, exp_date)

        try:
            send_email(
                SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
                FROM_EMAIL, to_email, subject,
                text_body=text_body,
                html_body=html_body,
                retry_max=RETRY_MAX,
                retry_backoff_seconds=RETRY_BACKOFF_SECONDS,
            )
            emailed += 1
            logging.info(f"Emailed row={idx} to={to_email} exp={exp_date}")

            # Mark + save immediately (so if script crashes later, state is still updated)
            mark_sent(sent_log, key)
            save_sent_log(SENT_LOG_FILE, sent_log)

        except Exception as e:
            failed += 1
            logging.error(f"Failed to email row={idx} to={to_email}: {e}")

    summary = (
        f"Run summary:\n"
        f"- Total rows: {len(df)}\n"
        f"- Expiring within {REMIND_DAYS} days: {len(expiring)}\n"
        f"- Emailed: {emailed}\n"
        f"- Already sent (skipped): {already_sent}\n"
        f"- Failed: {failed}\n"
        f"- Skipped (invalid/not in window): {len(skipped)}\n"
        f"- Log: {log_path}\n"
    )

    report_path = write_summary(REPORT_DIR, summary)
    logging.info(summary)
    logging.info(f"Summary written to: {report_path}")


if __name__ == "__main__":
    main()