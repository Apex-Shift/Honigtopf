"""Telnet honeypot – BusyBox / IoT style shell."""

from __future__ import annotations

import asyncio
from datetime import datetime

from src.geoloc import geolocate
from src.logger import EventLogger


class HonigtopfTelnet:
    def __init__(
        self,
        host: str,
        port: int,
        log_queue: asyncio.Queue,
        event_logger: EventLogger | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.log_queue = log_queue
        self.event_logger = event_logger or EventLogger()
        self.server: asyncio.Server | None = None
        self.running = False

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        peer = writer.get_extra_info("peername")
        ip = peer[0] if peer else "unknown"
        port = peer[1] if peer else 0
        ts = datetime.now().strftime("%H:%M:%S")

        await self.log_queue.put(f"[{ts}] 📡 TELNET CONNECT from {ip}:{port}\n")

        try:
            writer.write(b"login: ")
            await writer.drain()
            username = (await asyncio.wait_for(reader.readline(), timeout=30)).decode(
                "utf-8", errors="ignore"
            ).strip()

            writer.write(b"Password: ")
            await writer.drain()
            password = (await asyncio.wait_for(reader.readline(), timeout=30)).decode(
                "utf-8", errors="ignore"
            ).strip()

            location = await geolocate(ip)
            await self.log_queue.put(
                f"[{ts}] 🔑 TELNET AUTH | {ip} [{location}] | user='{username}' pass='{password}'\n"
            )

            self.event_logger.write(
                {
                    "service": "telnet",
                    "ip": ip,
                    "port": port,
                    "location": location,
                    "type": "CRED_HARVEST",
                    "username": username,
                    "password": password,
                }
            )

            # Fake BusyBox shell
            banner = (
                b"\r\nBusyBox v1.33.1 (2021-02-01) built-in shell (ash)\r\n"
                b"Enter 'help' for a list of built-in commands.\r\n\r\n"
                b"# "
            )
            writer.write(banner)
            await writer.drain()

            # Capture a few commands
            for _ in range(5):
                try:
                    line = await asyncio.wait_for(reader.readline(), timeout=45)
                except asyncio.TimeoutError:
                    break
                cmd = line.decode("utf-8", errors="ignore").strip()
                if not cmd:
                    continue
                await self.log_queue.put(f"[{ts}] 💥 TELNET CMD | {ip} | '{cmd}'\n")
                self.event_logger.write(
                    {
                        "service": "telnet",
                        "ip": ip,
                        "type": "COMMAND",
                        "command": cmd,
                    }
                )
                if cmd in ("exit", "logout", "quit"):
                    break
                # Fake responses for common botnet probes
                if any(x in cmd for x in ("wget", "curl", "tftp", "busybox", "chmod", "cd /tmp")):
                    writer.write(b"ok\r\n# ")
                else:
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
        await self.log_queue.put(f"[*] Telnet listening on {self.host}:{self.port}\n")

    async def stop(self) -> None:
        self.running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        await self.log_queue.put(f"[*] Telnet on port {self.port} stopped\n")
