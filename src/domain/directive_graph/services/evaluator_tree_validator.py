"""Evaluator tree validator — thin facade over EvaluatorTreeComplexitySpec.

Kept for callers that prefer a service-style API. The single source of
truth for limits and walking is ``EvaluatorTreeComplexitySpec``.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.directive_graph.directive_graph import DirectiveGraph
from domain.directive_graph.specifications.evaluator_complexity import EvaluatorTreeComplexitySpec


@dataclass(frozen=True)
class EvaluatorTreeViolation:
    """A single evaluator tree constraint violation.

    Attributes:
        directive_id: Execution ID of the offending directive.
        message: Human-readable description.
    """

    directive_id: str
    message: str


class EvaluatorTreeValidator:
    """Validates evaluator AST complexity across all directives.

    Delegates to ``EvaluatorTreeComplexitySpec`` to avoid duplicated walks.
    """

    def __init__(self) -> None:
        """Bind to the shared complexity specification."""
        self._spec = EvaluatorTreeComplexitySpec()

    def validate(self, graph: DirectiveGraph) -> list[EvaluatorTreeViolation]:
        """Return all evaluator tree violations for the graph."""
        violations: list[EvaluatorTreeViolation] = []
        for message in self._spec.violations(graph):
            # Messages look like: Directive 'RULE-001': evaluator ...
            directive_id = "*"
            if message.startswith("Directive ") and ":" in message:
                # Directive 'RULE-001': ...
                mid = message.split(":", 1)[0]
                directive_id = mid.removeprefix("Directive ").strip().strip("'\"")
            violations.append(EvaluatorTreeViolation(directive_id=directive_id, message=message))
        return violations
