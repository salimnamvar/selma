"""Evaluator tree validator domain service.

Walks every directive's evaluator AST and enforces the complexity limits
from SPECIFICATION.md §2.9.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.7
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.directive_graph.directive_graph import DirectiveGraph
from domain.directive_graph.specifications.evaluator_complexity import _walk_evaluator
from domain.directive_graph.specifications.evaluator_complexity import MAX_COMPOSITE_DEPTH
from domain.directive_graph.specifications.evaluator_complexity import MAX_EVALUATOR_NODES


@dataclass(frozen=True)
class EvaluatorTreeViolation:
    """A single evaluator tree constraint violation.

    Attributes:
        directive_id (str): Execution ID of the offending directive.
        message (str): Human-readable description.
    """

    directive_id: str
    message: str


class EvaluatorTreeValidator:
    """Validates evaluator AST complexity across all directives.

    Enforces:
    - Composite nesting depth ≤ 32
    - Total evaluator nodes per directive ≤ 256
    (Composite width ≤ 64 is enforced by Pydantic ``max_length`` on the
    ``sub_evaluators`` field and does not require re-checking here.)
    """

    def validate(self, graph: DirectiveGraph) -> list[EvaluatorTreeViolation]:
        """Return all evaluator tree violations for the graph.

        Args:
            graph (DirectiveGraph): The graph to validate.

        Returns:
            list[EvaluatorTreeViolation]: Empty list iff the graph is valid.
        """
        violations: list[EvaluatorTreeViolation] = []
        for directive in graph.directives:
            node_count, max_depth = _walk_evaluator(directive.evaluator_config, depth=0)
            if max_depth >= MAX_COMPOSITE_DEPTH:
                violations.append(
                    EvaluatorTreeViolation(
                        directive_id=directive.id,
                        message=(
                            f"Evaluator composite depth {max_depth} exceeds " f"maximum {MAX_COMPOSITE_DEPTH - 1}"
                        ),
                    )
                )
            if node_count > MAX_EVALUATOR_NODES:
                violations.append(
                    EvaluatorTreeViolation(
                        directive_id=directive.id,
                        message=(f"Evaluator node count {node_count} exceeds " f"maximum {MAX_EVALUATOR_NODES}"),
                    )
                )
        return violations
