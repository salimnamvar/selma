"""Domain exceptions for the Finding Lifecycle bounded context."""

from __future__ import annotations

# Re-export shared hard-deny for Finding callers (same 403 semantics).
from domain.authorization.exceptions import CapabilityDeniedError

__all__ = [
    "CapabilityDeniedError",
    "FindingDomainError",
    "FindingNotFoundError",
    "InvalidFindingTransitionError",
    "OptimisticConcurrencyError",
]


class FindingDomainError(Exception):
    """Base class for finding domain errors."""


class FindingNotFoundError(FindingDomainError):
    """Raised when a finding_id is not present in the store/aggregate."""

    def __init__(self, finding_id: str) -> None:
        self.finding_id = finding_id
        super().__init__(f"Finding not found: {finding_id!r}")


class InvalidFindingTransitionError(FindingDomainError):
    """Raised when a transition is illegal for the current FSM state."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class OptimisticConcurrencyError(FindingDomainError):
    """Raised when the expected projection version does not match (HTTP 409)."""

    def __init__(self, finding_id: str, expected: int, actual: int) -> None:
        self.finding_id = finding_id
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Optimistic concurrency conflict on {finding_id!r}: expected version {expected}, actual {actual}"
        )
