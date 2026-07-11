

--- SOURCE: src/domain/__init__.py ---

from domain.doctrine import PolicyDoctrine
from domain.enums import ContentType, IdentityOperation, PriorityCategory, ProhibitedField
from domain.identifiers import (
    Guidance,
    MachineId,
    SectionId,
    SemanticVersion,
    WritingPrincipleId,
)

__all__ = [
    "ContentType",
    "Guidance",
    "IdentityOperation",
    "MachineId",
    "PolicyDoctrine",
    "PriorityCategory",
    "ProhibitedField",
    "SemanticVersion",
    "SectionId",
    "WritingPrincipleId",
]



--- SOURCE: src/domain/doctrine.py ---

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.enums import PriorityCategory
from domain.identifiers import SectionId, SemanticVersion, WritingPrincipleId
from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import CrossLayerBinding
from domain.value_objects.document_section import DocumentSection
from domain.value_objects.identity_lifecycle import IdentityLifecycleIntent
from domain.value_objects.identity_resolution import IdentityResolution
from domain.value_objects.priority_hierarchy import PriorityHierarchy, PriorityLevel
from domain.value_objects.versioning_strategy import VersioningStrategy
from domain.value_objects.writing_principle import WritingPrinciple

MAX_SECTION_DEPTH = 3

REQUIRED_SECTION_IDS = frozenset(
    {
        "preamble",
        "governance",
        "definitions",
        "principles",
        "directives",
        "sanctions",
    }
)


