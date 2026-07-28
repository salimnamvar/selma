"""Rule evaluator port — evaluate executable rules against ASTs."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
import ast

from selma.domain.entities.finding import Finding
from selma.domain.entities.rule import Rule
from selma.domain.value_objects.result import Result


class RuleEvaluator(ABC):
    """Port for evaluating rules against source code ASTs."""

    @abstractmethod
    async def evaluate(
        self,
        a_tree: ast.AST,
        a_rule: Rule,
        a_file_path: str = "",
    ) -> Result[list[Finding]]:
        """Evaluate a single rule against an AST.

        Args:
            a_tree: Parsed AST from the parser port.
            a_rule: Domain executable rule.
            a_file_path: Path to the source file.

        Returns:
            Result containing findings, or a failure.
        """
        ...
