"""Uniqueness specifications for execution IDs.

Per SPECIFICATION.md §2.3 (Lineage-Uniqueness Refinement):
- Execution IDs (``id``) MUST be unique within a ruleset.
- ``lineage_id`` MAY be shared by multiple directives after fork/split.
- Primary key is ``(lineage_id, id)``; ``id`` alone is also globally unique.

Reference: SPECIFICATION.md §2.3
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.directive_graph.directive_graph import DirectiveGraph


class UniqueExecutionIdsSpec:
    """Every execution id within a DirectiveGraph must be unique."""

    def is_satisfied_by(self, a_object: DirectiveGraph) -> bool:
        """Return True iff all execution IDs are unique.

        Args:
            a_object: The graph to check.

        Returns:
            True when satisfied.
        """
        ids = [d.id for d in a_object.directives]
        return len(ids) == len(set(ids))

    def violations(self, a_object: DirectiveGraph) -> list[str]:
        """Return violation messages for each duplicate execution ID.

        Args:
            a_object: The graph to check.

        Returns:
            Human-readable violation descriptions.
        """
        seen: set[str] = set()
        duplicates: set[str] = set()
        for d in a_object.directives:
            if d.id in seen:
                duplicates.add(d.id)
            seen.add(d.id)
        return [f"Duplicate execution id: {eid!r}" for eid in sorted(duplicates)]
