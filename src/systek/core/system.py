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

def action_map() -> dict[str, tuple[str, bool, list[str]]]:
    return {
        "1": ("Mettre à jour le système", True, ["apt", "update"]),
        "2": ("Redémarrer le serveur", True, ["reboot"]),
        "3": ("Éteindre le serveur", True, ["poweroff"]),
        "4": ("Lister les services", False, ["systemctl", "list-units", "--type=service", "--no-pager"]),
        "5": ("Statut UFW", False, ["ufw", "status", "numbered"]),
        "6": ("Connexions réseau", False, ["ss", "-tunap"]),
        "7": ("Disques", False, ["lsblk", "-o", "NAME,SIZE,FSTYPE,MOUNTPOINT,TYPE"]),
        "8": ("Logs système", False, ["journalctl", "-n", "80", "--no-pager"]),
    }

def execute_action(key: str) -> str:
    actions = action_map()
    if key not in actions:
        return "Action inconnue."
    label, need_root, cmd = actions[key]
    if need_root and not is_root():
        return f"{label}\n\nCette action nécessite sudo."
    return f"{label}\n\n{run_command(cmd)}"
