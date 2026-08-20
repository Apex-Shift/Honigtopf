"""Persistent JSON line logger for Honigtopf events."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any


class EventLogger:
    def __init__(self, path: str = "logs/honigtopf_master.jsonl") -> None:
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def write(self, event: dict[str, Any]) -> None:
        event.setdefault("timestamp", datetime.utcnow().isoformat() + "Z")
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception:
            pass
