"""YAML document loading for policy doctrine."""

from __future__ import annotations

from typing import Any

from domain.policy_doctrine import PolicyDoctrine


def load_doctrine(document: dict[str, Any]) -> PolicyDoctrine:
    """Build a ``PolicyDoctrine`` from a parsed YAML document.

    Field presence and shape are validated by Pydantic — no manual key wiring.
    """
    return PolicyDoctrine.model_validate(document)