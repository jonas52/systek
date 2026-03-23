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
    os_release = Path("/etc/os-release")
    if os_release.exists():
        data = {}
        for line in os_release.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                data[k] = v.strip('"')
        return data.get("PRETTY_NAME", "Linux")
    return "Linux"


def update_system(pkg_manager: str):
    require_root()
    refresh = {
        "apt": ["apt", "update"],
        "dnf": ["dnf", "makecache"],
        "yum": ["yum", "makecache"],
        "pacman": ["pacman", "-Sy"],
    }
    upgrade = {
        "apt": ["apt", "upgrade", "-y"],
        "dnf": ["dnf", "upgrade", "-y"],
        "yum": ["yum", "update", "-y"],
        "pacman": ["pacman", "-Su", "--noconfirm"],
    }
    r1 = run_command(refresh[pkg_manager])
    r2 = run_command(upgrade[pkg_manager])
    return r1, r2


def reboot_system():
    require_root()
    return run_command(["reboot"])


def shutdown_system():
    require_root()
    return run_command(["poweroff"])
