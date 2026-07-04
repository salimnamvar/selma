"""SQ IR (lightweight)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SQDiagram:
    filename: str
    title: str = ""
    source: str = ""
    participants: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)  # ref targets
    notes: list[dict] = field(default_factory=list)
