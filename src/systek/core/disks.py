import psutil
from ..permissions import require_root
from ..shell import run_command


def list_disks():
    return run_command(["lsblk", "-o", "NAME,SIZE,FSTYPE,MOUNTPOINT,TYPE", "--noheadings"])


def mount_disk(device: str, mountpoint: str):
    require_root()
    run_command(["mkdir", "-p", mountpoint])
    return run_command(["mount", device, mountpoint])


def disk_usage():
    return psutil.disk_partitions(all=False)
