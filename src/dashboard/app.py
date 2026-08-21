"""Honigtopf V4 — Dashboard API with Rate Limiting and Full HTML Interface."""

from __future__ import annotations

import json
import os
import secrets
from fastapi import FastAPI, Request, Query, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.core.events import store

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Honigtopf Dashboard v4", version="4.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

security = HTTPBasic()
AUTH_CONFIG_PATH = "config/auth.json"


def load_credentials() -> tuple[str, str]:
    if not os.path.exists(AUTH_CONFIG_PATH):
        return "admin", "StrongDashboardPassword123!"
    try:
        with open(AUTH_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            return cfg.get("username", "admin"), cfg.get("password", "StrongDashboardPassword123!")
    except Exception:
        return "admin", "StrongDashboardPassword123!"


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    user, pwd = load_credentials()
    if not (secrets.compare_digest(credentials.username, user) and secrets.compare_digest(credentials.password, pwd)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


DASHBOARD_HTML = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Honigtopf v4 — Attack Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; font-family: 'Segoe UI', system-ui, sans-serif; background: #0d1117; color: #e6edf3; }
    header { background: #161b22; padding: 16px 24px; border-bottom: 1px solid #30363d; display: flex; align-items: center; gap: 20px; }
    header h1 { margin: 0; font-size: 1.4rem; color: #58a6ff; }
    .stats { display: flex; gap: 16px; flex-wrap: wrap; padding: 16px 24px; }
    .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px 20px; min-width: 140px; }
    .card .n { font-size: 1.8rem; font-weight: 700; color: #3fb950; }
    .card .l { font-size: 0.8rem; color: #8b949e; margin-top: 4px; }
    .filters { padding: 0 24px 12px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    .filters input, .filters select { background: #0d1117; border: 1px solid #30363d; color: #e6edf3; padding: 8px 12px; border-radius: 6px; }
    .filters button { background: #238636; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; }
    .filters button:hover { background: #2ea043; }
    .charts { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 0 24px 16px; }
    .chart-box { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px; }
    .table-wrap { padding: 0 24px 24px; }
    table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #21262d; }
    th { color: #8b949e; font-weight: 600; }
    tr:hover td { background: #161b22; }
    .tag { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: 600; }
    .tag-cred { background: #3d1f1f; color: #f85149; }
    .tag-recon { background: #1f3d2a; color: #3fb950; }
    .tag-cmd { background: #3d3a1f; color: #d29922; }
    .tag-exfil { background: #3d1f3a; color: #db61a2; }
  </style>
</head>
<body>
  <header>
    <h1>🍯 Honigtopf v4 Dashboard</h1>
    <span style="color:#8b949e;font-size:0.9rem">Live attack telemetry</span>
  </header>

  <div class="stats" id="stats"></div>

  <div class="filters">
    <input id="f_ip" placeholder="Filter IP" />
    <input id="f_loc" placeholder="Filter location" />
    <select id="f_type">
      <option value="">All types</option>
      <option value="RECON">RECON</option>
      <option value="CRED_HARVEST">CRED_HARVEST</option>
      <option value="COMMAND">COMMAND</option>
      <option value="DATA_EXFIL">DATA_EXFIL</option>
    </select>
    <select id="f_service">
      <option value="">All services</option>
      <option value="http">http</option>
      <option value="telnet">telnet</option>
      <option value="ftp">ftp</option>
      <option value="smb">smb</option>
    </select>
    <button onclick="refresh()">Apply filters</button>
    <button onclick="refresh()" style="background:#21262d">↻ Refresh</button>
  </div>

  <div class="charts">
    <div class="chart-box"><div id="chart_type"></div></div>
    <div class="chart-box"><div id="chart_service"></div></div>
    <div class="chart-box"><div id="chart_country"></div></div>
    <div class="chart-box"><div id="chart_timeline"></div></div>
  </div>

  <div class="table-wrap">
    <h3 style="color:#8b949e;font-weight:500">Recent events</h3>
    <table>
      <thead>
        <tr><th>Time</th><th>Service</th><th>Type</th><th>IP</th><th>Location</th><th>Detail</th></tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>

<script>
async function refresh() {
  const params = new URLSearchParams();
  const ip = document.getElementById('f_ip').value;
  const loc = document.getElementById('f_loc').value;
  const type = document.getElementById('f_type').value;
  const service = document.getElementById('f_service').value;
  if (ip) params.set('ip', ip);
  if (loc) params.set('location', loc);
  if (type) params.set('type', type);
  if (service) params.set('service', service);

  const [stats, events] = await Promise.all([
    fetch('/api/stats').then(r => r.json()),
    fetch('/api/events?' + params.toString()).then(r => r.json())
  ]);

  document.getElementById('stats').innerHTML = `
    <div class="card"><div class="n">${stats.total}</div><div class="l">Total events</div></div>
    <div class="card"><div class="n">${stats.unique_ips}</div><div class="l">Unique IPs</div></div>
    <div class="card"><div class="n">${stats.by_type.CRED_HARVEST || 0}</div><div class="l">Credentials</div></div>
    <div class="card"><div class="n">${stats.by_type.DATA_EXFIL || 0}</div><div class="l">Exfil attempts</div></div>
  `;

  // Charts
  const typeLabels = Object.keys(stats.by_type);
  const typeVals = Object.values(stats.by_type);
  Plotly.newPlot('chart_type', [{
    labels: typeLabels, values: typeVals, type: 'pie',
    marker: { colors: ['#3fb950','#f85149','#d29922','#db61a2','#58a6ff'] }
  }], { title: 'By type', paper_bgcolor: '#161b22', plot_bgcolor: '#161b22', font: { color: '#e6edf3' }, height: 280 }, {responsive: true});

  const svcLabels = Object.keys(stats.by_service);
  const svcVals = Object.values(stats.by_service);
  Plotly.newPlot('chart_service', [{
    x: svcLabels, y: svcVals, type: 'bar', marker: { color: '#58a6ff' }
  }], { title: 'By service', paper_bgcolor: '#161b22', plot_bgcolor: '#161b22', font: { color: '#e6edf3' }, height: 280 }, {responsive: true});

  const cLabels = Object.keys(stats.by_country).slice(0, 12);
  const cVals = cLabels.map(k => stats.by_country[k]);
  Plotly.newPlot('chart_country', [{
    x: cVals, y: cLabels, type: 'bar', orientation: 'h', marker: { color: '#3fb950' }
  }], { title: 'Top locations', paper_bgcolor: '#161b22', plot_bgcolor: '#161b22', font: { color: '#e6edf3' }, height: 280, margin: { l: 120 } }, {responsive: true});

  // Timeline
  const hours = {};
  events.forEach(e => {
    const h = (e.timestamp || '').slice(0, 13);
    if (h) hours[h] = (hours[h] || 0) + 1;
  });
  const tLabels = Object.keys(hours).sort();
  const tVals = tLabels.map(k => hours[k]);
  Plotly.newPlot('chart_timeline', [{
    x: tLabels, y: tVals, type: 'scatter', mode: 'lines+markers', line: { color: '#d29922' }
  }], { title: 'Activity timeline', paper_bgcolor: '#161b22', plot_bgcolor: '#161b22', font: { color: '#e6edf3' }, height: 280 }, {responsive: true});

  // Events Table
  const tagClass = t => {
    if (t === 'CRED_HARVEST') return 'tag-cred';
    if (t === 'COMMAND') return 'tag-cmd';
    if (t === 'DATA_EXFIL') return 'tag-exfil';
    return 'tag-recon';
  };
  const detail = e => {
    if (e.username) return `user=${e.username} pass=${e.password || ''}`;
    if (e.command) return e.command;
    if (e.target) return e.target;
    if (e.request) return e.request;
    if (e.captured) return JSON.stringify(e.captured);
    return e.path || '';
  };
  document.getElementById('tbody').innerHTML = events.slice(0, 100).map(e => `
    <tr>
      <td>${(e.timestamp || '').replace('T',' ').slice(0,19)}</td>
      <td>${e.service || ''}</td>
      <td><span class="tag ${tagClass(e.type)}">${e.type || ''}</span></td>
      <td>${e.ip || ''}</td>
      <td>${e.location || ''}</td>
      <td style="max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${detail(e)}</td>
    </tr>
  `).join('');
}

refresh();
setInterval(refresh, 15000);
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def dashboard(request: Request, username: str = Depends(verify_credentials)):
    return HTMLResponse(DASHBOARD_HTML)


@app.get("/api/stats")
@limiter.limit("30/minute")
async def api_stats(request: Request, username: str = Depends(verify_credentials)):
    return JSONResponse(store.stats())


@app.get("/api/events")
@limiter.limit("30/minute")
async def api_events(
    request: Request,
    ip: str = Query(""),
    location: str = Query(""),
    type: str = Query(""),
    service: str = Query(""),
    limit: int = Query(200),
    username: str = Depends(verify_credentials),
):
    filters = {}
    if ip:
        filters["ip"] = ip
    if location:
        filters["location"] = location
    if type:
        filters["type"] = type
    if service:
        filters["service"] = service
    return JSONResponse(store.recent(limit=limit, **filters))