"""Policy doctrine aggregate root."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain.policy_doctrine.contamination_guard import ContaminationGuard
from domain.policy_doctrine.cross_layer_binding import CrossLayerBinding
from domain.policy_doctrine.identity_resolution import IdentityResolution
from domain.policy_doctrine.lifecycle_definition import LifecycleDefinition
from domain.policy_doctrine.priority_hierarchy import PriorityHierarchy
from domain.policy_doctrine.sections import Section
from domain.policy_doctrine.version_strategy import SemanticVersion, VersionStrategy
from domain.policy_doctrine.writing_principles import WritingPrinciple


class PolicyDoctrine(BaseModel):
    """Aggregate root for the complete governance doctrine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(
        pattern=r"^[a-z][a-z0-9-]*$", min_length=1, description="Unique doctrine identifier"
    )
    version: SemanticVersion = Field(description="Doctrine version")
    description: str = Field(min_length=1, description="Human-readable purpose statement")
    spec_version: SemanticVersion = Field(description="Compatible specification version")
    schema_version: SemanticVersion = Field(description="Compatible rule schema version")
    schema_id: str = Field(
        pattern=r"^[a-z][a-z0-9-]*$", min_length=1, description="Identifier of the compatible rule schema"
    )
    cross_layer_binding: CrossLayerBinding = Field(description="Layer relationship constraints")
    identity_resolution: IdentityResolution = Field(description="Identity mapping policy")
    lifecycle_definition: LifecycleDefinition = Field(description="Lifecycle operation governance")
    contamination_guard: ContaminationGuard = Field(description="Policy-layer field constraints")
    writing_principles: tuple[WritingPrinciple, ...] = Field(min_length=1, description="Authoring principles")
    priority_hierarchy: PriorityHierarchy = Field(description="Authority levels and conflict-resolution intent")
    version_strategy: VersionStrategy = Field(description="Versioning intent")
    sections: tuple[Section, ...] = Field(min_length=1, description="Universal document section definitions")
