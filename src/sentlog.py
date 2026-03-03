import json
import os
from datetime import datetime

def _ensure_parent(path: str):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

def load_sent_log(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def make_key(email: str, exp_date, stage_days: int) -> str:
    return f"{email.strip().lower()}|{str(exp_date)}|D-{stage_days}"

def was_sent(sent_log: dict, key: str) -> bool:
    return key in sent_log

def mark_sent(sent_log: dict, key: str):
    sent_log[key] = {"sent_at": datetime.now().isoformat(timespec="seconds")}

def save_sent_log(path: str, sent_log: dict):
    _ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sent_log, f, indent=2)