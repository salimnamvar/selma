"""Specification protocol for graph-level invariants.

Specifications encapsulate a single business rule that can be evaluated
against a candidate object (typically a ``DirectiveGraph``).
"""

from __future__ import annotations

from typing import Protocol, TypeVar

T_contra = TypeVar("T_contra", contravariant=True)


class Specification(Protocol[T_contra]):
    """Boolean business rule with structured violation reporting.

    Implementations SHOULD be stateless and side-effect free.
    """

    def is_satisfied_by(self, candidate: T_contra) -> bool:
        """Return True iff the candidate satisfies this specification."""

    def violations(self, candidate: T_contra) -> list[str]:
        """Return human-readable violation messages (empty when satisfied)."""
