from __future__ import annotations

import re
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from domain.enums import (
    ContentType,
    IdentityOperation,
    MachineField,
    PriorityCategory,
    ResolutionStrategy,
)
from domain.identifiers import SectionId, WritingPrincipleId


# ═══════════════════════════════════════════════════════════════════════════════
# BASE
# ═══════════════════════════════════════════════════════════════════════════════


class DomainModel(BaseModel):
    """Base for all domain objects. Immutable, strict validation, no extra fields."""

    model_config = ConfigDict(frozen=True, extra="forbid")


# ═══════════════════════════════════════════════════════════════════════════════
# SCALAR VALUE OBJECTS
# ═══════════════════════════════════════════════════════════════════════════════


class SemanticVersion(DomainModel):
    """Semantic version with structured components, parsing, and compatibility logic."""

    major: int = Field(ge=0, description="Breaking changes that require migration")
    minor: int = Field(ge=0, description="New backward-compatible features")
    patch: int = Field(ge=0, description="Bug fixes and clarifications")

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Parse a semantic version from its string representation."""
        if not value:
            raise ValueError("Semantic version must be a non-empty string")
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", value)
        if not match:
            raise ValueError(f"Invalid semantic version format: {value!r}. Expected MAJOR.MINOR.PATCH")
        return cls(major=int(match[1]), minor=int(match[2]), patch=int(match[3]))

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def is_compatible_with(self, other: SemanticVersion) -> bool:
        """Check if two versions share the same MAJOR version."""
        return self.major == other.major


class MachineId(DomainModel):
    """Immutable lineage identifier assigned at directive authoring time."""

    prefix: str = Field(pattern=r"^[A-Z][A-Z0-9]+$", description="Namespace prefix (e.g., WP, AUTH, PAY)")
    number: int = Field(ge=0, description="Sequential number within the namespace")

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Parse a Machine ID from its string representation."""
        if not value:
            raise ValueError("Machine ID must be a non-empty string")
        match = re.fullmatch(r"([A-Z][A-Z0-9]+)-([0-9]+)", value)
        if not match:
            raise ValueError(f"Invalid Machine ID format: {value!r}. Expected PREFIX-NUMBER (e.g., AUTH-001)")
        return cls(prefix=match[1], number=int(match[2]))

    def __str__(self) -> str:
        return f"{self.prefix}-{self.number}"


# ═══════════════════════════════════════════════════════════════════════════════
# SHARED DOMAIN CONCEPTS
# ═══════════════════════════════════════════════════════════════════════════════


class ResolutionPrecedence(DomainModel):
    """Ordered chain of conflict resolution strategies.

    Eliminates duplication between CrossLayerBinding and PriorityHierarchy.
    """

    strategies: tuple[ResolutionStrategy, ...] = Field(
        min_length=1, description="Ordered resolution strategies from highest to lowest precedence"
    )

    @classmethod
    def default(cls) -> Self:
        """The canonical precedence chain defined by the governance doctrine."""
        return cls(
            strategies=(
                ResolutionStrategy.EXPLICIT_OVERRIDE,
                ResolutionStrategy.COMPATIBLE_OVERRIDES,
                ResolutionStrategy.PRIORITY,
                ResolutionStrategy.SPECIFICITY,
                ResolutionStrategy.RECENCY,
                ResolutionStrategy.CONFLICT_ARTIFACT,
            )
        )

    @model_validator(mode="after")
    def validate_no_duplicates(self) -> Self:
        seen: set[ResolutionStrategy] = set()
        for strategy in self.strategies:
            if strategy in seen:
                raise ValueError(f"Duplicate resolution strategy: {strategy}")
            seen.add(strategy)
        return self


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENT STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════


class DocumentSection(DomainModel):
    """A structural section defining the composition of a governance document."""

    id: SectionId
    title: str = Field(min_length=1, description="Human-readable section title")
    required: bool = Field(description="Whether this section must be present")
    content_type: ContentType = Field(description="Expected content format")
    guidance: str = Field(min_length=1, description="Authoring guidance for this section")
    columns: tuple[str, ...] | None = Field(default=None, description="Column headers for table sections")
    children: tuple[DocumentSection, ...] | None = Field(default=None, description="Subsections for mixed content")

    @model_validator(mode="after")
    def validate_structure(self) -> Self:
        """Enforce structural rules based on content type."""
        if self.content_type == ContentType.TABLE:
            if not self.columns or len(self.columns) == 0:
                raise ValueError(f"Table section '{self.id}' must define columns")
        elif self.columns is not None:
            raise ValueError(f"Non-table section '{self.id}' cannot define columns")

        if self.content_type == ContentType.MIXED:
            if not self.children or len(self.children) == 0:
                raise ValueError(f"Mixed section '{self.id}' must have children")
        elif self.children is not None:
            raise ValueError(f"Non-mixed section '{self.id}' cannot have children")

        return self


