"""ERD IR (lightweight)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ERDDiagram:
    filename: str
    title: str = ""
    source: str = ""
    entities: list[str] = field(default_factory=list)
    relationships: list[str] = field(default_factory=list)
    notes: list[dict] = field(default_factory=list)
