import subprocess
from .models import CommandResult


def run_command(cmd: list[str], check: bool = False) -> CommandResult:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(
            proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr
        )
    return CommandResult(
        ok=(proc.returncode == 0),
        stdout=proc.stdout.strip(),
        stderr=proc.stderr.strip(),
        returncode=proc.returncode,
    )
