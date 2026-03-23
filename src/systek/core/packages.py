from __future__ import annotations

from ..permissions import require_root
from ..shell import run_command


def detect_package_manager() -> str:
    for name in ("apt", "dnf", "yum", "pacman"):
        res = run_command(["which", name])
        if res.ok:
            return name
    return "unknown"


def install_package(pkg_manager: str, package: str):
    require_root()
    commands = {
        "apt": ["apt", "install", "-y", package],
        "dnf": ["dnf", "install", "-y", package],
        "yum": ["yum", "install", "-y", package],
        "pacman": ["pacman", "-S", "--noconfirm", package],
    }
    return run_command(commands[pkg_manager], timeout=180)


def remove_package(pkg_manager: str, package: str):
    require_root()
    commands = {
        "apt": ["apt", "remove", "-y", package],
        "dnf": ["dnf", "remove", "-y", package],
        "yum": ["yum", "remove", "-y", package],
        "pacman": ["pacman", "-R", "--noconfirm", package],
    }
    return run_command(commands[pkg_manager], timeout=180)


def hold_package(pkg_manager: str, package: str):
    require_root()
    if pkg_manager != "apt":
        return run_command(["bash", "-lc", "echo 'Hold supporté seulement avec apt' >&2; exit 1"])
    return run_command(["apt-mark", "hold", package])


def unhold_package(pkg_manager: str, package: str):
    require_root()
    if pkg_manager != "apt":
        return run_command(["bash", "-lc", "echo 'Unhold supporté seulement avec apt' >&2; exit 1"])
    return run_command(["apt-mark", "unhold", package])


def search_package(pkg_manager: str, package: str):
    commands = {
        "apt": ["apt-cache", "search", package],
        "dnf": ["dnf", "search", package],
        "yum": ["yum", "search", package],
        "pacman": ["pacman", "-Ss", package],
    }
    return run_command(commands[pkg_manager], timeout=60)
