from __future__ import annotations

import subprocess
from .models import CommandResult


def run_command(cmd: list[str], timeout: int = 30) -> CommandResult:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return CommandResult(
            ok=proc.returncode == 0,
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
            returncode=proc.returncode,
        )
    except FileNotFoundError as exc:
        return CommandResult(False, "", f"Commande introuvable: {cmd[0]} ({exc})", 127)
    except subprocess.TimeoutExpired:
        return CommandResult(False, "", f"Commande expirée après {timeout}s: {' '.join(cmd)}", 124)
    except Exception as exc:
        return CommandResult(False, "", str(exc), 1)
