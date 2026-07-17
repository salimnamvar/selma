"""Domain exceptions for the Directive Graph bounded context."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all directive-graph domain errors."""


class DirectiveNotFoundError(DomainError):
    """Raised when a referenced directive does not exist in the graph."""

    def __init__(self, execution_id: str) -> None:
        """Store the missing execution ID and format the message.

        Args:
            execution_id: Execution ID that was not found.
        """
        self.execution_id = execution_id
        super().__init__(f"Directive not found: {execution_id!r}")


class InvalidLifecycleTransitionError(DomainError):
    """Raised when a lifecycle transition violates status rules."""

    def __init__(self, message: str) -> None:
        """Create the error with a human-readable message.

        Args:
            message: Description of the illegal transition.
        """
        super().__init__(message)


class LifecycleInvariantError(DomainError):
    """Raised when a lifecycle operation would break a domain invariant."""

    def __init__(self, message: str) -> None:
        """Create the error with a human-readable message.

        Args:
            message: Description of the broken invariant.
        """
        super().__init__(message)
