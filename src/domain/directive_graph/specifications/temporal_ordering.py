"""Temporal ordering specification.

``expires_at``, when present, must be strictly after ``created_at``.
This is enforced at the entity level by ``model_validator`` and here at
the graph level for audit reporting.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.8
"""

from __future__ import annotations

from domain.directive_graph.directive_graph import DirectiveGraph


class ExpiresAfterCreatedSpec:
    """Directives with expires_at must have it strictly after created_at."""

    def is_satisfied_by(self, graph: DirectiveGraph) -> bool:
        """Return True iff all temporal orderings are valid.

        Args:
            graph (DirectiveGraph): The graph to check.

        Returns:
            bool: True when satisfied.
        """
        return len(self.violations(graph)) == 0

    def violations(self, graph: DirectiveGraph) -> list[str]:
        """Return violation messages for invalid temporal orderings.

        Args:
            graph (DirectiveGraph): The graph to check.

        Returns:
            list[str]: Human-readable violation descriptions.
        """
        messages: list[str] = []
        for d in graph.directives:
            if d.expires_at is not None and d.expires_at <= d.created_at:
                messages.append(
                    f"Directive {d.id!r}: expires_at ({d.expires_at!r}) is not "
                    f"after created_at ({d.created_at!r})"
                )
        return messages
