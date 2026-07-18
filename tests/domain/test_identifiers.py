"""Unit tests for domain identifiers and scalar value types."""

from __future__ import annotations

from pydantic import ValidationError
import pytest

from domain.policy_doctrine.version_strategy import SemanticVersion


@pytest.mark.unit
@pytest.mark.domain
class TestSemanticVersion:
    """SemanticVersion flat construction."""

    def test_construction(self) -> None:
        version = SemanticVersion(major=8, minor=2, patch=4)

        assert version.major == 8
        assert version.minor == 2
        assert version.patch == 4

    @pytest.mark.parametrize(
        ("major", "minor", "patch"),
        [
            (0, 0, 1),
            (8, 2, 4),
            (10, 0, 0),
        ],
        ids=["patch-only", "doctrine-version", "double-digit-major"],
    )
    def test_fields(self, major: int, minor: int, patch: int) -> None:
        version = SemanticVersion(major=major, minor=minor, patch=patch)

        assert version.major == major
        assert version.minor == minor
        assert version.patch == patch

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SemanticVersion(major=-1, minor=0, patch=0)
