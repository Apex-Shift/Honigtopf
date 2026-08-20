"""Honigtopf V2 – Professional dark GUI."""

from __future__ import annotations

import asyncio
import os
import threading
from datetime import datetime

import customtkinter as ctk

from src.engine import HonigtopfHTTP
from src.logger import EventLogger
from src.telnet import HonigtopfTelnet

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class HonigtopfGUI(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Honigtopf  v2 — Multi-Service Honeypot Framework")
        self.geometry("980x680")
        self.minsize(860, 580)

        self.loop: asyncio.AbstractEventLoop | None = None
        self.log_queue: asyncio.Queue | None = None
        self.http_engines: list[HonigtopfHTTP] = []
        self.telnet_engine: HonigtopfTelnet | None = None
        self.is_running = False
        self.event_logger = EventLogger()

        self._build_ui()
        self._refresh_profiles()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        # Top control bar
        top = ctk.CTkFrame(self, corner_radius=0)
        top.pack(fill="x", padx=0, pady=0)

        inner = ctk.CTkFrame(top, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(inner, text="HTTP Port", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 4))
        self.ent_http = ctk.CTkEntry(inner, width=70)
        self.ent_http.insert(0, "8080")
        self.ent_http.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(inner, text="Telnet Port", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 4))
        self.ent_telnet = ctk.CTkEntry(inner, width=60)
        self.ent_telnet.insert(0, "23")
        self.ent_telnet.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(inner, text="Profile", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 4))
        self.cmb_profile = ctk.CTkComboBox(inner, width=180, values=["loading…"])
        self.cmb_profile.pack(side="left", padx=(0, 12))

        self.btn_refresh = ctk.CTkButton(
            inner, text="↻", width=36, command=self._refresh_profiles
        )
        self.btn_refresh.pack(side="left", padx=(0, 16))

        self.btn_toggle = ctk.CTkButton(
            inner,
            text="DEPLOY HIVE",
            width=140,
            height=36,
            fg_color="#27ae60",
            hover_color="#1e8449",
            font=ctk.CTkFont(weight="bold"),
            command=self.toggle,
        )
        self.btn_toggle.pack(side="right")

        # Status line
        self.lbl_status = ctk.CTkLabel(
            self, text="Ready — select a profile and deploy", text_color="#888", anchor="w"
        )
        self.lbl_status.pack(fill="x", padx=20, pady=(4, 0))

        # Log area
        log_frame = ctk.CTkFrame(self)
        log_frame.pack(fill="both", expand=True, padx=16, pady=12)

        self.txt_logs = ctk.CTkTextbox(
            log_frame, font=ctk.CTkFont(family="Consolas", size=13), fg_color="#0d0d0d"
        )
        self.txt_logs.pack(fill="both", expand=True, padx=8, pady=8)

        # Bottom bar
        bottom = ctk.CTkFrame(self, height=36, corner_radius=0)
        bottom.pack(fill="x", side="bottom")
        self.lbl_footer = ctk.CTkLabel(
            bottom,
            text="Honigtopf v2  •  Authorized defensive use only",
            text_color="#555",
            font=ctk.CTkFont(size=11),
        )
        self.lbl_footer.pack(side="left", padx=16, pady=6)

    def _refresh_profiles(self) -> None:
        profiles_dir = "config/profiles"
        if os.path.isdir(profiles_dir):
            names = sorted(
                os.path.splitext(f)[0]
                for f in os.listdir(profiles_dir)
                if f.endswith(".json")
            )
        else:
            names = []
        if not names:
            names = ["(no profiles found)"]
        self.cmb_profile.configure(values=names)
        self.cmb_profile.set(names[0])

    # ------------------------------------------------------------------ Control
    def toggle(self) -> None:
        if not self.is_running:
            self._start()
        else:
            self._stop()

    def _start(self) -> None:
        try:
            http_port = int(self.ent_http.get().strip())
            telnet_port = int(self.ent_telnet.get().strip())
        except ValueError:
            self._log("Invalid port number\n")
            return

        profile = self.cmb_profile.get()
        if not profile or profile.startswith("("):
            self._log("No valid profile selected\n")
            return

        self.is_running = True
        self.btn_toggle.configure(text="SHUTDOWN", fg_color="#c0392b", hover_color="#922b21")
        self.ent_http.configure(state="disabled")
        self.ent_telnet.configure(state="disabled")
        self.cmb_profile.configure(state="disabled")
        self.lbl_status.configure(text=f"Active — HTTP :{http_port}  |  Telnet :{telnet_port}  |  Profile: {profile}", text_color="#2ecc71")

        threading.Thread(target=self._run_async, args=(http_port, telnet_port, profile), daemon=True).start()

    def _stop(self) -> None:
        self.is_running = False
        self.btn_toggle.configure(text="DEPLOY HIVE", fg_color="#27ae60", hover_color="#1e8449")
        self.ent_http.configure(state="normal")
        self.ent_telnet.configure(state="normal")
        self.cmb_profile.configure(state="normal")
        self.lbl_status.configure(text="Stopped", text_color="#e74c3c")

        if self.loop and self.loop.is_running():
            for eng in self.http_engines:
                asyncio.run_coroutine_threadsafe(eng.stop(), self.loop)
            if self.telnet_engine:
                asyncio.run_coroutine_threadsafe(self.telnet_engine.stop(), self.loop)
            self.loop.call_soon_threadsafe(self.loop.stop)

    def _run_async(self, http_port: int, telnet_port: int, profile: str) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.log_queue = asyncio.Queue()

        prof_path = f"config/profiles/{profile}.json"
        http = HonigtopfHTTP("0.0.0.0", http_port, prof_path, self.log_queue, self.event_logger)
        telnet = HonigtopfTelnet("0.0.0.0", telnet_port, self.log_queue, self.event_logger)
        self.http_engines = [http]
        self.telnet_engine = telnet

        self.loop.create_task(http.start())
        self.loop.create_task(telnet.start())
        self.loop.create_task(self._poll_logs())
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()

    async def _poll_logs(self) -> None:
        while self.is_running and self.log_queue:
            try:
                msg = await asyncio.wait_for(self.log_queue.get(), timeout=0.5)
                self.after(0, lambda m=msg: self._log(m))
                self.log_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception:
                break

    def _log(self, text: str) -> None:
        self.txt_logs.insert("end", text)
        self.txt_logs.see("end")
