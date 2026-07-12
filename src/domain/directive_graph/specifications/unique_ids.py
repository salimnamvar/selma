"""Uniqueness specifications for lineage and execution IDs.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.8
"""

from __future__ import annotations

from domain.directive_graph.directive_graph import DirectiveGraph


class UniqueLineageIdsSpec:
    """Every lineage_id within a DirectiveGraph must be unique.

    After fork/split, multiple directives may share the same lineage_id —
    this specification flags that as a violation.  Each lineage root MUST
    appear exactly once.
    """

    def is_satisfied_by(self, graph: DirectiveGraph) -> bool:
        """Return True iff all lineage_ids are unique.

        Args:
            graph (DirectiveGraph): The graph to check.

        Returns:
            bool: True when satisfied.
        """
        ids = [d.lineage_id for d in graph.directives]
        return len(ids) == len(set(ids))

    def violations(self, graph: DirectiveGraph) -> list[str]:
        """Return violation messages for each duplicate lineage_id.

        Args:
            graph (DirectiveGraph): The graph to check.

        Returns:
            list[str]: Human-readable violation descriptions.
        """
        seen: set[str] = set()
        duplicates: set[str] = set()
        for d in graph.directives:
            if d.lineage_id in seen:
                duplicates.add(d.lineage_id)
            seen.add(d.lineage_id)
        return [
            f"Duplicate lineage_id: {lid!r}" for lid in sorted(duplicates)
        ]


class UniqueExecutionIdsSpec:
    """Every execution id within a DirectiveGraph must be unique."""

    def is_satisfied_by(self, graph: DirectiveGraph) -> bool:
        """Return True iff all execution IDs are unique.

        Args:
            graph (DirectiveGraph): The graph to check.

        Returns:
            bool: True when satisfied.
        """
        ids = [d.id for d in graph.directives]
        return len(ids) == len(set(ids))

    def violations(self, graph: DirectiveGraph) -> list[str]:
        """Return violation messages for each duplicate execution ID.

        Args:
            graph (DirectiveGraph): The graph to check.

        Returns:
            list[str]: Human-readable violation descriptions.
        """
        seen: set[str] = set()
        duplicates: set[str] = set()
        for d in graph.directives:
            if d.id in seen:
                duplicates.add(d.id)
            seen.add(d.id)
        return [
            f"Duplicate execution id: {eid!r}" for eid in sorted(duplicates)
        ]
