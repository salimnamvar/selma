"""Unit tests for WritingPrinciple (policy_doctrine.yaml: writing_principles)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain.policy_doctrine import WritingPrinciple


@pytest.mark.unit
@pytest.mark.domain
class TestWritingPrinciple:
    """Writing principle field validation."""

    def test_empty_title_rejected(self) -> None:
        with pytest.raises(ValidationError):
            WritingPrinciple(id="WP-001", title="", description="Alpha")

    def test_valid_principle(self) -> None:
        principle = WritingPrinciple(id="WP-001", title="Precision", description="Use exact language")
        assert principle.id == "WP-001"
