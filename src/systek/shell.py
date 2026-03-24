from __future__ import annotations
import subprocess

def run_command(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if proc.returncode != 0:
        return f"[exit {proc.returncode}]\n{err or out or 'Commande échouée.'}"
    return out or "OK"
