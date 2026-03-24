from __future__ import annotations

import subprocess
from typing import Sequence


def run_command(cmd: Sequence[str]) -> str:
    proc = subprocess.run(list(cmd), capture_output=True, text=True)
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if proc.returncode != 0:
        return f"[exit {proc.returncode}]\n{err or out or 'Commande échouée.'}"
    return out or "OK"
