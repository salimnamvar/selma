"""Tests for the Lineage value object."""

from __future__ import annotations

from pydantic import ValidationError
import pytest

from domain.directive_graph.enums import LineageOperation
from domain.directive_graph.value_objects.lineage import Lineage


@pytest.mark.unit
@pytest.mark.domain
class TestLineageParentCardinality:
    def test_fork_with_one_parent(self) -> None:
        lin = Lineage(
            operation=LineageOperation.FORK,
            parent_lineage_ids=("RULE-001",),
            parent_execution_ids=("RULE-001",),
            timestamp="2026-01-01T00:00:00Z",
        )
        assert lin.operation == LineageOperation.FORK

    def test_fork_with_two_parents_raises(self) -> None:
        with pytest.raises(ValidationError, match="exactly 1 parent_lineage_id"):
            Lineage(
                operation=LineageOperation.FORK,
                parent_lineage_ids=("RULE-001", "RULE-002"),
                parent_execution_ids=("RULE-001", "RULE-002"),
                timestamp="2026-01-01T00:00:00Z",
            )

    def test_split_with_one_parent(self) -> None:
        lin = Lineage(
            operation=LineageOperation.SPLIT,
            parent_lineage_ids=("RULE-001",),
            parent_execution_ids=("RULE-001",),
            timestamp="2026-01-01T00:00:00Z",
        )
        assert lin.operation == LineageOperation.SPLIT

    def test_split_with_two_parents_raises(self) -> None:
        with pytest.raises(ValidationError, match="exactly 1 parent_lineage_id"):
            Lineage(
                operation=LineageOperation.SPLIT,
                parent_lineage_ids=("RULE-001", "RULE-002"),
                parent_execution_ids=("RULE-001", "RULE-002"),
                timestamp="2026-01-01T00:00:00Z",
            )

    def test_merge_with_two_parents(self) -> None:
        lin = Lineage(
            operation=LineageOperation.MERGE,
            parent_lineage_ids=("RULE-001", "RULE-002"),
            parent_execution_ids=("RULE-001", "RULE-002"),
            timestamp="2026-01-01T00:00:00Z",
        )
        assert lin.operation == LineageOperation.MERGE

    def test_merge_with_one_parent_raises(self) -> None:
        with pytest.raises(ValidationError, match="exactly 2 parent_lineage_ids"):
            Lineage(
                operation=LineageOperation.MERGE,
                parent_lineage_ids=("RULE-001",),
                parent_execution_ids=("RULE-001",),
                timestamp="2026-01-01T00:00:00Z",
            )

    def test_mismatched_execution_and_lineage_ids_raises(self) -> None:
        with pytest.raises(ValidationError, match="must match"):
            Lineage(
                operation=LineageOperation.FORK,
                parent_lineage_ids=("RULE-001",),
                parent_execution_ids=("RULE-001", "RULE-002"),
                timestamp="2026-01-01T00:00:00Z",
            )

    def test_frozen(self) -> None:
        lin = Lineage(
            operation=LineageOperation.FORK,
            parent_lineage_ids=("RULE-001",),
            parent_execution_ids=("RULE-001",),
            timestamp="2026-01-01T00:00:00Z",
        )
        with pytest.raises(Exception):
            lin.operation = LineageOperation.MERGE  # type: ignore[misc]
