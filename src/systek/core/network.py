import socket
import psutil
from ..shell import run_command


def get_hostname() -> str:
    return socket.gethostname()


def get_local_ips() -> list[str]:
    ips: list[str] = []
    for _, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                ips.append(addr.address)
    return ips


def list_interfaces() -> list[str]:
    return list(psutil.net_if_addrs().keys())


def network_connections():
    return run_command(["ss", "-tunap"])


def connectivity_test():
    return run_command(["ping", "-c", "2", "1.1.1.1"])
