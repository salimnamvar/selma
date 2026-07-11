"""Unit and contract tests for the PolicyDoctrine aggregate root."""

from __future__ import annotations

import typing
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from domain import (
    REQUIRED_SECTION_IDS,
    IdentityOperation,
    PolicyDoctrine,
    PriorityCategory,
    ProhibitedField,
    Section,
)
from domain.doctrine import Doctrine
from domain.identifiers import SemanticVersion
from domain.policy_doctrine import PolicyDoctrine as PolicyDoctrineClass
from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import (
    ConflictResolutionBinding,
    CrossLayerBinding,
    FieldLegality,
)
from domain.value_objects.identity_resolution import IdentityResolution, MachineIdSemantics
from domain.value_objects.lifecycle_definition import LifecycleDefinition
from domain.value_objects.priority_hierarchy import CrossLayerPrecedence, Level, PriorityHierarchy
from domain.value_objects.sections import Section as SectionModel
from domain.value_objects.version_strategy import Intent, VersionStrategy
from domain.value_objects.writing_principles import WritingPrinciple


def _unwrap_annotation(annotation: Any) -> Any:
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin is typing.Annotated:
        return _unwrap_annotation(args[0])
    if origin is tuple and args:
        return _unwrap_annotation(args[0])
    return annotation


def _nested_model(parent: type[BaseModel], key: str, value: Any) -> type[BaseModel] | None:
    field = parent.model_fields[key]
    annotation = _unwrap_annotation(field.annotation)
    if not isinstance(annotation, type) or not issubclass(annotation, BaseModel):
        return None
    if isinstance(value, (dict, str)):
        return annotation
    return None


def _assert_yaml_keys_match_model(
    value: Any,
    model: type[BaseModel],
    path: str,
    unknown_keys: list[str],
) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            if key not in model.model_fields:
                unknown_keys.append(child_path)
                continue
            nested = _nested_model(model, key, child)
            if nested is not None:
                _assert_yaml_keys_match_model(child, nested, child_path, unknown_keys)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_yaml_keys_match_model(item, model, f"{path}[{index}]", unknown_keys)


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

    def test_missing_required_sections_rejected(
        self,
        doctrine_document_copy: dict[str, Any],
    ) -> None:
        doctrine_document_copy["sections"] = [
            section
            for section in doctrine_document_copy["sections"]
            if section["id"] != "preamble"
        ]

        with pytest.raises(ValidationError, match="Missing required sections"):
            PolicyDoctrine.model_validate(doctrine_document_copy)

    def test_duplicate_principle_ids_rejected(
        self,
        doctrine_document_copy: dict[str, Any],
    ) -> None:
        duplicate = doctrine_document_copy["writing_principles"][0]
        doctrine_document_copy["writing_principles"] = [duplicate, duplicate]

        with pytest.raises(ValidationError, match="Duplicate IDs"):
            PolicyDoctrine.model_validate(doctrine_document_copy)


