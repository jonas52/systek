import subprocess
from .models import CommandResult

def run_command(cmd: list[str]) -> CommandResult:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return CommandResult(
            ok=(proc.returncode == 0),
            stdout=(proc.stdout or "").strip(),
            stderr=(proc.stderr or "").strip(),
            returncode=proc.returncode,
        )
    except FileNotFoundError as exc:
        return CommandResult(False, "", f"Commande introuvable: {exc}", 127)
    except Exception as exc:
        return CommandResult(False, "", str(exc), 1)