class DocumentStructure(DomainModel):
    """The complete tree of document sections with structural invariants."""

    sections: tuple[DocumentSection, ...] = Field(min_length=1, description="Root-level document sections")

    REQUIRED_SECTION_IDS: frozenset[str] = frozenset(
        {
            "preamble",
            "governance",
            "definitions",
            "principles",
            "directives",
            "sanctions",
        }
    )
    MAX_DEPTH: int = 3

    @model_validator(mode="after")
    def validate_tree(self) -> Self:
        """Enforce document structural invariants."""
        root_ids = [s.id for s in self.sections]

        if len(root_ids) != len(set(root_ids)):
            duplicates = {sid for sid in root_ids if root_ids.count(sid) > 1}
            raise ValueError(f"Duplicate root section IDs: {duplicates}")

        missing = self.REQUIRED_SECTION_IDS - set(root_ids)
        if missing:
            raise ValueError(f"Missing required sections: {missing}")

        for section in self.sections:
            depth = self._compute_depth(section)
            if depth > self.MAX_DEPTH:
                raise ValueError(f"Section '{section.id}' has depth {depth}, exceeds maximum {self.MAX_DEPTH}")

        return self

    @staticmethod
    def _compute_depth(section: DocumentSection, current: int = 1) -> int:
        if not section.children:
            return current
        return max(DocumentStructure._compute_depth(child, current + 1) for child in section.children)

    def find_section(self, section_id: SectionId) -> DocumentSection | None:
        """Retrieve a section by ID from anywhere in the tree."""
        for section in self.sections:
            if found := self._find_in_tree(section, section_id):
                return found
        return None

    @staticmethod
    def _find_in_tree(section: DocumentSection, section_id: SectionId) -> DocumentSection | None:
        if section.id == section_id:
            return section
        if section.children:
            for child in section.children:
                if found := DocumentStructure._find_in_tree(child, section_id):
                    return found
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# GOVERNANCE PRINCIPLES
# ═══════════════════════════════════════════════════════════════════════════════


class WritingPrinciple(DomainModel):
    """A governance principle that guides rule authors in writing directives."""

    id: WritingPrincipleId
    title: str = Field(min_length=1, description="Short principle name")
    description: str = Field(min_length=1, description="Detailed guidance")


