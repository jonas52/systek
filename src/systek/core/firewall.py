from __future__ import annotations

from ..permissions import require_root
from ..shell import run_command


def ufw_status():
    return run_command(["ufw", "status", "numbered"], timeout=30)


def enable_ufw():
    require_root()
    return run_command(["ufw", "--force", "enable"], timeout=60)


def disable_ufw():
    require_root()
    return run_command(["ufw", "disable"], timeout=60)


def add_rule(rule: str):
    require_root()
    return run_command(["ufw", "allow", rule], timeout=60)


def delete_rule(rule_number: str):
    require_root()
    return run_command(["ufw", "--force", "delete", rule_number], timeout=60)
