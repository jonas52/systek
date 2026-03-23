from __future__ import annotations

from .packages import install_package
from .network import ip_addresses


def install_cockpit(pkg_manager: str):
    result = install_package(pkg_manager, "cockpit")
    return result, ip_addresses()
