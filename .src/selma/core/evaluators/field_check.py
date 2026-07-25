"""Field check evaluator for Selma."""

from collections.abc import Callable
import operator
import re
from typing import Any

from selma.core.evaluators.base import EvaluatorBase

OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "eq": operator.eq,
    "neq": operator.ne,
    "gt": operator.gt,
    "gte": operator.ge,
    "lt": operator.lt,
    "lte": operator.le,
}


class FieldCheckEvaluator(EvaluatorBase):
    """Evaluates field values against operators."""

    def evaluate(self, config: dict, data: dict | list) -> bool:
        """Evaluate field check against data.

        Args:
            config: Must contain 'field', 'operator', and 'value'.
            data: Dictionary to check.

        Returns:
            True if condition matches.
        """
        if not isinstance(data, dict):
            return False

        field = config.get("field", "")
        op_name = config.get("operator", "")
        value = config.get("value")

        field_value = data.get(field)
        if field_value is None:
            return False

        if op_name in OPERATORS:
            return OPERATORS[op_name](field_value, value)

        if op_name == "contains":
            return str(value) in str(field_value)

        if op_name == "matches":
            return bool(re.search(str(value), str(field_value)))

        return False
