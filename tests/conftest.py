"""Shared pytest fixtures for the domain layer."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

from domain import PolicyDoctrine


@pytest.fixture(scope="session")
def doctrine_document() -> Dict[str, Any]:
    """Raw policy_doctrine.yaml as a mapping.

    Returns:
        Dict[str, Any]: Parsed YAML document.
    """
    repo_root: Path = Path(__file__).resolve().parents[1]
    doctrine_yaml: Path = repo_root / "docs" / "Regulation" / "policy_doctrine.yaml"
    result: Dict[str, Any] = yaml.safe_load(doctrine_yaml.read_text(encoding="utf-8"))
    return result


@pytest.fixture(scope="session")
def doctrine(doctrine_document: Dict[str, Any]) -> PolicyDoctrine:
    """PolicyDoctrine aggregate loaded from the normative YAML document.

    Args:
        doctrine_document (Dict[str, Any]): Parsed YAML document.

    Returns:
        PolicyDoctrine: Validated doctrine aggregate.
    """
    result: PolicyDoctrine = PolicyDoctrine.from_document(doctrine_document)
    return result
