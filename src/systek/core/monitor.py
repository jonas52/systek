import os
import time
import psutil


def cpu_percent() -> float:
    return psutil.cpu_percent(interval=0.2)


def ram_percent() -> float:
    return psutil.virtual_memory().percent


def disk_percent(path: str = "/") -> float:
    return psutil.disk_usage(path).percent


def load_average() -> tuple[float, float, float]:
    if hasattr(os, "getloadavg"):
        return os.getloadavg()
    return (0.0, 0.0, 0.0)


def uptime_seconds() -> float:
    return time.time() - psutil.boot_time()


def network_counters():
    return psutil.net_io_counters()


def cpu_temperature() -> float | None:
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None
        for _, entries in temps.items():
            for entry in entries:
                if entry.current is not None:
                    return float(entry.current)
    except Exception:
        return None
    return None
