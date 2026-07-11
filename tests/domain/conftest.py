"""Domain-layer fixtures and factories.

Fixtures here apply to tests under tests/domain/ only.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import pytest
import yaml

from domain import (
    ContentType,
    DocumentSection,
    PolicyDoctrine,
    PriorityCategory,
)


@pytest.fixture(scope="session")
def doctrine_document(policy_doctrine_yaml_path: Path) -> Dict[str, Any]:
    """Load the normative policy_doctrine.yaml once per session.

    Args:
        policy_doctrine_yaml_path (Path): Path to the YAML file.

    Returns:
        Dict[str, Any]: Parsed YAML document.
    """
    result: Dict[str, Any] = yaml.safe_load(policy_doctrine_yaml_path.read_text(encoding="utf-8"))
    return result


@pytest.fixture(scope="session")
def doctrine(doctrine_document: Dict[str, Any]) -> PolicyDoctrine:
    """Build PolicyDoctrine from the normative YAML once per session.

    Args:
        doctrine_document (Dict[str, Any]): Parsed YAML document.

    Returns:
        PolicyDoctrine: Validated doctrine aggregate.
    """
    result: PolicyDoctrine = PolicyDoctrine.from_document(doctrine_document)
    return result


@pytest.fixture
def doctrine_document_copy(doctrine_document: Dict[str, Any]) -> Dict[str, Any]:
    """Return a deep copy of the doctrine document for mutation tests.

    Args:
        doctrine_document (Dict[str, Any]): Session-scoped YAML mapping.

    Returns:
        Dict[str, Any]: Isolated mutable copy.
    """
    result: Dict[str, Any] = deepcopy(doctrine_document)
    return result


@pytest.fixture
def make_prose_section() -> Callable[..., DocumentSection]:
    """Factory for prose DocumentSection instances.

    Returns:
        Callable[..., DocumentSection]: Builder accepting field overrides.
    """

    def _make(
        a_id: str = "preamble",
        a_title: str = "Preamble",
        **a_overrides: Any,
    ) -> DocumentSection:
        payload: Dict[str, Any] = {
            "id": a_id,
            "title": a_title,
            "content_type": ContentType.PROSE,
            "guidance": f"Guidance for {a_title}",
        }
        payload.update(a_overrides)
        result: DocumentSection = DocumentSection.model_validate(payload)
        return result

    return _make


@pytest.fixture
def minimal_sections(
    make_prose_section: Callable[..., DocumentSection],
) -> Tuple[DocumentSection, ...]:
    """Return a complete, valid top-level section tree.

    Args:
        make_prose_section (Callable[..., DocumentSection]): Prose section factory.

    Returns:
        Tuple[DocumentSection, ...]: Required sections with directives children.
    """
    result: Tuple[DocumentSection, ...] = (
        make_prose_section(a_id="preamble", a_title="Preamble"),
        make_prose_section(a_id="governance", a_title="Governance"),
        DocumentSection(
            id="definitions",
            title="Definitions",
            content_type=ContentType.TABLE,
            columns=("Term", "Definition", "Exclusion"),
            guidance="Define terms",
        ),
        make_prose_section(a_id="principles", a_title="Principles"),
        DocumentSection(
            id="directives",
            title="Directives",
            content_type=ContentType.MIXED,
            guidance="List obligations",
            children=(
                DocumentSection(
                    id="specific_directives",
                    title="Specific Directives",
                    content_type=ContentType.TABLE,
                    columns=("Type", "Description", "Machine ID"),
                ),
                DocumentSection(
                    id="flexible_standards",
                    title="Flexible Standards",
                    content_type=ContentType.TABLE,
                    columns=("Description", "Machine ID"),
                ),
            ),
        ),
        DocumentSection(
            id="sanctions",
            title="Sanctions",
            content_type=ContentType.TABLE,
            columns=("Violation", "Action", "Remediation"),
            guidance="Consequences",
        ),
    )
    return result


@pytest.fixture
def full_priority_levels() -> List[Dict[str, Any]]:
    """Return a complete, ordered priority-level payload.

    Returns:
        List[Dict[str, Any]]: Level dicts matching PriorityCategory ranks.
    """
    titles: Dict[PriorityCategory, str] = {
        PriorityCategory.CONSTITUTIONAL: "Constitutional",
        PriorityCategory.STATUTORY: "Statutory",
        PriorityCategory.REGULATORY: "Regulatory",
        PriorityCategory.OPERATIONAL: "Operational",
        PriorityCategory.ADVISORY: "Advisory",
    }
    result: List[Dict[str, Any]] = [
        {
            "id": category.value,
            "level": category.rank,
            "title": titles[category],
            "description": f"{titles[category]} rules",
            "examples": (f"Example for {category.value}",),
        }
        for category in PriorityCategory
    ]
    return result


@pytest.fixture
def priority_hierarchy_payload(
    full_priority_levels: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Return a valid PriorityHierarchy model_validate payload.

    Args:
        full_priority_levels (List[Dict[str, Any]]): Ordered level dicts.

    Returns:
        Dict[str, Any]: Complete hierarchy mapping.
    """
    result: Dict[str, Any] = {
        "description": "Authority levels",
        "levels": full_priority_levels,
        "conflict_resolution_intent": "Higher wins",
        "cross_layer_precedence": {
            "normative_algorithm": "SPEC §2.15",
            "structural_override": "conflict_resolution field",
            "policy_role": "Declarative intent",
            "order": "override → priority → specificity → recency",
        },
    }
    return result
