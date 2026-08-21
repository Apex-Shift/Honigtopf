# Honigtopf v3.1
<img width="1366" height="707" alt="Sans titre" src="https://github.com/user-attachments/assets/4aa2a2b5-8a2d-439a-b745-a958fdd0b43d" />
<img width="1176" height="466" alt="Sans titre2" src="https://github.com/user-attachments/assets/645ed904-11ef-43c6-a234-4134e363b687" />

**Multi-service honeypot framework with advanced Plotly dashboard.**

Launch HTTP (IoT/router/server profiles), Telnet, FTP and SMB honeypots at the same time.  
All events are logged and visualized in a live web dashboard with filters and charts.

---

## Features

- **Multi-service concurrent deploy** — HTTP + Telnet + FTP + SMB together
- **18+ IoT / router / server profiles** (Hikvision, Cisco, Netgear, Synology, …)
- **Credential harvesting** on HTTP POST, Telnet, FTP
- **Honeyfile exfil lure** detection
- **SMB connection logger** (port 445 probes)
- **Live web dashboard** (Plotly):
  - Stats cards
  - Pie / bar / timeline charts
  - Filters by IP, location, type, service
  - Auto-refresh every 15s
- **Persistent JSONL event store**

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

1. Tick the services you want (HTTP / Telnet / FTP / SMB)
2. Set ports (defaults avoid privileged ports: 8080, 2323, 2121, 4455)
3. Click **DEPLOY ALL**
4. Open **Dashboard** → http://127.0.0.1:8050

---

## Default ports (non-root friendly)

| Service | Default port |
|---------|--------------|
| HTTP    | 8080         |
| Telnet  | 2323         |
| FTP     | 2121         |
| SMB     | 4455         |

Use 21 / 23 / 445 only if you run as root / admin and your provider allows it.

---

## Dashboard API

- `GET /` — HTML dashboard
- `GET /api/stats` — aggregated stats
- `GET /api/events?ip=&type=&service=&location=` — filtered events

---

## Project layout

```
HonigtopfV3/
├── main.py
├── config/profiles/ + templates/
├── src/
│   ├── core/          # events, geoloc, manager
│   ├── services/      # http, telnet, ftp, smb
│   ├── dashboard/     # FastAPI + Plotly
│   └── gui.py
├── logs/events.jsonl
└── reports/
```

---

## Disclaimer

Authorized defensive research only. Deploy only on systems you own or are allowed to monitor.
