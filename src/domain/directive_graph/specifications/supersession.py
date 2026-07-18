"""Supersession binding specification (SPECIFICATION.md §2.2.4).

When status is ``superseded``, ``metadata.migration.superseded_by`` MUST
reference an existing directive that is ``active`` or ``draft``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from domain.directive_graph.enums import DirectiveStatus

if TYPE_CHECKING:
    from domain.directive_graph.directive_graph import DirectiveGraph


class SupersessionBindingSpec:
    """Superseded directives must declare a valid successor."""

    def is_satisfied_by(self, a_object: DirectiveGraph) -> bool:
        """Return True iff all supersession bindings are valid."""
        return len(self.violations(a_object)) == 0

    def violations(self, a_object: DirectiveGraph) -> list[str]:
        """Return violation messages for invalid supersession bindings."""
        known = {d.id: d for d in a_object.directives}
        messages: list[str] = []
        for d in a_object.directives:
            if d.status != DirectiveStatus.SUPERSEDED:
                continue
            successor_id = None
            if d.metadata and d.metadata.migration:
                successor_id = d.metadata.migration.superseded_by
            if not successor_id:
                messages.append(f"Directive {d.id!r} is SUPERSEDED but has no metadata.migration.superseded_by")
                continue
            successor = known.get(successor_id)
            if successor is None:
                messages.append(f"Directive {d.id!r}: superseded_by references unknown id {successor_id!r}")
            elif successor.status not in (DirectiveStatus.ACTIVE, DirectiveStatus.DRAFT):
                messages.append(
                    f"Directive {d.id!r}: superseded_by {successor_id!r} must be "
                    f"active or draft (got {successor.status!r})"
                )
        return messages
