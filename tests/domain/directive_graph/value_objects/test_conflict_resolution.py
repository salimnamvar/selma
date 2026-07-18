"""Tests for ConflictResolution value object."""

from __future__ import annotations

from pydantic import ValidationError
import pytest

from domain.directive_graph.enums import ConflictStrategy
from domain.directive_graph.value_objects.conflict_resolution import ConflictResolution


@pytest.mark.unit
@pytest.mark.domain
class TestConflictResolution:
    def test_always_wins_without_defer_to(self) -> None:
        cr = ConflictResolution(strategy=ConflictStrategy.ALWAYS_WINS)
        assert cr.strategy == ConflictStrategy.ALWAYS_WINS
        assert cr.defer_to is None

    def test_never_wins_without_defer_to(self) -> None:
        cr = ConflictResolution(strategy=ConflictStrategy.NEVER_WINS)
        assert cr.defer_to is None

    def test_defer_to_with_target(self) -> None:
        cr = ConflictResolution(strategy=ConflictStrategy.DEFER_TO, defer_to="RULE-002")
        assert cr.defer_to == "RULE-002"

    def test_defer_to_without_target_raises(self) -> None:
        with pytest.raises(ValidationError, match="defer_to is required"):
            ConflictResolution(strategy=ConflictStrategy.DEFER_TO)

    def test_always_wins_with_defer_to_raises(self) -> None:
        with pytest.raises(ValidationError, match="defer_to must be None"):
            ConflictResolution(strategy=ConflictStrategy.ALWAYS_WINS, defer_to="RULE-002")

    def test_frozen(self) -> None:
        cr = ConflictResolution(strategy=ConflictStrategy.ALWAYS_WINS)
        with pytest.raises(Exception):
            cr.strategy = ConflictStrategy.NEVER_WINS  # type: ignore[misc]
