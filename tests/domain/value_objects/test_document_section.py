"""Unit tests for DocumentSection and DocumentStructure."""

from __future__ import annotations

from typing import Callable

import pytest
from pydantic import ValidationError

from domain import ContentType, DocumentSection, DocumentStructure


@pytest.mark.unit
@pytest.mark.domain
class TestDocumentSection:
    """Section content invariants and tree navigation."""

    def test_columns_forbidden_on_prose(self) -> None:
        with pytest.raises(ValidationError, match="columns"):
            DocumentSection(
                id="preamble",
                title="Preamble",
                content_type=ContentType.PROSE,
                columns=("A", "B"),
            )

    def test_max_depth_enforced(self) -> None:
        with pytest.raises(ValidationError, match="depth"):
            DocumentSection(
                id="a",
                title="A",
                content_type=ContentType.PROSE,
                children=(
                    DocumentSection(
                        id="b",
                        title="B",
                        content_type=ContentType.PROSE,
                        children=(
                            DocumentSection(
                                id="c",
                                title="C",
                                content_type=ContentType.PROSE,
                                children=(
                                    DocumentSection(
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

    def test_none_columns_coerced_to_empty(
        self,
        make_prose_section: Callable[..., DocumentSection],
    ) -> None:
        section = make_prose_section(
            id="preamble",
            title="Preamble",
            columns=None,
            children=None,
        )
        assert section.columns == ()
        assert section.children == ()

    def test_traverse_and_find(self) -> None:
        child = DocumentSection(
            id="specific_directives",
            title="Specific",
            content_type=ContentType.TABLE,
            columns=("Type", "Description"),
        )
        parent = DocumentSection(
            id="directives",
            title="Directives",
            content_type=ContentType.MIXED,
            children=(child,),
        )

        assert [section.id for section in parent.iter_nodes()] == [
            "directives",
            "specific_directives",
        ]
        assert list(parent.traverse()) == list(parent.iter_nodes())
        assert parent.get("specific_directives") is child
        assert parent.get("missing") is None
        assert parent.require("specific_directives") is child
        assert parent.has("specific_directives")
        assert not parent.has("missing")
        assert parent.collect_where(lambda node: node.id == "specific_directives") == [child]
        assert parent.max_depth() == 2


@pytest.mark.unit
@pytest.mark.domain
class TestDocumentStructure:
    """Structural invariants for the universal document template."""

    def test_required_sections(
        self,
        minimal_sections: tuple[DocumentSection, ...],
    ) -> None:
        incomplete = [section for section in minimal_sections if section.id != "preamble"]
        with pytest.raises(ValidationError, match="Missing required sections"):
            DocumentStructure(tuple(incomplete))

    def test_duplicate_ids(
        self,
        minimal_sections: tuple[DocumentSection, ...],
        make_prose_section: Callable[..., DocumentSection],
    ) -> None:
        sections = list(minimal_sections)
        sections.append(make_prose_section(id="preamble", title="Dup"))
        with pytest.raises(ValidationError, match="Duplicate section ID"):
            DocumentStructure(tuple(sections))

    def test_lookup(self, minimal_sections: tuple[DocumentSection, ...]) -> None:
        structure = DocumentStructure(minimal_sections)

        assert structure.get("flexible_standards") is not None
        assert structure.get("nope") is None
        assert frozenset(structure.ids) >= DocumentStructure.REQUIRED_SECTION_IDS
        assert len(structure) == len(minimal_sections)
