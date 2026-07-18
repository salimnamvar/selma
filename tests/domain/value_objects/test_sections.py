"""Unit tests for Section (policy_doctrine.yaml: sections)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from domain.policy_doctrine import Section


@pytest.mark.unit
@pytest.mark.domain
class TestSection:
    """Section content invariants and tree navigation."""

    def test_omitted_columns_and_children_default_to_none(
        self,
        make_prose_section: Callable[..., Section],
    ) -> None:
        section = make_prose_section(id="preamble", title="Preamble")
        assert section.columns is None
        assert section.children is None

    def test_null_columns_and_children_are_none(
        self,
        make_prose_section: Callable[..., Section],
    ) -> None:
        section = make_prose_section(
            id="preamble",
            title="Preamble",
            columns=None,
            children=None,
        )
        assert section.columns is None
        assert section.children is None
