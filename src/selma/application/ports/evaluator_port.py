"""RuleEvaluator port — abstract interface for rule evaluation."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
import ast

from selma.domain.entities.finding import Finding
from selma.domain.entities.rule import RuleDefinition
from selma.domain.value_objects.result import Result


class RuleEvaluator(ABC):
    """Port for evaluating rules against source code ASTs.

    Implementations live in the infrastructure layer.
    The application layer depends only on this abstraction.
    """

    @abstractmethod
    def evaluate(
        self,
        a_tree: ast.AST,
        a_rule: RuleDefinition,
        a_file_path: str = "",
    ) -> Result[list[Finding]]:
        """Evaluate a single rule against an AST.

        Args:
            a_tree: Parsed AST from the parser port (stdlib ast.AST).
            a_rule: Domain rule definition.
            a_file_path: Path to the source file.

        Returns:
            Result containing a list of findings, or a failure.
        """
