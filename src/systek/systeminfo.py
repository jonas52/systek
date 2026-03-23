from __future__ import annotations

import os
import platform
import socket
from pathlib import Path

import psutil


def os_pretty_name() -> str:
    p = Path("/etc/os-release")
    if p.exists():
        data = {}
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                data[k] = v.strip().strip('"')
        return data.get("PRETTY_NAME", "Linux")
    return "Linux"


def hostname() -> str:
    return socket.gethostname()


def kernel() -> str:
    return platform.release()


def user_name() -> str:
    return os.environ.get("SUDO_USER") or os.environ.get("USER") or "unknown"


def local_ips() -> list[str]:
    ips: list[str] = []
    for _, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if getattr(addr.family, "name", str(addr.family)) == "AF_INET" and not addr.address.startswith("127."):
                ips.append(addr.address)
    return ips


def package_manager() -> str:
    for cmd in ("apt", "dnf", "yum", "pacman"):
        path = shutil_which(cmd)
        if path:
            return cmd
    return "unknown"


def shutil_which(name: str) -> str | None:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / name
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None
