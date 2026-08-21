<img width="1366" height="720" alt="Sans titre" src="https://github.com/user-attachments/assets/a96f9117-adae-46b6-804e-0ccb5b6bbade" />

# Honigtopf v5.0

**Enterprise-grade multi-service honeypot framework with interactive emulation, real-time Webhook telemetry, rate-limited analytics, and native Docker / Headless CLI support.**

Honigtopf v5.0 is a modular defensive cybersecurity platform built to simulate multi-vector network surfaces (HTTP, Telnet, FTP, SMB), capture post-exploitation interaction, log attacker credentials, and dispatch instant security alerts via Webhooks and an isolated Plotly dashboard.

---

## 🚀 Key Features

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
- **Persistent Storage**: Non-blocking JSON Lines (`.jsonl`) event logger backed by a high-performance thread-safe memory queue [21].

### 🐳 Production & Headless Readiness
- **Native Decoupled CLI (`cli.py`)**: Fully scriptable command-line interface designed for server environments (headless VPS, Ansible, systemd). No GUI dependencies required.
- **Docker & Docker Compose**: Minimal Multi-Stage Alpine build running under a dedicated non-privileged user (`UID 1000`).
- **Low-Port Binding via Port Forwarding**: Expose standard privileged ports (`80`, `23`, `21`, `445`) safely mapped to internal non-root listening sockets without ever running Python as `root`.
- **System Health Checks**: Built-in socket auditing, configuration validation, and log health reporting (`python cli.py status`).

---

## 📌 Default Port Mapping & Privileged Rerouting

To maintain security, Honigtopf listens on unprivileged ports internally, while Docker or `iptables` maps them to standard network entrypoints:

| Service | Protocol | Internal Port | Standard Port (Docker) | Feature / Emulated Surface |
| :--- | :--- | :--- | :--- | :--- |
| **HTTP** | TCP | `8080` | `80` | IoT / Routers / Server Profiles |
| **Telnet** | TCP | `2323` | `23` | Emulated Stateful Shell (`Ubuntu 22.04`) |
| **FTP** | TCP | `2121` | `21` | Credential Harvesting & Honeyfile Lures |
| **SMB** | TCP | `4455` | `445` | IPC$ & Share Discovery Probe Logging |
| **Dashboard**| TCP | `8050` | `8050` (Localhost) | Rate-Limited Plotly Visual Analytics |

---

## 🛠️ Quick Start Guide

### Option 1: Deployment via Docker Compose (Recommended)

1. **Clone & Configure**:
   ```bash
   git clone https://github.com/your-repo/HonigtopfV5.git
   cd HonigtopfV5
   ```

2. **Setup Configurations**:
   * **`config/auth.json`** (Dashboard Credentials):
     ```json
     {
       "username": "admin",
       "password": "YourStrongPasswordHere!"
     }
     ```
   * **`config/settings.json`** (Real-Time Alert Webhooks):
     ```json
     {
       "webhook_url": "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
     }
     ```

3. **Deploy Container**:
   ```bash
   docker-compose up -d --build
   ```

4. **Verify Health**:
   ```bash
   docker exec honigtopf_v5_core python cli.py status
   ```

### Option 2: Local CLI Execution (Headless)

```bash
# Install dependencies
pip install -r requirements.txt

# Start default services (HTTP + Telnet)
python cli.py start --services http telnet

# Start all services with custom ports
python cli.py start --services http telnet ftp smb --http-port 8080 --telnet-port 2323

# Check system & socket health
python cli.py status
```

### Option 3: Graphical Interface (Desktop)

For local desktop monitoring with CustomTkinter GUI:
```bash
python main.py
```

---

## 💻 CLI Command Reference

Honigtopf includes a built-in CLI interface (`cli.py`) for automated deployments:

```plaintext
usage: cli.py [-h] {start,status} ...

Honigtopf v5.0 - Interface Ligne de Commande

positional arguments:
  {start,status}
    start        Démarrer les services de déception
    status       Vérifier la santé du framework et l'état des ports

options:
  -h, --help     show this help message and exit
```

### Start Flags (`cli.py start`)
* `--services`: List of services to activate (`http`, `telnet`, `ftp`, `smb`).
* `--http-port`: Override HTTP port.
* `--telnet-port`: Override Telnet port.
* `--ftp-port`: Override FTP port.
* `--smb-port`: Override SMB port.

---

## 📡 REST API Specifications

All endpoints require HTTP Basic Auth credentials (defined in `config/auth.json`) and are protected by rate limiting.

| Endpoint | Method | Rate Limit | Description |
| :--- | :--- | :--- | :--- |
| `/` | GET | 60 req/min | Interactive Plotly visual dashboard |
| `/api/stats` | GET | 30 req/min | Summary statistics (by type, country, service) |
| `/api/events` | GET | 30 req/min | Filtered raw logs (ip, service, type, location) |

---

## 📂 Project Structure

```plaintext
HonigtopfV5/
├── cli.py                    # Production CLI Entrypoint (Headless)
├── main.py                   # CustomTkinter Desktop GUI Entrypoint
├── Dockerfile                # Multi-stage Non-Root Alpine Build
├── docker-compose.yml        # Container Orchestration & Port Forwarding
├── config/
│   ├── auth.json             # Dashboard Basic Auth Credentials
│   ├── settings.json         # Webhook Integration Config
│   └── profiles/             # Web Emulation Templates
├── src/
│   ├── core/
│   │   ├── events.py         # Thread-safe Event Store & Notifier Dispatcher
│   │   ├── manager.py        # Service Async Manager
│   │   └── notifier.py       # Asynchronous Webhook Alert Engine
│   ├── services/
│   │   ├── http_hp.py        # Web Profile Emulation Engine
│   │   ├── telnet_hp.py      # Medium-Interaction Stateful Shell
│   │   ├── ftp_hp.py         # Credential & Lure Capture
│   │   └── smb_hp.py         # SMB Probe Logging
│   ├── dashboard/
│   │   └── app.py            # FastAPI + Plotly Analytics + Rate Limiter
│   └── gui.py                # Desktop GUI Module
├── logs/
│   └── events.jsonl          # Persistent Event Storage (JSON Lines)
└── reports/                  # Analytics & Export Summaries
```

---

## ⚠ Disclaimer

This framework is developed exclusively for authorized defensive security research, threat intelligence collection, and educational monitoring. Deploy Honigtopf only on infrastructure you own or have explicit authorization to monitor. The author assumes no responsibility for unauthorized deployment or misuse.
