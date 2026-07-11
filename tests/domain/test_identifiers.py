"""Unit tests for domain identifiers and scalar value types."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from domain import FieldPath, MachineId, SemanticVersion, is_major_compatible, major_version


@pytest.mark.unit
@pytest.mark.domain
class TestSemanticVersion:
    """SemanticVersion pattern validation and MAJOR compatibility."""

    _adapter: TypeAdapter[SemanticVersion] = TypeAdapter(SemanticVersion)

    @pytest.mark.parametrize(
        ("raw", "major", "minor", "patch"),
        [
            ("0.0.1", "0", "0", "1"),
            ("8.2.4", "8", "2", "4"),
            ("10.0.0", "10", "0", "0"),
        ],
        ids=["patch-only", "doctrine-version", "double-digit-major"],
    )
    def test_parse_string(
        self,
        raw: str,
        major: str,
        minor: str,
        patch: str,
    ) -> None:
        version = self._adapter.validate_python(raw)

        assert version == raw
        assert major_version(version) == major
        assert version.split(".") == [major, minor, patch]

    @pytest.mark.parametrize(
        "invalid",
        ["1.2", "1", "a.b.c", "1.2.3.4", ""],
        ids=["two-parts", "one-part", "non-numeric", "four-parts", "empty"],
    )
    def test_invalid_format_rejected(self, invalid: str) -> None:
        with pytest.raises(ValidationError):
            self._adapter.validate_python(invalid)

    def test_major_compatibility(self) -> None:
        left = self._adapter.validate_python("8.2.4")
        same_major = self._adapter.validate_python("8.0.0")
        other_major = self._adapter.validate_python("9.0.0")

        assert is_major_compatible(left, same_major)
        assert not is_major_compatible(left, other_major)


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


@pytest.mark.unit
@pytest.mark.domain
class TestFieldPath:
    """FieldPath string coercion into structured components."""

    @pytest.mark.parametrize(
        ("raw", "collection", "field"),
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
        raw: str,
        collection: str,
        field: str,
    ) -> None:
        path = FieldPath.model_validate(raw)

        assert path.collection == collection
        assert path.field == field
        assert str(path) == raw
        assert path.is_field(field)

    def test_empty_path_rejected(self) -> None:
        with pytest.raises(ValidationError):
            FieldPath.model_validate("   ")