"""FilePath value object — absolute file path with validation.

Immutable, validates non-empty.
"""

from __future__ import annotations

from pathlib import Path


class FilePath:
    """Absolute file path. Value object with validation."""

    __slots__ = ("_value",)

    def __init__(self, a_value: str) -> None:
        if not a_value:
            raise ValueError("FilePath cannot be empty")
        self._value = a_value

    @property
    def value(self) -> str:
        return self._value

    @property
    def extension(self) -> str:
        return Path(self._value).suffix

    @property
    def name(self) -> str:
        return Path(self._value).name

    def __eq__(self, a_other: object) -> bool:
        b_continue = True
        result = False
        if b_continue and not isinstance(a_other, FilePath):
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
        return f"FilePath({self._value!r})"