class PolicyDoctrine(BaseModel):
    """Aggregate root representing the complete governance doctrine.

    Owns all governance metadata, identity policies, writing principles,
    priority hierarchy, document structure, and versioning strategy.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(description="Unique doctrine identifier")
    version: SemanticVersion = Field(description="Doctrine version")
    description: str = Field(description="Human-readable purpose statement")
    spec_version: SemanticVersion = Field(description="Compatible specification version")
    rule_contract_version: SemanticVersion = Field(description="Compatible rule schema version")
    rule_contract_id: str = Field(description="Identifier of the compatible rule schema")

    cross_layer_binding: CrossLayerBinding = Field(description="Layer relationship constraints")
    identity_resolution: IdentityResolution = Field(description="Identity mapping policy")
    identity_lifecycle: IdentityLifecycleIntent = Field(description="Lifecycle operation governance")
    contamination_guard: ContaminationGuard = Field(description="Policy-layer field constraints")
    writing_principles: tuple[WritingPrinciple, ...] = Field(description="Authoring principles")
    priority_hierarchy: PriorityHierarchy = Field(description="Authority levels and conflict resolution")
    versioning_strategy: VersioningStrategy = Field(description="Versioning intent")
    sections: tuple[DocumentSection, ...] = Field(description="Universal document section definitions")

    @model_validator(mode="after")
    def check_no_duplicate_sections(self) -> "PolicyDoctrine":
        ids = [s.id for s in self.sections]
        if len(ids) != len(set(ids)):
            duplicates = {sid for sid in ids if ids.count(sid) > 1}
            raise ValueError(f"Duplicate section IDs: {duplicates}")
        return self

    @model_validator(mode="after")
    def check_required_sections_present(self) -> "PolicyDoctrine":
        present = {s.id for s in self.sections}
        missing = REQUIRED_SECTION_IDS - present
        if missing:
            raise ValueError(f"Missing required sections: {missing}")
        return self

    @model_validator(mode="after")
    def check_priority_level_ordering(self) -> "PolicyDoctrine":
        levels = sorted(self.priority_hierarchy.levels, key=lambda pl: pl.level)
        for i, level in enumerate(levels, start=1):
            if level.level != i:
                raise ValueError(f"Priority level {level.id} has level={level.level}, expected {i}")
        return self

    @model_validator(mode="after")
    def check_section_depth(self) -> "PolicyDoctrine":

        def _max_depth(section: DocumentSection, current: int = 1) -> int:
            if not section.children:
                return current
            return max(_max_depth(child, current + 1) for child in section.children)

        for section in self.sections:
            depth = _max_depth(section)
            if depth > MAX_SECTION_DEPTH:
                raise ValueError(f"Section '{section.id}' has depth {depth}, exceeds maximum {MAX_SECTION_DEPTH}")
        return self

    def get_section(self, section_id: SectionId) -> Optional[DocumentSection]:
        """Retrieve a document section by its identifier."""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None

    def get_writing_principle(self, principle_id: WritingPrincipleId) -> Optional[WritingPrinciple]:
        """Retrieve a writing principle by its identifier."""
        for principle in self.writing_principles:
            if principle.id == principle_id:
                return principle
        return None

    def get_priority_level(self, category: PriorityCategory) -> Optional[PriorityLevel]:
        """Retrieve a priority level by its category."""
        for level in self.priority_hierarchy.levels:
            if level.id == category:
                return level
        return None



--- SOURCE: src/domain/enums.py ---

from enum import StrEnum


class ContentType(StrEnum):
    """Content formats permitted in document sections."""

    PROSE = "prose"
    TABLE = "table"
    PROSE_OR_TABLE = "prose_or_table"
    MIXED = "mixed"


class IdentityOperation(StrEnum):
    """Lifecycle operations for rule lineage identity."""

    REVISION = "revision"
    FORK = "fork"
    MERGE = "merge"
    SPLIT = "split"
    RENAME = "rename"
    RETIRE = "retire"


class PriorityCategory(StrEnum):
    """Authority levels in the governance priority hierarchy."""

    CONSTITUTIONAL = "constitutional"
    STATUTORY = "statutory"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    ADVISORY = "advisory"


class ProhibitedField(StrEnum):
    """Schema fields that must never appear in policy prose."""

    PARAMETERS = "parameters"
    CONDITIONS = "conditions"
    EVALUATOR_HINT = "evaluator_hint"
    EVALUATOR_TYPE = "evaluator_type"
    EVALUATOR_CONFIG = "evaluator_config"
    WEIGHT = "weight"
    DEPENDS_ON = "depends_on"
    CONFLICTS_WITH = "conflicts_with"
    STATUS = "status"
    CREATED_AT = "created_at"
    EXPIRES_AT = "expires_at"
    REMEDIATION = "remediation"
    TARGET = "target"
    LINEAGE = "lineage"



--- SOURCE: src/domain/identifiers.py ---

from typing import Annotated

from pydantic import Field

MachineId = Annotated[
    str,
    Field(
        pattern=r"^[A-Z][A-Z0-9]+-[0-9]+$",
        description="Immutable lineage identifier assigned at directive authoring time",
    ),
]

WritingPrincipleId = Annotated[
    str,
    Field(pattern=r"^WP-\d{3}$", description="Unique writing principle identifier"),
]

SemanticVersion = Annotated[
    str,
    Field(pattern=r"^\d+\.\d+\.\d+$", description="Semantic version in MAJOR.MINOR.PATCH format"),
]

SectionId = Annotated[
    str,
    Field(pattern=r"^[a-z][a-z0-9_]*$", description="Unique document section identifier"),
]

Guidance = Annotated[
    str,
    Field(description="Governance guidance or policy prose"),
]

Description = Annotated[
    str,
    Field(description="Human-readable description"),
]



--- SOURCE: src/domain/value_objects/__init__.py ---

from domain.value_objects.contamination_guard import ContaminationGuard
from domain.value_objects.cross_layer_binding import CrossLayerBinding
from domain.value_objects.document_section import DocumentSection
from domain.value_objects.identity_lifecycle import IdentityLifecycleIntent
from domain.value_objects.identity_resolution import IdentityResolution
from domain.value_objects.priority_hierarchy import PriorityHierarchy
from domain.value_objects.versioning_strategy import VersioningStrategy
from domain.value_objects.writing_principle import WritingPrinciple

__all__ = [
    "ContaminationGuard",
    "CrossLayerBinding",
    "DocumentSection",
    "IdentityLifecycleIntent",
    "IdentityResolution",
    "PriorityHierarchy",
    "VersioningStrategy",
    "WritingPrinciple",
]



--- SOURCE: src/domain/value_objects/contamination_guard.py ---

from pydantic import BaseModel, ConfigDict, Field

from domain.enums import ProhibitedField
from domain.identifiers import Guidance


class ContaminationGuard(BaseModel):
    """Defines what is prohibited and allowed in the policy layer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prohibited_fields: frozenset[ProhibitedField] = Field(
        description="Schema fields that must not appear in policy prose"
    )
    allowed_machine_references: tuple[Guidance, ...] = Field(description="How Machine IDs may appear in policy")
    metadata_note: Guidance = Field(description="Constraints on schema metadata in policy")



