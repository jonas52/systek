from __future__ import annotations

import platform
import socket
from pathlib import Path

import psutil

from ..permissions import is_root
from ..shell import run_command


def host_info() -> dict[str, str]:
    os_name = "Linux"
    path = Path("/etc/os-release")
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("PRETTY_NAME="):
                os_name = line.split("=", 1)[1].strip().strip('"')
                break

    ips: list[str] = []
    for _, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if getattr(addr, "family", None) == socket.AF_INET and not addr.address.startswith("127."):
                ips.append(addr.address)

    return {
        "hostname": socket.gethostname(),
        "os": os_name,
        "kernel": platform.release(),
        "ips": ", ".join(sorted(set(ips))) or "N/A",
        "sudo": "COMPLET" if is_root() else "LIMITE",
    }


def actions() -> list[dict[str, object]]:
    return [
        {
            "key": "1",
            "category": "Système",
            "label": "Mettre à jour le cache APT",
            "root": True,
            "cmd": ["apt", "update"],
            "description": "Actualise la liste des paquets. Recommandé avant installation ou maintenance.",
        },
        {
            "key": "2",
            "category": "Système",
            "label": "Lister les services",
            "root": False,
            "cmd": ["systemctl", "list-units", "--type=service", "--no-pager"],
            "description": "Affiche les services systemd actifs et chargés.",
        },
        {
            "key": "3",
            "category": "Surveillance",
            "label": "Connexions réseau",
            "root": False,
            "cmd": ["ss", "-tunap"],
            "description": "Affiche sockets TCP/UDP et processus associés quand disponibles.",
        },
        {
            "key": "4",
            "category": "Surveillance",
            "label": "Disques et montages",
            "root": False,
            "cmd": ["lsblk", "-o", "NAME,SIZE,FSTYPE,MOUNTPOINT,TYPE"],
            "description": "Vue rapide des disques, partitions, FS et points de montage.",
        },
        {
            "key": "5",
            "category": "Pare-feu",
            "label": "Statut UFW",
            "root": False,
            "cmd": ["ufw", "status", "numbered"],
            "description": "Montre l'état du pare-feu UFW et les règles numérotées.",
        },
        {
            "key": "6",
            "category": "Logs",
            "label": "Logs système récents",
            "root": False,
            "cmd": ["journalctl", "-n", "80", "--no-pager"],
            "description": "Affiche les dernières entrées du journal système.",
        },
        {
            "key": "7",
            "category": "Système",
            "label": "Redémarrer le serveur",
            "root": True,
            "cmd": ["reboot"],
            "description": "Redémarre immédiatement la machine. À utiliser avec prudence.",
        },
        {
            "key": "8",
            "category": "Système",
            "label": "Éteindre le serveur",
            "root": True,
            "cmd": ["poweroff"],
            "description": "Éteint immédiatement la machine. À utiliser avec prudence.",
        },
    ]


def action_by_key(key: str) -> dict[str, object] | None:
    for action in actions():
        if action["key"] == key:
            return action
    return None


def execute_action(key: str) -> str:
    action = action_by_key(key)
    if action is None:
        return "Action inconnue. Utilise une commande de 1 à 8."
    if bool(action["root"]) and not is_root():
        return f"{action['label']}\n\nCette action nécessite sudo."
    result = run_command(action["cmd"])
    return f"{action['label']}\n\n{result}"
