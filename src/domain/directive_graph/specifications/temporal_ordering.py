"""Temporal ordering specification (reporting aid).

``expires_at`` vs ``created_at`` is enforced at the entity level.
This graph-level specification remains available for audit reporting only;
it is not registered in ``DirectiveGraphValidator`` to avoid duplication.
"""

from __future__ import annotations

from domain.directive_graph.directive_graph import DirectiveGraph


class ExpiresAfterCreatedSpec:
    """Directives with expires_at must have it strictly after created_at."""

    def is_satisfied_by(self, graph: DirectiveGraph) -> bool:
        """Return True iff all temporal orderings are valid."""
        return len(self.violations(graph)) == 0

    def violations(self, graph: DirectiveGraph) -> list[str]:
        """Return violation messages for invalid temporal orderings."""
        messages: list[str] = []
        for d in graph.directives:
            if d.expires_at is not None and d.expires_at <= d.created_at:
                messages.append(
                    f"Directive {d.id!r}: expires_at ({d.expires_at!r}) is not " f"after created_at ({d.created_at!r})"
                )
        return messages
