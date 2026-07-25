"""Structured Result type for Safe Coding Doctrine compliance (SC-003).

Every function SHALL return a typed Result[T] with is_success(), value, and message.
This module provides the canonical Result implementation.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
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

    def is_success(self) -> Result[bool]:
        """Return whether the operation succeeded.

        Precondition: None.
        Postcondition: Returns Result.success(True) if succeeded,
            Result.success(False) otherwise.
        Side effect: None.
        Resource: None.
        Failure: Never fails.
        """
        b_continue = True
        b_result: bool = False
        if b_continue:
            b_result = self._is_success
        return Result.success(b_result)

    def is_failure(self) -> Result[bool]:
        """Return whether the operation failed.

        Precondition: None.
        Postcondition: Returns Result.success(True) if failed,
            Result.success(False) otherwise.
        Side effect: None.
        Resource: None.
        Failure: Never fails.
        """
        b_continue = True
        b_result: bool = False
        if b_continue:
            b_result = not self._is_success
        return Result.success(b_result)

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
        b_continue = True
        result: Result[_U] = Result.failure("unreachable placeholder")

        if b_continue and not self._is_success:
            result = Result.failure(self.message)
            b_continue = False

        if b_continue:
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
        b_continue = True
        result: Result[_U] = Result.failure("unreachable placeholder")

        if b_continue and not self._is_success:
            result = Result.failure(self.message)
            b_continue = False

        if b_continue:
            result = a_fn(self.value)

        return result

    def unwrap(self) -> Result[_T]:
        """Return the success value, or Result.failure on failure.

        Preconditions:
            - Caller has verified is_success() or accepts the risk of failure.

        Postconditions:
            Returns Result.success with the wrapped value on success,
            or Result.failure on failure.

        Side Effects: None.

        Resource Ownership: None.

        Failure Modes: Returns Result.failure when called on a failure result.
        """
        b_continue = True
        result: Result[_T] = Result.failure("unreachable placeholder")

        if b_continue and self._is_success:
            result = Result.success(self.value)
            b_continue = False

        if b_continue:
            result = Result.failure(f"Called unwrap() on failure: {self.message}")

        return result

    def unwrap_or(self, a_default: _T) -> Result[_T]:
        """Return the success value, or Result.success with a_default on failure.

        Preconditions:
            - a_default is a valid fallback of type _T.

        Postconditions:
            Returns Result.success with the wrapped value on success,
            or Result.success(a_default) on failure.

        Side Effects: None.

        Resource Ownership: None.

        Failure Modes: None.
        """
        b_continue = True
        result: Result[_T] = Result.success(a_default)

        if b_continue and self._is_success:
            result = Result.success(self.value)

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
        b_continue = True
        result: Result[_U] = Result(
            _is_success=False, value=None, message="unreachable"
        )
        if b_continue:
            result = Result(_is_success=True, value=a_value, message=a_message)
        return result

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
        b_continue = True
        result: Result[Any] = Result(
            _is_success=False, value=None, message="unreachable"
        )
        if b_continue:
            result = Result(_is_success=False, value=None, message=a_message)
        return result


INVALID_RESULT: Result[Any] = Result.failure(
    "INVALID_RESULT: Uninitialized result sentinel"
)
