"""Tests for RuleEvaluator port contract."""

from __future__ import annotations

import ast

import pytest

from selma.application.ports.evaluator_port import RuleEvaluator
from selma.domain.entities.finding import Finding
from selma.domain.entities.rule import EvaluatorConfig
from selma.domain.entities.rule import Rule
from selma.domain.value_objects.enums import DeonticType
from selma.domain.value_objects.enums import Severity
from selma.domain.value_objects.result import Result


class _StubEvaluator(RuleEvaluator):
    async def evaluate(
        self,
        a_tree: ast.AST,
        a_rule: Rule,
        a_file_path: str = "",
    ) -> Result[list[Finding]]:
        return Result.success([])


@pytest.mark.asyncio
async def test_stub_evaluator() -> None:
    """Test stub evaluator."""
    rule = Rule(
        lineage_id="SC-001",
        id="SC-001",
        type=DeonticType.OBLIGATION,
        message="x",
        evaluator_type="ast_walk",
        evaluator_config=EvaluatorConfig(),
        weight=Severity.LOW,
    )
    result = await _StubEvaluator().evaluate(ast.parse("pass"), rule)
    assert result.is_success()
    assert result.unwrap() == []
