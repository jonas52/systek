from ..permissions import require_root
from ..shell import run_command


def detect_package_manager() -> str:
    candidates = ["apt", "dnf", "yum", "pacman"]
    for cmd in candidates:
        result = run_command(["which", cmd])
        if result.ok:
            return cmd
    raise RuntimeError("Aucun gestionnaire de paquets supporté détecté.")


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
        raise NotImplementedError("hold package actuellement supporté via apt seulement.")
    return run_command(["apt-mark", "hold", package])


def unhold_package(pkg_manager: str, package: str):
    require_root()
    if pkg_manager != "apt":
        raise NotImplementedError("unhold package actuellement supporté via apt seulement.")
    return run_command(["apt-mark", "unhold", package])
