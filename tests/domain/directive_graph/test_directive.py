"""Tests for the Directive entity.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.2
"""

from __future__ import annotations

from pydantic import ValidationError
import pytest

from domain.directive_graph.enums import DeonticType
from domain.directive_graph.enums import DirectiveStatus
from domain.directive_graph.enums import EvaluatorType
from tests.domain.directive_graph.conftest import make_active_directive_payload
from tests.domain.directive_graph.conftest import make_directive
from tests.domain.directive_graph.conftest import make_directive_payload


@pytest.mark.unit
@pytest.mark.domain
class TestDirectiveConstruction:
    def test_minimal_draft_directive(self) -> None:
        d = make_directive()
        assert d.lineage_id == "RULE-001"
        assert d.id == "RULE-001"
        assert d.type == DeonticType.OBLIGATION
        assert d.status == DirectiveStatus.DRAFT

    def test_evaluator_type_accessible_via_property(self) -> None:
        d = make_directive()
        assert d.evaluator_type == EvaluatorType.REGEX

    def test_evaluator_config_is_populated(self) -> None:
        from domain.directive_graph.evaluators import RegexEvaluator

        d = make_directive()
        assert isinstance(d.evaluator_config, RegexEvaluator)
        assert d.evaluator_config.pattern == "^test$"

    def test_active_with_authored_by_succeeds(self) -> None:
        d = make_directive(
            status="active",
            metadata={"audit": {"authored_by": "alice"}},
        )
        assert d.status == DirectiveStatus.ACTIVE

    def test_all_optional_fields_are_none_by_default(self) -> None:
        d = make_directive()
        assert d.scope is None
        assert d.conflict_resolution is None
        assert d.lineage is None
        assert d.expires_at is None
        assert d.anchor_ref is None
        assert d.metadata is None


@pytest.mark.unit
@pytest.mark.domain
class TestDirectiveInvariants:
    def test_active_without_authored_by_raises(self) -> None:
        with pytest.raises(ValidationError, match="authored_by"):
            make_directive(status="active")

    def test_active_with_empty_authored_by_raises(self) -> None:
        with pytest.raises(ValidationError):
            make_directive(
                status="active",
                metadata={"audit": {"authored_by": ""}},
            )

    def test_expires_before_created_raises(self) -> None:
        with pytest.raises(ValidationError, match="expires_at"):
            make_directive(
                created_at="2026-06-01T00:00:00Z",
                expires_at="2026-01-01T00:00:00Z",
            )

    def test_expires_equal_to_created_raises(self) -> None:
        with pytest.raises(ValidationError, match="expires_at"):
            make_directive(
                created_at="2026-01-01T00:00:00Z",
                expires_at="2026-01-01T00:00:00Z",
            )

    def test_expires_after_created_succeeds(self) -> None:
        d = make_directive(
            created_at="2026-01-01T00:00:00Z",
            expires_at="2027-01-01T00:00:00Z",
        )
        assert d.expires_at == "2027-01-01T00:00:00Z"

    def test_duplicate_depends_on_raises(self) -> None:
        with pytest.raises(ValidationError, match="Duplicate"):
            make_directive(depends_on=["RULE-002", "RULE-002"])

    def test_duplicate_conflicts_with_raises(self) -> None:
        with pytest.raises(ValidationError, match="Duplicate"):
            make_directive(conflicts_with=["RULE-003", "RULE-003"])

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            make_directive(unknown_field="value")


@pytest.mark.unit
@pytest.mark.domain
class TestDirectiveJsonRoundTrip:
    def test_round_trip_minimal(self) -> None:
        from domain.directive_graph.directive import Directive

        d = make_directive()
        dumped = d.model_dump(mode="json")
        restored = Directive.model_validate(dumped)
        assert restored.lineage_id == d.lineage_id
        assert restored.id == d.id
        assert restored.evaluator_config == d.evaluator_config

    def test_schema_format_parses_correctly(self) -> None:
        """Ensure JSON schema format (separate evaluator_type) is accepted."""
        from domain.directive_graph.directive import Directive

        raw = {
            "lineage_id": "AUTH-001",
            "id": "AUTH-001",
            "type": "prohibition",
            "message": "No unauthorized access",
            "evaluator_type": "field_check",
            "evaluator_config": {"field": "role", "operator": "neq", "value": "admin"},
            "status": "draft",
            "created_at": "2026-03-01T00:00:00Z",
        }
        d = Directive.model_validate(raw)
        from domain.directive_graph.evaluators import FieldCheckEvaluator

        assert isinstance(d.evaluator_config, FieldCheckEvaluator)
        assert d.evaluator_config.field == "role"
