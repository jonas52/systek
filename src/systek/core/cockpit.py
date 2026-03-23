from .packages import install_package
from .network import get_local_ips


def install_cockpit(pkg_manager: str):
    result = install_package(pkg_manager, "cockpit")
    ips = get_local_ips()
    return result, ips
