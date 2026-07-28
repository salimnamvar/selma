"""FilePath value object — absolute file path with validation.

Immutable, validates non-empty. Uses Pydantic v2 for validation.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel
from pydantic import ConfigDict


class FilePath(BaseModel):
    """Absolute file path. Value object with validation.

    Uses Pydantic v2 for immutable validation.
    """

    model_config = ConfigDict(frozen=True)

    _value: str

    def __init__(self, a_value: str) -> None:
        if not a_value:
            raise ValueError("FilePath cannot be empty")
        object.__setattr__(self, "_value", a_value)

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
        if (
            b_continue
            and isinstance(a_other, FilePath)
            and self._value == a_other._value
        ):
            result = True
        return result

    def __hash__(self) -> int:
        return hash(self._value)

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"FilePath({self._value!r})"
