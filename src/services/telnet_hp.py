"""Honigtopf V4 — Telnet Honeypot with Fake Shell."""

from __future__ import annotations

import asyncio
from typing import Any
from src.core.events import store


class TelnetHoneypot:
    def __init__(self, host: str = "0.0.0.0", port: int = 2323) -> None:
        self.host = host
        self.port = port
        self.server: asyncio.Server | None = None
        self.running = False
        self.name = "Telnet"

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        ip, _ = writer.get_extra_info("peername") or ("0.0.0.0", 0)

        writer.write(b"Ubuntu 22.04.3 LTS\r\nlogin: ")
        await writer.drain()

        # Capture Login
        username = (await reader.readline()).decode("utf-8", errors="ignore").strip()
        writer.write(b"Password: ")
        await writer.drain()
        password = (await reader.readline()).decode("utf-8", errors="ignore").strip()

        store.add({
            "service": "telnet",
            "type": "CRED_HARVEST",
            "ip": ip,
            "username": username,
            "password": password,
        })

        # Fake Shell Loop
        writer.write(b"\r\nWelcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-88-generic x86_64)\r\n")
        writer.write(f"{username}@srv-01:~$ ".encode())
        await writer.drain()

        fake_fs = {"pwd": "/home/" + username, "whoami": username, "id": f"uid=1000({username}) gid=1000 group=1000"}

        while True:
            line = await reader.readline()
            if not line:
                break
            cmd = line.decode("utf-8", errors="ignore").strip()
            if not cmd:
                continue

            # Log captured command
            store.add({"service": "telnet", "type": "COMMAND", "ip": ip, "command": cmd})

            # Response Emulation
            if cmd == "exit":
                break
            elif cmd in fake_fs:
                writer.write(f"{fake_fs[cmd]}\r\n".encode())
            elif cmd in ("ls", "dir"):
                writer.write(b"documents  downloads  notes.txt\r\n")
            elif cmd.startswith("cat"):
                writer.write(b"Permission denied\r\n")
            else:
                writer.write(f"bash: {cmd}: command not found\r\n".encode())

            writer.write(f"{username}@srv-01:~$ ".encode())
            await writer.drain()

        writer.close()
        await writer.wait_closed()

    async def start(self) -> None:
        self.server = await asyncio.start_server(self.handle_client, self.host, self.port)
        self.running = True

    async def stop(self) -> None:
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        self.running = False