"""Unit and contract tests for the PolicyDoctrine aggregate root."""

from __future__ import annotations

import typing
from typing import Any

import pytest
from pydantic import BaseModel

from domain import PolicyDoctrine
from domain.policy.policy_doctrine import PolicyDoctrine as PolicyDoctrineClass
from domain.policy.contamination_guard import ContaminationGuard
from domain.policy.cross_layer_binding import (
    ConflictResolutionBinding,
    CrossLayerBinding,
    FieldLegality,
)
from domain.policy.identity_resolution import IdentityResolution, MachineIdSemantics
from domain.policy.lifecycle_definition import LifecycleDefinition
from domain.policy.priority_hierarchy import CrossLayerPrecedence, Level, PriorityHierarchy
from domain.policy.sections import Section as SectionModel
from domain.policy.version_strategy import Intent, SemanticVersion, VersionStrategy
from domain.policy.writing_principles import WritingPrinciple
from infrastructure.yaml_adapter import flatten_doctrine_document


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
class TestPolicyDoctrineYamlContract:
    """Contract tests: normative policy_doctrine.yaml must load and map cleanly."""

    def test_yaml_field_names_match_model(
        self,
        doctrine_document: dict[str, Any],
    ) -> None:
        """Flattened YAML payload keys must match PolicyDoctrine fields (no aliases)."""
        flattened = flatten_doctrine_document(doctrine_document)
        unknown_keys: list[str] = []
        for key, value in flattened.items():
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

        for index, section in enumerate(flattened["sections"]):
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
            SemanticVersion,
            WritingPrinciple,
            SectionModel,
        )
        aliases = [
            f"{model.__name__}.{name}={field.alias}"
            for model in models
            for name, field in model.model_fields.items()
            if field.alias is not None and field.alias != name
        ]
        assert aliases == []

    def test_loads_normative_document(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.name == "universal-policy-doctrine"
        assert doctrine.version == SemanticVersion(major=8, minor=2, patch=4)
        assert doctrine.schema_id == "universal-rule-schema"

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

    def test_version_strategy_nested(self, doctrine: PolicyDoctrine) -> None:
        intent = doctrine.version_strategy.intent
        assert isinstance(intent, Intent)
        assert intent.major

    def test_writing_principles_loaded(self, doctrine: PolicyDoctrine) -> None:
        assert len(doctrine.writing_principles) == 5

    def test_sections_loaded(self, doctrine: PolicyDoctrine) -> None:
        assert len(doctrine.sections) >= 1
