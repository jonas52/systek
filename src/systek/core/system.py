from __future__ import annotations

from pathlib import Path
import platform
import getpass


def os_pretty_name() -> str:
    os_release = Path("/etc/os-release")
    if os_release.exists():
        values: dict[str, str] = {}
        for line in os_release.read_text(encoding="utf-8", errors="ignore").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                values[k] = v.strip().strip('"')
        return values.get("PRETTY_NAME", "Linux")
    return "Linux"


def kernel_version() -> str:
    return platform.release()


def current_user() -> str:
    return getpass.getuser()


def detect_package_manager() -> str:
    for candidate in ("apt", "dnf", "yum", "pacman", "zypper", "apk"):
        from shutil import which
        if which(candidate):
            return candidate
    return "unknown"