class WritingPrinciples(DomainModel):
    """Collection of writing principles with uniqueness guarantees and lookup."""

    principles: tuple[WritingPrinciple, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_ids(self) -> Self:
        ids = [p.id for p in self.principles]
        if len(ids) != len(set(ids)):
            duplicates = {pid for pid in ids if ids.count(pid) > 1}
            raise ValueError(f"Duplicate writing principle IDs: {duplicates}")
        return self

    def get(self, principle_id: WritingPrincipleId) -> WritingPrinciple | None:
        for principle in self.principles:
            if principle.id == principle_id:
                return principle
        return None

    def __iter__(self):  # type: ignore[override]
        return iter(self.principles)

    def __len__(self) -> int:
        return len(self.principles)


# ═══════════════════════════════════════════════════════════════════════════════
# PRIORITY HIERARCHY
# ═══════════════════════════════════════════════════════════════════════════════


class PriorityLevel(DomainModel):
    """An authority level in the governance priority hierarchy."""

    category: PriorityCategory = Field(description="Unique level identifier")
    rank: int = Field(ge=1, description="Numeric authority rank (1 = highest)")
    title: str = Field(min_length=1, description="Human-readable level name")
    description: str = Field(min_length=1, description="Scope and authority")
    examples: tuple[str, ...] = Field(min_length=1, description="Typical rules")


class PriorityHierarchy(DomainModel):
    """Declares authority levels and conflict resolution intent."""

    description: str = Field(min_length=1, description="How priority hierarchy works")
    levels: tuple[PriorityLevel, ...] = Field(min_length=1, description="Ordered levels")
    conflict_resolution_intent: str = Field(min_length=1, description="Governance intent for conflict resolution")
    cross_layer_precedence: ResolutionPrecedence = Field(description="How precedence maps across layers")

    @model_validator(mode="after")
    def validate_levels(self) -> Self:
        """Enforce sequential ranks and unique categories."""
        sorted_levels = sorted(self.levels, key=lambda pl: pl.rank)

        for i, level in enumerate(sorted_levels, start=1):
            if level.rank != i:
                raise ValueError(f"Priority level '{level.category}' has rank {level.rank}, expected {i}")

        categories = [l.category for l in self.levels]
        if len(categories) != len(set(categories)):
            duplicates = {c for c in categories if categories.count(c) > 1}
            raise ValueError(f"Duplicate priority categories: {duplicates}")

        return self

    def get_level(self, category: PriorityCategory) -> PriorityLevel | None:
        for level in self.levels:
            if level.category == category:
                return level
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# IDENTITY POLICY
# ═══════════════════════════════════════════════════════════════════════════════


class LifecycleOperation(DomainModel):
    """A single identity lifecycle operation with its governance guidance."""

    operation: IdentityOperation
    guidance: str = Field(min_length=1, description="When to use this operation")


class IdentityLifecycleIntent(DomainModel):
    """Governance intent for identity lifecycle operations.

    Uses a collection rather than fixed fields for extensibility (OCP).
    """

    operations: tuple[LifecycleOperation, ...] = Field(min_length=1)
    dag_intent: str = Field(min_length=1, description="Constraint on lineage ancestry graph")

    @model_validator(mode="after")
    def validate_completeness_and_uniqueness(self) -> Self:
        present = {op.operation for op in self.operations}
        required = set(IdentityOperation)

        missing = required - present
        if missing:
            raise ValueError(f"Missing lifecycle operations: {missing}")

        if len(present) != len(self.operations):
            raise ValueError("Duplicate lifecycle operations")

        return self

    def get_guidance(self, operation: IdentityOperation) -> str | None:
        for op in self.operations:
            if op.operation == operation:
                return op.guidance
        return None


class MachineIdSemantics(DomainModel):
    """Defines the semantics of the Machine ID concept."""

    definition: str = Field(min_length=1, description="What Machine ID represents")
    exclusions: tuple[str, ...] = Field(min_length=1, description="What Machine ID is not")
    assignment: str = Field(min_length=1, description="How Machine ID is assigned")
    governance_intent: str = Field(min_length=1, description="Why Machine ID matters")


class IdentityMapping(DomainModel):
    """Identity field locations across policy, schema, and specification layers."""

    canonical_field: str = Field(min_length=1)
    policy_location: str = Field(min_length=1)
    schema_lineage_location: str = Field(min_length=1)
    schema_execution_location: str = Field(min_length=1)
    spec_lineage_location: str = Field(min_length=1)
    spec_execution_location: str = Field(min_length=1)


class IdentityResolution(DomainModel):
    """Describes how identities map across layers."""

    mapping: IdentityMapping
    rule: str = Field(min_length=1, description="Identity mapping rule")
    machine_id_semantics: MachineIdSemantics
    uniqueness: str = Field(min_length=1, description="Uniqueness constraint")
    lifecycle: str = Field(min_length=1, description="Reference to lifecycle operations")


# ═══════════════════════════════════════════════════════════════════════════════
# CONTAMINATION GUARD
# ═══════════════════════════════════════════════════════════════════════════════


class ContaminationGuard(DomainModel):
    """Defines separation between governance intent and executable logic."""

    prohibited_fields: frozenset[MachineField] = Field(
        description="Executable fields that must not appear in policy prose"
    )
    allowed_machine_references: tuple[str, ...] = Field(
        min_length=1, description="How Machine IDs may appear in policy"
    )
    metadata_note: str = Field(min_length=1, description="Constraints on schema metadata")


# ═══════════════════════════════════════════════════════════════════════════════
# CROSS-LAYER BINDING
# ═══════════════════════════════════════════════════════════════════════════════


class ConflictResolutionBinding(DomainModel):
    """Describes how each layer contributes to conflict resolution."""

    policy_role: str = Field(min_length=1, description="Policy layer's role")
    schema_role: str = Field(min_length=1, description="Schema layer's role")
    spec_role: str = Field(min_length=1, description="Specification layer's role")
    precedence: ResolutionPrecedence = Field(description="Resolution precedence chain")


class FieldLegality(DomainModel):
    """Defines what each layer may contain."""

    policy_layer: str = Field(min_length=1)
    schema_layer: str = Field(min_length=1)
    spec_layer: str = Field(min_length=1)


class CrossLayerBinding(DomainModel):
    """Describes the structural relationship between policy, schema, and specification layers."""

    normative_source: str = Field(min_length=1, description="Authoritative behavioral source")
    policy_layer_purpose: str = Field(min_length=1)
    schema_layer_purpose: str = Field(min_length=1)
    enforcement: str = Field(min_length=1, description="How governance intent is enforced")
    conflict_resolution: ConflictResolutionBinding
    runtime_prohibition: str = Field(min_length=1, description="Runtime usage prohibition")
    field_legality: FieldLegality


# ═══════════════════════════════════════════════════════════════════════════════
# VERSIONING STRATEGY
# ═══════════════════════════════════════════════════════════════════════════════


class VersionComponentIntent(DomainModel):
    """Describes when to increment each version component."""

    major: str = Field(min_length=1)
    minor: str = Field(min_length=1)
    patch: str = Field(min_length=1)


class VersioningStrategy(DomainModel):
    """Describes versioning intent for doctrine, schema, and specification."""

    format: str = Field(pattern=r"^MAJOR\.MINOR\.PATCH$", description="Version format")
    intent: VersionComponentIntent
    migration_intent: str = Field(min_length=1)
    synchronization_intent: str = Field(min_length=1)


# ═══════════════════════════════════════════════════════════════════════════════
# DOCTRINE METADATA
# ═══════════════════════════════════════════════════════════════════════════════


class DoctrineMetadata(DomainModel):
    """Core metadata identifying the doctrine and its cross-document compatibility."""

    name: str = Field(min_length=1, description="Unique doctrine identifier")
    version: SemanticVersion
    description: str = Field(min_length=1, description="Human-readable purpose")
    spec_version: SemanticVersion = Field(description="Compatible specification version")
    rule_contract_version: SemanticVersion = Field(description="Compatible rule schema version")
    rule_contract_id: str = Field(min_length=1, description="Compatible rule schema identifier")

    @model_validator(mode="after")
    def validate_version_compatibility(self) -> Self:
        """All three versions must share the same MAJOR version."""
        if not self.version.is_compatible_with(self.spec_version):
            raise ValueError(
                f"Doctrine version {self.version} and spec version {self.spec_version} "
                "must share the same MAJOR version"
            )
        if not self.version.is_compatible_with(self.rule_contract_version):
            raise ValueError(
                f"Doctrine version {self.version} and rule contract version "
                f"{self.rule_contract_version} must share the same MAJOR version"
            )
        return self


# ═══════════════════════════════════════════════════════════════════════════════
# AGGREGATE ROOT
# ═══════════════════════════════════════════════════════════════════════════════


class PolicyDoctrine(DomainModel):
    """Aggregate root representing the complete governance doctrine.

    Owns all governance metadata, identity policies, writing principles,
    priority hierarchy, document structure, and versioning strategy.

    The root is intentionally lean: it delegates validation and lookup
    to its constituent value objects.
    """

    metadata: DoctrineMetadata
    cross_layer_binding: CrossLayerBinding
    identity_resolution: IdentityResolution
    identity_lifecycle: IdentityLifecycleIntent
    contamination_guard: ContaminationGuard
    writing_principles: WritingPrinciples
    priority_hierarchy: PriorityHierarchy
    versioning_strategy: VersioningStrategy
    document_structure: DocumentStructure

    @computed_field  # type: ignore[prop-decorator]
    @property
    def name(self) -> str:
        return self.metadata.name

    @computed_field  # type: ignore[prop-decorator]
    @property
    def version(self) -> SemanticVersion:
        return self.metadata.version

    def get_section(self, section_id: SectionId) -> DocumentSection | None:
        """Retrieve a document section by its identifier."""
        return self.document_structure.find_section(section_id)

    def get_writing_principle(self, principle_id: WritingPrincipleId) -> WritingPrinciple | None:
        """Retrieve a writing principle by its identifier."""
        return self.writing_principles.get(principle_id)

    def get_priority_level(self, category: PriorityCategory) -> PriorityLevel | None:
        """Retrieve a priority level by its category."""
        return self.priority_hierarchy.get_level(category)
