from __future__ import annotations
import os
import time
import psutil

def snapshot() -> dict[str, object]:
    net = psutil.net_io_counters()
    temps = None
    try:
        st = psutil.sensors_temperatures()
        for entries in st.values():
            for entry in entries:
                if getattr(entry, "current", None) is not None:
                    temps = float(entry.current)
                    raise StopIteration
    except StopIteration:
        pass
    except Exception:
        temps = None
    return {
        "cpu": psutil.cpu_percent(interval=0.05),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "load": os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0),
        "uptime": int(time.time() - psutil.boot_time()),
        "rx": getattr(net, "bytes_recv", 0),
        "tx": getattr(net, "bytes_sent", 0),
        "temp": temps,
    }

def human_bytes(value: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"

def human_uptime(seconds: int) -> str:
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    mins, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}j")
    if hours or days:
        parts.append(f"{hours}h")
    parts.append(f"{mins}m")
    return " ".join(parts)
