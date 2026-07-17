"""Lineage DAG validator domain service.

Implements the mechanical validation algorithm from SPECIFICATION.md §2.2.3:

1. Build ancestry graph from parent_lineage_ids → child lineage_id
2. Detect cycles
3. Validate parent existence (lineage + execution IDs)
4. Validate operation consistency (also on Lineage VO)
5. Validate ancestry depth ≤ 64
6. Validate no self-reference
7. Validate temporal ordering (child timestamp ≥ parent timestamps)

Reference: SPECIFICATION.md §2.2.3
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.directive_graph.directive_graph import DirectiveGraph
from domain.directive_graph.enums import LineageOperation

MAX_ANCESTRY_DEPTH: int = 64


@dataclass(frozen=True)
class LineageViolation:
    """A single lineage constraint violation.

    Attributes:
        directive_id: Execution ID of the offending directive (or ``*``).
        message: Human-readable description.
    """

    directive_id: str
    message: str


class LineageValidator:
    """Validates lineage records across the directive graph per §2.2.3."""

    def validate(self, graph: DirectiveGraph) -> list[LineageViolation]:
        """Return all lineage violations for the graph.

        Args:
            graph: The graph to validate.

        Returns:
            Empty list iff the graph is valid.
        """
        violations: list[LineageViolation] = []
        violations.extend(self._validate_self_references(graph))
        violations.extend(self._validate_parent_references(graph))
        violations.extend(self._validate_operation_consistency(graph))
        violations.extend(self._validate_cycles(graph))
        violations.extend(self._validate_temporal_ordering(graph))
        violations.extend(self._validate_ancestry_depth(graph))
        return violations

    def _validate_self_references(self, graph: DirectiveGraph) -> list[LineageViolation]:
        """A rule MUST NOT list its own lineage_id or id as a parent."""
        violations: list[LineageViolation] = []
        for d in graph.directives:
            if d.lineage is None:
                continue
            if d.lineage_id in d.lineage.parent_lineage_ids:
                violations.append(
                    LineageViolation(
                        directive_id=d.id,
                        message=(
                            f"Rule references itself in parent_lineage_ids "
                            f"(lineage_id={d.lineage_id!r})"
                        ),
                    )
                )
            if d.id in d.lineage.parent_execution_ids:
                violations.append(
                    LineageViolation(
                        directive_id=d.id,
                        message=f"Rule references itself in parent_execution_ids (id={d.id!r})",
                    )
                )
        return violations

    def _validate_parent_references(self, graph: DirectiveGraph) -> list[LineageViolation]:
        """Every lineage parent ID must reference a directive in the graph."""
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
                            message=(f"Lineage parent_lineage_id {pid!r} does not " f"exist in the graph"),
                        )
                    )
            for pid in d.lineage.parent_execution_ids:
                if pid not in known_ids:
                    violations.append(
                        LineageViolation(
                            directive_id=d.id,
                            message=(f"Lineage parent_execution_id {pid!r} does not " f"exist in the graph"),
                        )
                    )
        return violations

    def _validate_operation_consistency(self, graph: DirectiveGraph) -> list[LineageViolation]:
        """fork/split → 1 parent lineage; merge → 2 parent lineages."""
        violations: list[LineageViolation] = []
        for d in graph.directives:
            if d.lineage is None:
                continue
            op = d.lineage.operation
            n = len(d.lineage.parent_lineage_ids)
            if op in (LineageOperation.FORK, LineageOperation.SPLIT) and n != 1:
                violations.append(
                    LineageViolation(
                        directive_id=d.id,
                        message=f"{op} requires exactly 1 parent_lineage_id; got {n}",
                    )
                )
            elif op == LineageOperation.MERGE and n != 2:
                violations.append(
                    LineageViolation(
                        directive_id=d.id,
                        message=f"merge requires exactly 2 parent_lineage_ids; got {n}",
                    )
                )
        return violations

    def _validate_cycles(self, graph: DirectiveGraph) -> list[LineageViolation]:
        """Detect directed cycles in parent_lineage_ids → child lineage_id."""
        adjacency: dict[str, list[str]] = {}
        for d in graph.directives:
            adjacency.setdefault(d.lineage_id, [])
            if d.lineage is None:
                continue
            for parent_id in d.lineage.parent_lineage_ids:
                adjacency.setdefault(parent_id, [])
                # edge: parent → child
                adjacency[parent_id].append(d.lineage_id)

        cyclic = self._cyclic_nodes(adjacency)
        if not cyclic:
            return []
        return [
            LineageViolation(
                directive_id="*",
                message=f"Lineage DAG cycle detected involving lineage_id {nid!r}",
            )
            for nid in cyclic
        ]

    def _validate_temporal_ordering(self, graph: DirectiveGraph) -> list[LineageViolation]:
        """Child lineage.timestamp MUST be ≥ max(parent lineage timestamps)."""
        by_exec = {d.id: d for d in graph.directives}
        violations: list[LineageViolation] = []
        for d in graph.directives:
            if d.lineage is None:
                continue
            child_ts = d.lineage.timestamp
            for pid in d.lineage.parent_execution_ids:
                parent = by_exec.get(pid)
                if parent is None:
                    continue
                if parent.lineage is not None and parent.lineage.timestamp > child_ts:
                    violations.append(
                        LineageViolation(
                            directive_id=d.id,
                            message=(
                                f"Parent timestamp violates temporal ordering: "
                                f"parent {pid!r} lineage.timestamp "
                                f"{parent.lineage.timestamp!r} > child {child_ts!r}"
                            ),
                        )
                    )
        return violations

    def _validate_ancestry_depth(self, graph: DirectiveGraph) -> list[LineageViolation]:
        """Ancestry depth must not exceed max_ancestry_depth (64)."""
        # Build lineage_id → parent lineage_ids adjacency for depth on lineage roots
        parent_map: dict[str, list[str]] = {}
        for d in graph.directives:
            parent_map.setdefault(d.lineage_id, [])
            if d.lineage is not None:
                # Prefer the most specific parents recorded for this lineage root
                parents = list(d.lineage.parent_lineage_ids)
                if not parent_map[d.lineage_id]:
                    parent_map[d.lineage_id] = parents
                else:
                    # union
                    parent_map[d.lineage_id] = list(set(parent_map[d.lineage_id]) | set(parents))

        violations: list[LineageViolation] = []
        for d in graph.directives:
            depth = self._measure_depth(d.lineage_id, parent_map, visited=set())
            if depth > MAX_ANCESTRY_DEPTH:
                violations.append(
                    LineageViolation(
                        directive_id=d.id,
                        message=(f"Lineage ancestry depth {depth} exceeds " f"maximum {MAX_ANCESTRY_DEPTH}"),
                    )
                )
        return violations

    def _measure_depth(
        self,
        node_id: str,
        parent_map: dict[str, list[str]],
        visited: set[str],
    ) -> int:
        """Return ancestry depth of the given lineage node.

        Cycles return 0 here; cycle violations are reported separately.
        """
        if node_id in visited:
            return 0
        parents = parent_map.get(node_id, [])
        if not parents:
            return 0
        visited = visited | {node_id}
        return 1 + max(self._measure_depth(pid, parent_map, visited) for pid in parents)

    @staticmethod
    def _cyclic_nodes(adjacency: dict[str, list[str]]) -> list[str]:
        """Return sorted node IDs that participate in at least one cycle."""
        white, grey, black = 0, 1, 2
        all_nodes: set[str] = set(adjacency)
        for neighbours in adjacency.values():
            all_nodes.update(neighbours)
        colour: dict[str, int] = dict.fromkeys(all_nodes, white)
        cyclic_nodes: set[str] = set()

        for start in list(all_nodes):
            if colour[start] != white:
                continue
            stack: list[tuple[str, object]] = [(start, iter(adjacency.get(start, [])))]
            colour[start] = grey
            while stack:
                node, neighbours = stack[-1]
                try:
                    nxt = next(neighbours)  # type: ignore[call-overload]
                    if colour.get(nxt, white) == grey:
                        cyclic_nodes.update(n for n, _ in stack)
                        cyclic_nodes.add(nxt)
                    elif colour.get(nxt, white) == white:
                        colour[nxt] = grey
                        stack.append((nxt, iter(adjacency.get(nxt, []))))
                except StopIteration:
                    colour[node] = black
                    stack.pop()

        return sorted(cyclic_nodes)
