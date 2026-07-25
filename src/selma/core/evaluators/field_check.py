"""Field check evaluator for Selma."""

import re

from selma.core.evaluators.base import EvaluatorBase


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
        operator = config.get("operator", "")
        value = config.get("value")

        # Simple dot-notation field access
        field_value = data.get(field)

        if field_value is None:
            return False

        match operator:
            case "eq":
                return field_value == value
            case "neq":
                return field_value != value
            case "gt":
                return field_value > value
            case "gte":
                return field_value >= value
            case "lt":
                return field_value < value
            case "lte":
                return field_value <= value
            case "contains":
                return str(value) in str(field_value)
            case "matches":
                return bool(re.search(str(value), str(field_value)))
            case _:
                return False
