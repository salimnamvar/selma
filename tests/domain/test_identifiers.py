"""Unit tests for domain identifiers and scalar value types."""

from __future__ import annotations

from typing import Annotated

import pytest
from pydantic import Field, TypeAdapter, ValidationError

from domain.value_objects.version_strategy import SemanticVersion

MachineId = Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9]+-[0-9]+$")]


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


@pytest.mark.unit
@pytest.mark.domain
class TestMachineId:
    """MachineId constrained-string validation (syntax only, no class behavior)."""

    @pytest.mark.parametrize(
        "valid",
        ["AUTH-001", "PAY-800", "A1-0"],
        ids=["auth", "pay", "short-prefix"],
    )
    def test_accepts_valid_ids(self, valid: str) -> None:
        adapter: TypeAdapter[MachineId] = TypeAdapter(MachineId)
        assert adapter.validate_python(valid) == valid

    @pytest.mark.parametrize(
        "invalid",
        ["bad-id", "auth-001", "AUTH", "001-AUTH"],
        ids=["lowercase", "no-number-sep", "prefix-only", "reversed"],
    )
    def test_rejects_invalid_ids(self, invalid: str) -> None:
        adapter: TypeAdapter[MachineId] = TypeAdapter(MachineId)
        with pytest.raises(ValidationError):
            adapter.validate_python(invalid)
