"""Cross-reference validity specification.

All IDs referenced in ``depends_on``, ``conflicts_with``, and
``conflict_resolution.defer_to`` must resolve to existing directives.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.8
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.directive_graph.directive_graph import DirectiveGraph


class ValidCrossReferencesSpec:
    """Every directive reference in the graph must resolve to an existing directive."""

    def is_satisfied_by(self, a_object: DirectiveGraph) -> bool:
        """Return True iff all cross-references resolve.

        Args:
            a_object (DirectiveGraph): The graph to check.

        Returns:
            bool: True when satisfied.
        """
        return len(self.violations(a_object)) == 0

    def violations(self, a_object: DirectiveGraph) -> list[str]:
        """Return violation messages for every dangling reference.

        Args:
            a_object (DirectiveGraph): The graph to check.

        Returns:
            list[str]: Human-readable violation descriptions.
        """
        known_ids = a_object.execution_ids()
        messages: list[str] = []
        for d in a_object.directives:
            for ref in d.depends_on:
                if ref not in known_ids:
                    messages.append(f"Directive {d.id!r}: depends_on references unknown id {ref!r}")
            for ref in d.conflicts_with:
                if ref not in known_ids:
                    messages.append(f"Directive {d.id!r}: conflicts_with references unknown id {ref!r}")
            if d.conflict_resolution and d.conflict_resolution.defer_to:
                ref = d.conflict_resolution.defer_to
                if ref not in known_ids:
                    messages.append(f"Directive {d.id!r}: conflict_resolution.defer_to references unknown id {ref!r}")
        return messages
