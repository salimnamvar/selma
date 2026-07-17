"""Tests for the Directive entity."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from tests.domain.directive_graph.conftest import make_directive, make_domain_directive_payload

from domain.directive_graph.directive import Directive
from domain.directive_graph.enums import DeonticType, DirectiveStatus, EvaluatorType
from domain.directive_graph.evaluators import FieldCheckEvaluator, RegexEvaluator
from domain.directive_graph.exceptions import InvalidLifecycleTransitionError
from infrastructure.mappers.directive_graph_mapper import DirectiveGraphMapper


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

    def test_domain_shaped_construction(self) -> None:
        d = Directive.model_validate(make_domain_directive_payload())
        assert d.id == "RULE-001"


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
class TestDirectiveLifecycleMethods:
    def test_activate_from_draft(self) -> None:
        d = make_directive(metadata={"audit": {"authored_by": "alice"}})
        active = d.activate()
        assert active.status == DirectiveStatus.ACTIVE
        assert d.status == DirectiveStatus.DRAFT  # original unchanged

    def test_activate_without_author_raises(self) -> None:
        d = make_directive()
        with pytest.raises(InvalidLifecycleTransitionError):
            d.activate()

    def test_retire_from_active(self) -> None:
        d = make_directive(status="active", metadata={"audit": {"authored_by": "alice"}})
        retired = d.retire()
        assert retired.status == DirectiveStatus.DEPRECATED

    def test_supersede_requires_successor(self) -> None:
        d = make_directive(status="active", metadata={"audit": {"authored_by": "alice"}})
        superseded = d.supersede("RULE-002")
        assert superseded.status == DirectiveStatus.SUPERSEDED
        assert superseded.metadata is not None
        assert superseded.metadata.migration is not None
        assert superseded.metadata.migration.superseded_by == "RULE-002"


@pytest.mark.unit
@pytest.mark.domain
class TestDirectiveJsonRoundTrip:
    def test_round_trip_minimal(self) -> None:
        d = make_directive()
        dumped = d.model_dump(mode="json")
        restored = Directive.model_validate(dumped)
        assert restored.lineage_id == d.lineage_id
        assert restored.id == d.id
        assert restored.evaluator_config == d.evaluator_config

    def test_schema_format_parses_via_acl(self) -> None:
        """Ensure JSON schema format is accepted through the ACL mapper."""
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
        d = DirectiveGraphMapper().directive_to_domain(raw)
        assert isinstance(d.evaluator_config, FieldCheckEvaluator)
        assert d.evaluator_config.field == "role"

    def test_domain_rejects_wire_split_evaluator_type(self) -> None:
        """Domain model does not accept top-level evaluator_type without merge."""
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
        with pytest.raises(ValidationError):
            Directive.model_validate(raw)
