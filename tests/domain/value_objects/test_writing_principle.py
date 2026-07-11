"""Unit tests for WritingPrinciple and WritingPrinciples."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from domain import WritingPrinciple, WritingPrinciples, find_principle


@pytest.mark.unit
@pytest.mark.domain
class TestWritingPrinciples:
    """Collection uniqueness and lookup behavior."""

    _adapter: TypeAdapter[WritingPrinciples] = TypeAdapter(WritingPrinciples)

    def test_unique_ids_required(self) -> None:
        principle = WritingPrinciple(
            id="WP-001",
            title="Precision",
            description="Use exact language",
        )
        with pytest.raises(ValidationError, match="Duplicate"):
            self._adapter.validate_python((principle, principle))

    def test_empty_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._adapter.validate_python(())

    def test_get_and_membership(self) -> None:
        collection = self._adapter.validate_python(
            (
                WritingPrinciple(id="WP-001", title="A", description="Alpha"),
                WritingPrinciple(id="WP-002", title="B", description="Beta"),
            )
        )

        assert find_principle(collection, "WP-001") is not None
        assert find_principle(collection, "WP-099") is None
        assert len(collection) == 2