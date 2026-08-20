"""Central event store for Honigtopf V3."""

from __future__ import annotations

import json
import os
import threading
from collections import deque
from datetime import datetime
from typing import Any


class EventStore:
    def __init__(self, path: str = "logs/events.jsonl", max_memory: int = 5000) -> None:
        self.path = path
        self.max_memory = max_memory
        self._lock = threading.Lock()
        self._memory: deque[dict[str, Any]] = deque(maxlen=max_memory)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def add(self, event: dict[str, Any]) -> None:
        event.setdefault("timestamp", datetime.utcnow().isoformat() + "Z")
        with self._lock:
            self._memory.append(event)
            try:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event, ensure_ascii=False) + "\n")
            except Exception:
                pass

    def recent(self, limit: int = 200, **filters: Any) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self._memory)
        items.reverse()
        out = []
        for e in items:
            if self._match(e, filters):
                out.append(e)
                if len(out) >= limit:
                    break
        return out

    def all_filtered(self, **filters: Any) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self._memory)
        return [e for e in items if self._match(e, filters)]

    def stats(self) -> dict[str, Any]:
        with self._lock:
            items = list(self._memory)
        by_type: dict[str, int] = {}
        by_service: dict[str, int] = {}
        by_country: dict[str, int] = {}
        ips: set[str] = set()
        for e in items:
            by_type[e.get("type", "?")] = by_type.get(e.get("type", "?"), 0) + 1
            by_service[e.get("service", "?")] = by_service.get(e.get("service", "?"), 0) + 1
            loc = e.get("location") or "UNKNOWN"
            # simplify to country if "City, Country (XX)"
            country = loc.split(",")[-1].strip() if "," in loc else loc
            by_country[country] = by_country.get(country, 0) + 1
            if e.get("ip"):
                ips.add(e["ip"])
        return {
            "total": len(items),
            "unique_ips": len(ips),
            "by_type": by_type,
            "by_service": by_service,
            "by_country": by_country,
        }

    @staticmethod
    def _match(e: dict[str, Any], filters: dict[str, Any]) -> bool:
        for k, v in filters.items():
            if v is None or v == "":
                continue
            if str(e.get(k, "")).lower() != str(v).lower():
                # allow partial match for some fields
                if k in ("ip", "location", "type", "service") and str(v).lower() not in str(e.get(k, "")).lower():
                    return False
                if k not in ("ip", "location", "type", "service"):
                    return False
        return True


# Global singleton
store = EventStore()
