"""Shared pytest fixtures for the domain layer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from domain import PolicyDoctrine

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCTRINE_YAML = REPO_ROOT / "docs" / "Regulation" / "policy_doctrine.yaml"


@pytest.fixture(scope="session")
def doctrine_document() -> dict[str, Any]:
    """Raw policy_doctrine.yaml as a mapping."""
    return yaml.safe_load(DOCTRINE_YAML.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def doctrine(doctrine_document: dict[str, Any]) -> PolicyDoctrine:
    """PolicyDoctrine aggregate loaded from the normative YAML document."""
    return PolicyDoctrine.from_document(doctrine_document)
