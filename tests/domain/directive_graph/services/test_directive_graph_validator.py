"""Tests for the DirectiveGraphValidator — cross-directive invariants.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.7
"""

from __future__ import annotations

import pytest

from domain.directive_graph.directive_graph import DirectiveGraph
from domain.directive_graph.services.directive_graph_validator import (
    DirectiveGraphValidator,
    ValidationResult,
)
from tests.domain.directive_graph.conftest import make_directive_payload, make_graph_payload


@pytest.fixture
def validator() -> DirectiveGraphValidator:
    return DirectiveGraphValidator()


@pytest.mark.unit
@pytest.mark.domain
class TestValidationOfValidGraph:
    def test_minimal_graph_is_valid(self, validator: DirectiveGraphValidator) -> None:
        g = DirectiveGraph.model_validate(make_graph_payload())
        result = validator.validate(g)
        assert result.is_valid is True
        assert result.errors == ()


@pytest.mark.unit
@pytest.mark.domain
class TestUniqueIdViolations:
    def test_duplicate_lineage_id_produces_error(self, validator: DirectiveGraphValidator) -> None:
        g = DirectiveGraph.model_validate(
            make_graph_payload(
                rules=[
                    make_directive_payload(lineage_id="RULE-001", id="RULE-001"),
                    make_directive_payload(lineage_id="RULE-001", id="RULE-001-A"),
                ]
            )
        )
        result = validator.validate(g)
        assert result.is_valid is False
        assert any("RULE-001" in e for e in result.errors)

    def test_duplicate_execution_id_produces_error(self, validator: DirectiveGraphValidator) -> None:
        g = DirectiveGraph.model_validate(
            make_graph_payload(
                rules=[
                    make_directive_payload(lineage_id="RULE-001", id="RULE-001"),
                    make_directive_payload(lineage_id="RULE-002", id="RULE-001"),
                ]
            )
        )
        result = validator.validate(g)
        assert result.is_valid is False
        assert any("execution id" in e.lower() for e in result.errors)


@pytest.mark.unit
@pytest.mark.domain
class TestCrossReferenceViolations:
    def test_dangling_depends_on_produces_error(self, validator: DirectiveGraphValidator) -> None:
        g = DirectiveGraph.model_validate(
            make_graph_payload(
                rules=[make_directive_payload(depends_on=["UNKNOWN-999"])]
            )
        )
        result = validator.validate(g)
        assert result.is_valid is False
        assert any("UNKNOWN-999" in e for e in result.errors)

    def test_dangling_conflicts_with_produces_error(self, validator: DirectiveGraphValidator) -> None:
        g = DirectiveGraph.model_validate(
            make_graph_payload(
                rules=[make_directive_payload(conflicts_with=["GHOST-001"])]
            )
        )
        result = validator.validate(g)
        assert result.is_valid is False

    def test_valid_cross_references_are_accepted(self, validator: DirectiveGraphValidator) -> None:
        g = DirectiveGraph.model_validate(
            make_graph_payload(
                rules=[
                    make_directive_payload(lineage_id="RULE-001", id="RULE-001", depends_on=["RULE-002"]),
                    make_directive_payload(lineage_id="RULE-002", id="RULE-002"),
                ]
            )
        )
        result = validator.validate(g)
        # Should be valid (no cross-reference violations)
        cross_ref_errors = [e for e in result.errors if "references unknown" in e]
        assert cross_ref_errors == []


@pytest.mark.unit
@pytest.mark.domain
class TestCycleViolations:
    def test_dependency_cycle_produces_error(self, validator: DirectiveGraphValidator) -> None:
        g = DirectiveGraph.model_validate(
            make_graph_payload(
                rules=[
                    make_directive_payload(lineage_id="RULE-001", id="RULE-001", depends_on=["RULE-002"]),
                    make_directive_payload(lineage_id="RULE-002", id="RULE-002", depends_on=["RULE-001"]),
                ]
            )
        )
        result = validator.validate(g)
        assert result.is_valid is False
        assert any("cycle" in e.lower() for e in result.errors)


@pytest.mark.unit
@pytest.mark.domain
class TestEvaluatorComplexityViolations:
    def _make_deep_composite(self, depth: int) -> dict:
        """Build a composite evaluator nested ``depth`` levels deep."""
        from domain.directive_graph.enums import EvaluatorType
        inner: dict = {"evaluator_type": "regex", "pattern": "^x$"}
        for _ in range(depth):
            inner = {"evaluator_type": "composite", "logic": "and", "sub_evaluators": [inner]}
        return inner

    def test_depth_within_limit_is_valid(self, validator: DirectiveGraphValidator) -> None:
        composite = self._make_deep_composite(depth=5)
        payload = make_directive_payload(
            evaluator_type="composite",
            evaluator_config=composite.get("sub_evaluators", [composite])[0]
            if "sub_evaluators" in composite else composite,
        )
        # Build using full composite at top level
        payload["evaluator_type"] = composite["evaluator_type"]
        payload["evaluator_config"] = {
            k: v for k, v in composite.items() if k != "evaluator_type"
        }
        g = DirectiveGraph.model_validate(make_graph_payload(rules=[payload]))
        result = validator.validate(g)
        depth_errors = [e for e in result.errors if "depth" in e.lower()]
        assert depth_errors == []


@pytest.mark.unit
@pytest.mark.domain
class TestValidationResultStructure:
    def test_valid_result_has_empty_errors(self, validator: DirectiveGraphValidator) -> None:
        g = DirectiveGraph.model_validate(make_graph_payload())
        result = validator.validate(g)
        assert isinstance(result, ValidationResult)
        assert isinstance(result.errors, tuple)
        assert isinstance(result.is_valid, bool)
