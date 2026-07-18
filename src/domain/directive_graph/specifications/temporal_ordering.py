"""Temporal ordering specification (reporting aid).

``expires_at`` vs ``created_at`` is enforced at the entity level.
This graph-level specification remains available for audit reporting only;
it is not registered in ``DirectiveGraphValidator`` to avoid duplication.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.directive_graph.directive_graph import DirectiveGraph


class ExpiresAfterCreatedSpec:
    """Directives with expires_at must have it strictly after created_at."""

    def is_satisfied_by(self, a_object: DirectiveGraph) -> bool:
        """Return True iff all temporal orderings are valid."""
        return len(self.violations(a_object)) == 0

    def violations(self, a_object: DirectiveGraph) -> list[str]:
        """Return violation messages for invalid temporal orderings."""
        messages: list[str] = []
        for d in a_object.directives:
            if d.expires_at is not None and d.expires_at <= d.created_at:
                messages.append(
                    f"Directive {d.id!r}: expires_at ({d.expires_at!r}) is not after created_at ({d.created_at!r})"
                )
        return messages
