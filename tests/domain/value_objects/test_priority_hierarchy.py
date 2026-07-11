"""Unit tests for AuthorityHierarchy value objects."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from pydantic import ValidationError

from domain import AuthorityHierarchy, PriorityCategory


@pytest.mark.unit
@pytest.mark.domain
class TestAuthorityHierarchy:
    """Ordering, completeness, and authority comparison."""

    def test_complete_hierarchy(self, priority_hierarchy_payload: dict[str, Any]) -> None:
        hierarchy = AuthorityHierarchy.model_validate(priority_hierarchy_payload)

        assert hierarchy.get(PriorityCategory.CONSTITUTIONAL) is not None
        assert hierarchy.outranks(
            PriorityCategory.CONSTITUTIONAL,
            PriorityCategory.ADVISORY,
        )

    def test_missing_category_rejected(
        self,
        priority_hierarchy_payload: dict[str, Any],
        full_priority_levels: list[dict[str, Any]],
    ) -> None:
        payload = deepcopy(priority_hierarchy_payload)
        payload["levels"] = full_priority_levels[:-1]

        with pytest.raises(ValidationError, match="missing categories"):
            AuthorityHierarchy.model_validate(payload)

    def test_out_of_order_rejected(
        self,
        priority_hierarchy_payload: dict[str, Any],
        full_priority_levels: list[dict[str, Any]],
    ) -> None:
        levels = list(full_priority_levels)
        levels[0], levels[1] = levels[1], levels[0]
        payload = deepcopy(priority_hierarchy_payload)
        payload["levels"] = levels

        with pytest.raises(ValidationError, match="expected"):
            AuthorityHierarchy.model_validate(payload)
