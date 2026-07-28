"""Tests for RuleEvaluator port — abstract interface."""

import ast

import pytest

from selma.application.ports.evaluator_port import RuleEvaluator
from selma.domain.entities.finding import Finding
from selma.domain.entities.rule import RuleDefinition
from selma.domain.value_objects.result import Result


class TestRuleEvaluatorAbstract:
    """RuleEvaluator should be abstract."""

    def test_cannot_instantiate(self) -> None:
        """RuleEvaluator cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            RuleEvaluator()  # type: ignore[abstract]

    def test_requires_evaluate_method(self) -> None:
        """Subclass must implement evaluate to be concrete."""

        class IncompleteEvaluator(RuleEvaluator):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteEvaluator()  # type: ignore[abstract]

    def test_concrete_subclass_can_instantiate(self) -> None:
        """A complete implementation can be instantiated."""

        class ConcreteEvaluator(RuleEvaluator):
            def evaluate(
                self,
                a_tree: ast.AST,
                a_rule: RuleDefinition,
                a_file_path: str = "",
            ) -> Result[list[Finding]]:
                return Result.success([])

        evaluator = ConcreteEvaluator()
        assert isinstance(evaluator, RuleEvaluator)
