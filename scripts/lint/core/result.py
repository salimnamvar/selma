"""Structured Result type for Safe Coding Doctrine compliance (SC-003).

Every function SHALL return a typed Result[T] with is_success(), value, and message.
This module provides the canonical Result implementation and INVALID_RESULT sentinel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Callable
from typing import Generic
from typing import TypeVar

_T = TypeVar("_T")
_U = TypeVar("_U")


@dataclass(frozen=True)
class Result(Generic[_T]):
    """Immutable structured result returned by all functions.

    Result[T] carries either a success value or a failure message.
    Success results have is_success() == True and a non-None value.
    Failure results have is_success() == False and value == None.

    Attributes:
        _is_success: Whether the operation completed successfully.
        value: The result value, present only when is_success() is True.
        message: Human-readable description of the outcome, always present.
    """

    _is_success: bool
    value: _T | None
    message: str

    def is_success(self) -> bool:
        """Return whether the operation succeeded."""
        return self._is_success

    def is_failure(self) -> bool:
        """Return whether the operation failed."""
        return not self._is_success

    def __bool__(self) -> bool:
        """True when the result represents success. Enables ``if result:`` guards."""
        return self._is_success

    def map(self, a_fn: Callable[[_T], _U]) -> Result[_U]:
        """Transform the success value, preserving failure unchanged.

        Preconditions:
            - a_fn is a pure callable that transforms _T to _U.

        Postconditions:
            Returns Result[_U] with a_fn applied to value on success,
            or the original failure message on failure.

        Side Effects: None.

        Resource Ownership: None.

        Failure Modes: None.
        """
        b_continue: bool = True
        result: Result[_U] = INVALID_RESULT  # type: ignore[assignment]

        if b_continue and not self._is_success:
            result = Result.failure(self.message)
            b_continue = False

        if b_continue and self.value is not None:
            result = Result.success(a_fn(self.value), self.message)

        return result

    def flat_map(self, a_fn: Callable[[_T], Result[_U]]) -> Result[_U]:
        """Chain a function that itself returns a Result.

        Preconditions:
            - a_fn accepts _T and returns Result[_U].

        Postconditions:
            Returns a_fn(value) on success, or the original failure on failure.

        Side Effects: None.

        Resource Ownership: None.

        Failure Modes: None.
        """
        b_continue: bool = True
        result: Result[_U] = INVALID_RESULT  # type: ignore[assignment]

        if b_continue and not self._is_success:
            result = Result.failure(self.message)
            b_continue = False

        if b_continue and self.value is not None:
            result = a_fn(self.value)

        return result

    def unwrap(self) -> _T:
        """Return the success value, or raise ValueError on failure.

        Preconditions:
            - Caller has verified is_success() or accepts the risk of ValueError.

        Postconditions:
            Returns the wrapped value on success.

        Side Effects: None.

        Resource Ownership: None.

        Failure Modes: Raises ValueError when called on a failure result.
        """
        b_continue: bool = True
        result: Any = None

        if b_continue and self._is_success and self.value is not None:
            result = self.value
            b_continue = False

        if b_continue:
            raise ValueError(f"Called unwrap() on failure: {self.message}")

        return result

    def unwrap_or(self, a_default: _T) -> _T:
        """Return the success value, or a_default on failure.

        Preconditions:
            - a_default is a valid fallback of type _T.

        Postconditions:
            Returns the wrapped value on success, a_default on failure.

        Side Effects: None.

        Resource Ownership: None.

        Failure Modes: None.
        """
        b_continue: bool = True
        result: _T = a_default

        if b_continue and self._is_success and self.value is not None:
            result = self.value

        return result

    @staticmethod
    def success(a_value: _U, a_message: str = "Success") -> Result[_U]:
        """Create a successful result with a value.

        Preconditions:
            - a_value is the value to wrap.
            - a_message is a human-readable description.

        Postconditions:
            Returns Result with is_success=True.

        Side Effects: None.

        Resource Ownership: None.

        Failure Modes: None — always succeeds.
        """
        return Result(_is_success=True, value=a_value, message=a_message)

    @staticmethod
    def failure(a_message: str) -> Result[Any]:
        """Create a failure result with no value.

        Preconditions:
            - a_message is a human-readable failure description.

        Postconditions:
            Returns Result with is_success=False and value=None.

        Side Effects: None.

        Resource Ownership: None.

        Failure Modes: None — always creates failure result.
        """
        return Result(_is_success=False, value=None, message=a_message)


INVALID_RESULT: Result[Any] = Result(
    _is_success=False,
    value=None,
    message="INVALID_RESULT: function postcondition cannot be satisfied",
)
