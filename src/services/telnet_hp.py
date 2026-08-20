"""Telnet honeypot."""

from __future__ import annotations

import asyncio
from typing import Any

from src.core.events import store
from src.core.geoloc import geolocate


class TelnetHoneypot:
    def __init__(self, host: str, port: int = 23) -> None:
        self.host = host
        self.port = port
        self.server: asyncio.Server | None = None
        self.running = False
        self.name = f"telnet:{port}"

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        ip = peer[0] if peer else "?"
        port = peer[1] if peer else 0
        try:
            writer.write(b"login: ")
            await writer.drain()
            user = (await asyncio.wait_for(reader.readline(), 30)).decode("utf-8", errors="ignore").strip()
            writer.write(b"Password: ")
            await writer.drain()
            pwd = (await asyncio.wait_for(reader.readline(), 30)).decode("utf-8", errors="ignore").strip()

            location = await geolocate(ip)
            store.add({
                "service": "telnet",
                "profile": self.name,
                "ip": ip,
                "port": port,
                "location": location,
                "type": "CRED_HARVEST",
                "username": user,
                "password": pwd,
            })

            writer.write(b"\r\nBusyBox v1.33.1 (ash)\r\n# ")
            await writer.drain()
            for _ in range(5):
                try:
                    line = await asyncio.wait_for(reader.readline(), 40)
                except asyncio.TimeoutError:
                    break
                cmd = line.decode("utf-8", errors="ignore").strip()
                if not cmd:
                    continue
                store.add({
                    "service": "telnet",
                    "ip": ip,
                    "location": location,
                    "type": "COMMAND",
                    "command": cmd,
                })
                if cmd in ("exit", "quit", "logout"):
                    break
                writer.write(b"sh: " + cmd.encode() + b": not found\r\n# ")
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
        self.server = await asyncio.start_server(self.handle, self.host, self.port)
        self.running = True

    async def stop(self) -> None:
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
