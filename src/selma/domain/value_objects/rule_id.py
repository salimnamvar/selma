"""RuleId value object — unique identifier for a lint rule.

Immutable, defined by its string value. Implements equality and hashing.
"""

from __future__ import annotations


class RuleId:
    """Unique identifier for a lint rule. Immutable value object.

    Examples: "SC001", "SC-001", "a-prefix", "mutable-default"
    """

    __slots__ = ("_value",)

    def __init__(self, a_value: str) -> None:
        if not a_value:
            raise ValueError("RuleId cannot be empty")
        self._value = a_value

    @property
    def value(self) -> str:
        return self._value

    def __eq__(self, a_other: object) -> bool:
        b_continue = True
        result = False
        if b_continue and not isinstance(a_other, RuleId):
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
        return f"RuleId({self._value!r})"
