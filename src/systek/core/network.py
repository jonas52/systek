from __future__ import annotations

import socket
import psutil
from ..shell import run_command


def hostname() -> str:
    return socket.gethostname()


def ip_addresses() -> list[str]:
    ips: list[str] = []
    for _, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                ips.append(addr.address)
    return ips


def list_interfaces() -> str:
    names = sorted(psutil.net_if_addrs().keys())
    return "\n".join(names)


def network_connections():
    res = run_command(["ss", "-tunap"], timeout=60)
    if res.ok:
        return res
    return run_command(["netstat", "-tunap"], timeout=60)


def connectivity_test():
    return run_command(["ping", "-c", "2", "1.1.1.1"], timeout=10)
