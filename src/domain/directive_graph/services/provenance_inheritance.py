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

from domain.directive_graph.directive import Directive
from domain.directive_graph.directive_graph import DirectiveGraph
from domain.directive_graph.scalars import ActorId


class ProvenanceInheritanceService:
    """Computes creator_provenance across the lineage chain for a directive."""

    def compute_provenance(self, directive: Directive, graph: DirectiveGraph) -> frozenset[ActorId]:
        """Return the set of all actors in the directive's full lineage.

        Args:
            directive: The directive whose provenance to compute.
            graph: The graph containing the directive.

        Returns:
            All authored_by actors through the lineage.
        """
        return frozenset(self._collect(directive, graph, visited=set()))

    def _collect(
        self,
        directive: Directive,
        graph: DirectiveGraph,
        visited: set[str],
    ) -> set[ActorId]:
        """Recursively collect authored_by actors through ancestry."""
        if directive.id in visited:
            return set()
        visited = visited | {directive.id}

        actors: set[ActorId] = set()
        authored_by = directive.metadata and directive.metadata.audit and directive.metadata.audit.authored_by
        if authored_by:
            actors.add(authored_by)

        if directive.lineage is None:
            return actors

        for parent_exec_id in directive.lineage.parent_execution_ids:
            parent = graph.get_by_id(parent_exec_id)
            if parent is not None:
                actors |= self._collect(parent, graph, visited)
        return actors
