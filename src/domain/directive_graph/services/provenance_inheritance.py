"""Provenance inheritance domain service.

Computes ``creator_provenance`` for a directive — the set of all actor IDs
that authored any directive in its lineage chain.

Per SPECIFICATION.md §3.2 and x-creator-provenance:
- create / modify: { authored_by }
- fork / split: inherited from parent (same set, via parent walk)
- merge: sorted-set union of both parents' provenances (via parent walk)

Reference: SPECIFICATION.md §3.2
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.directive_graph.directive import Directive
    from domain.directive_graph.directive_graph import DirectiveGraph
    from domain.directive_graph.scalars import ActorId


class ProvenanceInheritanceService:
    """Computes creator_provenance across the lineage chain for a directive."""

    def compute_provenance(self, a_directive: Directive, a_graph: DirectiveGraph) -> frozenset[ActorId]:
        """Return the set of all actors in the directive's full lineage.

        Args:
            a_directive: The directive whose provenance to compute.
            a_graph: The graph containing the directive.

        Returns:
            All authored_by actors through the lineage.
        """
        return frozenset(self._collect(a_directive, a_graph, a_visited=set()))

    def _collect(
        self,
        a_directive: Directive,
        a_graph: DirectiveGraph,
        a_visited: set[str],
    ) -> set[ActorId]:
        """Recursively collect authored_by actors through ancestry."""
        if a_directive.id in a_visited:
            result: set[ActorId] = set()
        else:
            a_visited = a_visited | {a_directive.id}

            actors: set[ActorId] = set()
            authored_by = a_directive.metadata and a_directive.metadata.audit and a_directive.metadata.audit.authored_by
            if authored_by:
                actors.add(authored_by)

            if a_directive.lineage is not None:
                for parent_exec_id in a_directive.lineage.parent_execution_ids:
                    parent = a_graph.get_by_id(parent_exec_id)
                    if parent is not None:
                        actors |= self._collect(parent, a_graph, a_visited)
            result = actors
        return result
