```markdown
# Honigtopf v4.0

<img width="1366" height="707" alt="Honigtopf Dashboard Preview" src="https://github.com/user-attachments/assets/4aa2a2b5-8a2d-439a-b745-a958fdd0b43d" />
<img width="1176" height="466" alt="Honigtopf GUI Preview" src="https://github.com/user-attachments/assets/645ed904-11ef-43c6-a234-4134e363b687" />

**Enterprise-grade multi-service honeypot framework with real-time telemetry, threat intelligence, and emulated execution environments.**

Honigtopf v4.0 is an advanced defensive security tool designed to simulate multi-vector attack surfaces (HTTP, Telnet, FTP, SMB), capture malicious payload interactions, harvest attacker credentials, and output live visual analytics through a hardened dashboard.

---

## 🚀 Key Features in v4.0

### 🛡️ Core Infrastructure & Services
- **Concurrent Multi-Service Deployment**: Simultaneously run HTTP, Telnet, FTP, and SMB services on configurable ports.
- **Medium-Interaction Shell Emulation**: Telnet service provides a stateful, interactive emulated Linux shell (supporting commands like `ls`, `pwd`, `whoami`, `cat`, `exit`) to prolong engagement and capture post-exploitation command telemetry.
- **18+ Hardware & Service Profiles**: Emulate realistic IoT, router, and server environments (Hikvision, Cisco, Netgear, Synology, Apache, IIS, etc.).
- **Credential Harvesting & Lure Tracking**: Intercept HTTP POST auth attempts, Telnet/FTP logins, and honeyfile exfiltration attempts.
- **SMB Probe Logging**: Capture stealth connection scanning and authorization probes on port 445/4455.

### 🔒 Dashboard Hardening & Analytics
- **Secured Analytics Dashboard**: Live telemetry powered by **FastAPI** and **Plotly.js** with responsive statistical breakdown, location charts, event tables, and auto-refresh mechanisms.
- **HTTP Basic Authentication**: Fully protected endpoints via constant-time basic auth credential checks.
- **API Rate Limiting**: Built-in anti-bruteforce and DDoS protection (`slowapi`) restricting unauthorized API access attempts.
- **Dynamic Credential Management**: On-the-fly password resets via `config/auth.json` or directly through the GUI management window.

### 📢 Integration & Alerts
- **Real-Time Alerting Engine**: Asynchronous multi-platform Webhook notifier (Discord/Microsoft Teams) providing instant critical event dispatching without slowing down honeypot listening sockets.
- **Persistent Storage**: Non-blocking JSON Lines (`.jsonl`) event logger backed by a high-performance thread-safe memory queue[cite: 21].

---

## 📌 Default Listening Ports

To run without elevated root/administrator privileges, high-port defaults are configured out-of-the-box:

| Service | Protocol | Default Port | Emulated Surface |
| :--- | :--- | :--- | :--- |
| **HTTP** | TCP | `8080` | Web Services / Routers / Cameras |
| **Telnet** | TCP | `2323` | Emulated Linux Shell (`Ubuntu 22.04 LTS`) |
| **FTP** | TCP | `2121` | Anonymous & Standard Auth File Servers |
| **SMB** | TCP | `4455` | Network Shares / IPC$ Probes |
| **Dashboard** | TCP | `8050` | Real-time FastAPI Management Console |

*Note: Use standard privileged ports (`80`, `23`, `21`, `445`) by executing with administrative rights or binding through network-level NAT / port forwarding.*

---

## 🛠️ Installation & Setup

### 1. Requirements
Ensure you have Python 3.10+ installed.

```bash
git clone [https://github.com/apex-shift/HonigtopfV4.git](https://github.com/apex-shift/HonigtopfV4.git)
cd HonigtopfV4
pip install -r requirements.txt

```

### 2. Configuration Setup

Create or update your configuration files under `config/`:

**`config/auth.json`** (Dashboard Credentials):

```json
{
  "username": "admin",
  "password": "YourStrongPasswordHere!"
}

```

**`config/settings.json`** (Real-Time Webhook Integration):

```json
{
  "webhook_url": "[https://discord.com/api/webhooks/YOUR_WEBHOOK_URL](https://discord.com/api/webhooks/YOUR_WEBHOOK_URL)"
}

```

---

## ⚡ Execution

Launch the graphical interface management platform:

```bash
python main.py

```

1. **Select Active Services**: Toggle HTTP, Telnet, FTP, or SMB modules.
2. **Configure Network Ports**: Assign custom ports or leave default bindings (`0.0.0.0` for full network coverage).
3. **Select Web Profile**: Choose your HTTP emulation template from `config/profiles/`.
4. **Deploy**: Click **DEPLOY ALL** to spin up async service loops.
5. **Access Dashboard**: Click **Open Dashboard** or navigate to `http://<YOUR_IP>:8050`.

---

## 📡 REST API & Security Specs

All API endpoints are rate-limited and protected behind HTTP Basic Auth.

| Endpoint | Method | Rate Limit | Description |
| --- | --- | --- | --- |
| `/` | `GET` | `60 req/min` | Visual Plotly HTML dashboard interface |
| `/api/stats` | `GET` | `30 req/min` | Aggregated global statistics & metadata

 |
| `/api/events` | `GET` | `30 req/min` | Filtered log queries (`ip`, `location`, `type`, `service`)

 |

---

## 📂 Project Architecture

```text
HonigtopfV4/
├── main.py                   # Main GUI Entrypoint
├── config/
│   ├── auth.json             # Dynamic Auth Credentials
│   ├── settings.json         # Global Integrations (Webhooks)
│   └── profiles/             # Web Service Emulation Templates
│       └── templates/
├── src/
│   ├── core/
│   │   ├── events.py         # Thread-safe Event Store & Dispatcher
│   │   ├── manager.py        # Async Lifecycle Service Manager
│   │   └── notifier.py       # Real-time Webhook Notification Engine
│   ├── services/             # Low & Medium Interaction Drivers
│   │   ├── http_hp.py
│   │   ├── telnet_hp.py      # Stateful Interactive Shell Simulator
│   │   ├── ftp_hp.py
│   │   └── smb_hp.py
│   ├── dashboard/            # FastAPI + Rate Limiter + Plotly Interface
│   │   └── app.py
│   └── gui.py                # CustomTkinter GUI & Auth Management
├── logs/
│   └── events.jsonl          # Persistent Raw Log Storage
└── reports/                  # Analytics Exports

```

---

## ⚠️ Disclaimer

This software is developed strictly for **authorized defensive research, security monitoring, and educational purposes**. Deploy this honeypot only within environments you own or explicitly have authorization to monitor. The developers assume no liability for misuse or unauthorized deployment.

```

```