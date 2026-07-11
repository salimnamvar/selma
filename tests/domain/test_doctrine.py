"""Unit and contract tests for the PolicyDoctrine aggregate root."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from domain import (
    DocumentSection,
    DocumentStructure,
    IdentityOperation,
    PolicyDoctrine,
    PriorityCategory,
    ProhibitedField,
    ResolutionStrategy,
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
            PolicyDoctrine.from_dict(doctrine_document_copy)

    def test_missing_section_rejected(
        self,
        doctrine_document_copy: dict[str, Any],
    ) -> None:
        del doctrine_document_copy["writing_principles"]

        with pytest.raises(ValueError, match="missing required section"):
            PolicyDoctrine.from_dict(doctrine_document_copy)


@pytest.mark.integration
@pytest.mark.domain
class TestPolicyDoctrineYamlContract:
    """Contract tests: normative policy_doctrine.yaml must load and map cleanly.

    These tests pin domain behavior to the governance document under
    docs/Regulation/policy_doctrine.yaml.
    """

    def test_loads_normative_document(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.name == "universal-policy-doctrine"
        assert str(doctrine.version) == "8.2.4"
        assert doctrine.schema_id == "universal-rule-schema"

    def test_version_compatibility(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.version.is_compatible(doctrine.spec_version)
        assert doctrine.version.is_compatible(doctrine.schema_version)

    def test_cross_layer_binding_fields(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.cross_layer_binding.policy_purpose
        assert doctrine.cross_layer_binding.conflict_resolution_binding.schema_layer

    def test_conflict_resolution_binding_fields(self, doctrine: PolicyDoctrine) -> None:
        binding = doctrine.cross_layer_binding.conflict_resolution_binding
        data = binding.model_dump()
        assert set(data) == {"policy_layer", "schema_layer", "spec_layer", "precedence"}
        assert binding.strategies == ResolutionStrategy.chain()

    def test_cross_layer_precedence(self, doctrine: PolicyDoctrine) -> None:
        precedence = doctrine.priority_hierarchy.cross_layer_precedence
        assert "SPECIFICATION.md" in precedence.precedence_algorithm
        assert precedence.policy_role
        assert precedence.order
        assert precedence.strategies[0] == ResolutionStrategy.EXPLICIT_OVERRIDE
        assert precedence.strategies[-1] == ResolutionStrategy.CONFLICT_ARTIFACT

    def test_machine_id_exclusions(self, doctrine: PolicyDoctrine) -> None:
        exclusions = doctrine.identity_resolution.machine_id_semantics.exclusions
        assert "execution ID" in exclusions
        assert "runtime lookup key" in exclusions

    def test_lifecycle_definition_operations(self, doctrine: PolicyDoctrine) -> None:
        lifecycle = doctrine.lifecycle_definition
        assert frozenset(IdentityOperation) == frozenset(lifecycle._GUIDANCE_ENUM)
        assert "two distinct" in lifecycle.get_guidance(IdentityOperation.FORK).lower()
        assert "combine" in lifecycle.get_guidance(IdentityOperation.MERGE).lower()

    def test_versioning_intent_nested(self, doctrine: PolicyDoctrine) -> None:
        intent = doctrine.version_strategy.intent
        assert "breaking" in intent.major.lower()
        assert intent.minor
        assert intent.patch

    def test_writing_principles(self, doctrine: PolicyDoctrine) -> None:
        assert len(doctrine.writing_principles) == 5
        principle = doctrine.writing_principles.get("WP-001")
        assert principle is not None
        assert "Precision" in principle.title

    def test_sections_and_lookups(self, doctrine: PolicyDoctrine) -> None:
        assert {section.id for section in doctrine.sections} >= DocumentStructure.REQUIRED_SECTION_IDS
        assert doctrine.sections.get("directives") is not None
        assert doctrine.sections.get("flexible_standards") is not None
        assert doctrine.sections.get("specific_directives") is not None

    def test_contamination_guard(self, doctrine: PolicyDoctrine) -> None:
        guard = doctrine.contamination_guard
        assert guard.is_prohibited(ProhibitedField.PARAMETERS)
        assert guard.is_prohibited("evaluator_hint")
        assert not guard.is_prohibited("machine_id")
        assert set(guard.prohibited_fields) == set(ProhibitedField)

    def test_priority_outranks(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.priority_hierarchy.outranks(
            PriorityCategory.CONSTITUTIONAL,
            PriorityCategory.OPERATIONAL,
        )
        rank = doctrine.priority_hierarchy.get(PriorityCategory.STATUTORY)
        assert rank is not None
        assert rank.rank == 2

    def test_identity_field_paths(self, doctrine: PolicyDoctrine) -> None:
        resolution = doctrine.identity_resolution
        assert resolution.schema_lineage_location.field == "lineage_id"
        assert resolution.schema_execution_location.field == "id"

    def test_schema_encoding_is_authoring_guidance(
        self,
        doctrine: PolicyDoctrine,
    ) -> None:
        flexible = doctrine.sections.get("flexible_standards")
        assert flexible is not None
        assert flexible.schema_encoding is not None
        assert isinstance(flexible.schema_encoding, str)

    def test_section_depth_within_limit(self, doctrine: PolicyDoctrine) -> None:
        for section in doctrine.sections:
            assert section.max_depth() <= DocumentSection.MAX_DEPTH
