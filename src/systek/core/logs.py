from pathlib import Path
from ..shell import run_command


def system_logs(lines: int = 100):
    return run_command(["journalctl", "-n", str(lines), "--no-pager"])


def export_system_logs(output_file: str):
    result = run_command(["journalctl", "-n", "500", "--no-pager"])
    if result.ok:
        Path(output_file).write_text(result.stdout, encoding="utf-8")
    return result
