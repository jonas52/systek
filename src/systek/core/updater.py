from __future__ import annotations

from pathlib import Path
from ..permissions import require_root
from ..shell import run_command


def update_systek(install_dir: str = "/opt/systek"):
    require_root()
    install_path = Path(install_dir)
    if not install_path.exists():
        return run_command(["bash", "-lc", "echo 'Installation /opt/systek introuvable' >&2; exit 1"])
    return run_command(["bash", "-lc", f"cd {install_dir} && ./.venv/bin/pip install -U -r requirements.txt && ./.venv/bin/pip install -U ."], timeout=180)
