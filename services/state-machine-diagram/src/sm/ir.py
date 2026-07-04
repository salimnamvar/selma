"""SM IR (lightweight)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SMDiagram:
    filename: str
    title: str = ""
    source: str = ""
    states: list[dict[str, Any]] = field(default_factory=list)  # {name, color?}
    transitions: list[dict[str, Any]] = field(default_factory=list)
    notes: list[dict] = field(default_factory=list)
