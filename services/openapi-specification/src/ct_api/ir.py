from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class OASDoc:
    filename: str
    source: str = ""
    data: dict | None = None
    paths: list[str] = field(default_factory=list)
    ops: list[str] = field(default_factory=list)
