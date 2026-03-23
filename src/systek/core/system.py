from __future__ import annotations

import platform
import socket
from pathlib import Path
from ..permissions import require_root
from ..shell import run_command


def get_hostname() -> str:
    return socket.gethostname()


def get_kernel() -> str:
    return platform.release()


def get_os_name() -> str:
    path = Path("/etc/os-release")
    if path.exists():
        values = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                key, val = line.split("=", 1)
                values[key] = val.strip('"')
        return values.get("PRETTY_NAME", "Linux")
    return "Linux"


def update_system(pkg_manager: str):
    require_root()
    mapping = {
        "apt": (["apt", "update"], ["apt", "upgrade", "-y"]),
        "dnf": (["dnf", "makecache"], ["dnf", "upgrade", "-y"]),
        "yum": (["yum", "makecache"], ["yum", "update", "-y"]),
        "pacman": (["pacman", "-Sy"], ["pacman", "-Su", "--noconfirm"]),
    }
    prepare, upgrade = mapping[pkg_manager]
    return run_command(prepare, timeout=120), run_command(upgrade, timeout=180)


def reboot_system():
    require_root()
    return run_command(["reboot"])


def shutdown_system():
    require_root()
    return run_command(["poweroff"])
