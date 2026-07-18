"""Tests for ConflictResolver domain service (SPEC §2.15)."""

from __future__ import annotations

import pytest
from tests.domain.directive_graph.conftest import make_graph

from domain.directive_graph.services.conflict_resolver import ConflictResolver


def _pair(
    *,
    a_overrides: dict | None = None,
    b_overrides: dict | None = None,
):
    """Build a two-directive graph and return (a, b, graph)."""
    a_payload = {
        "lineage_id": "RULE-001",
        "id": "RULE-001",
        "type": "obligation",
        "message": "a",
        "evaluator_type": "regex",
        "evaluator_config": {"pattern": "^test$"},
        "status": "draft",
        "created_at": "2026-01-01T00:00:00Z",
    }
    b_payload = {
        "lineage_id": "RULE-002",
        "id": "RULE-002",
        "type": "obligation",
        "message": "b",
        "evaluator_type": "regex",
        "evaluator_config": {"pattern": "^test$"},
        "status": "draft",
        "created_at": "2026-01-01T00:00:00Z",
    }
    if a_overrides:
        a_payload.update(a_overrides)
    if b_overrides:
        b_payload.update(b_overrides)
    g = make_graph(rules=[a_payload, b_payload])
    a = g.get_by_id("RULE-001")
    b = g.get_by_id("RULE-002")
    assert a is not None
    assert b is not None
    return a, b, g


@pytest.fixture
def resolver() -> ConflictResolver:
    return ConflictResolver()


@pytest.mark.unit
@pytest.mark.domain
class TestExplicitOverrides:
    def test_always_wins(self, resolver: ConflictResolver) -> None:
        a, b, g = _pair(a_overrides={"conflict_resolution": {"strategy": "always_wins"}})
        result = resolver.resolve(a, b, g)
        assert result.winner is not None
        assert result.winner.id == "RULE-001"
        assert result.method == "explicit_always_wins"

    def test_never_wins(self, resolver: ConflictResolver) -> None:
        a, b, g = _pair(a_overrides={"conflict_resolution": {"strategy": "never_wins"}})
        result = resolver.resolve(a, b, g)
        assert result.winner is not None
        assert result.winner.id == "RULE-002"
        assert result.method == "explicit_never_wins"

    def test_compatible_always_never(self, resolver: ConflictResolver) -> None:
        a, b, g = _pair(
            a_overrides={"conflict_resolution": {"strategy": "always_wins"}},
            b_overrides={"conflict_resolution": {"strategy": "never_wins"}},
        )
        result = resolver.resolve(a, b, g)
        assert result.winner is not None
        assert result.winner.id == "RULE-001"
        assert result.method == "compatible_always_never"

    def test_dual_never_wins_unresolvable(self, resolver: ConflictResolver) -> None:
        a, b, g = _pair(
            a_overrides={"conflict_resolution": {"strategy": "never_wins"}},
            b_overrides={"conflict_resolution": {"strategy": "never_wins"}},
        )
        result = resolver.resolve(a, b, g)
        assert result.method == "unresolvable"
        assert result.artifact is not None

    def test_always_wins_plus_defer_to_unresolvable(self, resolver: ConflictResolver) -> None:
        a, b, g = _pair(
            a_overrides={"conflict_resolution": {"strategy": "always_wins"}},
            b_overrides={"conflict_resolution": {"strategy": "defer_to", "defer_to": "RULE-001"}},
        )
        result = resolver.resolve(a, b, g)
        assert result.method == "unresolvable"


@pytest.mark.unit
@pytest.mark.domain
class TestPriorityResolution:
    def test_constitutional_beats_advisory(self, resolver: ConflictResolver) -> None:
        a, b, g = _pair(
            a_overrides={"priority": "constitutional"},
            b_overrides={"priority": "advisory"},
        )
        result = resolver.resolve(a, b, g)
        assert result.winner is not None
        assert result.winner.id == "RULE-001"
        assert result.method == "priority"

    def test_equal_priority_falls_through_to_next(self, resolver: ConflictResolver) -> None:
        a, b, g = _pair(
            a_overrides={"priority": "operational"},
            b_overrides={"priority": "operational"},
        )
        result = resolver.resolve(a, b, g)
        assert result.method in ("specificity", "recency", "unresolvable")


@pytest.mark.unit
@pytest.mark.domain
class TestRecencyResolution:
    def test_newer_wins(self, resolver: ConflictResolver) -> None:
        a, b, g = _pair(
            a_overrides={"created_at": "2026-12-01T00:00:00Z"},
            b_overrides={"created_at": "2026-01-01T00:00:00Z"},
        )
        result = resolver.resolve(a, b, g)
        assert result.winner is not None
        assert result.winner.id == "RULE-001"
        assert result.method == "recency"


@pytest.mark.unit
@pytest.mark.domain
class TestUnresolvable:
    def test_both_always_wins_produces_artifact(self, resolver: ConflictResolver) -> None:
        a, b, g = _pair(
            a_overrides={"conflict_resolution": {"strategy": "always_wins"}},
            b_overrides={"conflict_resolution": {"strategy": "always_wins"}},
        )
        result = resolver.resolve(a, b, g)
        assert result.method == "unresolvable"
        assert result.artifact is not None
