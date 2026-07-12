"""Lineage validator domain service.

Validates:
1. Lineage parent IDs reference directives that exist in the graph.
2. Lineage ancestry depth does not exceed max_ancestry_depth = 64
   (SPECIFICATION.md §2.2.3 / x-identity-limits).

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.7
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.directive_graph.directive_graph import DirectiveGraph

MAX_ANCESTRY_DEPTH: int = 64


@dataclass(frozen=True)
class LineageViolation:
    """A single lineage constraint violation.

    Attributes:
        directive_id (str): Execution ID of the offending directive.
        message (str): Human-readable description.
    """

    directive_id: str
    message: str


class LineageValidator:
    """Validates lineage records across the directive graph."""

    def validate(self, graph: DirectiveGraph) -> list[LineageViolation]:
        """Return all lineage violations for the graph.

        Args:
            graph (DirectiveGraph): The graph to validate.

        Returns:
            list[LineageViolation]: Empty list iff the graph is valid.
        """
        violations: list[LineageViolation] = []
        violations.extend(self._validate_parent_references(graph))
        violations.extend(self._validate_ancestry_depth(graph))
        return violations

    def _validate_parent_references(self, graph: DirectiveGraph) -> list[LineageViolation]:
        """Check that every lineage parent_execution_id exists in the graph.

        Args:
            graph (DirectiveGraph): The graph to check.

        Returns:
            list[LineageViolation]: Violations for unresolvable parent IDs.
        """
        known_ids = graph.execution_ids()
        known_lineage_ids = graph.lineage_ids()
        violations: list[LineageViolation] = []
        for d in graph.directives:
            if d.lineage is None:
                continue
            for pid in d.lineage.parent_lineage_ids:
                if pid not in known_lineage_ids:
                    violations.append(
                        LineageViolation(
                            directive_id=d.id,
                            message=(
                                f"Lineage parent_lineage_id {pid!r} does not "
                                f"exist in the graph"
                            ),
                        )
                    )
            for pid in d.lineage.parent_execution_ids:
                if pid not in known_ids:
                    violations.append(
                        LineageViolation(
                            directive_id=d.id,
                            message=(
                                f"Lineage parent_execution_id {pid!r} does not "
                                f"exist in the graph"
                            ),
                        )
                    )
        return violations

    def _validate_ancestry_depth(self, graph: DirectiveGraph) -> list[LineageViolation]:
        """Check that no lineage ancestry chain exceeds max_ancestry_depth.

        Builds a parent map from lineage records and DFS-measures depth from
        each directive.

        Args:
            graph (DirectiveGraph): The graph to check.

        Returns:
            list[LineageViolation]: Violations for chains exceeding 64 hops.
        """
        # Build execution_id → set of parent execution IDs
        parent_map: dict[str, list[str]] = {d.id: [] for d in graph.directives}
        for d in graph.directives:
            if d.lineage is not None:
                parent_map[d.id] = list(d.lineage.parent_execution_ids)

        violations: list[LineageViolation] = []
        for d in graph.directives:
            depth = self._measure_depth(d.id, parent_map, visited=set())
            if depth > MAX_ANCESTRY_DEPTH:
                violations.append(
                    LineageViolation(
                        directive_id=d.id,
                        message=(
                            f"Lineage ancestry depth {depth} exceeds "
                            f"maximum {MAX_ANCESTRY_DEPTH}"
                        ),
                    )
                )
        return violations

    def _measure_depth(
        self,
        node_id: str,
        parent_map: dict[str, list[str]],
        visited: set[str],
    ) -> int:
        """Return the ancestry depth of the given node.

        Args:
            node_id (str): The node whose ancestry depth to measure.
            parent_map (dict[str, list[str]]): Parent adjacency map.
            visited (set[str]): Cycle guard (nodes already on the path).

        Returns:
            int: Maximum ancestry depth (0 = no parents).
        """
        if node_id in visited:
            return 0  # cycle guard; cycles are caught by NoDependencyCyclesSpec
        parents = parent_map.get(node_id, [])
        if not parents:
            return 0
        visited = visited | {node_id}
        return 1 + max(
            self._measure_depth(pid, parent_map, visited) for pid in parents
        )
