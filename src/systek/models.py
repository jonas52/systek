from dataclasses import dataclass
from typing import Optional

@dataclass
class CommandResult:
    ok: bool
    stdout: str
    stderr: str
    returncode: int

@dataclass
class ActionSpec:
    number: int
    label: str
    category: str
    description: str
    requires_root: bool = False
    arg_hint: Optional[str] = None
