"""Tests for domain enumerations.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.6
"""

from __future__ import annotations

import pytest

from domain.directive_graph.enums import (
    CompositeLogic,
    ConflictStrategy,
    DeonticType,
    DirectiveStatus,
    EvaluatorType,
    FieldCheckOperator,
    FilterOperator,
    LineageOperation,
    LineagePreservation,
    PriorityLevel,
    PRIORITY_RANK,
    SemanticWeightType,
    SeverityWeight,
    TargetType,
    ThresholdOperator,
)


@pytest.mark.unit
@pytest.mark.domain
class TestDeonticType:
    def test_values_match_schema_strings(self) -> None:
        assert DeonticType.OBLIGATION == "obligation"
        assert DeonticType.PROHIBITION == "prohibition"
        assert DeonticType.PERMISSION == "permission"

    def test_all_three_values_exist(self) -> None:
        assert len(DeonticType) == 3

    def test_membership_by_string(self) -> None:
        assert DeonticType("obligation") is DeonticType.OBLIGATION


@pytest.mark.unit
@pytest.mark.domain
class TestDirectiveStatus:
    def test_values_match_schema_strings(self) -> None:
        assert DirectiveStatus.DRAFT == "draft"
        assert DirectiveStatus.ACTIVE == "active"
        assert DirectiveStatus.DEPRECATED == "deprecated"
        assert DirectiveStatus.SUPERSEDED == "superseded"


@pytest.mark.unit
@pytest.mark.domain
class TestPriorityLevel:
    def test_rank_mapping_is_complete(self) -> None:
        for level in PriorityLevel:
            assert level in PRIORITY_RANK

    def test_constitutional_is_highest_authority(self) -> None:
        assert PRIORITY_RANK[PriorityLevel.CONSTITUTIONAL] == 1

    def test_advisory_is_lowest_authority(self) -> None:
        assert PRIORITY_RANK[PriorityLevel.ADVISORY] == 5

    def test_ranks_are_strictly_increasing(self) -> None:
        levels = [
            PriorityLevel.CONSTITUTIONAL,
            PriorityLevel.STATUTORY,
            PriorityLevel.REGULATORY,
            PriorityLevel.OPERATIONAL,
            PriorityLevel.ADVISORY,
        ]
        ranks = [PRIORITY_RANK[lvl] for lvl in levels]
        assert ranks == sorted(ranks)


@pytest.mark.unit
@pytest.mark.domain
class TestEvaluatorType:
    def test_four_types_match_schema(self) -> None:
        assert EvaluatorType.REGEX == "regex"
        assert EvaluatorType.FIELD_CHECK == "field_check"
        assert EvaluatorType.THRESHOLD == "threshold"
        assert EvaluatorType.COMPOSITE == "composite"
        assert len(EvaluatorType) == 4


@pytest.mark.unit
@pytest.mark.domain
class TestCompositeLogic:
    def test_three_operators(self) -> None:
        assert CompositeLogic.AND == "and"
        assert CompositeLogic.OR == "or"
        assert CompositeLogic.NOT == "not"


@pytest.mark.unit
@pytest.mark.domain
class TestLineageOperation:
    def test_three_operations(self) -> None:
        assert LineageOperation.FORK == "fork"
        assert LineageOperation.MERGE == "merge"
        assert LineageOperation.SPLIT == "split"
