"""Policy doctrine aggregate root."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.base import require_unique
from domain.enums import PriorityCategory, ProhibitedField
from domain.identifiers import SchemaId, SemanticVersion
from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import CrossLayerBinding
from domain.value_objects.identity_resolution import IdentityResolution
from domain.value_objects.lifecycle_definition import LifecycleDefinition
from domain.value_objects.priority_hierarchy import PriorityHierarchy
from domain.value_objects.sections import DIRECTIVES_CHILD_IDS, REQUIRED_SECTION_IDS, Section
from domain.value_objects.version_strategy import VersionStrategy
from domain.value_objects.writing_principles import WritingPrinciple


class PolicyDoctrine(BaseModel):
    """Aggregate root for the complete governance doctrine.

    Doctrine metadata fields (from the YAML ``doctrine`` block) flatten directly
    into this model. Use ``infrastructure.yaml_adapter.load_doctrine`` to load
    from the normative nested YAML document shape.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1, description="Unique doctrine identifier")
    version: SemanticVersion = Field(description="Doctrine version")
    description: str = Field(min_length=1, description="Human-readable purpose statement")
    spec_version: SemanticVersion = Field(description="Compatible specification version")
    schema_version: SemanticVersion = Field(description="Compatible rule schema version")
    schema_id: SchemaId = Field(description="Identifier of the compatible rule schema")
    cross_layer_binding: CrossLayerBinding = Field(description="Layer relationship constraints")
    identity_resolution: IdentityResolution = Field(description="Identity mapping policy")
    lifecycle_definition: LifecycleDefinition = Field(description="Lifecycle operation governance")
    contamination_guard: ContaminationGuard = Field(description="Policy-layer field constraints")
    writing_principles: tuple[WritingPrinciple, ...] = Field(
        min_length=1,
        description="Authoring principles",
    )
    priority_hierarchy: PriorityHierarchy = Field(description="Authority levels and conflict-resolution intent")
    version_strategy: VersionStrategy = Field(description="Versioning intent")
    sections: tuple[Section, ...] = Field(
        min_length=1,
        description="Universal document section definitions",
    )

    @model_validator(mode="after")
    def _validate_aggregate(self) -> Self:
        """Enforce cross-field invariants across doctrine sections."""
        if not self.version.is_compatible(self.spec_version):
            raise ValueError(f"MAJOR version mismatch: doctrine={self.version} vs spec={self.spec_version}")
        if not self.version.is_compatible(self.schema_version):
            raise ValueError(f"MAJOR version mismatch: doctrine={self.version} vs schema={self.schema_version}")

        require_unique(
            [str(principle.id) for principle in self.writing_principles],
            label="IDs",
        )

        sections_by_id = {str(node.id): node for section in self.sections for node in section.traverse()}
        require_unique(list(sections_by_id.keys()), label="section ID")

        missing = REQUIRED_SECTION_IDS - sections_by_id.keys()
        if missing:
            raise ValueError(f"Missing required sections: {sorted(missing)}")

        directives = sections_by_id.get("directives")
        if directives is not None and directives.children:
            child_ids = {str(child.id) for child in directives.children}
            missing_children = DIRECTIVES_CHILD_IDS - child_ids
            if missing_children:
                raise ValueError(f"Directives section missing expected children: {sorted(missing_children)}")
        return self

    def is_compatible_with(
        self,
        spec_version: SemanticVersion,
        schema_version: SemanticVersion,
    ) -> bool:
        """Return True when this doctrine is MAJOR-compatible with both artifacts."""
        return self.version.is_compatible(spec_version) and self.version.is_compatible(schema_version)

    def is_field_allowed(self, field: str | ProhibitedField) -> bool:
        """Return True when ``field`` may appear in policy-layer prose."""
        result = True
        try:
            prohibited_field = field if isinstance(field, ProhibitedField) else ProhibitedField(field)
            result = prohibited_field not in self.contamination_guard.prohibited_fields
        except ValueError:
            pass
        return result

    def outranks(self, left: PriorityCategory, right: PriorityCategory) -> bool:
        """Return True when ``left`` has higher authority than ``right``."""
        return self.priority_hierarchy.outranks(left, right)

    def get_sections(self, id: str) -> Section | None:
        """Return a ``sections`` entry by ``id`` (tree-wide), or None."""
        return next(
            (node for section in self.sections for node in section.traverse() if str(node.id) == id),
            None,
        )

    def require_sections(self, id: str) -> Section:
        """Return a ``sections`` entry by ``id``, or raise KeyError."""
        result = self.get_sections(id)
        if result is None:
            raise KeyError(f"Item with key '{id}' not found")
        return result

    def get_writing_principles(self, id: str) -> WritingPrinciple | None:
        """Return a ``writing_principles`` entry by ``id``, or None."""
        return next(
            (principle for principle in self.writing_principles if str(principle.id) == id),
            None,
        )


