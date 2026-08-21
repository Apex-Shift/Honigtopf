"""Honigtopf V3 control GUI – multi-service launcher."""

from __future__ import annotations

import asyncio
import os
import threading
import webbrowser

import customtkinter as ctk

from src.core.manager import ServiceManager

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class HonigtopfGUI(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Honigtopf v4 — Multi-Service Honeypot")
        self.geometry("1000x720")
        self.minsize(880, 600)

        self.manager = ServiceManager()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.is_running = False
        self._dash_thread = None

        self._build()

    def _build(self) -> None:
        # Header
        top = ctk.CTkFrame(self, corner_radius=0)
        top.pack(fill="x")
        ctk.CTkLabel(
            top, text="🍯 Honigtopf v3", font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left", padx=16, pady=12)
        ctk.CTkButton(
            top, text="Open Dashboard", width=130, command=self._open_dashboard
        ).pack(side="right", padx=16, pady=12)

        # Config grid
        cfg = ctk.CTkFrame(self)
        cfg.pack(fill="x", padx=16, pady=10)

        # HTTP
        row1 = ctk.CTkFrame(cfg, fg_color="transparent")
        row1.pack(fill="x", pady=4)
        self.chk_http = ctk.CTkCheckBox(row1, text="HTTP")
        self.chk_http.select()
        self.chk_http.pack(side="left", padx=8)
        ctk.CTkLabel(row1, text="Port").pack(side="left")
        self.ent_http_port = ctk.CTkEntry(row1, width=70)
        self.ent_http_port.insert(0, "8080")
        self.ent_http_port.pack(side="left", padx=6)
        ctk.CTkLabel(row1, text="Profile").pack(side="left", padx=(12, 4))
        profiles = self._list_profiles()
        self.cmb_profile = ctk.CTkComboBox(row1, values=profiles or ["apache"], width=160)
        if profiles:
            self.cmb_profile.set(profiles[0])
        self.cmb_profile.pack(side="left")

        # Extra HTTP instances note
        ctk.CTkLabel(
            cfg,
            text="Tip: add more HTTP listeners by deploying again with different ports after stop, or edit manager in code for multi-HTTP.",
            text_color="#666",
            font=ctk.CTkFont(size=11),
        ).pack(anchor="w", padx=12)

        # Telnet / FTP / SMB
        row2 = ctk.CTkFrame(cfg, fg_color="transparent")
        row2.pack(fill="x", pady=6)
        self.chk_telnet = ctk.CTkCheckBox(row2, text="Telnet")
        self.chk_telnet.select()
        self.chk_telnet.pack(side="left", padx=8)
        self.ent_telnet = ctk.CTkEntry(row2, width=60)
        self.ent_telnet.insert(0, "2323")
        self.ent_telnet.pack(side="left")

        self.chk_ftp = ctk.CTkCheckBox(row2, text="FTP")
        self.chk_ftp.select()
        self.chk_ftp.pack(side="left", padx=(20, 4))
        self.ent_ftp = ctk.CTkEntry(row2, width=60)
        self.ent_ftp.insert(0, "2121")
        self.ent_ftp.pack(side="left")

        self.chk_smb = ctk.CTkCheckBox(row2, text="SMB")
        self.chk_smb.pack(side="left", padx=(20, 4))
        self.ent_smb = ctk.CTkEntry(row2, width=60)
        self.ent_smb.insert(0, "4455")
        self.ent_smb.pack(side="left")

        # Buttons
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=6)
        self.btn_toggle = ctk.CTkButton(
            btns,
            text="DEPLOY ALL",
            width=160,
            height=40,
            fg_color="#27ae60",
            hover_color="#1e8449",
            font=ctk.CTkFont(weight="bold"),
            command=self.toggle,
        )
        self.btn_toggle.pack(side="left")
        self.lbl_status = ctk.CTkLabel(btns, text="Idle", text_color="#888")
        self.lbl_status.pack(side="left", padx=16)

        # Log
        self.txt = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=13), fg_color="#0d0d0d")
        self.txt.pack(fill="both", expand=True, padx=16, pady=12)
        self._log("[*] Honigtopf v3 ready. Select services and deploy.\n")
        self._log("[*] Dashboard will be at http://127.0.0.1:8050\n")

    def _list_profiles(self) -> list[str]:
        d = "config/profiles"
        if not os.path.isdir(d):
            return []
        return sorted(os.path.splitext(f)[0] for f in os.listdir(d) if f.endswith(".json"))

    def _log(self, msg: str) -> None:
        self.txt.insert("end", msg)
        self.txt.see("end")

    def toggle(self) -> None:
        if not self.is_running:
            self._start()
        else:
            self._stop()

    def _start(self) -> None:
        self.manager = ServiceManager()
        host = "0.0.0.0"

        if self.chk_http.get():
            port = int(self.ent_http_port.get())
            prof = self.cmb_profile.get()
            path = f"config/profiles/{prof}.json"
            self.manager.add_http(host, port, path)

        if self.chk_telnet.get():
            self.manager.add_telnet(host, int(self.ent_telnet.get()))

        if self.chk_ftp.get():
            self.manager.add_ftp(host, int(self.ent_ftp.get()))

        if self.chk_smb.get():
            self.manager.add_smb(host, int(self.ent_smb.get()))

        if not self.manager.services:
            self._log("[-] No service selected\n")
            return

        self.is_running = True
        self.btn_toggle.configure(text="SHUTDOWN ALL", fg_color="#c0392b")
        self.lbl_status.configure(text="Running", text_color="#2ecc71")
        threading.Thread(target=self._run_loop, daemon=True).start()
        self._start_dashboard()

    def _stop(self) -> None:
        self.is_running = False
        self.btn_toggle.configure(text="DEPLOY ALL", fg_color="#27ae60")
        self.lbl_status.configure(text="Stopped", text_color="#e74c3c")
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._async_stop(), self.loop)

    async def _async_stop(self) -> None:
        msgs = await self.manager.stop_all()
        for m in msgs:
            self.after(0, lambda x=m: self._log(x + "\n"))
        self.loop.call_soon_threadsafe(self.loop.stop)

    def _run_loop(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        async def boot():
            msgs = await self.manager.start_all()
            for m in msgs:
                self.after(0, lambda x=m: self._log(x + "\n"))
            self.after(0, lambda: self._log("[*] All selected services are up.\n"))

        self.loop.create_task(boot())
        self.loop.run_forever()

    def _start_dashboard(self) -> None:
        def run():
            import uvicorn
            from src.dashboard.app import app
            # Bind to 0.0.0.0 to allow access from local network / router IP
            uvicorn.run(app, host="0.0.0.0", port=8050, log_level="warning")

        if self._dash_thread is None or not self._dash_thread.is_alive():
            self._dash_thread = threading.Thread(target=run, daemon=True)
            self._dash_thread.start()
            self._log("[*] Dashboard running at: http://0.0.0.0:8050\n")

    def _open_dashboard(self) -> None:
        webbrowser.open("http://127.0.0.1:8050")
