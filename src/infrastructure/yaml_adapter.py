"""YAML document loading for policy doctrine."""

from __future__ import annotations

from typing import Any

from domain.policy_doctrine import PolicyDoctrine

_SECTION_KEYS: tuple[str, ...] = (
    "cross_layer_binding",
    "identity_resolution",
    "lifecycle_definition",
    "contamination_guard",
    "writing_principles",
    "priority_hierarchy",
    "version_strategy",
    "sections",
)


def flatten_doctrine_document(document: dict[str, Any]) -> dict[str, Any]:
    """Flatten the YAML ``doctrine`` block into the ``PolicyDoctrine`` field layout."""
    if "doctrine" not in document:
        raise ValueError("Document must contain a top-level 'doctrine' block")
    for key in _SECTION_KEYS:
        if key not in document:
            raise ValueError(f"Document missing required section '{key}'")
    return {
        **document["doctrine"],
        **{key: document[key] for key in _SECTION_KEYS},
    }


def load_doctrine(document: dict[str, Any]) -> PolicyDoctrine:
    """Build a ``PolicyDoctrine`` from the normative YAML document shape."""
    return PolicyDoctrine.model_validate(flatten_doctrine_document(document))