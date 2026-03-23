from ..permissions import require_root
from ..shell import run_command


def list_services():
    return run_command(["systemctl", "list-units", "--type=service", "--no-pager", "--all"])


def service_status(service: str):
    return run_command(["systemctl", "status", service, "--no-pager"])


def restart_service(service: str):
    require_root()
    return run_command(["systemctl", "restart", service])


def start_service(service: str):
    require_root()
    return run_command(["systemctl", "start", service])


def stop_service(service: str):
    require_root()
    return run_command(["systemctl", "stop", service])


def enable_service(service: str):
    require_root()
    return run_command(["systemctl", "enable", service])


def disable_service(service: str):
    require_root()
    return run_command(["systemctl", "disable", service])


def service_logs(service: str, lines: int = 100):
    return run_command(["journalctl", "-u", service, "-n", str(lines), "--no-pager"])
