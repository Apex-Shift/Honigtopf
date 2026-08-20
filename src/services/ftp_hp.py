"""Minimal FTP honeypot – captures credentials and commands."""

from __future__ import annotations

import asyncio
from typing import Any

from src.core.events import store
from src.core.geoloc import geolocate


class FTPHoneypot:
    def __init__(self, host: str, port: int = 21) -> None:
        self.host = host
        self.port = port
        self.server: asyncio.Server | None = None
        self.running = False
        self.name = f"ftp:{port}"

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        ip = peer[0] if peer else "?"
        port = peer[1] if peer else 0
        location = "UNKNOWN"

        async def send(code: str, msg: str) -> None:
            writer.write(f"{code} {msg}\r\n".encode())
            await writer.drain()

        try:
            await send("220", "FTP Server ready (Honigtopf)")
            user = ""
            while True:
                try:
                    line = await asyncio.wait_for(reader.readline(), 60)
                except asyncio.TimeoutError:
                    break
                if not line:
                    break
                cmd = line.decode("utf-8", errors="ignore").strip()
                if not cmd:
                    continue
                upper = cmd.upper()
                parts = cmd.split(maxsplit=1)
                verb = parts[0].upper()
                arg = parts[1] if len(parts) > 1 else ""

                if verb == "USER":
                    user = arg
                    await send("331", "Password required")
                elif verb == "PASS":
                    location = await geolocate(ip)
                    store.add({
                        "service": "ftp",
                        "profile": self.name,
                        "ip": ip,
                        "port": port,
                        "location": location,
                        "type": "CRED_HARVEST",
                        "username": user,
                        "password": arg,
                    })
                    await send("230", "Login successful")
                elif verb in ("QUIT", "BYE"):
                    await send("221", "Goodbye")
                    break
                elif verb in ("SYST",):
                    await send("215", "UNIX Type: L8")
                elif verb in ("PWD", "XPWD"):
                    await send("257", "\"/\" is current directory")
                elif verb in ("TYPE", "CWD", "PASV", "PORT", "LIST", "NLST", "RETR", "STOR", "SIZE"):
                    store.add({
                        "service": "ftp",
                        "ip": ip,
                        "location": location,
                        "type": "COMMAND",
                        "command": cmd,
                    })
                    if verb in ("LIST", "NLST"):
                        await send("150", "Here comes the directory listing")
                        await send("226", "Directory send OK")
                    elif verb == "PASV":
                        await send("227", "Entering Passive Mode (127,0,0,1,200,10)")
                    else:
                        await send("200", "OK")
                else:
                    await send("502", "Command not implemented")
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
