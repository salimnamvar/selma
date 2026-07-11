"""Unit tests for PriorityHierarchy value objects."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

import pytest
from pydantic import ValidationError

from domain import PriorityCategory, PriorityHierarchy


@pytest.mark.unit
@pytest.mark.domain
class TestPriorityHierarchy:
    """Ordering, completeness, and authority comparison."""

    def test_complete_hierarchy(self, priority_hierarchy_payload: Dict[str, Any]) -> None:
        hierarchy: PriorityHierarchy = PriorityHierarchy.model_validate(priority_hierarchy_payload)

        assert hierarchy.get(PriorityCategory.CONSTITUTIONAL) is not None
        assert hierarchy.outranks(
            PriorityCategory.CONSTITUTIONAL,
            PriorityCategory.ADVISORY,
        )

    def test_missing_category_rejected(
        self,
        priority_hierarchy_payload: Dict[str, Any],
        full_priority_levels: List[Dict[str, Any]],
    ) -> None:
        payload: Dict[str, Any] = deepcopy(priority_hierarchy_payload)
        payload["levels"] = full_priority_levels[:-1]

        with pytest.raises(ValidationError, match="missing categories"):
            PriorityHierarchy.model_validate(payload)

    def test_out_of_order_rejected(
        self,
        priority_hierarchy_payload: Dict[str, Any],
        full_priority_levels: List[Dict[str, Any]],
    ) -> None:
        levels: List[Dict[str, Any]] = list(full_priority_levels)
        levels[0], levels[1] = levels[1], levels[0]
        payload: Dict[str, Any] = deepcopy(priority_hierarchy_payload)
        payload["levels"] = levels

        with pytest.raises(ValidationError, match="expected"):
            PriorityHierarchy.model_validate(payload)
