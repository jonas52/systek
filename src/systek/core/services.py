from __future__ import annotations

from ..permissions import require_root
from ..shell import run_command


def list_services():
    return run_command(["systemctl", "list-units", "--type=service", "--no-pager", "--all"], timeout=60)


def service_status(service: str):
    return run_command(["systemctl", "status", service, "--no-pager"], timeout=60)


def restart_service(service: str):
    require_root()
    return run_command(["systemctl", "restart", service], timeout=60)


def start_service(service: str):
    require_root()
    return run_command(["systemctl", "start", service], timeout=60)


def stop_service(service: str):
    require_root()
    return run_command(["systemctl", "stop", service], timeout=60)


def enable_service(service: str):
    require_root()
    return run_command(["systemctl", "enable", service], timeout=60)


def disable_service(service: str):
    require_root()
    return run_command(["systemctl", "disable", service], timeout=60)


def service_logs(service: str, lines: int = 80):
    return run_command(["journalctl", "-u", service, "-n", str(lines), "--no-pager"], timeout=60)
