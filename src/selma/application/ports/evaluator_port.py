"""RuleEvaluator port -- abstract interface for rule evaluation."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from selma.domain.entities.finding import Finding
from selma.domain.value_objects.result import Result


class RuleEvaluator(ABC):
    """Port for evaluating rules against source code ASTs.

    Implementations live in the infrastructure layer.
    The application layer depends only on this abstraction.
    """

    @abstractmethod
    def evaluate(
        self,
        a_tree: Any,
        a_rule: dict[str, Any],
        a_file_path: str = "",
    ) -> Result[list[Finding]]:
        """Evaluate a single rule against an AST.

        Args:
            a_tree: Parsed AST from the parser port.
            a_rule: Rule definition as a dict.
            a_file_path: Path to the source file.

        Returns:
            Result containing a list of findings, or a failure.
        """