--- SOURCE: src/domain/value_objects/cross_layer_binding.py ---

from pydantic import BaseModel, ConfigDict, Field

from domain.identifiers import Guidance


class ConflictResolutionBinding(BaseModel):
    """Describes how each layer contributes to conflict resolution."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    policy: Guidance = Field(description="Policy layer's role in conflict resolution")
    schema_layer: Guidance = Field(alias="schema", description="Schema layer's role in conflict resolution")
    spec: Guidance = Field(description="Specification layer's role in conflict resolution")
    precedence: Guidance = Field(description="Declared precedence chain")


class FieldLegality(BaseModel):
    """Defines what each layer may contain."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_layer: Guidance = Field(description="What the policy layer may contain")
    schema_layer: Guidance = Field(description="What the schema layer may contain")
    spec_layer: Guidance = Field(description="What the specification layer may contain")


class CrossLayerBinding(BaseModel):
    """Describes the structural relationship between policy, schema, and specification layers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    normative_source: str = Field(description="The authoritative behavioral source")
    this_layer_purpose: Guidance = Field(description="Purpose of the policy layer")
    schema_layer_purpose: Guidance = Field(description="Purpose of the schema layer")
    enforcement: Guidance = Field(description="How governance intent is enforced")
    conflict_resolution_binding: ConflictResolutionBinding = Field(
        description="How each layer contributes to conflict resolution"
    )
    runtime_prohibition: Guidance = Field(description="What this file must not do at runtime")
    field_legality: FieldLegality = Field(description="What each layer may contain")



--- SOURCE: src/domain/value_objects/document_section.py ---

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from domain.enums import ContentType
from domain.identifiers import Guidance, SectionId


class DocumentSection(BaseModel):
    """A structural section defining the composition of a governance document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: SectionId = Field(description="Unique section identifier")
    title: str = Field(description="Human-readable section title")
    required: bool = Field(description="Whether this section must be present")
    content_type: ContentType = Field(description="Expected content format")
    guidance: Guidance = Field(description="Authoring guidance for this section")
    columns: Optional[tuple[str, ...]] = Field(default=None, description="Table column headers")
    children: Optional[tuple["DocumentSection", ...]] = Field(default=None, description="Subsections")
    schema_encoding: Optional[str] = Field(default=None, description="Schema encoding instructions")



--- SOURCE: src/domain/value_objects/identity_lifecycle.py ---

from pydantic import BaseModel, ConfigDict, Field

from domain.identifiers import Guidance


class IdentityLifecycleIntent(BaseModel):
    """Describes when to use each identity lifecycle operation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    revision: Guidance = Field(description="When to use revision")
    fork: Guidance = Field(description="When to use fork")
    merge: Guidance = Field(description="When to use merge")
    split: Guidance = Field(description="When to use split")
    rename: Guidance = Field(description="When to use rename")
    retire: Guidance = Field(description="When to use retire")
    dag_intent: Guidance = Field(description="Constraint on lineage ancestry graph structure")



--- SOURCE: src/domain/value_objects/identity_resolution.py ---

from pydantic import BaseModel, ConfigDict, Field

from domain.identifiers import Guidance


class MachineIdSemantics(BaseModel):
    """Defines the semantics of the Machine ID concept."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    definition: Guidance = Field(description="What Machine ID represents")
    exclusions: tuple[Guidance, ...] = Field(alias="not", description="What Machine ID is not")
    assignment: Guidance = Field(description="How Machine ID is assigned")
    governance_intent: Guidance = Field(description="Why Machine ID matters for governance")


