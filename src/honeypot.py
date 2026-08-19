import asyncio
import json
import os
import urllib.parse
import aiohttp
from datetime import datetime

class HonigtopfEngine:
    def __init__(self, host: str, port: int, profile_path: str, log_queue: asyncio.Queue):
        self.host = host
        self.port = port
        self.profile_path = profile_path
        self.log_queue = log_queue
        self.server = None
        self.profile_data = self._load_profile()
        self.session = None

    def _load_profile(self):
        try:
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "template_path" in data and os.path.exists(data["template_path"]):
                    with open(data["template_path"], 'r', encoding='utf-8') as html_f:
                        data["body"] = html_f.read()
                return data
        except Exception:
            return {"status_code": "200 OK", "headers": {"Server": "Honigtopf-Core/1.0"}, "body": "Default Honeypot"}

    async def _geolocate_ip(self, ip: str) -> str:
        if ip in ("127.0.0.1", "localhost") or ip.startswith("192.168.") or ip.startswith("10."):
            return "LOCAL_NET"
        
        try:
            url = f"http://ip-api.com{ip}?fields=status,country,countryCode"
            async with self.session.get(url, timeout=3) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        return f"{data.get('country')} ({data.get('countryCode')})"
        except Exception:
            pass
        return "UNKNOWN_LOCATION"

    def _detect_scanner(self, user_agent: str, request_line: str) -> str:
        ua = user_agent.lower()
        req = request_line.lower()
        if "nmap" in ua: return "Nmap Recon Tool"
        if "shodan" in ua: return "Shodan IoT Crawler"
        if "censys" in ua: return "Censys Inspector"
        if "setup.cgi" in req or "unauth" in req: return "IoT Exploit Botnet (Mirai)"
        return "Web Browser / Probe"

    def _write_persistent_log(self, data: dict):
        try:
            os.makedirs("logs", exist_ok=True)
            with open("logs/honigtopf_master.json", "a", encoding="utf-8") as f:
                f.write(json.dumps(data) + "\n")
        except Exception:
            pass

    async def handle_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        client_ip, client_port = writer.get_extra_info('peername')
        try:
            data = await reader.read(4096)
            if not data:
                writer.close()
                return

            request_text = data.decode('utf-8', errors='ignore')
            parts = request_text.split('\r\n\r\n')
            header_part = parts[0]
            body_part = parts[1] if len(parts) > 1 else ""

            lines = header_part.split('\r\n')
            request_line = lines[0] if lines else "UNKNOWN HTTP REQUEST"
            
            user_agent = "Unknown"
            content_length = 0
            for line in lines:
                if line.lower().startswith("user-agent:"):
                    user_agent = line.split(":", 1)[1].strip()
                if line.lower().startswith("content-length:"):
                    content_length = int(line.split(":", 1)[1].strip())

            timestamp = datetime.now().strftime('%H:%M:%S')
            scanner_type = self._detect_scanner(user_agent, request_line)
            
            location = await self._geolocate_ip(client_ip)

            parsed_url = urllib.parse.urlparse(request_line.split(' ')[1] if len(request_line.split(' ')) > 1 else "/")
            query_params = urllib.parse.parse_qs(parsed_url.query)

            event_log = {
                "timestamp": datetime.now().isoformat(),
                "ip": client_ip,
                "port": client_port,
                "location": location,
                "request": request_line,
                "user_agent": user_agent,
                "type": "RECON"
            }

            if "download" in query_params:
                target_file = query_params["download"][0]
                alert_msg = f"[{timestamp}] 🚨 [EXFILTRATION ATTEMPT] | IP: {client_ip} [{location}] | Tried to download honeyfile: '{target_file}'\n"
                await self.log_queue.put(alert_msg)
                event_log["type"] = "DATA_EXFIL"
                event_log["target_file"] = target_file
                self._write_persistent_log(event_log)

            elif request_line.startswith("POST"):
                if len(body_part.encode('utf-8')) < content_length:
                    remaining = content_length - len(body_part.encode('utf-8'))
                    extra_body = await reader.read(remaining)
                    body_part += extra_body.decode('utf-8', errors='ignore')

                parsed_body = urllib.parse.parse_qs(body_part)
                creds = {k: v for k, v in parsed_body.items()}
                
                alert_msg = f"[{timestamp}] 🔑 [CREDENTIALS CAPTURED] | IP: {client_ip} [{location}] | Auth Data: {json.dumps(creds)}\n"
                await self.log_queue.put(alert_msg)
                event_log["type"] = "CRED_HARVEST"
                event_log["captured_data"] = creds
                self._write_persistent_log(event_log)
                
            else:
                alert_msg = f"[{timestamp}] ⚠️ [HTTP RECON] {scanner_type} | IP: {client_ip} [{location}] | Req: '{request_line}'\n"
                await self.log_queue.put(alert_msg)
                self._write_persistent_log(event_log)

            response_body = self.profile_data['body']
            status = self.profile_data['status_code']
            response_headers = [
                f"HTTP/1.1 {status}",
                f"Server: {self.profile_data['headers'].get('Server', 'Apache')}",
                f"Content-Type: {self.profile_data['headers'].get('Content-Type', 'text/html')}",
                f"Content-Length: {len(response_body.encode('utf-8'))}",
                "Connection: close"
            ]
            full_response = "\r\n".join(response_headers) + "\r\n\r\n" + response_body
            writer.write(full_response.encode('utf-8'))
            await writer.drain()

        except Exception:
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self):
        self.session = aiohttp.ClientSession()
        self.server = await asyncio.start_server(self.handle_request, self.host, self.port)
        await self.log_queue.put(f"[*] HTTP Service Active on http://{self.host}:{self.port}\n")

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        if self.session:
            await self.session.close()
