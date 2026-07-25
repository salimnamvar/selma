"""Tests for evaluators."""

from selma.core.evaluators.composite import CompositeEvaluator
from selma.core.evaluators.field_check import FieldCheckEvaluator
from selma.core.evaluators.regex_eval import RegexEvaluator
from selma.core.evaluators.threshold import ThresholdEvaluator


class TestFieldCheckEvaluator:
    """Tests for FieldCheckEvaluator."""

    def test_eq_operator(self):
        evaluator = FieldCheckEvaluator()
        config = {"field": "name", "operator": "eq", "value": "hello"}
        data = {"name": "hello"}
        assert evaluator.evaluate(config, data) is True

    def test_neq_operator(self):
        evaluator = FieldCheckEvaluator()
        config = {"field": "name", "operator": "neq", "value": "hello"}
        data = {"name": "world"}
        assert evaluator.evaluate(config, data) is True

    def test_gt_operator(self):
        evaluator = FieldCheckEvaluator()
        config = {"field": "count", "operator": "gt", "value": 5}
        data = {"count": 10}
        assert evaluator.evaluate(config, data) is True

    def test_contains_operator(self):
        evaluator = FieldCheckEvaluator()
        config = {"field": "name", "operator": "contains", "value": "ell"}
        data = {"name": "hello"}
        assert evaluator.evaluate(config, data) is True

    def test_missing_field(self):
        evaluator = FieldCheckEvaluator()
        config = {"field": "missing", "operator": "eq", "value": "hello"}
        data = {"name": "hello"}
        assert evaluator.evaluate(config, data) is False

    def test_non_dict_data(self):
        evaluator = FieldCheckEvaluator()
        config = {"field": "name", "operator": "eq", "value": "hello"}
        assert evaluator.evaluate(config, "not a dict") is False


class TestRegexEvaluator:
    """Tests for RegexEvaluator."""

    def test_basic_match(self):
        evaluator = RegexEvaluator()
        config = {"pattern": r"hello"}
        assert evaluator.evaluate(config, "hello world") is True

    def test_no_match(self):
        evaluator = RegexEvaluator()
        config = {"pattern": r"^hello$"}
        assert evaluator.evaluate(config, "hello world") is False

    def test_with_flags(self):
        evaluator = RegexEvaluator()
        config = {"pattern": r"hello", "flags": "i"}
        assert evaluator.evaluate(config, "HELLO") is True

    def test_list_match(self):
        evaluator = RegexEvaluator()
        config = {"pattern": r"test"}
        assert evaluator.evaluate(config, ["foo", "bar", "test"]) is True


class TestThresholdEvaluator:
    """Tests for ThresholdEvaluator."""

    def test_gt_threshold(self):
        evaluator = ThresholdEvaluator()
        config = {"field": "count", "operator": "gt", "threshold": 5}
        data = {"count": 10}
        assert evaluator.evaluate(config, data) is True

    def test_lte_threshold(self):
        evaluator = ThresholdEvaluator()
        config = {"field": "count", "operator": "lte", "threshold": 5}
        data = {"count": 5}
        assert evaluator.evaluate(config, data) is True

    def test_non_numeric_value(self):
        evaluator = ThresholdEvaluator()
        config = {"field": "name", "operator": "gt", "threshold": 5}
        data = {"name": "hello"}
        assert evaluator.evaluate(config, data) is False


class TestCompositeEvaluator:
    """Tests for CompositeEvaluator."""

    def test_and_logic(self):
        evaluator = CompositeEvaluator(
            {"field_check": FieldCheckEvaluator()}
        )
        config = {
            "logic": "and",
            "sub_evaluators": [
                {"evaluator_type": "field_check", "evaluator_config": {"field": "a", "operator": "eq", "value": 1}},
                {"evaluator_type": "field_check", "evaluator_config": {"field": "b", "operator": "eq", "value": 2}},
            ],
        }
        data = {"a": 1, "b": 2}
        assert evaluator.evaluate(config, data) is True

    def test_or_logic(self):
        evaluator = CompositeEvaluator(
            {"field_check": FieldCheckEvaluator()}
        )
        config = {
            "logic": "or",
            "sub_evaluators": [
                {"evaluator_type": "field_check", "evaluator_config": {"field": "a", "operator": "eq", "value": 1}},
                {"evaluator_type": "field_check", "evaluator_config": {"field": "b", "operator": "eq", "value": 2}},
            ],
        }
        data = {"a": 1, "b": 3}
        assert evaluator.evaluate(config, data) is True

    def test_not_logic(self):
        evaluator = CompositeEvaluator(
            {"field_check": FieldCheckEvaluator()}
        )
        config = {
            "logic": "not",
            "sub_evaluators": [
                {"evaluator_type": "field_check", "evaluator_config": {"field": "a", "operator": "eq", "value": 1}},
            ],
        }
        data = {"a": 2}
        assert evaluator.evaluate(config, data) is True
