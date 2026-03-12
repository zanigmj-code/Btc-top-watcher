import json
import os
from typing import Dict, Any

HISTORY_FILE = "history.json"


def append_history(entry: Dict[str, Any]) -> None:
    history = []

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)

    # check if today's entry already exists
    for item in history:
        if item["date"] == entry["date"]:
            return

    history.append(entry)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)