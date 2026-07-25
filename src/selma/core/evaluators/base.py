"""Base evaluator for Selma."""

from abc import ABC
from abc import abstractmethod

class EvaluatorBase(ABC):
    """Abstract base class for all evaluators."""

    @abstractmethod
    def evaluate(self, config: dict, data: dict | list) -> bool:
        """Evaluate a rule against data.

        Args:
            config: Evaluator configuration from the rule.
            data: The data to evaluate against.

        Returns:
            True if the rule matches (violation found), False otherwise.
        """
        ...
