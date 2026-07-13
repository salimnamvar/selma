"""Tests for DirectiveLifecycleFactory."""

from __future__ import annotations

import pytest
from tests.domain.directive_graph.conftest import make_directive_payload, make_graph

from domain.directive_graph.enums import DirectiveStatus
from domain.directive_graph.events import DirectiveForked, DirectiveMerged, DirectiveRetired
from domain.directive_graph.factories.lifecycle import DirectiveLifecycleFactory, compute_merge_execution_id


@pytest.fixture
def factory() -> DirectiveLifecycleFactory:
    return DirectiveLifecycleFactory()


@pytest.mark.unit
@pytest.mark.domain
class TestActivateRetire:
    def test_activate(self, factory: DirectiveLifecycleFactory) -> None:
        g = make_graph(
            rules=[
                make_directive_payload(
                    metadata={"audit": {"authored_by": "alice"}},
                )
            ]
        )
        result = factory.activate(g, "RULE-001")
        d = result.graph.get_by_id("RULE-001")
        assert d is not None
        assert d.status == DirectiveStatus.ACTIVE
        assert len(result.events) == 1

    def test_retire(self, factory: DirectiveLifecycleFactory) -> None:
        g = make_graph(
            rules=[
                make_directive_payload(
                    status="active",
                    metadata={"audit": {"authored_by": "alice"}},
                )
            ]
        )
        result = factory.retire(g, "RULE-001")
        d = result.graph.get_by_id("RULE-001")
        assert d is not None
        assert d.status == DirectiveStatus.DEPRECATED
        assert isinstance(result.events[0], DirectiveRetired)


@pytest.mark.unit
@pytest.mark.domain
class TestFork:
    def test_fork_shares_lineage_id(self, factory: DirectiveLifecycleFactory) -> None:
        g = make_graph(
            rules=[
                make_directive_payload(
                    status="active",
                    metadata={"audit": {"authored_by": "alice"}},
                )
            ]
        )
        result = factory.fork(
            g,
            parent_execution_id="RULE-001",
            child_execution_ids=("RULE-001-A", "RULE-001-B"),
            timestamp="2026-06-01T00:00:00Z",
        )
        assert len(result.graph.directives) == 3
        parent = result.graph.get_by_id("RULE-001")
        assert parent is not None
        assert parent.status == DirectiveStatus.DEPRECATED
        children = result.graph.get_by_lineage_id("RULE-001")
        active_children = [c for c in children if c.id != "RULE-001"]
        assert len(active_children) == 2
        assert all(c.lineage_id == "RULE-001" for c in active_children)
        assert all(c.lineage is not None and c.lineage.operation == "fork" for c in active_children)
        assert isinstance(result.events[0], DirectiveForked)


@pytest.mark.unit
@pytest.mark.domain
class TestMerge:
    def test_merge_deterministic_id(self, factory: DirectiveLifecycleFactory) -> None:
        g = make_graph(
            rules=[
                make_directive_payload(
                    lineage_id="AUTH-001",
                    id="AUTH-001",
                    status="active",
                    metadata={"audit": {"authored_by": "alice"}},
                ),
                make_directive_payload(
                    lineage_id="PAY-800",
                    id="PAY-800",
                    status="active",
                    metadata={"audit": {"authored_by": "bob"}},
                ),
            ]
        )
        ts = "2026-07-01T12:00:00Z"
        expected_id = compute_merge_execution_id(
            "AUTH-001",
            ("AUTH-001", "PAY-800"),
            ("AUTH-001", "PAY-800"),
            ts,
        )
        result = factory.merge(g, "AUTH-001", "PAY-800", timestamp=ts)
        merged = result.graph.get_by_id(expected_id)
        assert merged is not None
        assert merged.lineage_id == "AUTH-001"  # lex min
        assert merged.lineage is not None
        assert merged.lineage.operation == "merge"
        a = result.graph.get_by_id("AUTH-001")
        b = result.graph.get_by_id("PAY-800")
        assert a is not None and a.status == DirectiveStatus.DEPRECATED
        assert b is not None and b.status == DirectiveStatus.DEPRECATED
        assert isinstance(result.events[0], DirectiveMerged)


@pytest.mark.unit
@pytest.mark.domain
class TestSplit:
    def test_split_three_children(self, factory: DirectiveLifecycleFactory) -> None:
        g = make_graph(
            rules=[
                make_directive_payload(
                    status="active",
                    metadata={"audit": {"authored_by": "alice"}},
                )
            ]
        )
        result = factory.split(
            g,
            parent_execution_id="RULE-001",
            child_execution_ids=("RULE-001-A", "RULE-001-B", "RULE-001-C"),
            timestamp="2026-06-01T00:00:00Z",
        )
        assert len(result.graph.directives) == 4
        assert result.graph.get_by_id("RULE-001-A") is not None
        assert result.graph.get_by_id("RULE-001-B") is not None
        assert result.graph.get_by_id("RULE-001-C") is not None
