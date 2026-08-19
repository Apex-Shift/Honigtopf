import customtkinter as ctk
import asyncio
import threading
import os
from src.honeypot import HonigtopfEngine
from src.telnet_core import HonigtopfTelnet

class HonigtopfGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Honigtopf ")
        self.geometry("850x600")
        ctk.set_appearance_mode("dark")

        self.loop = None
        self.http_engine = None
        self.telnet_engine = None
        self.log_queue = asyncio.Queue()
        self.is_running = False

        self._create_widgets()

    def _create_widgets(self):
        self.config_frame = ctk.CTkFrame(self)
        self.config_frame.pack(pady=15, padx=20, fill="x")

        # Config HTTP
        self.lbl_port = ctk.CTkLabel(self.config_frame, text="Port HTTP:")
        self.lbl_port.pack(side="left", padx=5, pady=10)
        self.ent_port = ctk.CTkEntry(self.config_frame, width=70)
        self.ent_port.insert(0, "8080")
        self.ent_port.pack(side="left", padx=5, pady=10)

        # Config Telnet
        self.lbl_tport = ctk.CTkLabel(self.config_frame, text="Port Telnet:")
        self.lbl_tport.pack(side="left", padx=5, pady=10)
        self.ent_tport = ctk.CTkEntry(self.config_frame, width=60)
        self.ent_tport.insert(0, "23")
        self.ent_tport.pack(side="left", padx=5, pady=10)

        # Combo Profils Nettoyés (Sans extension .json)
        self.lbl_profile = ctk.CTkLabel(self.config_frame, text="Profil IoT:")
        self.lbl_profile.pack(side="left", padx=5, pady=10)
        
        profiles_dir = "config/profiles"
        if os.path.exists(profiles_dir):
            # On extrait uniquement le nom du fichier, sans l'extension
            profiles = [os.path.splitext(f)[0] for f in os.listdir(profiles_dir) if f.endswith('.json')]
        else:
            profiles = ["dvr_hikvision", "router_gateway", "printer_hp"]

        self.cmb_profile = ctk.CTkComboBox(self.config_frame, values=profiles)
        self.cmb_profile.pack(side="left", padx=5, pady=10)

        self.btn_toggle = ctk.CTkButton(self.config_frame, text="DEPLOY HIVE", fg_color="green", command=self.toggle_service)
        self.btn_toggle.pack(side="right", padx=10, pady=10)

        # Zone de logs
        self.log_frame = ctk.CTkFrame(self)
        self.log_frame.pack(pady=10, padx=20, fill="both", expand=True)
        self.txt_logs = ctk.CTkTextbox(self.log_frame, font=("Courier New", 12))
        self.txt_logs.pack(fill="both", expand=True, padx=15, pady=15)

    def toggle_service(self):
        if not self.is_running:
            self.is_running = True
            self.btn_toggle.configure(text="SHUTDOWN", fg_color="red")
            self.ent_port.configure(state="disabled")
            self.ent_tport.configure(state="disabled")
            self.cmb_profile.configure(state="disabled")
            threading.Thread(target=self.start_async_core, daemon=True).start()
        else:
            self.is_running = False
            self.btn_toggle.configure(text="DEPLOY HIVE", fg_color="green")
            self.ent_port.configure(state="normal")
            self.ent_tport.configure(state="normal")
            self.cmb_profile.configure(state="normal")
            if self.loop:
                asyncio.run_coroutine_threadsafe(self.http_engine.stop(), self.loop)
                asyncio.run_coroutine_threadsafe(self.telnet_engine.stop(), self.loop)

    def start_async_core(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        h_port = int(self.ent_port.get())
        t_port = int(self.ent_tport.get())
        # Le chemin reconstruit proprement l'extension manquante
        prof_path = f"config/profiles/{self.cmb_profile.get()}.json"

        self.http_engine = HonigtopfEngine("0.0.0.0", h_port, prof_path, self.log_queue)
        self.telnet_engine = HonigtopfTelnet("0.0.0.0", t_port, self.log_queue)

        self.loop.create_task(self.http_engine.start())
        self.loop.create_task(self.telnet_engine.start())
        self.loop.create_task(self.poll_queue())
        self.loop.run_forever()

    async def poll_queue(self):
        while self.is_running:
            msg = await self.log_queue.get()
            self.txt_logs.insert("end", msg)
            self.txt_logs.see("end")
            self.log_queue.task_done()
