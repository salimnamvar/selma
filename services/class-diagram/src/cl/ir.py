"""CL IR (lightweight)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CLDiagram:
    filename: str
    title: str = ""
    source: str = ""
    classes: list[str] = field(default_factory=list)
    enums: list[str] = field(default_factory=list)
    notes: list[dict] = field(default_factory=list)
    cl_type: str = "domain"  # "domain" or "runtime"
