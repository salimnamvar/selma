"""RuleId value object — unique identifier for a lint rule.

Immutable, defined by its string value. Uses Pydantic v2 for validation.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict


class RuleId(BaseModel):
    """Unique identifier for a lint rule. Immutable value object.

    Examples: "SC001", "SC-001", "a-prefix", "mutable-default"
    """

    model_config = ConfigDict(frozen=True)

    _value: str

    def __init__(self, a_value: str) -> None:
        if not a_value:
            raise ValueError("RuleId cannot be empty")
        object.__setattr__(self, "_value", a_value)

    @property
    def value(self) -> str:
        return self._value

    def __eq__(self, a_other: object) -> bool:
        b_continue = True
        result = False
        if b_continue and isinstance(a_other, RuleId) and self._value == a_other._value:
            result = True
        return result

    def __hash__(self) -> int:
        return hash(self._value)

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"RuleId({self._value!r})"
