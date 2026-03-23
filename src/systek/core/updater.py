from pathlib import Path
from ..permissions import require_root
from ..shell import run_command


def update_systek(install_dir: str = "/opt/systek"):
    require_root()
    git_dir = Path(install_dir) / ".git"
    if not git_dir.exists():
        raise RuntimeError("Installation non Git, update automatique indisponible.")
    pull = run_command(["git", "-C", install_dir, "pull", "origin", "main"])
    pip_sync = run_command([f"{install_dir}/.venv/bin/pip", "install", "-r", f"{install_dir}/requirements.txt"])
    editable = run_command([f"{install_dir}/.venv/bin/pip", "install", "-e", install_dir])
    return pull, pip_sync, editable