class IdentityResolution(BaseModel):
    """Describes how identities map across policy, schema, and specification layers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    canonical_field: str = Field(description="The canonical identity field name")
    policy_location: str = Field(description="Where identity appears in policy")
    schema_lineage_location: str = Field(description="Where lineage ID appears in schema")
    schema_execution_location: str = Field(description="Where execution ID appears in schema")
    spec_lineage_location: str = Field(description="Where lineage ID appears in spec")
    spec_execution_location: str = Field(description="Where execution ID appears in spec")
    rule: Guidance = Field(description="Identity mapping rule")
    machine_id_semantics: MachineIdSemantics = Field(description="Detailed semantics of Machine ID")
    uniqueness: Guidance = Field(description="Uniqueness constraint for lineage IDs")
    lifecycle: Guidance = Field(description="Reference to identity lifecycle operations")



--- SOURCE: src/domain/value_objects/priority_hierarchy.py ---

from pydantic import BaseModel, ConfigDict, Field

from domain.enums import PriorityCategory
from domain.identifiers import Description, Guidance


class PriorityLevel(BaseModel):
    """An authority level in the governance priority hierarchy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: PriorityCategory = Field(description="Unique level identifier")
    level: int = Field(description="Numeric authority rank (1 = highest)")
    title: str = Field(description="Human-readable level name")
    description: Description = Field(description="Scope and authority of this level")
    examples: tuple[Description, ...] = Field(description="Typical rules at this authority level")


class CrossLayerPrecedence(BaseModel):
    """Describes how conflict resolution maps across layers."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    normative_algorithm: str = Field(description="Where the algorithm lives")
    structural_override: str = Field(description="Schema-level override mechanism")
    policy_role: Guidance = Field(description="Policy layer's role")
    order: Guidance = Field(description="Precedence chain order")


class PriorityHierarchy(BaseModel):
    """Declares the authority levels and conflict resolution intent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    description: Guidance = Field(description="How priority hierarchy works")
    levels: tuple[PriorityLevel, ...] = Field(description="Ordered authority levels")
    conflict_resolution_intent: Guidance = Field(description="Governance intent for conflict resolution")
    cross_layer_precedence: CrossLayerPrecedence = Field(description="How precedence maps across layers")



--- SOURCE: src/domain/value_objects/versioning_strategy.py ---

from pydantic import BaseModel, ConfigDict, Field

from domain.identifiers import Guidance


class VersionIntent(BaseModel):
    """Describes when to increment each version component."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    major: Guidance = Field(description="When to increment MAJOR version")
    minor: Guidance = Field(description="When to increment MINOR version")
    patch: Guidance = Field(description="When to increment PATCH version")


class VersioningStrategy(BaseModel):
    """Describes versioning intent for doctrine, schema, and specification documents."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version_format: str = Field(description="Version format pattern")
    intent: VersionIntent = Field(description="Version increment intent")
    migration_intent: Guidance = Field(description="Migration rules when crossing MAJOR boundaries")
    synchronization_intent: Guidance = Field(description="How versions synchronize across documents")



--- SOURCE: src/domain/value_objects/writing_principle.py ---

from pydantic import BaseModel, ConfigDict, Field

from domain.identifiers import Description, WritingPrincipleId


class WritingPrinciple(BaseModel):
    """A governance principle that guides rule authors in writing directives."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: WritingPrincipleId = Field(description="Unique principle identifier")
    title: str = Field(description="Short principle name")
    description: Description = Field(description="Detailed guidance for applying this principle")

