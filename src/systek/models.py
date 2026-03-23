from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Action:
    key: str
    label: str
    category: str
    description: str
    requires_root: bool = False
    prompt: str = ""
    example: str = ""


@dataclass
class ActionResult:
    title: str
    body: str
    ok: bool = True