@pytest.mark.integration
@pytest.mark.domain
class TestPolicyDoctrineYamlContract:
    """Contract tests: normative policy_doctrine.yaml must load and map cleanly."""

    def test_yaml_field_names_match_model(
        self,
        doctrine_document: dict[str, Any],
    ) -> None:
        """Every YAML key must match a Pydantic field name (no aliases)."""
        unknown_keys: list[str] = []
        for key, value in doctrine_document.items():
            if key not in PolicyDoctrine.model_fields:
                unknown_keys.append(key)
                continue
            nested = _nested_model(PolicyDoctrine, key, value)
            if nested is not None:
                if isinstance(value, list):
                    for index, item in enumerate(value):
                        _assert_yaml_keys_match_model(item, nested, f"{key}[{index}]", unknown_keys)
                else:
                    _assert_yaml_keys_match_model(value, nested, key, unknown_keys)

        for index, section in enumerate(doctrine_document["sections"]):
            _assert_yaml_keys_match_model(section, SectionModel, f"sections[{index}]", unknown_keys)
            for child_index, child in enumerate(section.get("children", ())):
                _assert_yaml_keys_match_model(
                    child,
                    SectionModel,
                    f"sections[{index}].children[{child_index}]",
                    unknown_keys,
                )

        assert unknown_keys == []

    def test_model_has_no_field_aliases(self) -> None:
        models = (
            PolicyDoctrineClass,
            Doctrine,
            CrossLayerBinding,
            ConflictResolutionBinding,
            FieldLegality,
            IdentityResolution,
            MachineIdSemantics,
            LifecycleDefinition,
            ContaminationGuard,
            PriorityHierarchy,
            Level,
            CrossLayerPrecedence,
            VersionStrategy,
            Intent,
            WritingPrinciple,
            SectionModel,
            SemanticVersion,
        )
        aliases = [
            f"{model.__name__}.{name}={field.alias}"
            for model in models
            for name, field in model.model_fields.items()
            if field.alias is not None and field.alias != name
        ]
        assert aliases == []

    def test_loads_normative_document(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.doctrine.name == "universal-policy-doctrine"
        assert str(doctrine.doctrine.version) == "8.2.4"
        assert doctrine.doctrine.schema_id == "universal-rule-schema"

    def test_version_compatibility(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.is_compatible_with(
            doctrine.doctrine.spec_version,
            doctrine.doctrine.schema_version,
        )
        assert doctrine.doctrine.version.is_compatible(doctrine.doctrine.spec_version)
        assert doctrine.doctrine.version.is_compatible(doctrine.doctrine.schema_version)

    def test_cross_layer_binding_fields(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.cross_layer_binding.policy_purpose
        assert doctrine.cross_layer_binding.conflict_resolution_binding.schema_layer

    def test_conflict_resolution_binding_fields(self, doctrine: PolicyDoctrine) -> None:
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

    def test_lifecycle_definition_operations(self, doctrine: PolicyDoctrine) -> None:
        assert "two distinct" in doctrine.get_lifecycle_definition(IdentityOperation.FORK).lower()
        assert "combine" in doctrine.get_lifecycle_definition(IdentityOperation.MERGE).lower()

    def test_version_strategy_nested(self, doctrine: PolicyDoctrine) -> None:
        intent = doctrine.version_strategy.intent
        assert "breaking" in intent.major.lower()
        assert intent.minor
        assert intent.patch

    def test_writing_principles(self, doctrine: PolicyDoctrine) -> None:
        assert len(doctrine.writing_principles) == 5
        principle = doctrine.get_writing_principles("WP-001")
        assert principle is not None
        assert "Precision" in principle.title

    def test_sections_and_lookups(self, doctrine: PolicyDoctrine) -> None:
        assert {str(section.id) for section in doctrine.sections} >= REQUIRED_SECTION_IDS
        assert doctrine.get_sections("directives") is not None
        assert doctrine.get_sections("flexible_standards") is not None
        assert doctrine.require_sections("specific_directives") is not None

    def test_contamination_guard(self, doctrine: PolicyDoctrine) -> None:
        guard = doctrine.contamination_guard
        assert doctrine.prohibited_fields_contains(ProhibitedField.PARAMETERS)
        assert doctrine.prohibited_fields_contains("evaluator_hint")
        assert not doctrine.prohibited_fields_contains("machine_id")
        assert set(guard.prohibited_fields) == set(ProhibitedField)
        assert guard.prohibited_fields_contains("parameters")
        assert guard.prohibited_fields_contains("weight")
        assert not guard.prohibited_fields_contains("description")

    def test_priority_outranks(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.outranks(
            PriorityCategory.CONSTITUTIONAL,
            PriorityCategory.OPERATIONAL,
        )
        levels_entry = doctrine.priority_hierarchy.get_levels(PriorityCategory.STATUTORY)
        assert levels_entry is not None
        assert levels_entry.rank == 2

    def test_identity_locations_are_governance_text(self, doctrine: PolicyDoctrine) -> None:
        resolution = doctrine.identity_resolution
        assert resolution.schema_lineage_location.endswith("lineage_id")
        assert resolution.schema_execution_location.endswith("id")

    def test_schema_encoding_is_authoring_guidance(
        self,
        doctrine: PolicyDoctrine,
    ) -> None:
        flexible = doctrine.get_sections("flexible_standards")
        assert flexible is not None
        assert flexible.schema_encoding is not None
        assert str(flexible.schema_encoding)

    def test_section_depth_within_limit(self, doctrine: PolicyDoctrine) -> None:
        for section in doctrine.sections:
            assert section.max_depth() <= Section.MAX_DEPTH