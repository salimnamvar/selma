from typing import ClassVar

from pydantic import ConfigDict, Field

from domain.identifiers import Guidance
from domain.value_objects.base import DomainValueObject


class ConflictResolutionBinding(DomainValueObject):
    """Describes how each layer contributes to conflict resolution."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    policy: Guidance = Field(description="Policy layer's role in conflict resolution")
    schema_layer: Guidance = Field(alias="schema", description="Schema layer's role in conflict resolution")
    spec: Guidance = Field(description="Specification layer's role in conflict resolution")
    precedence: Guidance = Field(description="Declared precedence chain")


class FieldLegality(DomainValueObject):
    """Defines what each layer may contain."""

    policy_layer: Guidance = Field(description="What the policy layer may contain")
    schema_layer: Guidance = Field(description="What the schema layer may contain")
    spec_layer: Guidance = Field(description="What the specification layer may contain")


class CrossLayerBinding(DomainValueObject):
    """Describes the structural relationship between policy, schema, and specification layers."""

    normative_source: str = Field(description="The authoritative behavioral source")
    this_layer_purpose: Guidance = Field(description="Purpose of the policy layer")
    schema_layer_purpose: Guidance = Field(description="Purpose of the schema layer")
    enforcement: Guidance = Field(description="How governance intent is enforced")
    conflict_resolution_binding: ConflictResolutionBinding = Field(
        description="How each layer contributes to conflict resolution"
    )
    runtime_prohibition: Guidance = Field(description="What this file must not do at runtime")
    field_legality: FieldLegality = Field(description="What each layer may contain")
