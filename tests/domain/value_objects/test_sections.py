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

    def test_columns_forbidden_on_prose(self) -> None:
        with pytest.raises(ValidationError, match="columns"):
            Section(
                id="preamble",
                title="Preamble",
                content_type=ContentType.PROSE,
                columns=("A", "B"),
            )

    def test_max_depth_enforced(self) -> None:
        with pytest.raises(ValidationError, match="depth"):
            Section(
                id="a",
                title="A",
                content_type=ContentType.PROSE,
                children=(
                    Section(
                        id="b",
                        title="B",
                        content_type=ContentType.PROSE,
                        children=(
                            Section(
                                id="c",
                                title="C",
                                content_type=ContentType.PROSE,
                                children=(
                                    Section(
                                        id="d",
                                        title="D",
                                        content_type=ContentType.PROSE,
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            )

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

    def test_traverse(self) -> None:
        child = Section(
            id="specific_directives",
            title="Specific",
            content_type=ContentType.TABLE,
            columns=("Type", "Description"),
        )
        parent = Section(
            id="directives",
            title="Directives",
            content_type=ContentType.MIXED,
            children=(child,),
        )

        assert [section.id for section in parent.traverse()] == [
            "directives",
            "specific_directives",
        ]
        assert parent.max_depth() == 2