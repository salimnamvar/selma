"""Threshold evaluator for Selma."""

from collections.abc import Callable
import operator
from typing import Any

from selma.core.evaluators.base import EvaluatorBase

OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "gt": operator.gt,
    "gte": operator.ge,
    "lt": operator.lt,
    "lte": operator.le,
}


class ThresholdEvaluator(EvaluatorBase):
    """Evaluates numeric thresholds."""

    def evaluate(self, config: dict, data: dict | list) -> bool:
        """Evaluate threshold condition against data.

        Args:
            config: Must contain 'field', 'operator', and 'threshold'.
            data: Dictionary containing the field.

        Returns:
            True if threshold condition is met.
        """
        if not isinstance(data, dict):
            return False

        field = config.get("field", "")
        op_name = config.get("operator", "")
        threshold = config.get("threshold", 0)

        field_value = data.get(field)
        if field_value is None:
            return False

        try:
            numeric_value = float(field_value)
        except (TypeError, ValueError):
            return False

        op_func = OPERATORS.get(op_name)
        return op_func(numeric_value, threshold) if op_func else False
