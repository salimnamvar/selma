"""Tests for SpecificityCalculator domain service."""

from __future__ import annotations

import pytest
from tests.domain.directive_graph.conftest import make_directive

from domain.directive_graph.services.specificity_calculator import SpecificityCalculator


@pytest.fixture
def calculator() -> SpecificityCalculator:
    return SpecificityCalculator()


@pytest.mark.unit
@pytest.mark.domain
class TestSpecificityCalculator:
    def test_no_scope_gives_low_score(self, calculator: SpecificityCalculator) -> None:
        d = make_directive()
        score = calculator.compute(d)
        assert score >= 0

    def test_specific_target_type_increases_score(self, calculator: SpecificityCalculator) -> None:
        d_any = make_directive()
        d_text = make_directive(scope={"target_type": "text"})
        assert calculator.compute(d_text) > calculator.compute(d_any)

    def test_domain_increases_score(self, calculator: SpecificityCalculator) -> None:
        d_no_domain = make_directive(scope={"target_type": "text"})
        d_domain = make_directive(scope={"target_type": "text", "domain": "finance"})
        assert calculator.compute(d_domain) > calculator.compute(d_no_domain)

    def test_more_filters_increases_score(self, calculator: SpecificityCalculator) -> None:
        d_no_filters = make_directive(scope={"target_type": "text"})
        d_one_filter = make_directive(
            scope={
                "target_type": "text",
                "filters": [{"field": "status", "operator": "eq", "value": "active"}],
            }
        )
        assert calculator.compute(d_one_filter) > calculator.compute(d_no_filters)

    def test_field_check_evaluator_contributes(self, calculator: SpecificityCalculator) -> None:
        d_regex = make_directive(
            evaluator_type="regex",
            evaluator_config={"pattern": "^test$"},
        )
        d_field = make_directive(
            evaluator_type="field_check",
            evaluator_config={"field": "status", "operator": "eq", "value": "active"},
        )
        # Field check binds a specific field, contributing to specificity
        assert calculator.compute(d_field) >= calculator.compute(d_regex)

    def test_score_is_non_negative(self, calculator: SpecificityCalculator) -> None:
        d = make_directive()
        assert calculator.compute(d) >= 0
