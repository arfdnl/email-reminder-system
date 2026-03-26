import os
from dotenv import load_dotenv

load_dotenv()

REMIND_SCHEDULE_DAYS = [
    int(x.strip())
    for x in os.getenv("REMIND_SCHEDULE_DAYS", "30,7,1").split(",")
    if x.strip()
]
REMIND_SCHEDULE_DAYS = sorted(set(REMIND_SCHEDULE_DAYS), reverse=True)
MAX_WINDOW_DAYS = max(REMIND_SCHEDULE_DAYS) if REMIND_SCHEDULE_DAYS else 30

TEST_MODE = os.getenv("TEST_MODE", "true").lower() == "true"

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
TEST_TO_EMAIL = os.getenv("TEST_TO_EMAIL", "")

DATA_FILE = os.getenv("DATA_FILE", "data/clients.xlsx")
LOG_DIR = os.getenv("LOG_DIR", "logs")
REPORT_DIR = os.getenv("REPORT_DIR", "reports")

RETRY_MAX = int(os.getenv("RETRY_MAX", "3"))
RETRY_BACKOFF_SECONDS = int(os.getenv("RETRY_BACKOFF_SECONDS", "2"))

SENT_LOG_FILE = os.getenv("SENT_LOG_FILE", "state/sent_log.json")

MAX_EMAILS_PER_RUN = int(os.getenv("MAX_EMAILS_PER_RUN", "30"))