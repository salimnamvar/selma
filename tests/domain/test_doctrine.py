"""Unit and contract tests for the PolicyDoctrine aggregate root."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from domain import (
    REQUIRED_SECTION_IDS,
    DocumentSection,
    IdentityOperation,
    PolicyDoctrine,
    PriorityCategory,
    ProhibitedField,
    field_path_field,
    is_major_compatible,
)


@pytest.mark.unit
@pytest.mark.domain
class TestPolicyDoctrineInvariants:
    """Cross-field invariants owned by the aggregate root."""

    def test_major_mismatch_rejected(
        self,
        doctrine_document_copy: dict[str, Any],
    ) -> None:
        doctrine_document_copy["doctrine"]["spec_version"] = "9.0.0"

        with pytest.raises(ValidationError, match="MAJOR version mismatch"):
            PolicyDoctrine.model_validate(doctrine_document_copy)

    def test_missing_section_rejected(
        self,
        doctrine_document_copy: dict[str, Any],
    ) -> None:
        del doctrine_document_copy["writing_principles"]

        with pytest.raises(ValidationError):
            PolicyDoctrine.model_validate(doctrine_document_copy)


@pytest.mark.integration
@pytest.mark.domain
class TestPolicyDoctrineYamlContract:
    """Contract tests: normative policy_doctrine.yaml must load and map cleanly."""

    def test_loads_normative_document(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.doctrine.name == "universal-policy-doctrine"
        assert doctrine.doctrine.version == "8.2.4"
        assert doctrine.doctrine.schema_id == "universal-rule-schema"

    def test_version_compatibility(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.is_compatible_with(
            doctrine.doctrine.spec_version,
            doctrine.doctrine.schema_version,
        )
        assert is_major_compatible(doctrine.doctrine.version, doctrine.doctrine.spec_version)
        assert is_major_compatible(doctrine.doctrine.version, doctrine.doctrine.schema_version)

    def test_cross_layer_binding_fields(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.cross_layer_binding.policy_purpose
        assert doctrine.cross_layer_binding.conflict_resolution_binding.schema_layer

    def test_conflict_resolution_intent_fields(self, doctrine: PolicyDoctrine) -> None:
        binding = doctrine.cross_layer_binding.conflict_resolution_binding
        data = binding.model_dump()
        assert set(data) == {"policy_layer", "schema_layer", "spec_layer", "precedence"}
        assert "strategies" not in data

    def test_cross_layer_precedence_is_intent_only(self, doctrine: PolicyDoctrine) -> None:
        precedence = doctrine.priority_hierarchy.cross_layer_precedence
        assert "SPECIFICATION.md" in precedence.precedence_algorithm
        assert precedence.policy_role
        assert precedence.order
        assert not hasattr(precedence, "strategies")

    def test_machine_id_exclusions(self, doctrine: PolicyDoctrine) -> None:
        exclusions = doctrine.identity_resolution.machine_id_semantics.exclusions
        assert "execution ID" in exclusions
        assert "runtime lookup key" in exclusions

    def test_lifecycle_guidance_operations(self, doctrine: PolicyDoctrine) -> None:
        assert "two distinct" in doctrine.get_lifecycle_guidance(IdentityOperation.FORK).lower()
        assert "combine" in doctrine.get_lifecycle_guidance(IdentityOperation.MERGE).lower()

    def test_versioning_intent_nested(self, doctrine: PolicyDoctrine) -> None:
        intent = doctrine.version_strategy.intent
        assert "breaking" in intent.major.lower()
        assert intent.minor
        assert intent.patch

    def test_writing_principles(self, doctrine: PolicyDoctrine) -> None:
        assert len(doctrine.writing_principles) == 5
        principle = doctrine.get_principle("WP-001")
        assert principle is not None
        assert "Precision" in principle.title

    def test_sections_and_lookups(self, doctrine: PolicyDoctrine) -> None:
        assert {str(section.id) for section in doctrine.sections} >= REQUIRED_SECTION_IDS
        assert doctrine.get_section("directives") is not None
        assert doctrine.get_section("flexible_standards") is not None
        assert doctrine.require_section("specific_directives") is not None

    def test_contamination_guard(self, doctrine: PolicyDoctrine) -> None:
        assert not doctrine.is_policy_field_allowed(ProhibitedField.PARAMETERS)
        assert not doctrine.is_policy_field_allowed("evaluator_hint")
        assert doctrine.is_policy_field_allowed("machine_id")
        assert set(doctrine.contamination_guard.prohibited_fields) == set(ProhibitedField)
        assert doctrine.contamination_guard.collect_violations(
            ["parameters", "description", "weight"]
        ) == ("parameters", "weight")

    def test_priority_outranks(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.outranks(
            PriorityCategory.CONSTITUTIONAL,
            PriorityCategory.OPERATIONAL,
        )
        rank = doctrine.priority_hierarchy.get(PriorityCategory.STATUTORY)
        assert rank is not None
        assert rank.rank == 2

    def test_identity_field_paths(self, doctrine: PolicyDoctrine) -> None:
        resolution = doctrine.identity_resolution
        assert field_path_field(resolution.schema_lineage_location) == "lineage_id"
        assert field_path_field(resolution.schema_execution_location) == "id"

    def test_schema_encoding_is_authoring_guidance(
        self,
        doctrine: PolicyDoctrine,
    ) -> None:
        flexible = doctrine.get_section("flexible_standards")
        assert flexible is not None
        assert flexible.schema_encoding is not None
        assert str(flexible.schema_encoding)

    def test_section_depth_within_limit(self, doctrine: PolicyDoctrine) -> None:
        for section in doctrine.sections:
            assert section.max_depth() <= DocumentSection.MAX_DEPTH