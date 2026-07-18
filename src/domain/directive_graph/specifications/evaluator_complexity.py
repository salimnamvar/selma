"""Evaluator tree complexity specification.

Enforces per-directive limits from SPECIFICATION.md §2.9 / x-complexity-limits:
- max composite depth: 32
- max composite width: 64 (enforced by Pydantic ``max_length`` on ``sub_evaluators``)
- max evaluator nodes per directive: 256

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.8
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from domain.directive_graph.evaluators import CompositeEvaluator
from domain.directive_graph.evaluators import Evaluator

if TYPE_CHECKING:
    from domain.directive_graph.directive_graph import DirectiveGraph

MAX_COMPOSITE_DEPTH: int = 32
MAX_EVALUATOR_NODES: int = 256


def _walk_evaluator(a_evaluator: Evaluator, a_depth: int) -> tuple[int, int]:
    """Return ``(node_count, max_depth)`` for the evaluator subtree.

    Args:
        a_evaluator (Evaluator): Root of the subtree.
        a_depth (int): Current nesting depth (0 = root).

    Returns:
        tuple[int, int]: (total nodes, maximum depth reached in this subtree).
    """
    total, max_d = 1, a_depth
    if isinstance(a_evaluator, CompositeEvaluator):
        for child in a_evaluator.sub_evaluators:
            child_count, child_depth = _walk_evaluator(child, a_depth + 1)
            total += child_count
            max_d = max(max_d, child_depth)
    return total, max_d


class EvaluatorTreeComplexitySpec:
    """Per-directive evaluator tree must not exceed depth or node count limits."""

    def is_satisfied_by(self, a_object: DirectiveGraph) -> bool:
        """Return True iff all directives comply with complexity limits.

        Args:
            a_object (DirectiveGraph): The graph to check.

        Returns:
            bool: True when satisfied.
        """
        return len(self.violations(a_object)) == 0

    def violations(self, a_object: DirectiveGraph) -> list[str]:
        """Return violation messages for each directive that exceeds limits.

        Args:
            a_object (DirectiveGraph): The graph to check.

        Returns:
            list[str]: Human-readable violation descriptions.
        """
        messages: list[str] = []
        for directive in a_object.directives:
            node_count, max_depth = _walk_evaluator(directive.evaluator_config, a_depth=0)
            if max_depth >= MAX_COMPOSITE_DEPTH:
                messages.append(
                    f"Directive {directive.id!r}: evaluator composite depth "
                    f"{max_depth} exceeds max {MAX_COMPOSITE_DEPTH - 1}"
                )
            if node_count > MAX_EVALUATOR_NODES:
                messages.append(
                    f"Directive {directive.id!r}: evaluator node count {node_count} exceeds max {MAX_EVALUATOR_NODES}"
                )
        return messages
