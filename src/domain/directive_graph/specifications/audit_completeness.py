"""Audit completeness specification (reporting aid).

Active-author is enforced at the entity level by ``Directive`` validators.
This graph-level specification remains available for audit reporting only;
it is not registered in ``DirectiveGraphValidator`` to avoid duplication.
"""

from __future__ import annotations

from domain.directive_graph.directive_graph import DirectiveGraph
from domain.directive_graph.enums import DirectiveStatus


class ActiveDirectiveRequiresAuthorSpec:
    """All active directives must have metadata.audit.authored_by populated."""

    def is_satisfied_by(self, graph: DirectiveGraph) -> bool:
        """Return True iff all active directives have an author."""
        return len(self.violations(graph)) == 0

    def violations(self, graph: DirectiveGraph) -> list[str]:
        """Return violation messages for active directives missing authored_by."""
        messages: list[str] = []
        for d in graph.directives:
            if d.status != DirectiveStatus.ACTIVE:
                continue
            authored_by = d.metadata and d.metadata.audit and d.metadata.audit.authored_by
            if not authored_by:
                messages.append(f"Directive {d.id!r} is ACTIVE but has no " f"metadata.audit.authored_by")
        return messages
