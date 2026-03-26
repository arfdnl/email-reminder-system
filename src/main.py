import os
import logging
from datetime import datetime

from config import (
    REMIND_SCHEDULE_DAYS, MAX_WINDOW_DAYS,
    TEST_MODE,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
    FROM_EMAIL, TEST_TO_EMAIL,
    DATA_FILE, LOG_DIR, REPORT_DIR,
    RETRY_MAX, RETRY_BACKOFF_SECONDS,
    SENT_LOG_FILE,
    MAX_EMAILS_PER_RUN,
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


def clean_value(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def format_date_ddmmyyyy(value) -> str:
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y")
    try:
        dt = datetime.strptime(str(value), "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return str(value)


def make_text_body(row, exp_date, stage_days: int) -> str:
    formatted_date = format_date_ddmmyyyy(exp_date)

    return f"""Reminder: Client Renewal Expiring Soon (D-{stage_days})

INDIVIDUAL/COMPANY: {clean_value(row['INDIVIDUAL/COMPANY'])}
OFFICER NAME/NAME: {clean_value(row['OFFICER NAME/NAME'])}
EMAIL: {clean_value(row['CUST EMAIL'])}
NO TEL: {clean_value(row['NO TEL'])}
EXPIRED DATE: {formatted_date}
PC / SVR: {clean_value(row['PC / SVR'])}

Generated at: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
"""


def make_html_body(row, exp_date, stage_days: int) -> str:
    formatted_date = format_date_ddmmyyyy(exp_date)

    def esc(x):
        s = clean_value(x)
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f"""
<html>
  <body style="margin:0;padding:0;background:#f4f6fb;font-family:Arial, sans-serif;">
    <div style="max-width:680px;margin:0 auto;padding:24px;">
      <div style="background:#ffffff;border-radius:12px;box-shadow:0 2px 10px rgba(0,0,0,0.05);overflow:hidden;">

        <div style="padding:20px;text-align:center;">
          <img src="cid:kyrol_logo" alt="Kyrol Security Labs" style="max-width:220px;height:auto;" />
        </div>

        <!-- HEADER -->
        <div style="padding:18px 24px;background:#002250;color:#ffffff;">
          <h2 style="margin:0;">Renewal Reminder (D-{stage_days})</h2>
          <p style="margin:6px 0 0 0;color:#ffffff;">
            Expiry Date: <strong style="color:#ffffff;">{formatted_date}</strong>
          </p>
        </div>

        <div style="padding:24px;">
          <p style="margin:0 0 14px 0;color:#222;">
            This is an automated renewal reminder. Details below:
          </p>

          <table style="width:100%;border-collapse:collapse;font-size:14px;">
            <tr>
              <td style="padding:10px;border-bottom:1px solid #eee;color:#666;width:38%;">Individual/Company</td>
              <td style="padding:10px;border-bottom:1px solid #eee;color:#111;"><b>{esc(row.get("INDIVIDUAL/COMPANY"))}</b></td>
            </tr>
            <tr>
              <td style="padding:10px;border-bottom:1px solid #eee;color:#666;">Officer Name</td>
              <td style="padding:10px;border-bottom:1px solid #eee;color:#111;">{esc(row.get("OFFICER NAME/NAME"))}</td>
            </tr>
            <tr>
              <td style="padding:10px;border-bottom:1px solid #eee;color:#666;">Email</td>
              <td style="padding:10px;border-bottom:1px solid #eee;color:#111;">{esc(row.get("CUST EMAIL"))}</td>
            </tr>
            <tr>
              <td style="padding:10px;border-bottom:1px solid #eee;color:#666;">Phone</td>
              <td style="padding:10px;border-bottom:1px solid #eee;color:#111;">{esc(row.get("NO TEL"))}</td>
            </tr>
            <tr>
              <td style="padding:10px;color:#666;">PC / SVR</td>
              <td style="padding:10px;color:#111;">{esc(row.get("PC / SVR"))}</td>
            </tr>
          </table>

          <!-- ACTION BOX (FIXED COLOR MATCHING) -->
          <div style="margin-top:18px;padding:12px;background:#e6eef7;border-radius:10px;border:1px solid #b3c7e6;color:#002250;">
            <b>Action:</b> Please proceed with renewal before expiry.
          </div>

          <p style="margin:16px 0 0 0;font-size:12px;color:#777;">
            For inquiries: sales@kyrolsecuritylabs.com | 03-8685 5032
          </p>
        </div>

        <div style="padding:14px 22px;background:#fafafa;color:#888;font-size:12px;">
          This email was generated automatically by the Renewal Reminder System.
        </div>

      </div>
    </div>
  </body>
</html>
""".strip()


def validate_env():
    if TEST_MODE and not TEST_TO_EMAIL:
        raise ValueError("TEST_MODE is true but TEST_TO_EMAIL is empty.")

    if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
        raise ValueError("SMTP settings missing. Set SMTP_HOST, SMTP_USER, SMTP_PASS.")


def main():
    log_path = setup_logging()
    logging.info("Starting email reminder job...")
    logging.info(f"DATA_FILE={DATA_FILE} TEST_MODE={TEST_MODE}")
    logging.info(f"REMIND_SCHEDULE_DAYS={REMIND_SCHEDULE_DAYS} MAX_WINDOW_DAYS={MAX_WINDOW_DAYS}")
    logging.info(f"MAX_EMAILS_PER_RUN={MAX_EMAILS_PER_RUN}")
    logging.info(f"SENT_LOG_FILE={SENT_LOG_FILE}")

    validate_env()

    df = load_clients(DATA_FILE)
    candidates, skipped = filter_expiring(df, MAX_WINDOW_DAYS)

    sent_log = load_sent_log(SENT_LOG_FILE)

    emailed = 0
    failed = 0
    already_sent = 0
    not_stage = 0

    for idx, row, exp_date, days_left in candidates:
        if days_left not in REMIND_SCHEDULE_DAYS:
            not_stage += 1
            continue

        if emailed >= MAX_EMAILS_PER_RUN:
            logging.warning(f"Reached MAX_EMAILS_PER_RUN={MAX_EMAILS_PER_RUN}. Stopping sends.")
            break

        raw_emails = str(row["EMAIL"]).strip()
        email_list = [e.strip() for e in raw_emails.split(",") if e.strip()]
        real_email = ", ".join(email_list)

        to_email = TEST_TO_EMAIL if TEST_MODE else real_email

        stage_days = days_left
        key = make_key(real_email, exp_date, stage_days)
        if was_sent(sent_log, key):
            already_sent += 1
            logging.info(f"Skipping row={idx} (already sent) key={key}")
            continue

        subject = f"[Renewal Reminder] (D-{stage_days}): Expires {format_date_ddmmyyyy(exp_date)}"
        text_body = make_text_body(row, exp_date, stage_days)
        html_body = make_html_body(row, exp_date, stage_days)

        try:
            send_email(
                SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
                FROM_EMAIL, to_email, subject,
                text_body=text_body,
                html_body=html_body,
                inline_image_path="assets/kyrol_logo.png",
                inline_image_cid="kyrol_logo",
                retry_max=RETRY_MAX,
                retry_backoff_seconds=RETRY_BACKOFF_SECONDS,
            )
            emailed += 1
            logging.info(f"Emailed row={idx} to={to_email} exp={exp_date} days_left={days_left}")

            mark_sent(sent_log, key)
            save_sent_log(SENT_LOG_FILE, sent_log)

        except Exception as e:
            failed += 1
            logging.error(f"Failed to email row={idx} to={to_email}: {e}")

    summary = (
        f"Run summary:\n"
        f"- Total rows: {len(df)}\n"
        f"- Candidates in window (<= {MAX_WINDOW_DAYS} days): {len(candidates)}\n"
        f"- On schedule (days_left in {REMIND_SCHEDULE_DAYS}): {len(candidates) - not_stage}\n"
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