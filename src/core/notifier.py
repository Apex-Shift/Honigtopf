"""Honigtopf V4 — Webhook Alert System."""

from __future__ import annotations

import json
import urllib.request
from typing import Any


class AlertNotifier:
    def __init__(self, webhook_url: str = "") -> None:
        self.webhook_url = webhook_url

    def send_alert(self, event: dict[str, Any]) -> None:
        if not self.webhook_url:
            return

        payload = {
            "username": "Honigtopf Sentinel",
            "embeds": [
                {
                    "title": f"🚨 Attack Detected: {event.get('service', 'Unknown').upper()}",
                    "color": 15158332 if event.get("type") == "CRED_HARVEST" else 3447003,
                    "fields": [
                        {"name": "IP Address", "value": str(event.get("ip")), "inline": True},
                        {"name": "Event Type", "value": str(event.get("type")), "inline": True},
                        {"name": "Details", "value": json.dumps(event, indent=2)[:1024]},
                    ],
                }
            ],
        }

        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "Honigtopf-V4"},
            )
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            pass  # Fail silent to avoid blocking honeypot threads