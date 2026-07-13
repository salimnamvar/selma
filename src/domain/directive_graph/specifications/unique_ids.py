"""Uniqueness specifications for execution IDs.

Per SPECIFICATION.md §2.3 (Lineage-Uniqueness Refinement):
- Execution IDs (``id``) MUST be unique within a ruleset.
- ``lineage_id`` MAY be shared by multiple directives after fork/split.
- Primary key is ``(lineage_id, id)``; ``id`` alone is also globally unique.

Reference: SPECIFICATION.md §2.3
"""

from __future__ import annotations

from domain.directive_graph.directive_graph import DirectiveGraph


class UniqueExecutionIdsSpec:
    """Every execution id within a DirectiveGraph must be unique."""

    def is_satisfied_by(self, graph: DirectiveGraph) -> bool:
        """Return True iff all execution IDs are unique.

        Args:
            graph: The graph to check.

        Returns:
            True when satisfied.
        """
        ids = [d.id for d in graph.directives]
        return len(ids) == len(set(ids))

    def violations(self, graph: DirectiveGraph) -> list[str]:
        """Return violation messages for each duplicate execution ID.

        Args:
            graph: The graph to check.

        Returns:
            Human-readable violation descriptions.
        """
        seen: set[str] = set()
        duplicates: set[str] = set()
        for d in graph.directives:
            if d.id in seen:
                duplicates.add(d.id)
            seen.add(d.id)
        return [f"Duplicate execution id: {eid!r}" for eid in sorted(duplicates)]
