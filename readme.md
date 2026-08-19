# 🍯 Honigtopf

Honigtopf (German for *Honeypot*) is a high-performance, asynchronous multi-service IoT deception framework designed to mislead automated scanners, crawlers, and malicious threat actors. By emulating legacy headers, vulnerable software banners, and fully functional device dashboards, Honigtopf creates convincing digital illusions to actively capture reconnaissance data, credential harvesting attempts, and file exfiltration tactics.

Equipped with a modern dark-themed CustomTkinter GUI and driven by a non-blocking `asyncio` backend, Honigtopf allows security professionals to deploy multiple honeypot profiles simultaneously on custom ports alongside an active Telnet monitoring hive.

---

## ✨ Key Features

- **Multi-Service Concurrent Spawning:** Deploy separate honeypot instances simultaneously (e.g., Hikvision DVR on port 80, Netgear Gateway on port 8080, HP LaserJet on port 9000).
- **Asynchronous Protocol Architecture:** Engineered with high-performance `asyncio` and `aiohttp` to ensure responsive multi-socket operations without interface freezes.
- **Deceptive IoT Profile System:** Modular design driven by `.json` configuration headers coupled with fully customized, realistic `.html` landing pages (Cisco IOS, Apache CentOS, IIS, Netgear Smart Wizard, and Hikvision Login).
- **Real-Time Global Geolocation:** Intercepts incoming connections and resolves attacker origin (Country and Code) on-the-fly using asynchronous network telemetry.
- **Advanced Attack Interception:**
  - **Credential Harvester:** Captures raw parameters (`username`, `password`, `pin`) from form submissions (`POST`).
  - **Exfiltration Lure:** Tracks interactions with decoy sensitive files (e.g., clicking on `backup_db.sql`).
- **Integrated Telnet Core:** Emulates a standard BusyBox shell environments on port 23 to capture automated botnet brute-force credentials and initial payloads.
- **Persistent JSON Logger:** Automatically archives every individual threat telemetry trace locally under centralized logs for post-incident parsing.

---

## 📂 Project Architecture

```text
Honigtopf/
│
├── config/
│   ├── profiles/           # Software header definitions (.json)
│   │   ├── apache.json
│   │   ├── cisco.json
│   │   ├── dvr_hikvision.json
│   │   ├── iis.json
│   │   ├── printer_hp.json
│   │   └── router_gateway.json
│   │
│   └── templates/          # Deceptive frontend mirages (.html)
│       ├── apache.html
│       ├── cisco.html
│       ├── hikvision.html
│       ├── iis.html
│       ├── hp_printer.html
│       └── router_gateway.html
│
├── src/
│   ├── honeypot.py         # Asynchronous HTTP Engine & Threat Logic
│   ├── telnet_core.py      # Independent Telnet Botnet Honeypot Core
│   └── gui.py              # CustomTkinter Multi-Service Desktop App
│
├── logs/
│   └── honigtopf_master.json # Persistent attack telemetry log storage
│
└── main.py                 # Core bootloader and execution entrypoint
```

---

## 🚀 Installation & Deployment

### Prerequisites
Ensure you have Python 3.10+ installed.

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com
   cd Honigtopf
   ```

2. Install the required non-blocking dependencies:
   ```bash
   pip install customtkinter aiohttp
   ```

3. Launch the Deception Control Center:
   ```bash
   python main.py
   ```

4. Configure your desired target ports inside the graphical table panel, select your profile nodes, and click **LAUNCH** to engage the trap arrays.

---

## 🛡️ Disclaimer

**CRITICAL NOTICE:** This software is provided for educational, research, and authorized defensive simulation purposes only. The user assumes all responsibility for its implementation. The developer is completely exempt from any liability regarding unintended operational issues, network exposure risks, or malicious use cases violating local cyber legislations. Always deploy honeypots within controlled, authorized staging environments.
