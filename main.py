import os
import json

def ensure_environment():
    """Vérifie que les structures de dossiers et les fichiers JSON sont là."""
    os.makedirs("config/profiles", exist_ok=True)
    
    # Création automatique du profil iis par défaut si inexistant
    iis_path = "config/profiles/iis.json"
    if not os.path.exists(iis_path):
        default_iis = {
            "name": "iis_85_vulnerable",
            "description": "Simulates an outdated Microsoft IIS 8.5 server",
            "status_code": "200 OK",
            "headers": {
                "Server": "Microsoft-IIS/8.5",
                "X-Powered-By": "ASP.NET",
                "X-AspNet-Version": "4.0.30319",
                "Content-Type": "text/html; charset=UTF-8",
                "Connection": "close"
            },
            "body": "<html><head><title>IIS8.5</title></head><body><h1>Welcome to IIS 8.5</h1></body></html>"
        }
        with open(iis_path, "w", encoding="utf-8") as f:
            json.dump(default_iis, f, indent=4)

if __name__ == "__main__":
    ensure_environment()
    
    # Import décalé de la GUI pour laisser l'environnement s'initialiser
    from src.gui import HonigtopfGUI
    app = HonigtopfGUI()
    app.mainloop()
