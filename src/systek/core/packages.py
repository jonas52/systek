from ..permissions import require_root
from ..shell import run_command


def detect_package_manager() -> str:
    for cmd in ["apt", "dnf", "yum", "pacman"]:
        result = run_command(["which", cmd])
        if result.ok:
            return cmd
    return "unknown"


def install_package(pkg_manager: str, package: str):
    require_root()
    mapping = {
        "apt": ["apt", "install", "-y", package],
        "dnf": ["dnf", "install", "-y", package],
        "yum": ["yum", "install", "-y", package],
        "pacman": ["pacman", "-S", "--noconfirm", package],
    }
    return run_command(mapping[pkg_manager])


def remove_package(pkg_manager: str, package: str):
    require_root()
    mapping = {
        "apt": ["apt", "remove", "-y", package],
        "dnf": ["dnf", "remove", "-y", package],
        "yum": ["yum", "remove", "-y", package],
        "pacman": ["pacman", "-R", "--noconfirm", package],
    }
    return run_command(mapping[pkg_manager])


def search_package(pkg_manager: str, package: str):
    mapping = {
        "apt": ["apt-cache", "search", package],
        "dnf": ["dnf", "search", package],
        "yum": ["yum", "search", package],
        "pacman": ["pacman", "-Ss", package],
    }
    return run_command(mapping[pkg_manager])


def hold_package(pkg_manager: str, package: str):
    require_root()
    if pkg_manager != "apt":
        raise NotImplementedError("Hold package disponible uniquement via apt actuellement.")
    return run_command(["apt-mark", "hold", package])


def unhold_package(pkg_manager: str, package: str):
    require_root()
    if pkg_manager != "apt":
        raise NotImplementedError("Unhold package disponible uniquement via apt actuellement.")
    return run_command(["apt-mark", "unhold", package])
