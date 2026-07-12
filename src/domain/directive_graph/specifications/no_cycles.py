"""Cycle-detection specifications for dependency and defer_to graphs.

Uses iterative DFS with a visited/in-stack set to detect directed cycles.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.8
"""

from __future__ import annotations

from domain.directive_graph.directive_graph import DirectiveGraph


def _has_cycle(adjacency: dict[str, list[str]]) -> list[str]:
    """Return a list of node IDs that participate in cycles (empty if none).

    Uses iterative DFS with a ``white/grey/black`` colouring scheme.

    Args:
        adjacency (dict[str, list[str]]): Directed graph as adjacency list.

    Returns:
        list[str]: Node IDs involved in at least one cycle.
    """
    WHITE, GREY, BLACK = 0, 1, 2
    # Snapshot all nodes (including implicit targets) before iterating
    all_nodes: set[str] = set(adjacency)
    for neighbours in adjacency.values():
        all_nodes.update(neighbours)
    colour: dict[str, int] = {node: WHITE for node in all_nodes}
    cyclic_nodes: set[str] = set()

    for start in list(all_nodes):
        if colour[start] != WHITE:
            continue
        # Iterative DFS: stack contains (node, iterator_over_neighbours)
        stack: list[tuple[str, iter]] = [(start, iter(adjacency.get(start, [])))]
        colour[start] = GREY
        while stack:
            node, neighbours = stack[-1]
            try:
                nxt = next(neighbours)
                if colour.get(nxt, WHITE) == GREY:
                    # Cycle detected — mark the whole grey chain
                    cyclic_nodes.update(n for n, _ in stack)
                    cyclic_nodes.add(nxt)
                elif colour.get(nxt, WHITE) == WHITE:
                    colour[nxt] = GREY
                    stack.append((nxt, iter(adjacency.get(nxt, []))))
            except StopIteration:
                colour[node] = BLACK
                stack.pop()

    return sorted(cyclic_nodes)


class NoDependencyCyclesSpec:
    """The ``depends_on`` graph across all directives must be acyclic."""

    def is_satisfied_by(self, graph: DirectiveGraph) -> bool:
        """Return True iff the depends_on graph is acyclic.

        Args:
            graph (DirectiveGraph): The graph to check.

        Returns:
            bool: True when satisfied.
        """
        return len(self.violations(graph)) == 0

    def violations(self, graph: DirectiveGraph) -> list[str]:
        """Return violation messages for each cycle participant.

        Args:
            graph (DirectiveGraph): The graph to check.

        Returns:
            list[str]: Human-readable violation descriptions.
        """
        adjacency: dict[str, list[str]] = {d.id: list(d.depends_on) for d in graph.directives}
        cyclic = _has_cycle(adjacency)
        if not cyclic:
            return []
        return [f"Cycle detected in depends_on graph involving directive id {nid!r}" for nid in cyclic]


class NoDeferToCyclesSpec:
    """The ``conflict_resolution.defer_to`` graph must be acyclic."""

    def is_satisfied_by(self, graph: DirectiveGraph) -> bool:
        """Return True iff the defer_to graph is acyclic.

        Args:
            graph (DirectiveGraph): The graph to check.

        Returns:
            bool: True when satisfied.
        """
        return len(self.violations(graph)) == 0

    def violations(self, graph: DirectiveGraph) -> list[str]:
        """Return violation messages for each cycle participant.

        Args:
            graph (DirectiveGraph): The graph to check.

        Returns:
            list[str]: Human-readable violation descriptions.
        """
        adjacency: dict[str, list[str]] = {}
        for d in graph.directives:
            adjacency[d.id] = []
            if d.conflict_resolution and d.conflict_resolution.defer_to:
                adjacency[d.id].append(d.conflict_resolution.defer_to)
        cyclic = _has_cycle(adjacency)
        if not cyclic:
            return []
        return [f"Cycle detected in defer_to graph involving directive id {nid!r}" for nid in cyclic]
