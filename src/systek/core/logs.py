from __future__ import annotations

from ..shell import run_command


def system_logs(lines: int = 100):
    return run_command(["journalctl", "-n", str(lines), "--no-pager"], timeout=60)


def export_system_logs(output_file: str):
    logs = system_logs(500)
    if logs.ok:
        with open(output_file, "w", encoding="utf-8") as handle:
            handle.write(logs.stdout)
    return logs
