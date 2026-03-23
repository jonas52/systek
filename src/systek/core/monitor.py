from __future__ import annotations

import os
import socket
import time
import psutil


def cpu_percent() -> float:
    return psutil.cpu_percent(interval=0.1)


def ram_percent() -> float:
    return psutil.virtual_memory().percent


def disk_percent(path: str = "/") -> float:
    return psutil.disk_usage(path).percent


def load_average() -> tuple[float, float, float]:
    if hasattr(os, "getloadavg"):
        return os.getloadavg()
    return (0.0, 0.0, 0.0)


def uptime_human() -> str:
    seconds = int(time.time() - psutil.boot_time())
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    if days:
        return f"{days}j {hours}h {minutes}m"
    return f"{hours}h {minutes}m"


def net_summary() -> tuple[str, str]:
    counters = psutil.net_io_counters()
    rx = counters.bytes_recv / 1024 / 1024
    tx = counters.bytes_sent / 1024 / 1024
    return (f"{rx:.1f} MB", f"{tx:.1f} MB")


def local_ips() -> list[str]:
    ips: list[str] = []
    for _, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                ips.append(addr.address)
    return ips


def cpu_temperature() -> float | None:
    try:
        temps = psutil.sensors_temperatures()
    except Exception:
        return None
    if not temps:
        return None
    for entries in temps.values():
        for entry in entries:
            current = getattr(entry, "current", None)
            if current is not None:
                return float(current)
    return None
