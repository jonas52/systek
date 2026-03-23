from dataclasses import dataclass


@dataclass(slots=True)
class CommandResult:
    ok: bool
    stdout: str
    stderr: str
    returncode: int


@dataclass(slots=True)
class ActionDefinition:
    number: int
    category: str
    label: str
    description: str
    requires_root: bool = False
    args_hint: str = ""
