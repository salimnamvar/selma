"""Unit tests for Section (policy_doctrine.yaml: sections)."""

from __future__ import annotations

from typing import Callable

import pytest
from pydantic import ValidationError

from domain import ContentType, Section


@pytest.mark.unit
@pytest.mark.domain
class TestSection:
    """Section content invariants and tree navigation."""

    def test_omitted_columns_and_children_default_to_empty(
        self,
        make_prose_section: Callable[..., Section],
    ) -> None:
        section = make_prose_section(id="preamble", title="Preamble")
        assert section.columns == ()
        assert section.children == ()

    def test_null_columns_coerced_to_empty(
        self,
        make_prose_section: Callable[..., Section],
    ) -> None:
        section = make_prose_section(
            id="preamble",
            title="Preamble",
            columns=None,
            children=None,
        )
        assert section.columns == ()
        assert section.children == ()
