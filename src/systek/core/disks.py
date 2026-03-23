import psutil
from ..permissions import require_root
from ..shell import run_command


def list_disks():
    return run_command(["lsblk", "-o", "NAME,SIZE,FSTYPE,MOUNTPOINT,TYPE", "--noheadings"])


def mount_disk(device: str, mountpoint: str):
    require_root()
    run_command(["mkdir", "-p", mountpoint])
    return run_command(["mount", device, mountpoint])


def disk_usage_report() -> str:
    lines = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            lines.append(f"{part.mountpoint:<20} {usage.percent:>5.1f}%  {usage.used // (1024**3)}G/{usage.total // (1024**3)}G")
        except PermissionError:
            continue
    return "\n".join(lines) or "Aucune information disque disponible."
