"""Tests for the evaluator hierarchy."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from domain.directive_graph.enums import CompositeLogic, EvaluatorType, FieldCheckOperator, ThresholdOperator
from domain.directive_graph.evaluators import (
    CompositeEvaluator,
    Evaluator,
    FieldCheckEvaluator,
    RegexEvaluator,
    ThresholdEvaluator,
)
from infrastructure.mappers.directive_graph_mapper import DirectiveGraphMapper

_adapter = TypeAdapter(Evaluator)
_mapper = DirectiveGraphMapper()


@pytest.mark.unit
@pytest.mark.domain
class TestRegexEvaluator:
    def test_constructs_directly(self) -> None:
        ev = RegexEvaluator(evaluator_type=EvaluatorType.REGEX, pattern="^test$")
        assert ev.pattern == "^test$"
        assert ev.flags == ""

    def test_constructs_from_domain_shape(self) -> None:
        data = {"evaluator_type": "regex", "pattern": "^abc$", "flags": "i"}
        ev = _adapter.validate_python(data)
        assert isinstance(ev, RegexEvaluator)
        assert ev.pattern == "^abc$"
        assert ev.flags == "i"

    def test_constructs_from_schema_format_via_acl(self) -> None:
        data = {"evaluator_type": "regex", "evaluator_config": {"pattern": "^abc$", "flags": "i"}}
        flat = _mapper._flatten_evaluator(data)
        ev = _adapter.validate_python(flat)
        assert isinstance(ev, RegexEvaluator)
        assert ev.pattern == "^abc$"
        assert ev.flags == "i"

    def test_frozen(self) -> None:
        ev = RegexEvaluator(evaluator_type=EvaluatorType.REGEX, pattern="^x$")
        with pytest.raises(Exception):
            ev.pattern = "^y$"  # type: ignore[misc]

    def test_rejects_invalid_flags(self) -> None:
        with pytest.raises(ValidationError):
            RegexEvaluator(evaluator_type=EvaluatorType.REGEX, pattern="^x$", flags="g")

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            RegexEvaluator(evaluator_type=EvaluatorType.REGEX, pattern="^x$", unknown=True)  # type: ignore[call-arg]


@pytest.mark.unit
@pytest.mark.domain
class TestFieldCheckEvaluator:
    def test_constructs_directly(self) -> None:
        ev = FieldCheckEvaluator(
            evaluator_type=EvaluatorType.FIELD_CHECK,
            field="content.type",
            operator=FieldCheckOperator.EQ,
            value="invoice",
        )
        assert ev.field == "content.type"

    def test_constructs_from_domain_shape(self) -> None:
        data = {
            "evaluator_type": "field_check",
            "field": "status",
            "operator": "eq",
            "value": "active",
        }
        ev = _adapter.validate_python(data)
        assert isinstance(ev, FieldCheckEvaluator)

    def test_rejects_empty_field(self) -> None:
        with pytest.raises(ValidationError):
            FieldCheckEvaluator(
                evaluator_type=EvaluatorType.FIELD_CHECK,
                field="",
                operator=FieldCheckOperator.EQ,
                value=1,
            )


@pytest.mark.unit
@pytest.mark.domain
class TestThresholdEvaluator:
    def test_constructs_directly(self) -> None:
        ev = ThresholdEvaluator(
            evaluator_type=EvaluatorType.THRESHOLD,
            field="amount",
            operator=ThresholdOperator.GT,
            threshold=100.0,
        )
        assert ev.threshold == 100.0

    def test_rejects_nan(self) -> None:
        with pytest.raises(ValidationError):
            ThresholdEvaluator(
                evaluator_type=EvaluatorType.THRESHOLD,
                field="amount",
                operator=ThresholdOperator.GT,
                threshold=float("nan"),
            )


@pytest.mark.unit
@pytest.mark.domain
class TestCompositeEvaluator:
    def test_and_with_two_children(self) -> None:
        child = RegexEvaluator(evaluator_type=EvaluatorType.REGEX, pattern="^a$")
        ev = CompositeEvaluator(
            evaluator_type=EvaluatorType.COMPOSITE,
            logic=CompositeLogic.AND,
            sub_evaluators=[child, child],
        )
        assert len(ev.sub_evaluators) == 2

    def test_not_requires_exactly_one(self) -> None:
        child = RegexEvaluator(evaluator_type=EvaluatorType.REGEX, pattern="^a$")
        with pytest.raises(ValidationError, match="exactly 1"):
            CompositeEvaluator(
                evaluator_type=EvaluatorType.COMPOSITE,
                logic=CompositeLogic.NOT,
                sub_evaluators=[child, child],
            )

    def test_not_with_one_child(self) -> None:
        child = RegexEvaluator(evaluator_type=EvaluatorType.REGEX, pattern="^a$")
        ev = CompositeEvaluator(
            evaluator_type=EvaluatorType.COMPOSITE,
            logic=CompositeLogic.NOT,
            sub_evaluators=[child],
        )
        assert len(ev.sub_evaluators) == 1

    def test_nested_via_acl_flatten(self) -> None:
        wire = {
            "evaluator_type": "composite",
            "evaluator_config": {
                "logic": "and",
                "sub_evaluators": [
                    {"evaluator_type": "regex", "evaluator_config": {"pattern": "^x$"}},
                    {"evaluator_type": "regex", "evaluator_config": {"pattern": "^y$"}},
                ],
            },
        }
        flat = _mapper._flatten_evaluator(wire)
        ev = _adapter.validate_python(flat)
        assert isinstance(ev, CompositeEvaluator)
        assert len(ev.sub_evaluators) == 2
