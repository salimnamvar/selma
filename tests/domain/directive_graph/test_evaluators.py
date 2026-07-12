"""Tests for the evaluator hierarchy.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.4
"""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from domain.directive_graph.enums import (
    CompositeLogic,
    EvaluatorType,
    FieldCheckOperator,
    ThresholdOperator,
)
from domain.directive_graph.evaluators import (
    CompositeEvaluator,
    Evaluator,
    FieldCheckEvaluator,
    RegexEvaluator,
    ThresholdEvaluator,
)

_adapter = TypeAdapter(Evaluator)


@pytest.mark.unit
@pytest.mark.domain
class TestRegexEvaluator:
    def test_constructs_directly(self) -> None:
        ev = RegexEvaluator(evaluator_type=EvaluatorType.REGEX, pattern="^test$")
        assert ev.pattern == "^test$"
        assert ev.flags == ""

    def test_constructs_from_schema_format(self) -> None:
        data = {"evaluator_type": "regex", "evaluator_config": {"pattern": "^abc$", "flags": "i"}}
        ev = _adapter.validate_python(data)
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

    def test_constructs_from_schema_format(self) -> None:
        data = {
            "evaluator_type": "field_check",
            "evaluator_config": {"field": "status", "operator": "eq", "value": "active"},
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
    def test_constructs_with_finite_threshold(self) -> None:
        ev = ThresholdEvaluator(
            evaluator_type=EvaluatorType.THRESHOLD,
            field="risk_score",
            operator=ThresholdOperator.GT,
            threshold=0.7,
        )
        assert ev.threshold == 0.7

    def test_rejects_nan_threshold(self) -> None:
        import math
        with pytest.raises(ValidationError):
            ThresholdEvaluator(
                evaluator_type=EvaluatorType.THRESHOLD,
                field="score",
                operator=ThresholdOperator.GT,
                threshold=math.nan,
            )

    def test_rejects_inf_threshold(self) -> None:
        import math
        with pytest.raises(ValidationError):
            ThresholdEvaluator(
                evaluator_type=EvaluatorType.THRESHOLD,
                field="score",
                operator=ThresholdOperator.GT,
                threshold=math.inf,
            )


@pytest.mark.unit
@pytest.mark.domain
class TestCompositeEvaluator:
    def test_constructs_and_logic(self) -> None:
        ev = CompositeEvaluator(
            evaluator_type=EvaluatorType.COMPOSITE,
            logic=CompositeLogic.AND,
            sub_evaluators=[
                RegexEvaluator(evaluator_type=EvaluatorType.REGEX, pattern="^a$"),
                RegexEvaluator(evaluator_type=EvaluatorType.REGEX, pattern="^b$"),
            ],
        )
        assert ev.logic == CompositeLogic.AND
        assert len(ev.sub_evaluators) == 2

    def test_not_with_one_sub_evaluator(self) -> None:
        ev = CompositeEvaluator(
            evaluator_type=EvaluatorType.COMPOSITE,
            logic=CompositeLogic.NOT,
            sub_evaluators=[RegexEvaluator(evaluator_type=EvaluatorType.REGEX, pattern="^x$")],
        )
        assert ev.logic == CompositeLogic.NOT

    def test_not_with_two_sub_evaluators_raises(self) -> None:
        with pytest.raises(ValidationError, match="exactly 1 sub-evaluator"):
            CompositeEvaluator(
                evaluator_type=EvaluatorType.COMPOSITE,
                logic=CompositeLogic.NOT,
                sub_evaluators=[
                    RegexEvaluator(evaluator_type=EvaluatorType.REGEX, pattern="^a$"),
                    RegexEvaluator(evaluator_type=EvaluatorType.REGEX, pattern="^b$"),
                ],
            )

    def test_recursive_nesting(self) -> None:
        inner = CompositeEvaluator(
            evaluator_type=EvaluatorType.COMPOSITE,
            logic=CompositeLogic.AND,
            sub_evaluators=[
                RegexEvaluator(evaluator_type=EvaluatorType.REGEX, pattern="^x$"),
            ],
        )
        outer = CompositeEvaluator(
            evaluator_type=EvaluatorType.COMPOSITE,
            logic=CompositeLogic.OR,
            sub_evaluators=[inner],
        )
        assert isinstance(outer.sub_evaluators[0], CompositeEvaluator)

    def test_constructs_from_schema_format(self) -> None:
        data = {
            "evaluator_type": "composite",
            "evaluator_config": {
                "logic": "and",
                "sub_evaluators": [
                    {
                        "evaluator_type": "regex",
                        "evaluator_config": {"pattern": "^x$"},
                    }
                ],
            },
        }
        ev = _adapter.validate_python(data)
        assert isinstance(ev, CompositeEvaluator)
        assert isinstance(ev.sub_evaluators[0], RegexEvaluator)


@pytest.mark.unit
@pytest.mark.domain
class TestEvaluatorDiscriminatedUnion:
    def test_routes_regex(self) -> None:
        ev = _adapter.validate_python({"evaluator_type": "regex", "pattern": "^x$"})
        assert isinstance(ev, RegexEvaluator)

    def test_routes_field_check(self) -> None:
        ev = _adapter.validate_python(
            {"evaluator_type": "field_check", "field": "f", "operator": "eq", "value": 1}
        )
        assert isinstance(ev, FieldCheckEvaluator)

    def test_routes_threshold(self) -> None:
        ev = _adapter.validate_python(
            {"evaluator_type": "threshold", "field": "f", "operator": "gt", "threshold": 0.5}
        )
        assert isinstance(ev, ThresholdEvaluator)

    def test_routes_composite(self) -> None:
        ev = _adapter.validate_python(
            {
                "evaluator_type": "composite",
                "logic": "or",
                "sub_evaluators": [{"evaluator_type": "regex", "pattern": "^x$"}],
            }
        )
        assert isinstance(ev, CompositeEvaluator)

    def test_rejects_unknown_evaluator_type(self) -> None:
        with pytest.raises(ValidationError):
            _adapter.validate_python({"evaluator_type": "unknown", "field": "x"})
