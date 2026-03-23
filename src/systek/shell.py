from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(slots=True)
class CommandResult:
    ok: bool
    stdout: str
    stderr: str
    returncode: int
    command: str


def run_command(cmd: list[str], timeout: int = 30) -> CommandResult:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return CommandResult(
            ok=proc.returncode == 0,
            stdout=(proc.stdout or "").strip(),
            stderr=(proc.stderr or "").strip(),
            returncode=proc.returncode,
            command=" ".join(cmd),
        )
    except FileNotFoundError as exc:
        return CommandResult(False, "", str(exc), 127, " ".join(cmd))
    except subprocess.TimeoutExpired:
        return CommandResult(False, "", f"Commande expirée après {timeout}s", 124, " ".join(cmd))
