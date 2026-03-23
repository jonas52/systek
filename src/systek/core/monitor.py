from __future__ import annotations

import os
import socket
import time
import psutil


def cpu_percent() -> float:
    return psutil.cpu_percent(interval=0.0)


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


def hostname() -> str:
    return socket.gethostname()


def local_ips() -> list[str]:
    ips: list[str] = []
    for _name, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if getattr(addr, "family", None) == socket.AF_INET and not addr.address.startswith("127."):
                ips.append(addr.address)
    return ips


def network_rates(interval: float = 0.15) -> tuple[float, float]:
    c1 = psutil.net_io_counters()
    time.sleep(interval)
    c2 = psutil.net_io_counters()
    if c1 is None or c2 is None:
        return 0.0, 0.0
    rx = max(0.0, (c2.bytes_recv - c1.bytes_recv) / interval)
    tx = max(0.0, (c2.bytes_sent - c1.bytes_sent) / interval)
    return rx, tx


def human_bytes(num: float) -> str:
    units = ["B/s", "KB/s", "MB/s", "GB/s"]
    value = float(num)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB/s"


def cpu_temperature() -> str:
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return "N/A"
        for _label, entries in temps.items():
            for entry in entries:
                current = getattr(entry, "current", None)
                if current is not None:
                    return f"{current:.1f}°C"
    except Exception:
        pass
    return "N/A"
