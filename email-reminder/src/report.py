import os
from datetime import datetime

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def write_summary(report_dir: str, summary: str) -> str:
    ensure_dir(report_dir)
    filename = f"summary_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.txt"
    path = os.path.join(report_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(summary)
    return path