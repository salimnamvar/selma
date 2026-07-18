"""Specificity calculator domain service.

Computes a deterministic specificity score for a directive based on
SPECIFICATION.md §2.8.2.

The score is used by ``ConflictResolver`` as the third tie-breaking factor
(after explicit overrides and priority comparison).

Higher score = more specific = wins in conflict resolution.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.7
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from domain.directive_graph.enums import TargetType
from domain.directive_graph.evaluators import CompositeEvaluator
from domain.directive_graph.evaluators import Evaluator
from domain.directive_graph.evaluators import FieldCheckEvaluator
from domain.directive_graph.evaluators import ThresholdEvaluator

if TYPE_CHECKING:
    from domain.directive_graph.directive import Directive


def _count_field_bindings(a_evaluator: Evaluator) -> int:
    """Count the number of field-binding leaf evaluators in the AST.

    Args:
        a_evaluator (Evaluator): Root evaluator to inspect.

    Returns:
        int: Number of FieldCheck + Threshold evaluators in the tree.
    """
    if isinstance(a_evaluator, (FieldCheckEvaluator, ThresholdEvaluator)):
        result = 1
    elif isinstance(a_evaluator, CompositeEvaluator):
        result = sum(_count_field_bindings(child) for child in a_evaluator.sub_evaluators)
    else:
        result = 0
    return result


class SpecificityCalculator:
    """Computes the specificity score for a directive.

    Scoring heuristic (aligned with SPECIFICATION.md §2.8.2):
    - ``target_type != ANY``: +10 (narrows scope to a specific content kind)
    - ``domain`` present:      +5  (narrows to a regulatory domain)
    - ``jurisdiction`` present: +5 (narrows to a jurisdiction)
    - Each scope filter:        +2 (each predicate narrows applicability)
    - Each field binding in evaluator: +1 (each bound field increases specificity)
    """

    def compute(self, a_directive: Directive) -> int:
        """Return the specificity score for the directive.

        Args:
            a_directive (Directive): The directive to score.

        Returns:
            int: Non-negative specificity score; higher = more specific.
        """
        score = 0
        scope = a_directive.scope
        if scope is not None:
            if scope.target_type != TargetType.ANY:
                score += 10
            if scope.domain is not None:
                score += 5
            if scope.jurisdiction is not None:
                score += 5
            score += len(scope.filters) * 2
        score += _count_field_bindings(a_directive.evaluator_config)
        return score
