from ..permissions import require_root
from ..shell import run_command


def ufw_status():
    return run_command(["ufw", "status", "numbered"])


def enable_ufw():
    require_root()
    return run_command(["ufw", "--force", "enable"])


def disable_ufw():
    require_root()
    return run_command(["ufw", "disable"])


def add_rule(rule: str):
    require_root()
    return run_command(["ufw", "allow", rule])


def delete_rule(rule_number: str):
    require_root()
    return run_command(["ufw", "--force", "delete", rule_number])
