"""Minimal SMB/Samba honeypot – logs connection attempts and basic negotiate traffic."""

from __future__ import annotations

import asyncio
from typing import Any

from src.core.events import store
from src.core.geoloc import geolocate


class SMBHoneypot:
    """
    Lightweight SMB listener.
    Does not implement full SMB protocol – captures connection metadata
    and any readable strings (useful against scanners probing 445).
    """

    def __init__(self, host: str, port: int = 445) -> None:
        self.host = host
        self.port = port
        self.server: asyncio.Server | None = None
        self.running = False
        self.name = f"smb:{port}"

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        ip = peer[0] if peer else "?"
        port = peer[1] if peer else 0
        try:
            data = await asyncio.wait_for(reader.read(4096), timeout=15)
            location = await geolocate(ip)
            # Extract printable strings as possible usernames / paths
            printable = "".join(chr(b) if 32 <= b < 127 else " " for b in data)
            tokens = [t for t in printable.split() if len(t) > 2][:20]

            store.add({
                "service": "smb",
                "profile": self.name,
                "ip": ip,
                "port": port,
                "location": location,
                "type": "RECON",
                "bytes_received": len(data),
                "tokens": tokens,
            })

            # Send a minimal SMB-looking reject so scanners don't hang forever
            # (not a valid SMB packet – just closes after short delay)
            await asyncio.sleep(0.3)
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
