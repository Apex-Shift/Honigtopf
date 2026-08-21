"""Honigtopf v5.0 - Production CLI Interface."""

from __future__ import annotations

import argparse
import asyncio
import os
import socket
import sys
from typing import Any

from src.core.manager import ServiceManager


def check_port(host: str, port: int) -> bool:
    """Vérifie si un port réseau répond localement."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except (OSError, ConnectionRefusedError):
        return False


async def check_health() -> None:
    """Affiche un rapport d'état de santé complet du système (Command: status)."""
    print("=== Honigtopf v4.0 Health Status ===")

    # 1. Verification des fichiers de configuration
    auth_ok = os.path.exists("config/auth.json")
    settings_ok = os.path.exists("config/settings.json")
    print(f"[*] Config Auth (`config/auth.json`)    : {'OK' if auth_ok else 'MISSING (Using defaults)'}")
    print(f"[*] Config Webhook (`config/settings.json`): {'OK' if settings_ok else 'DISABLED'}")

    # 2. Etat des Logs / Event Store
    log_file = "logs/events.jsonl"
    if os.path.exists(log_file):
        size_kb = os.path.getsize(log_file) / 1024
        with open(log_file, "r", encoding="utf-8") as f:
            count = sum(1 for _ in f)
        print(f"[*] Event Store (`{log_file}`)          : OK ({count} évènements, {size_kb:.1f} KB)")
    else:
        print(f"[*] Event Store (`{log_file}`)          : NON INITIALISÉ")

    # 3. Sonde des sockets actifs (Dashboard & Honeypots)
    ports_to_check = {
        "Dashboard": 8050,
        "HTTP": 8080,
        "Telnet": 2323,
        "FTP": 2121,
        "SMB": 4455,
    }
    print("\n--- Listening Sockets ---")
    active_count = 0
    for name, port in ports_to_check.items():
        is_open = check_port("127.0.0.1", port)
        status_str = "ACTIVE (LISTENING)" if is_open else "INACTIVE"
        print(f"[{'✓' if is_open else '✗'}] Service {name:<10} (Port {port}): {status_str}")
        if is_open:
            active_count += 1

    if active_count == 0:
        print("\n[-] Aucun service n'écoute actuellement.")
        sys.exit(1)
    else:
        print(f"\n[+] Système opérationnel ({active_count} sockets actifs).")


async def start_services(services: list[str], ports: dict[str, Any]) -> None:
    """Instancie la boucle asynchrone et lance les services sélectionnés."""
    manager = ServiceManager()
    config_ports = {s: ports.get(s) for s in services if ports.get(s)}

    print(f"[+] Initialisation des modules : {', '.join(services)}")
    await manager.start_all(selected_services=services, custom_ports=config_ports)

    print("[+] Honigtopf v4.0 (CLI) est actif. Écoute réseau en cours... (Ctrl+C pour quitter)")
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        print("[*] Interruption demandée.")
    finally:
        print("[-] Fermeture des sockets et arrêt des modules...")
        await manager.stop_all()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Honigtopf v4.0 - Interface Ligne de Commande",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Commande START
    start_parser = subparsers.add_parser("start", help="Démarrer les services de déception")
    start_parser.add_argument(
        "--services",
        nargs="+",
        default=["http", "telnet"],
        choices=["http", "telnet", "ftp", "smb"],
        help="Services à activer (Défaut: http telnet)",
    )
    start_parser.add_argument("--http-port", type=int, help="Port alternatif HTTP")
    start_parser.add_argument("--telnet-port", type=int, help="Port alternatif Telnet")
    start_parser.add_argument("--ftp-port", type=int, help="Port alternatif FTP")
    start_parser.add_argument("--smb-port", type=int, help="Port alternatif SMB")

    # Commande STATUS
    subparsers.add_parser("status", help="Vérifier la santé du framework et l'état des ports")

    args = parser.parse_args()

    if args.command == "start":
        ports = {
            "http": args.http_port,
            "telnet": args.telnet_port,
            "ftp": args.ftp_port,
            "smb": args.smb_port,
        }
        try:
            asyncio.run(start_services(args.services, ports))
        except KeyboardInterrupt:
            print("\n[-] Session arrêtée par l'administrateur.")
            sys.exit(0)

    elif args.command == "status":
        asyncio.run(check_health())


if __name__ == "__main__":
    main()