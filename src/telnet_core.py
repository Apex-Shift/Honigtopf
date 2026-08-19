import asyncio
from datetime import datetime

class HonigtopfTelnet:
    def __init__(self, host: str, port: int, log_queue: asyncio.Queue):
        self.host = host
        self.port = port
        self.log_queue = log_queue
        self.server = None

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        client_ip, client_port = writer.get_extra_info('peername')
        timestamp = datetime.now().strftime('%H:%M:%S')
        await self.log_queue.put(f"[{timestamp}] 📡 TELNET CONNECT: Attacker from {client_ip}:{client_port}\n")

        try:
            # 1. Demande de Username
            writer.write(b"Verification login: ")
            await writer.drain()
            username = (await reader.readline()).decode('utf-8', errors='ignore').strip()

            # 2. Demande de Password
            writer.write(b"Password: ")
            await writer.drain()
            password = (await reader.readline()).decode('utf-8', errors='ignore').strip()

            # Log des identifiants interceptés
            await self.log_queue.put(f"[{timestamp}] 🔑 TELNET BRUTEFORCE -> IP: {client_ip} | User: '{username}' | Pass: '{password}'\n")

            # 3. Simulation d'un shell BusyBox IoT
            writer.write(b"\n\nWelcome to BusyBox v1.22.1 (Cisco IOS Emulator)\n$ ")
            await writer.drain()

            # Lecture de la commande envoyée par l'attaquant ou le botnet
            command_data = await reader.readline()
            command = command_data.decode('utf-8', errors='ignore').strip()

            if command:
                await self.log_queue.put(f"[{timestamp}] 💥 TELNET COMMAND: IP: {client_ip} | Cmd: '{command}'\n")
                # Réponse générique pour faire croire au botnet que l'exécution a réussi
                writer.write(b"auth_ok\n$ ")
                await writer.drain()

        except Exception as e:
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self):
        self.server = await asyncio.start_server(self.handle_client, self.host, self.port)
        await self.log_queue.put(f"[*] Telnet Service Active on port {self.port} (Monitoring Botnets)\n")

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
