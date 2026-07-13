"""Tests for scalar types.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.5
"""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from domain.directive_graph.scalars import (
    ActorId,
    AnchorReference,
    DirectiveReference,
    ExecutionId,
    FiniteFloat,
    LineageId,
    PolicyContractId,
    RegexFlags,
    RegexPattern,
    SemanticVersion,
    UtcTimestamp,
)

_lineage_id_adapter = TypeAdapter(LineageId)
_execution_id_adapter = TypeAdapter(ExecutionId)
_utc_adapter = TypeAdapter(UtcTimestamp)
_regex_pattern_adapter = TypeAdapter(RegexPattern)
_regex_flags_adapter = TypeAdapter(RegexFlags)
_anchor_adapter = TypeAdapter(AnchorReference)
_policy_id_adapter = TypeAdapter(PolicyContractId)
_finite_adapter = TypeAdapter(FiniteFloat)
_actor_adapter = TypeAdapter(ActorId)
_directive_ref_adapter = TypeAdapter(DirectiveReference)


@pytest.mark.unit
@pytest.mark.domain
class TestLineageId:
    def test_valid_values(self) -> None:
        assert _lineage_id_adapter.validate_python("RULE-001") == "RULE-001"
        assert _lineage_id_adapter.validate_python("AB-123") == "AB-123"
        assert _lineage_id_adapter.validate_python("TRAF001-0") == "TRAF001-0"

    def test_rejects_lowercase(self) -> None:
        with pytest.raises(ValidationError):
            _lineage_id_adapter.validate_python("rule-001")

    def test_rejects_with_suffix(self) -> None:
        with pytest.raises(ValidationError):
            _lineage_id_adapter.validate_python("RULE-001-A")

    def test_rejects_empty(self) -> None:
        with pytest.raises(ValidationError):
            _lineage_id_adapter.validate_python("")


@pytest.mark.unit
@pytest.mark.domain
class TestExecutionId:
    def test_valid_base_form(self) -> None:
        assert _execution_id_adapter.validate_python("RULE-001") == "RULE-001"

    def test_valid_with_one_suffix(self) -> None:
        assert _execution_id_adapter.validate_python("RULE-001-A") == "RULE-001-A"

    def test_valid_with_two_suffixes(self) -> None:
        assert _execution_id_adapter.validate_python("RULE-001-A-B") == "RULE-001-A-B"

    def test_rejects_lowercase_suffix(self) -> None:
        with pytest.raises(ValidationError):
            _execution_id_adapter.validate_python("RULE-001-a")


@pytest.mark.unit
@pytest.mark.domain
class TestUtcTimestamp:
    def test_valid_utc(self) -> None:
        assert _utc_adapter.validate_python("2026-01-15T12:30:00Z") == "2026-01-15T12:30:00Z"

    def test_valid_with_subseconds(self) -> None:
        ts = "2026-01-15T12:30:00.123Z"
        assert _utc_adapter.validate_python(ts) == ts

    def test_rejects_offset(self) -> None:
        with pytest.raises(ValidationError):
            _utc_adapter.validate_python("2026-01-15T12:30:00+05:30")

    def test_rejects_missing_z(self) -> None:
        with pytest.raises(ValidationError):
            _utc_adapter.validate_python("2026-01-15T12:30:00")

    def test_lexicographic_ordering(self) -> None:
        earlier = "2026-01-01T00:00:00Z"
        later = "2026-12-31T23:59:59Z"
        assert earlier < later


@pytest.mark.unit
@pytest.mark.domain
class TestRegexPattern:
    def test_valid_pattern(self) -> None:
        assert _regex_pattern_adapter.validate_python("^test$") == "^test$"

    def test_rejects_empty(self) -> None:
        with pytest.raises(ValidationError):
            _regex_pattern_adapter.validate_python("")

    def test_rejects_too_long(self) -> None:
        with pytest.raises(ValidationError):
            _regex_pattern_adapter.validate_python("a" * 4097)

    def test_accepts_max_length(self) -> None:
        assert len(_regex_pattern_adapter.validate_python("a" * 4096)) == 4096


@pytest.mark.unit
@pytest.mark.domain
class TestRegexFlags:
    def test_empty_flags(self) -> None:
        assert _regex_flags_adapter.validate_python("") == ""

    def test_valid_flags(self) -> None:
        assert _regex_flags_adapter.validate_python("i") == "i"
        assert _regex_flags_adapter.validate_python("im") == "im"
        assert _regex_flags_adapter.validate_python("ims") == "ims"

    def test_rejects_invalid_flag(self) -> None:
        with pytest.raises(ValidationError):
            _regex_flags_adapter.validate_python("g")


@pytest.mark.unit
@pytest.mark.domain
class TestAnchorReference:
    def test_section_ref(self) -> None:
        assert _anchor_adapter.validate_python("section:definitions") == "section:definitions"
        assert _anchor_adapter.validate_python("section:auth/claims") == "section:auth/claims"

    def test_json_pointer(self) -> None:
        assert _anchor_adapter.validate_python("/rules/0/message") == "/rules/0/message"

    def test_rejects_plain_string(self) -> None:
        with pytest.raises(ValidationError):
            _anchor_adapter.validate_python("not-a-ref")


@pytest.mark.unit
@pytest.mark.domain
class TestPolicyContractId:
    def test_accepts_canonical_value(self) -> None:
        assert _policy_id_adapter.validate_python("universal-policy-doctrine") == "universal-policy-doctrine"

    def test_rejects_other_value(self) -> None:
        with pytest.raises(ValidationError):
            _policy_id_adapter.validate_python("other-policy")


@pytest.mark.unit
@pytest.mark.domain
class TestFiniteFloat:
    def test_valid_finite_value(self) -> None:
        assert _finite_adapter.validate_python(1.5) == 1.5
        assert _finite_adapter.validate_python(0.0) == 0.0
        assert _finite_adapter.validate_python(-100.0) == -100.0

    def test_rejects_nan(self) -> None:
        import math

        with pytest.raises(ValidationError):
            _finite_adapter.validate_python(math.nan)

    def test_rejects_positive_infinity(self) -> None:
        import math

        with pytest.raises(ValidationError):
            _finite_adapter.validate_python(math.inf)

    def test_rejects_negative_infinity(self) -> None:
        import math

        with pytest.raises(ValidationError):
            _finite_adapter.validate_python(-math.inf)


@pytest.mark.unit
@pytest.mark.domain
class TestSemanticVersion:
    def test_valid_version(self) -> None:
        sv = SemanticVersion("1.2.3")
        assert sv.major == 1
        assert sv.minor == 2
        assert sv.patch == 3

    def test_rejects_invalid_format(self) -> None:
        with pytest.raises(ValidationError):
            SemanticVersion("1.2")

    def test_major_compatibility(self) -> None:
        assert SemanticVersion("1.0.0").is_major_compatible(SemanticVersion("1.9.9"))
        assert not SemanticVersion("1.0.0").is_major_compatible(SemanticVersion("2.0.0"))

    def test_frozen(self) -> None:
        sv = SemanticVersion("1.0.0")
        with pytest.raises(Exception):
            sv.root = "2.0.0"  # type: ignore[misc]

    def test_str(self) -> None:
        assert str(SemanticVersion("1.2.3")) == "1.2.3"
