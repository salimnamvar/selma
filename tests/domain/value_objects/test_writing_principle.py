"""Unit tests for WritingPrinciple and WritingPrinciples."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from domain import WritingPrinciple, WritingPrinciples


@pytest.mark.unit
@pytest.mark.domain
class TestWritingPrinciples:
    """Collection uniqueness and lookup behavior."""

    def test_unique_ids_required(self) -> None:
        principle = WritingPrinciple(
            id="WP-001",
            title="Precision",
            description="Use exact language",
        )
        with pytest.raises(ValidationError, match="Duplicate"):
            WritingPrinciples((principle, principle))

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValidationError, match="must not be empty"):
            WritingPrinciples(())

    def test_get_and_membership(self) -> None:
        collection = WritingPrinciples(
            (
                WritingPrinciple(id="WP-001", title="A", description="Alpha"),
                WritingPrinciple(id="WP-002", title="B", description="Beta"),
            )
        )

        assert collection.get("WP-001") is not None
        assert collection.get("WP-099") is None
        assert "WP-002" in collection
        assert "WP-099" not in collection
        assert len(collection) == 2