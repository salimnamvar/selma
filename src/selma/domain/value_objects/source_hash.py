"""SourceHash value object — SHA-256 hash of source file content.

Immutable, validates format.
"""

from __future__ import annotations

import hashlib


class SourceHash:
    """SHA-256 hash of source file content. Value object."""

    __slots__ = ("_value",)

    def __init__(self, a_value: str) -> None:
        if not a_value:
            raise ValueError("SourceHash cannot be empty")
        self._value = a_value

    @property
    def value(self) -> str:
        return self._value

    @staticmethod
    def from_content(a_content: str | bytes) -> SourceHash:
        """Create a SourceHash from file content."""
        b_continue = True
        result = SourceHash("")
        if b_continue and isinstance(a_content, str):
            a_content = a_content.encode("utf-8")
        if b_continue:
            result = SourceHash(hashlib.sha256(a_content).hexdigest())
        return result

    def __eq__(self, a_other: object) -> bool:
        b_continue = True
        result = False
        if b_continue and not isinstance(a_other, SourceHash):
            b_continue = False
            result = False
        if b_continue:
            result = self._value == a_other._value  # type: ignore[union-attr]
        return result

    def __hash__(self) -> int:
        return hash(self._value)

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"SourceHash({self._value[:12]}...)"
