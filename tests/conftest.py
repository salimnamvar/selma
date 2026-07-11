"""Root pytest fixtures shared across the entire suite.

Keep this file thin: path helpers and session-wide read-only resources only.
Package-specific fixtures live in nested conftest.py files.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Return the repository root directory.

    Returns:
        Path: Absolute path to the project root.
    """
    result: Path = Path(__file__).resolve().parents[1]
    return result


@pytest.fixture(scope="session")
def policy_doctrine_yaml_path(repo_root: Path) -> Path:
    """Return the path to the normative policy doctrine YAML.

    Args:
        repo_root (Path): Repository root.

    Returns:
        Path: Absolute path to policy_doctrine.yaml.
    """
    result: Path = repo_root / "docs" / "Regulation" / "policy_doctrine.yaml"
    return result
