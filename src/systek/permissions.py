import os

def is_root() -> bool:
    return os.geteuid() == 0

def require_root() -> None:
    if not is_root():
        raise PermissionError("Cette action nécessite sudo/root.")
