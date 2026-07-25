"""Threshold evaluator for Selma."""

from selma.core.evaluators.base import EvaluatorBase


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
        operator = config.get("operator", "")
        threshold = config.get("threshold", 0)

        field_value = data.get(field)

        if field_value is None:
            return False

        try:
            numeric_value = float(field_value)
        except (TypeError, ValueError):
            return False

        match operator:
            case "gt":
                return numeric_value > threshold
            case "gte":
                return numeric_value >= threshold
            case "lt":
                return numeric_value < threshold
            case "lte":
                return numeric_value <= threshold
            case _:
                return False
