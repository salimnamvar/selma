"""YAML document loading for policy doctrine."""

from __future__ import annotations

from typing import Any

from domain.policy_doctrine import PolicyDoctrine

_REQUIRED_TOP_LEVEL_KEYS: tuple[str, ...] = (
    "doctrine",
    "cross_layer_binding",
    "identity_resolution",
    "lifecycle_definition",
    "contamination_guard",
    "writing_principles",
    "priority_hierarchy",
    "version_strategy",
    "sections",
)


def load_doctrine(document: dict[str, Any]) -> PolicyDoctrine:
    """Build a ``PolicyDoctrine`` from the normative YAML document shape."""
    if "doctrine" not in document:
        raise ValueError("Document must contain a top-level 'doctrine' block")
    for key in _REQUIRED_TOP_LEVEL_KEYS:
        if key not in document:
            raise ValueError(f"Document missing required section '{key}'")
    return PolicyDoctrine.model_validate(document)