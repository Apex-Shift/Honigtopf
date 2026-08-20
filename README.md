# Honigtopf v2

**Multi-service IoT & server honeypot framework.**

Honigtopf (German for *honeypot*) is an asynchronous deception framework that emulates vulnerable IoT devices, routers, cameras, printers, NAS systems and classic web servers. It captures reconnaissance probes, credential stuffing attempts and file-exfiltration lures while presenting convincing login pages and service banners.

---

## Features

- **18 ready-to-use profiles**  
  Hikvision, Dahua, Axis, Cisco, Netgear, TP-Link, D-Link, ASUS, MikroTik, HP LaserJet, Synology, QNAP, Apache, Nginx, IIS, Tomcat, WordPress, phpMyAdmin
- **HTTP + Telnet** honeypots running concurrently
- **Credential harvesting** from POST forms
- **Honeyfile download lure** detection
- **Live geolocation** of attackers
- **Persistent JSONL logging**
- **Modern dark CustomTkinter GUI**
- Fully asynchronous (`asyncio`) – UI never freezes

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

1. Choose a profile from the dropdown  
2. Set HTTP and Telnet ports  
3. Click **DEPLOY HIVE**

---

## Project Layout

```
Honigtopf/
├── main.py
├── requirements.txt
├── config/
│   ├── profiles/          # 18 JSON profiles
│   └── templates/         # Matching HTML pages
├── src/
│   ├── engine.py          # HTTP honeypot
│   ├── telnet.py          # Telnet / BusyBox honeypot
│   ├── geoloc.py
│   ├── logger.py
│   └── gui.py
└── logs/
    └── honigtopf_master.jsonl
```

---

## Adding a New Profile

1. Create `config/profiles/mydevice.json`
2. Create `config/templates/mydevice.html`
3. Click the ↻ button in the GUI (or restart)

Example profile:

```json
{
  "name": "mydevice",
  "description": "My custom device",
  "status_code": "200 OK",
  "headers": {
    "Server": "MyDevice/1.0",
    "Content-Type": "text/html"
  },
  "template_path": "config/templates/mydevice.html"
}
```

---

## Disclaimer

For authorized defensive research and education only.  
Deploy only on networks you own or have explicit permission to monitor.  
The authors accept no liability for misuse.

---

**Honigtopf v2** — make the attackers waste their time.
