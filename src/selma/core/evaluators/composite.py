"""Composite evaluator for Selma."""

from selma.core.evaluators.base import EvaluatorBase


class CompositeEvaluator(EvaluatorBase):
    """Evaluates multiple sub-evaluators with logic operators."""

    def __init__(self, evaluator_registry: dict[str, EvaluatorBase] | None = None) -> None:
        """Initialize composite evaluator.

        Args:
            evaluator_registry: Map of evaluator_type to evaluator instance.
        """
        self.evaluator_registry = evaluator_registry or {}

    def evaluate(self, config: dict, data: dict | list) -> bool:
        """Evaluate composite condition.

        Args:
            config: Must contain 'logic' and 'sub_evaluators'.
            data: Data to evaluate.

        Returns:
            True if composite condition is met.
        """
        logic = config.get("logic", "and")
        sub_evaluators = config.get("sub_evaluators", [])

        results = []
        for sub_config in sub_evaluators:
            evaluator_type = sub_config.get("evaluator_type", "")
            evaluator_config = sub_config.get("evaluator_config", {})

            evaluator = self.evaluator_registry.get(evaluator_type)
            if evaluator:
                results.append(evaluator.evaluate(evaluator_config, data))

        if not results:
            return False

        match logic:
            case "and":
                return all(results)
            case "or":
                return any(results)
            case "not":
                return not results[0] if results else False
            case _:
                return False
