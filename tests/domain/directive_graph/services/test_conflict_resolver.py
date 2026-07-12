"""Tests for ConflictResolver domain service."""

from __future__ import annotations

import pytest

from domain.directive_graph.enums import ConflictStrategy
from domain.directive_graph.enums import PriorityLevel
from domain.directive_graph.services.conflict_resolver import ConflictResolutionResult
from domain.directive_graph.services.conflict_resolver import ConflictResolver
from domain.directive_graph.value_objects.conflict_resolution import ConflictResolution
from tests.domain.directive_graph.conftest import make_directive
from tests.domain.directive_graph.conftest import make_graph


@pytest.fixture
def resolver() -> ConflictResolver:
    return ConflictResolver()


@pytest.mark.unit
@pytest.mark.domain
class TestExplicitOverrides:
    def test_always_wins(self, resolver: ConflictResolver) -> None:
        a = make_directive(
            lineage_id="RULE-001",
            id="RULE-001",
            conflict_resolution={"strategy": "always_wins"},
        )
        b = make_directive(lineage_id="RULE-002", id="RULE-002")
        g = make_graph(rules=[a.model_dump(mode="json"), b.model_dump(mode="json")])
        result = resolver.resolve(a, b, g)
        assert result.winner is not None
        assert result.winner.id == "RULE-001"
        assert result.method == "explicit_always_wins"

    def test_never_wins(self, resolver: ConflictResolver) -> None:
        a = make_directive(
            lineage_id="RULE-001",
            id="RULE-001",
            conflict_resolution={"strategy": "never_wins"},
        )
        b = make_directive(lineage_id="RULE-002", id="RULE-002")
        g = make_graph(rules=[a.model_dump(mode="json"), b.model_dump(mode="json")])
        result = resolver.resolve(a, b, g)
        assert result.winner is not None
        assert result.winner.id == "RULE-002"
        assert result.method == "explicit_never_wins"


@pytest.mark.unit
@pytest.mark.domain
class TestPriorityResolution:
    def test_constitutional_beats_advisory(self, resolver: ConflictResolver) -> None:
        a = make_directive(lineage_id="RULE-001", id="RULE-001", priority="constitutional")
        b = make_directive(lineage_id="RULE-002", id="RULE-002", priority="advisory")
        g = make_graph(rules=[a.model_dump(mode="json"), b.model_dump(mode="json")])
        result = resolver.resolve(a, b, g)
        assert result.winner is not None
        assert result.winner.id == "RULE-001"
        assert result.method == "priority"

    def test_equal_priority_falls_through_to_next(self, resolver: ConflictResolver) -> None:
        a = make_directive(lineage_id="RULE-001", id="RULE-001", priority="operational")
        b = make_directive(lineage_id="RULE-002", id="RULE-002", priority="operational")
        g = make_graph(rules=[a.model_dump(mode="json"), b.model_dump(mode="json")])
        result = resolver.resolve(a, b, g)
        # Falls through to specificity then recency
        assert result.method in ("specificity", "recency", "unresolvable")


@pytest.mark.unit
@pytest.mark.domain
class TestRecencyResolution:
    def test_newer_wins(self, resolver: ConflictResolver) -> None:
        a = make_directive(
            lineage_id="RULE-001",
            id="RULE-001",
            created_at="2026-12-01T00:00:00Z",
        )
        b = make_directive(
            lineage_id="RULE-002",
            id="RULE-002",
            created_at="2026-01-01T00:00:00Z",
        )
        g = make_graph(rules=[a.model_dump(mode="json"), b.model_dump(mode="json")])
        result = resolver.resolve(a, b, g)
        assert result.winner is not None
        assert result.winner.id == "RULE-001"
        assert result.method == "recency"


@pytest.mark.unit
@pytest.mark.domain
class TestUnresolvable:
    def test_both_always_wins_produces_artifact(self, resolver: ConflictResolver) -> None:
        a = make_directive(
            lineage_id="RULE-001",
            id="RULE-001",
            conflict_resolution={"strategy": "always_wins"},
        )
        b = make_directive(
            lineage_id="RULE-002",
            id="RULE-002",
            conflict_resolution={"strategy": "always_wins"},
        )
        g = make_graph(rules=[a.model_dump(mode="json"), b.model_dump(mode="json")])
        result = resolver.resolve(a, b, g)
        assert result.method == "unresolvable"
        assert result.artifact is not None
