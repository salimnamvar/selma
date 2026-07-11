"""Unit tests for domain identifiers and scalar value types."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from domain import FieldPath, MachineId, SemanticVersion


@pytest.mark.unit
@pytest.mark.domain
class TestSemanticVersion:
    """SemanticVersion parsing, compatibility, and ordering."""

    @pytest.mark.parametrize(
        ("a_raw", "a_major", "a_minor", "a_patch"),
        [
            ("0.0.1", 0, 0, 1),
            ("8.2.4", 8, 2, 4),
            ("10.0.0", 10, 0, 0),
        ],
        ids=["patch-only", "doctrine-version", "double-digit-major"],
    )
    def test_parse_string(
        self,
        a_raw: str,
        a_major: int,
        a_minor: int,
        a_patch: int,
    ) -> None:
        # Arrange / Act — coercion is owned by Pydantic model_validate
        version: SemanticVersion = SemanticVersion.model_validate(a_raw)

        # Assert
        assert version.major == a_major
        assert version.minor == a_minor
        assert version.patch == a_patch
        assert str(version) == a_raw

    @pytest.mark.parametrize(
        "a_invalid",
        ["1.2", "1", "a.b.c", "1.2.3.4", ""],
        ids=["two-parts", "one-part", "non-numeric", "four-parts", "empty"],
    )
    def test_invalid_format_rejected(self, a_invalid: str) -> None:
        with pytest.raises(ValidationError):
            SemanticVersion.model_validate(a_invalid)

    def test_major_compatibility(self) -> None:
        left: SemanticVersion = SemanticVersion.model_validate("8.2.4")
        same_major: SemanticVersion = SemanticVersion.model_validate("8.0.0")
        other_major: SemanticVersion = SemanticVersion.model_validate("9.0.0")

        assert left.is_compatible(same_major)
        assert not left.is_compatible(other_major)

    def test_ordering(self) -> None:
        assert SemanticVersion.model_validate("1.0.0") < SemanticVersion.model_validate("1.0.1")
        assert SemanticVersion.model_validate("2.0.0") > SemanticVersion.model_validate("1.9.9")
        assert SemanticVersion.model_validate("1.0.0") <= SemanticVersion.model_validate("1.0.0")


@pytest.mark.unit
@pytest.mark.domain
class TestMachineId:
    """MachineId Annotated constraint validation."""

    @pytest.mark.parametrize(
        "a_valid",
        ["AUTH-001", "PAY-800", "A1-0"],
        ids=["auth", "pay", "short-prefix"],
    )
    def test_accepts_valid_ids(self, a_valid: str) -> None:
        adapter: TypeAdapter[MachineId] = TypeAdapter(MachineId)
        assert adapter.validate_python(a_valid) == a_valid

    @pytest.mark.parametrize(
        "a_invalid",
        ["bad-id", "auth-001", "AUTH", "001-AUTH"],
        ids=["lowercase", "no-number-sep", "prefix-only", "reversed"],
    )
    def test_rejects_invalid_ids(self, a_invalid: str) -> None:
        adapter: TypeAdapter[MachineId] = TypeAdapter(MachineId)
        with pytest.raises(ValidationError):
            adapter.validate_python(a_invalid)


@pytest.mark.unit
@pytest.mark.domain
class TestFieldPath:
    """FieldPath string coercion into structured components."""

    @pytest.mark.parametrize(
        ("a_raw", "a_collection", "a_field"),
        [
            ("rules[].lineage_id", "rules", "lineage_id"),
            ("CG-IR nodes[].directive_id", "CG-IR nodes", "directive_id"),
            ("rules.id", "rules", "id"),
            ("standalone", "standalone", "standalone"),
        ],
        ids=["bracket-path", "spaced-collection", "dot-path", "bare-token"],
    )
    def test_parse_path(
        self,
        a_raw: str,
        a_collection: str,
        a_field: str,
    ) -> None:
        path: FieldPath = FieldPath.model_validate(a_raw)

        assert path.collection == a_collection
        assert path.field == a_field
        assert str(path) == a_raw

    def test_empty_path_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FieldPath.model_validate("   ")
