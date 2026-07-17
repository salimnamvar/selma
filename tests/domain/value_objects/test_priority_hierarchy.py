"""Unit tests for PriorityHierarchy value objects."""

from __future__ import annotations

from typing import Any

import pytest

from domain.policy_doctrine import PriorityHierarchy


@pytest.mark.unit
@pytest.mark.domain
class TestPriorityHierarchy:
    """Declarative authority-level hierarchy."""

    def test_complete_hierarchy(self, priority_hierarchy_payload: dict[str, Any]) -> None:
        hierarchy = PriorityHierarchy.model_validate(priority_hierarchy_payload)

        assert len(hierarchy.levels) > 0
