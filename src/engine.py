"""Asynchronous HTTP honeypot engine."""

from __future__ import annotations

import asyncio
import json
import os
import urllib.parse
from datetime import datetime
from typing import Any

import aiohttp

from src.geoloc import geolocate
from src.logger import EventLogger


class HonigtopfHTTP:
    def __init__(
        self,
        host: str,
        port: int,
        profile_path: str,
        log_queue: asyncio.Queue,
        event_logger: EventLogger | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.profile_path = profile_path
        self.log_queue = log_queue
        self.event_logger = event_logger or EventLogger()
        self.server: asyncio.Server | None = None
        self.session: aiohttp.ClientSession | None = None
        self.profile = self._load_profile()
        self.running = False

    def _load_profile(self) -> dict[str, Any]:
        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tpl = data.get("template_path")
            if tpl and os.path.exists(tpl):
                with open(tpl, "r", encoding="utf-8") as hf:
                    data["body"] = hf.read()
            return data
        except Exception:
            return {
                "name": "fallback",
                "status_code": "200 OK",
                "headers": {"Server": "Honigtopf/2.0", "Content-Type": "text/html"},
                "body": "<html><body><h1>Service Available</h1></body></html>",
            }

    def _detect_scanner(self, user_agent: str, request_line: str) -> str:
        ua = (user_agent or "").lower()
        req = (request_line or "").lower()
        signatures = [
            ("nmap", "Nmap Scanner"),
            ("masscan", "Masscan"),
            ("zmap", "ZMap"),
            ("shodan", "Shodan Crawler"),
            ("censys", "Censys"),
            ("binaryedge", "BinaryEdge"),
            ("zoomeye", "ZoomEye"),
            ("fofa", "FOFA"),
            ("mirai", "Mirai-like Botnet"),
            ("setup.cgi", "IoT Exploit Probe"),
            ("unauth", "Unauth Access Probe"),
            ("gpon", "GPON Exploit"),
            ("curl", "curl / script"),
            ("python-requests", "Python Script"),
            ("go-http-client", "Go Scanner"),
            ("libwww", "libwww"),
            ("sqlmap", "SQLmap"),
            ("nikto", "Nikto"),
            ("dirbuster", "DirBuster"),
            ("gobuster", "Gobuster"),
            ("wfuzz", "Wfuzz"),
        ]
        for key, label in signatures:
            if key in ua or key in req:
                return label
        return "Browser / Generic Probe"

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        client_ip = peer[0] if peer else "unknown"
        client_port = peer[1] if peer else 0
        ts = datetime.now().strftime("%H:%M:%S")

        try:
            raw = await asyncio.wait_for(reader.read(8192), timeout=8)
            if not raw:
                return

            text = raw.decode("utf-8", errors="ignore")
            header_block, _, body = text.partition("\r\n\r\n")
            lines = header_block.split("\r\n")
            request_line = lines[0] if lines else "UNKNOWN"

            headers: dict[str, str] = {}
            for line in lines[1:]:
                if ":" in line:
                    k, v = line.split(":", 1)
                    headers[k.strip().lower()] = v.strip()

            user_agent = headers.get("user-agent", "Unknown")
            content_length = int(headers.get("content-length", "0") or 0)

            # Read remaining body if needed
            if request_line.upper().startswith("POST") and len(body.encode()) < content_length:
                extra = await reader.read(content_length - len(body.encode()))
                body += extra.decode("utf-8", errors="ignore")

            location = await geolocate(client_ip, self.session)
            scanner = self._detect_scanner(user_agent, request_line)

            # Parse path / query
            path = "/"
            try:
                parts = request_line.split()
                if len(parts) >= 2:
                    parsed = urllib.parse.urlparse(parts[1])
                    path = parsed.path or "/"
                    query = urllib.parse.parse_qs(parsed.query)
                else:
                    query = {}
            except Exception:
                query = {}

            event: dict[str, Any] = {
                "service": "http",
                "profile": self.profile.get("name", "unknown"),
                "ip": client_ip,
                "port": client_port,
                "location": location,
                "request": request_line,
                "user_agent": user_agent,
                "path": path,
                "type": "RECON",
            }

            # Honeyfile download lure
            if "download" in query:
                target = query["download"][0]
                msg = f"[{ts}] 🚨 EXFIL ATTEMPT | {client_ip} [{location}] | file={target}\n"
                await self.log_queue.put(msg)
                event["type"] = "DATA_EXFIL"
                event["target_file"] = target
                self.event_logger.write(event)

            # Credential harvest
            elif request_line.upper().startswith("POST"):
                creds = urllib.parse.parse_qs(body)
                flat = {k: v[0] if len(v) == 1 else v for k, v in creds.items()}
                msg = f"[{ts}] 🔑 CREDENTIALS | {client_ip} [{location}] | {json.dumps(flat)}\n"
                await self.log_queue.put(msg)
                event["type"] = "CRED_HARVEST"
                event["captured"] = flat
                self.event_logger.write(event)

            else:
                msg = f"[{ts}] ⚠️  HTTP RECON | {scanner} | {client_ip} [{location}] | {request_line}\n"
                await self.log_queue.put(msg)
                self.event_logger.write(event)

            # Build response
            status = self.profile.get("status_code", "200 OK")
            body_html = self.profile.get("body", "")
            resp_headers = [
                f"HTTP/1.1 {status}",
                f"Server: {self.profile.get('headers', {}).get('Server', 'Apache')}",
                f"Content-Type: {self.profile.get('headers', {}).get('Content-Type', 'text/html')}",
                f"Content-Length: {len(body_html.encode('utf-8'))}",
                "Connection: close",
            ]
            # Add extra profile headers
            for k, v in self.profile.get("headers", {}).items():
                if k.lower() not in ("server", "content-type", "content-length", "connection"):
                    resp_headers.append(f"{k}: {v}")

            full = "\r\n".join(resp_headers) + "\r\n\r\n" + body_html
            writer.write(full.encode("utf-8"))
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
        await self.log_queue.put(
            f"[*] HTTP [{self.profile.get('name', '?')}] listening on {self.host}:{self.port}\n"
        )

    async def stop(self) -> None:
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        if self.session:
            await self.session.close()
        await self.log_queue.put(f"[*] HTTP on port {self.port} stopped\n")
