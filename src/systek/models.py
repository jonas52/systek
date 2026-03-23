from dataclasses import dataclass


@dataclass
class CommandResult:
    ok: bool
    stdout: str
    stderr: str
    returncode: int


@dataclass
class ActionDefinition:
    key: str
    label: str
    category: str
    requires_root: bool
    description: str
