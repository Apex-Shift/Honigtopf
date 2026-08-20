"""HTTP honeypot service."""

from __future__ import annotations

import asyncio
import json
import os
import urllib.parse
from datetime import datetime
from typing import Any

import aiohttp

from src.core.events import store
from src.core.geoloc import geolocate


class HTTPHoneypot:
    def __init__(self, host: str, port: int, profile_path: str) -> None:
        self.host = host
        self.port = port
        self.profile_path = profile_path
        self.profile = self._load()
        self.server: asyncio.Server | None = None
        self.session: aiohttp.ClientSession | None = None
        self.running = False
        self.name = self.profile.get("name", f"http:{port}")

    def _load(self) -> dict[str, Any]:
        try:
            with open(self.profile_path, encoding="utf-8") as f:
                data = json.load(f)
            tpl = data.get("template_path")
            if tpl and os.path.exists(tpl):
                with open(tpl, encoding="utf-8") as hf:
                    data["body"] = hf.read()
            return data
        except Exception:
            return {
                "name": "fallback",
                "status_code": "200 OK",
                "headers": {"Server": "Honigtopf/3.0", "Content-Type": "text/html"},
                "body": "<h1>OK</h1>",
            }

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        ip = peer[0] if peer else "?"
        port = peer[1] if peer else 0
        try:
            raw = await asyncio.wait_for(reader.read(8192), timeout=10)
            if not raw:
                return
            text = raw.decode("utf-8", errors="ignore")
            header, _, body = text.partition("\r\n\r\n")
            lines = header.split("\r\n")
            req = lines[0] if lines else "UNKNOWN"
            headers = {}
            for line in lines[1:]:
                if ":" in line:
                    k, v = line.split(":", 1)
                    headers[k.strip().lower()] = v.strip()
            ua = headers.get("user-agent", "")
            cl = int(headers.get("content-length", 0) or 0)
            if req.upper().startswith("POST") and len(body.encode()) < cl:
                extra = await reader.read(cl - len(body.encode()))
                body += extra.decode("utf-8", errors="ignore")

            location = await geolocate(ip, self.session)
            path = "/"
            query = {}
            try:
                parts = req.split()
                if len(parts) >= 2:
                    parsed = urllib.parse.urlparse(parts[1])
                    path = parsed.path or "/"
                    query = urllib.parse.parse_qs(parsed.query)
            except Exception:
                pass

            event: dict[str, Any] = {
                "service": "http",
                "profile": self.name,
                "ip": ip,
                "port": port,
                "location": location,
                "request": req,
                "user_agent": ua,
                "path": path,
                "type": "RECON",
            }

            if "download" in query:
                event["type"] = "DATA_EXFIL"
                event["target"] = query["download"][0]
            elif req.upper().startswith("POST"):
                creds = urllib.parse.parse_qs(body)
                event["type"] = "CRED_HARVEST"
                event["captured"] = {k: (v[0] if len(v) == 1 else v) for k, v in creds.items()}

            store.add(event)

            status = self.profile.get("status_code", "200 OK")
            html = self.profile.get("body", "")
            resp = [
                f"HTTP/1.1 {status}",
                f"Server: {self.profile.get('headers', {}).get('Server', 'Apache')}",
                f"Content-Type: {self.profile.get('headers', {}).get('Content-Type', 'text/html')}",
                f"Content-Length: {len(html.encode())}",
                "Connection: close",
            ]
            for k, v in self.profile.get("headers", {}).items():
                if k.lower() not in ("server", "content-type", "content-length", "connection"):
                    resp.append(f"{k}: {v}")
            writer.write(("\r\n".join(resp) + "\r\n\r\n" + html).encode())
            await writer.drain()
        except Exception:
            pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def start(self) -> None:
        self.session = aiohttp.ClientSession()
        self.server = await asyncio.start_server(self.handle, self.host, self.port)
        self.running = True

    async def stop(self) -> None:
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        if self.session:
            await self.session.close()
