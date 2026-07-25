"""Structured Result type for Safe Coding Doctrine compliance (SC-003).

Every function SHALL return a typed Result[T] with is_success(), value, and message.
Uses Pydantic v2 BaseModel with frozen config.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from typing import Generic
from typing import TypeVar

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import PrivateAttr

_T = TypeVar("_T")
_U = TypeVar("_U")


class Result(BaseModel, Generic[_T]):
    """Immutable structured result returned by all functions.

    Result[T] carries either a success value or a failure message.
    Success results have is_success() == True.
    Failure results have is_success() == False and value == None.
    """

    model_config = ConfigDict(frozen=True)

    value: _T | None
    message: str
    _is_success: bool = PrivateAttr(default=False)

    def model_post_init(self, __context: object) -> None:
        """Initialize private attributes."""
        if not hasattr(self, "_is_success"):
            object.__setattr__(self, "_is_success", False)

    def is_success(self) -> bool:
        """Return whether the operation succeeded."""
        return self._is_success

    def is_failure(self) -> bool:
        """Return whether the operation failed."""
        return not self._is_success

    def __bool__(self) -> bool:
        """True when the result represents success."""
        return self._is_success

    def map(self, a_fn: Callable[[_T], _U]) -> Result[_U]:
        """Transform the success value, preserving failure unchanged."""
        if not self._is_success:
            return Result.failure(self.message)
        return Result.success(a_fn(self.value), self.message)

    def flat_map(self, a_fn: Callable[[_T], Result[_U]]) -> Result[_U]:
        """Chain a function that itself returns a Result."""
        if not self._is_success:
            return Result.failure(self.message)
        return a_fn(self.value)

    def unwrap(self) -> _T:
        """Return the success value, or raise ValueError on failure."""
        if self._is_success:
            return self.value  # type: ignore[return-value]
        raise ValueError(f"Called unwrap() on failure: {self.message}")

    def unwrap_or(self, a_default: _T) -> _T:
        """Return the success value, or a_default on failure."""
        if self._is_success:
            return self.value  # type: ignore[assignment]
        return a_default

    @staticmethod
    def success(a_value: _U, a_message: str = "Success") -> Result[_U]:
        """Create a successful result with a value."""
        r = Result(value=a_value, message=a_message)
        object.__setattr__(r, "_is_success", True)
        return r

    @staticmethod
    def failure(a_message: str) -> Result[Any]:
        """Create a failure result with no value."""
        r = Result(value=None, message=a_message)
        object.__setattr__(r, "_is_success", False)
        return r


INVALID_RESULT: Result[Any] = Result.failure(
    "INVALID_RESULT: Uninitialized result sentinel (SC-004)"
)
