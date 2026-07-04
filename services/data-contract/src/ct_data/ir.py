"""ODCS light IR."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ODCSDoc:
    filename: str
    source: str = ""
    data: dict[str, Any] | None = None  # parsed if yaml available
    top_keys: list[str] = field(default_factory=list)
