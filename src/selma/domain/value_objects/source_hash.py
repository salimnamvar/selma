"""SourceHash value object — SHA-256 hash of source file content.

Immutable, validates format. Uses Pydantic v2 for validation.
"""

from __future__ import annotations

import hashlib

from pydantic import BaseModel
from pydantic import ConfigDict


class SourceHash(BaseModel):
    """SHA-256 hash of source file content. Value object."""

    model_config = ConfigDict(frozen=True)

    _value: str

    def __init__(self, a_value: str) -> None:
        if not a_value:
            raise ValueError("SourceHash cannot be empty")
        object.__setattr__(self, "_value", a_value)

    @property
    def value(self) -> str:
        return self._value

    @staticmethod
    def from_content(a_content: str | bytes) -> SourceHash:
        """Create a SourceHash from file content."""
        raw = a_content
        if isinstance(a_content, str):
            raw = a_content.encode("utf-8")
        return SourceHash(hashlib.sha256(raw).hexdigest())  # type: ignore[arg-type]

    def __eq__(self, a_other: object) -> bool:
        b_continue = True
        result = False
        if (
            b_continue
            and isinstance(a_other, SourceHash)
            and self._value == a_other._value
        ):
            result = True
        return result

    def __hash__(self) -> int:
        return hash(self._value)

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"SourceHash({self._value[:12]}...)"
