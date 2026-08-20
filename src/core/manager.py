"""Multi-service honeypot manager."""

from __future__ import annotations

import asyncio
from typing import Any

from src.services.ftp_hp import FTPHoneypot
from src.services.http_hp import HTTPHoneypot
from src.services.smb_hp import SMBHoneypot
from src.services.telnet_hp import TelnetHoneypot


class ServiceManager:
    def __init__(self) -> None:
        self.services: list[Any] = []
        self.loop: asyncio.AbstractEventLoop | None = None
        self.running = False

    def add_http(self, host: str, port: int, profile_path: str) -> HTTPHoneypot:
        s = HTTPHoneypot(host, port, profile_path)
        self.services.append(s)
        return s

    def add_telnet(self, host: str, port: int = 23) -> TelnetHoneypot:
        s = TelnetHoneypot(host, port)
        self.services.append(s)
        return s

    def add_ftp(self, host: str, port: int = 21) -> FTPHoneypot:
        s = FTPHoneypot(host, port)
        self.services.append(s)
        return s

    def add_smb(self, host: str, port: int = 445) -> SMBHoneypot:
        s = SMBHoneypot(host, port)
        self.services.append(s)
        return s

    async def start_all(self) -> list[str]:
        messages = []
        for s in self.services:
            try:
                await s.start()
                messages.append(f"[+] {getattr(s, 'name', type(s).__name__)} started on port {s.port}")
            except Exception as e:
                messages.append(f"[-] Failed to start {getattr(s, 'name', '?')}: {e}")
        self.running = True
        return messages

    async def stop_all(self) -> list[str]:
        messages = []
        for s in self.services:
            try:
                await s.stop()
                messages.append(f"[*] Stopped {getattr(s, 'name', type(s).__name__)}")
            except Exception as e:
                messages.append(f"[-] Error stopping service: {e}")
        self.services.clear()
        self.running = False
        return messages

    def status(self) -> list[dict[str, Any]]:
        out = []
        for s in self.services:
            out.append({
                "name": getattr(s, "name", type(s).__name__),
                "port": s.port,
                "running": getattr(s, "running", False),
            })
        return out
