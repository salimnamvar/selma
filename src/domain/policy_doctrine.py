"""Policy doctrine aggregate root (policy_doctrine.yaml)."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, Field, model_validator

from domain.base import VO_CONFIG
from domain.doctrine import Doctrine
from domain.enums import IdentityOperation, PriorityCategory, ProhibitedField
from domain.identifiers import SemanticVersion
from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import CrossLayerBinding
from domain.value_objects.identity_resolution import IdentityResolution
from domain.value_objects.lifecycle_definition import LifecycleDefinition
from domain.value_objects.priority_hierarchy import PriorityHierarchy
from domain.value_objects.sections import DIRECTIVES_CHILD_IDS, REQUIRED_SECTION_IDS, Section
from domain.value_objects.version_strategy import VersionStrategy
from domain.value_objects.writing_principles import WritingPrinciple


class PolicyDoctrine(BaseModel):
    """Aggregate root mirroring the policy_doctrine.yaml document structure."""

    model_config = VO_CONFIG

    doctrine: Doctrine = Field(description="Doctrine identity and version matrix")
    cross_layer_binding: CrossLayerBinding = Field(description="Layer relationship constraints")
    identity_resolution: IdentityResolution = Field(description="Identity mapping policy")
    lifecycle_definition: LifecycleDefinition = Field(description="Lifecycle operation governance")
    contamination_guard: ContaminationGuard = Field(description="Policy-layer field constraints")
    writing_principles: tuple[WritingPrinciple, ...] = Field(
        min_length=1,
        description="Authoring principles",
    )
    priority_hierarchy: PriorityHierarchy = Field(
        description="Authority levels and conflict-resolution intent"
    )
    version_strategy: VersionStrategy = Field(description="Versioning intent")
    sections: tuple[Section, ...] = Field(
        min_length=1,
        description="Universal document section definitions",
    )

    @model_validator(mode="after")
    def _validate_aggregate(self) -> Self:
        """Enforce cross-field invariants across doctrine sections."""
        if not self.doctrine.version.is_compatible(self.doctrine.spec_version):
            raise ValueError(
                f"MAJOR version mismatch: doctrine={self.doctrine.version} "
                f"vs spec={self.doctrine.spec_version}"
            )
        if not self.doctrine.version.is_compatible(self.doctrine.schema_version):
            raise ValueError(
                f"MAJOR version mismatch: doctrine={self.doctrine.version} "
                f"vs schema={self.doctrine.schema_version}"
            )

        principle_ids = [str(principle.id) for principle in self.writing_principles]
        if len(principle_ids) != len(set(principle_ids)):
            dupes = {item for item in principle_ids if principle_ids.count(item) > 1}
            raise ValueError(f"Duplicate IDs found: {dupes}")

        present = {str(section.id) for section in self.sections}
        missing = REQUIRED_SECTION_IDS - present
        if missing:
            raise ValueError(f"Missing required sections: {sorted(missing)}")

        nested_ids = [str(node.id) for section in self.sections for node in section.traverse()]
        if len(nested_ids) != len(set(nested_ids)):
            dupes = {item for item in nested_ids if nested_ids.count(item) > 1}
            raise ValueError(f"Duplicate section ID found: {dupes}")

        directives = self.get_sections("directives")
        if directives is not None and directives.children:
            child_ids = {str(child.id) for child in directives.children}
            missing_children = DIRECTIVES_CHILD_IDS - child_ids
            if missing_children:
                raise ValueError(
                    f"Directives section missing expected children: {sorted(missing_children)}"
                )
        return self

    def is_compatible_with(
        self,
        spec_version: SemanticVersion,
        schema_version: SemanticVersion,
    ) -> bool:
        """Return True when this doctrine is MAJOR-compatible with both artifacts."""
        return self.doctrine.is_compatible_with(spec_version, schema_version)

    def prohibited_fields_contains(self, field: str | ProhibitedField) -> bool:
        """Return True when ``field`` is listed in ``contamination_guard.prohibited_fields``."""
        return self.contamination_guard.prohibited_fields_contains(field)

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

    def get_lifecycle_definition(self, operation: IdentityOperation) -> str:
        """Return the ``lifecycle_definition`` text for an identity operation."""
        return getattr(self.lifecycle_definition, operation.value)