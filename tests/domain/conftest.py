"""Domain-layer fixtures and factories.

Fixtures here apply to tests under tests/domain/ only.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

import pytest
import yaml

from domain import (
    ContentType,
    PolicyDoctrine,
    PriorityCategory,
    Section,
)
from infrastructure.yaml_adapter import load_doctrine


@pytest.fixture(scope="session")
def doctrine_document(policy_doctrine_yaml_path: Path) -> dict[str, Any]:
    """Load the normative policy_doctrine.yaml once per session."""
    return yaml.safe_load(policy_doctrine_yaml_path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def doctrine(doctrine_document: dict[str, Any]) -> PolicyDoctrine:
    """Build PolicyDoctrine from the normative YAML once per session."""
    return load_doctrine(doctrine_document)


@pytest.fixture
def doctrine_document_copy(doctrine_document: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy of the doctrine document for mutation tests."""
    return deepcopy(doctrine_document)


@pytest.fixture
def make_prose_section() -> Callable[..., Section]:
    """Factory for prose Section instances."""

    def _make(
        id: str = "preamble",
        title: str = "Preamble",
        **overrides: Any,
    ) -> Section:
        payload: dict[str, Any] = {
            "id": id,
            "title": title,
            "content_type": ContentType.PROSE,
            "guidance": f"Guidance for {title}",
        }
        payload.update(overrides)
        return Section.model_validate(payload)

    return _make


@pytest.fixture
def minimal_sections(
    make_prose_section: Callable[..., Section],
) -> tuple[Section, ...]:
    """Return a complete, valid top-level section tree."""
    return (
        make_prose_section(id="preamble", title="Preamble"),
        make_prose_section(id="governance", title="Governance"),
        Section(
            id="definitions",
            title="Definitions",
            content_type=ContentType.TABLE,
            columns=("Term", "Definition", "Exclusion"),
            guidance="Define terms",
        ),
        make_prose_section(id="principles", title="Principles"),
        Section(
            id="directives",
            title="Directives",
            content_type=ContentType.MIXED,
            guidance="List obligations",
            children=(
                Section(
                    id="specific_directives",
                    title="Specific Directives",
                    content_type=ContentType.TABLE,
                    columns=("Type", "Description", "Machine ID"),
                ),
                Section(
                    id="flexible_standards",
                    title="Flexible Standards",
                    content_type=ContentType.TABLE,
                    columns=("Description", "Machine ID"),
                ),
            ),
        ),
        Section(
            id="sanctions",
            title="Sanctions",
            content_type=ContentType.TABLE,
            columns=("Violation", "Action", "Remediation"),
            guidance="Consequences",
        ),
    )


@pytest.fixture
def full_priority_levels() -> list[dict[str, Any]]:
    """Return a complete, ordered priority-rank payload."""
    titles: dict[PriorityCategory, str] = {
        PriorityCategory.CONSTITUTIONAL: "Constitutional",
        PriorityCategory.STATUTORY: "Statutory",
        PriorityCategory.REGULATORY: "Regulatory",
        PriorityCategory.OPERATIONAL: "Operational",
        PriorityCategory.ADVISORY: "Advisory",
    }
    return [
        {
            "category": category.value,
            "rank": rank,
            "title": titles[category],
            "description": f"{titles[category]} rules",
            "examples": (f"Example for {category.value}",),
        }
        for rank, category in enumerate(PriorityCategory, start=1)
    ]


@pytest.fixture
def priority_hierarchy_payload(
    full_priority_levels: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return a valid PriorityHierarchy model_validate payload."""
    return {
        "description": "Authority levels",
        "levels": full_priority_levels,
        "conflict_resolution": "Higher wins",
        "cross_layer_precedence": {
            "precedence_algorithm": "SPEC §2.15",
            "structural_override": "conflict_resolution field",
            "policy_role": "Declarative intent",
            "order": "override → priority → specificity → recency",
        },
    }
