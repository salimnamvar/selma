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
        """Transform the success value, preserving failure unchanged.

        Success with value=None is valid (SC-003); the mapper receives None.
        """
        b_continue = True
        result: Result[_U] = Result.failure("unreachable")
        if b_continue and not self._is_success:
            b_continue = False
            result = Result.failure(self.message)
        if b_continue:
            result = Result.success(a_fn(self.value), self.message)  # type: ignore[arg-type]
        return result

    def flat_map(self, a_fn: Callable[[_T], Result[_U]]) -> Result[_U]:
        """Chain a function that itself returns a Result.

        Success with value=None is valid; the chained function receives None.
        """
        b_continue = True
        result: Result[_U] = Result.failure("unreachable")
        if b_continue and not self._is_success:
            b_continue = False
            result = Result.failure(self.message)
        if b_continue:
            result = a_fn(self.value)  # type: ignore[arg-type]
        return result

    def unwrap(self) -> _T:
        """Return the success value.

        Preconditions: caller has verified is_success() is True, or accepts
        that failure yields a typed null-like value for non-success paths.
        Prefer unwrap_or for recoverable defaults. Does not raise (SC-002).
        """
        b_continue = True
        result: _T | None = None
        if b_continue and self._is_success:
            b_continue = False
            result = self.value  # type: ignore[assignment]
        if b_continue:
            result = None  # type: ignore[assignment]
        return result  # type: ignore[return-value]

    def unwrap_or(self, a_default: _T) -> _T:
        """Return the success value, or a_default on failure."""
        b_continue = True
        result: _T = a_default
        if b_continue and self._is_success:
            b_continue = False
            result = self.value  # type: ignore[assignment]
        if b_continue:
            result = a_default
        return result

    @staticmethod
    def success(a_value: _U, a_message: str = "Success") -> Result[_U]:
        """Create a successful result with a value."""
        r = Result(value=a_value, message=a_message)
        object.__setattr__(r, "_is_success", True)
        return r

    @staticmethod
    def failure(a_message: str) -> Result[Any]:
        """Create a failure result with no value."""
        r: Result[Any] = Result(value=None, message=a_message)
        object.__setattr__(r, "_is_success", False)
        return r


INVALID_RESULT: Result[Any] = Result.failure(
    "INVALID_RESULT: Uninitialized result sentinel (SC-004)"
)
