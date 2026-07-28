"""Pydantic v2 models for policy_doctrine.yaml.

Models the governance intent layer — reasoning, guidance, examples.
Contains NO machine-executable logic. Used by agents and humans to
reason about rule intent, not to execute evaluations.

Schema contract: schema/policy_doctrine.yaml
Normative source: SPECIFICATION.md 8.2.4
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

# ─── Policy-Specific Enums ───────────────────────────────────────────────────
# These are policy-layer enums, not core domain concepts.


class ContentType(StrEnum):
    """Content type for document sections."""

    PROSE = "prose"
    TABLE = "table"
    PROSE_OR_TABLE = "prose_or_table"
    MIXED = "mixed"


class PriorityCategory(StrEnum):
    """Priority hierarchy categories in policy documents."""

    CONSTITUTIONAL = "constitutional"
    STATUTORY = "statutory"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    ADVISORY = "advisory"


# ─── Doctrine Metadata ────────────────────────────────────────────────────────


class DoctrineMeta(BaseModel):
    """Doctrine identification and versioning."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Doctrine identifier")
    version: str = Field(description="Semantic version")
    description: str = Field(description="What this doctrine defines")
    spec_version: str = Field(description="SPECIFICATION.md version")
    schema_version: str = Field(description="rule_schema.json version")
    schema_id: str = Field(description="Schema identifier")


# ─── Cross-Layer Binding ─────────────────────────────────────────────────────


class FieldLegality(BaseModel):
    """Describes what each layer may contain."""

    model_config = ConfigDict(frozen=True)

    policy_layer: str = Field(description="Descriptive only. No executable fields.")
    schema_layer: str = Field(
        description="Executable fields only. No prose governance."
    )
    spec_layer: str = Field(description="System behavior. Defines invariants for both.")


class ConflictResolutionBinding(BaseModel):
    """How conflict resolution spans layers."""

    model_config = ConfigDict(frozen=True)

    policy_layer: str = Field(description="Policy's role in conflict resolution")
    schema_layer: str = Field(description="Schema's role in conflict resolution")
    spec_layer: str = Field(description="Spec's role in conflict resolution")
    precedence: str = Field(description="Resolution precedence chain")


class CrossLayerBinding(BaseModel):
    """Binding contract between policy, schema, and spec layers."""

    model_config = ConfigDict(frozen=True)

    normative_source: str = Field(description="The normative behavioral source")
    policy_purpose: str = Field(description="What the policy layer does")
    schema_purpose: str = Field(description="What the schema layer does")
    enforcement: str = Field(description="How governance intent is enforced")
    conflict_resolution_binding: ConflictResolutionBinding
    runtime_prohibition: str = Field(description="Runtime access prohibition")
    field_legality: FieldLegality


# ─── Identity Resolution ─────────────────────────────────────────────────────


class MachineIdSemantics(BaseModel):
    """Semantics of the Machine ID in governance context."""

    model_config = ConfigDict(frozen=True)

    definition: str = Field(description="What Machine ID is")
    exclusions: tuple[str, ...] = Field(description="What Machine ID is NOT")
    assignment: str = Field(description="When and how assigned")
    governance_intent: str = Field(description="Why Machine ID matters for governance")


class IdentityResolution(BaseModel):
    """How identity maps across layers."""

    model_config = ConfigDict(frozen=True)

    canonical_field: str = Field(description="Canonical identifier name in policy")
    policy_location: str = Field(description="Where Machine ID appears in policy")
    schema_lineage_location: str = Field(description="Schema field for lineage")
    schema_execution_location: str = Field(description="Schema field for execution ID")
    spec_lineage_location: str = Field(description="Spec field for lineage")
    spec_execution_location: str = Field(description="Spec field for execution ID")
    identity_mapping: str = Field(description="How identity maps across layers")
    machine_id_semantics: MachineIdSemantics
    uniqueness: str = Field(description="Uniqueness constraint")
    lifecycle_reference: str = Field(description="Where lifecycle is defined")


# ─── Lifecycle Definition ────────────────────────────────────────────────────


class LifecycleDefinition(BaseModel):
    """Describes WHEN to use each lifecycle operation."""

    model_config = ConfigDict(frozen=True)

    revision: str = Field(description="When to use revision")
    fork: str = Field(description="When to use fork")
    merge: str = Field(description="When to use merge")
    split: str = Field(description="When to use split")
    rename: str = Field(description="When to use rename")
    retire: str = Field(description="When to use retire")
    dag_intent: str = Field(description="DAG invariant intent")


# ─── Contamination Guard ─────────────────────────────────────────────────────


class ContaminationGuard(BaseModel):
    """Defines what MUST NOT appear in policy."""

    model_config = ConfigDict(frozen=True)

    prohibited_fields: tuple[str, ...] = Field(
        description="Fields that must not appear"
    )
    allowed_machine_references: tuple[str, ...] = Field(
        description="Permitted cross-references"
    )
    metadata_constraints: str = Field(description="Metadata usage constraints")


# ─── Writing Principles ──────────────────────────────────────────────────────


class WritingPrinciple(BaseModel):
    """A single writing principle for policy authors."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Principle identifier (e.g. WP-001)")
    title: str = Field(description="Short title")
    description: str = Field(description="What this principle requires")


# ─── Priority Hierarchy ──────────────────────────────────────────────────────


class PriorityLevelDefinition(BaseModel):
    """A single priority level in the hierarchy."""

    model_config = ConfigDict(frozen=True)

    category: PriorityCategory = Field(description="Priority category")
    rank: int = Field(description="Numeric rank (1=highest)")
    title: str = Field(description="Human-readable title")
    description: str = Field(description="What this level means")
    examples: tuple[str, ...] = Field(
        default_factory=tuple, description="Example rules"
    )


class CrossLayerPrecedence(BaseModel):
    """How precedence works across layers."""

    model_config = ConfigDict(frozen=True)

    precedence_algorithm: str = Field(description="Where the algorithm is defined")
    structural_override: str = Field(description="Schema override field")
    policy_role: str = Field(description="Policy's role in precedence")
    order: str = Field(description="Precedence order")


class PriorityHierarchy(BaseModel):
    """Declarative priority hierarchy (governance intent, not code)."""

    model_config = ConfigDict(frozen=True)

    description: str = Field(description="What priority hierarchy means")
    levels: tuple[PriorityLevelDefinition, ...] = Field(description="Priority levels")
    conflict_resolution: str = Field(description="How conflicts are resolved (intent)")
    cross_layer_precedence: CrossLayerPrecedence


# ─── Version Strategy ────────────────────────────────────────────────────────


class VersionIntent(BaseModel):
    """What each version bump means."""

    model_config = ConfigDict(frozen=True)

    major: str = Field(description="Major version meaning")
    minor: str = Field(description="Minor version meaning")
    patch: str = Field(description="Patch version meaning")


class VersionStrategy(BaseModel):
    """Declarative versioning strategy."""

    model_config = ConfigDict(frozen=True)

    description: str = Field(description="Versioning overview")
    version_format: str = Field(description="Version format string")
    intent: VersionIntent
    migration_intent: str = Field(description="Migration governance intent")
    synchronization_intent: str = Field(description="Cross-doc sync intent")


# ─── Document Sections ───────────────────────────────────────────────────────


class SectionChild(BaseModel):
    """A child section within a parent section."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Section identifier")
    title: str = Field(description="Section title")
    content_type: ContentType = Field(description="Expected content type")
    columns: tuple[str, ...] = Field(default_factory=tuple, description="Table columns")
    guidance: str = Field(default="", description="How to write this section")
    schema_encoding: str = Field(default="", description="How this maps to schema")


class DocumentSection(BaseModel):
    """A section in a policy document template."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Section identifier")
    title: str = Field(description="Section title")
    required: bool = Field(description="Whether this section is mandatory")
    content_type: ContentType = Field(description="Expected content type")
    columns: tuple[str, ...] = Field(default_factory=tuple, description="Table columns")
    guidance: str = Field(default="", description="How to write this section")
    children: tuple[SectionChild, ...] = Field(
        default_factory=tuple, description="Sub-sections"
    )


# ─── Policy Doctrine Root ────────────────────────────────────────────────────


class PolicyDoctrine(BaseModel):
    """Root model for policy_doctrine.yaml.

    The governance intent layer. Contains NO machine-executable logic.
    Used by agents and humans to reason about rule intent.
    """

    model_config = ConfigDict(frozen=True)

    doctrine: DoctrineMeta
    cross_layer_binding: CrossLayerBinding
    identity_resolution: IdentityResolution
    lifecycle_definition: LifecycleDefinition
    contamination_guard: ContaminationGuard
    writing_principles: tuple[WritingPrinciple, ...]
    priority_hierarchy: PriorityHierarchy
    version_strategy: VersionStrategy
    sections: tuple[DocumentSection, ...] = Field(
        description="Universal document section template"
    )


# ─── Directive Policy (per-rule governance document) ─────────────────────────


class DirectiveTerm(BaseModel):
    """A defined term in a directive policy."""

    model_config = ConfigDict(frozen=True)

    term: str = Field(description="The term being defined")
    definition: str = Field(description="What it IS")
    exclusion: str = Field(description="What it IS NOT")


class Principle(BaseModel):
    """A foundational principle referenced by a directive."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Principle identifier (e.g. P1)")
    title: str = Field(description="Short title")
    description: str = Field(description="What this principle requires")


class SpecificDirective(BaseModel):
    """A specific directive entry in a policy document."""

    model_config = ConfigDict(frozen=True)

    type: str = Field(
        description="Deontic classification (e.g. 'Obligation', 'Prohibition')"
    )
    description: str = Field(description="What the directive requires")
    machine_id: str = Field(description="Cross-reference to rule.lineage_id")
    context_conditions: str = Field(default="", description="When this applies")
    title: str = Field(default="", description="Short title")


class SanctionRow(BaseModel):
    """A row in the sanctions table."""

    model_config = ConfigDict(frozen=True)

    violation_context: str = Field(description="What constitutes a violation")
    enforcement_action: str = Field(description="How it's enforced")
    remediation_path: str = Field(description="How to fix it")


class DirectiveCatalogEntry(BaseModel):
    """An entry in the directive catalog index."""

    model_config = ConfigDict(frozen=True)

    machine_id: str = Field(description="Machine ID (cross-reference)")
    title: str = Field(description="Short title")
    policy_file: str = Field(default="", description="Path to policy YAML")
    rule_file: str = Field(default="", description="Path to rule JSON")


class Preamble(BaseModel):
    """Preamble section of a directive policy."""

    model_config = ConfigDict(frozen=True, extra="allow")

    title: str = Field(default="Preamble")
    purpose: str = Field(default="", description="Why this directive exists")
    scope: str = Field(default="", description="What this directive covers")
    existential_need: str = Field(default="", description="The problem this solves")


class Governance(BaseModel):
    """Governance section of a directive policy."""

    model_config = ConfigDict(frozen=True, extra="allow")

    title: str = Field(default="Governance & Amendment")
    authority: str = Field(default="", description="Who governs this directive")
    amendment_process: tuple[str, ...] = Field(default_factory=tuple)
    versioning: str = Field(default="")
    identity: dict[str, Any] = Field(default_factory=dict)


class Definitions(BaseModel):
    """Definitions section of a directive policy."""

    model_config = ConfigDict(frozen=True, extra="allow")

    title: str = Field(default="Definitions")
    terms: tuple[DirectiveTerm, ...] = Field(default_factory=tuple)


class Principles(BaseModel):
    """Principles section of a directive policy."""

    model_config = ConfigDict(frozen=True, extra="allow")

    title: str = Field(default="Foundational Principles")
    description: str = Field(default="")
    items: tuple[Principle, ...] = Field(default_factory=tuple)


class Directives(BaseModel):
    """Directives section of a directive policy."""

    model_config = ConfigDict(frozen=True, extra="allow")

    title: str = Field(default="Directives (Rules & Standards)")
    specific_directives: tuple[SpecificDirective, ...] = Field(default_factory=tuple)
    flexible_standards: tuple[dict[str, Any], ...] = Field(default_factory=tuple)


class Sanctions(BaseModel):
    """Sanctions section of a directive policy."""

    model_config = ConfigDict(frozen=True, extra="allow")

    title: str = Field(default="Sanctions & Remedies")
    rows: tuple[SanctionRow, ...] = Field(default_factory=tuple)


class Guidance(BaseModel):
    """Guidance section — for human/AI reasoning only."""

    model_config = ConfigDict(frozen=True, extra="allow")

    title: str = Field(default="Guidance, Examples, and Reasoning")
    purpose: str = Field(default="")
    reasoning: str = Field(default="", description="Why this rule exists (reasoning)")
    explanation: str = Field(default="", description="How to understand the examples")
    correct_example: str = Field(default="", description="Correct implementation")
    incorrect_example: str = Field(default="", description="Anti-pattern")
    related_machine_ids: tuple[str, ...] = Field(default_factory=tuple)
    exceptions: str = Field(default="", description="When this rule doesn't apply")


class References(BaseModel):
    """References section of a directive policy."""

    model_config = ConfigDict(frozen=True, extra="allow")

    title: str = Field(default="References & Annexes")
    source_doctrine: str = Field(default="")
    policy_schema: str = Field(default="")
    rule_schema: str = Field(default="")
    paired_rule: str = Field(default="")
    anchor_ref: str = Field(default="")
    related: tuple[str, ...] = Field(default_factory=tuple)


class DirectiveDoctrineMeta(BaseModel):
    """Metadata for a per-rule directive policy document."""

    model_config = ConfigDict(frozen=True, extra="allow")

    name: str = Field(description="Doctrine name")
    version: str = Field(description="Version")
    description: str = Field(description="What this doctrine covers")
    spec_version: str = Field(default="")
    schema_version: str = Field(default="")
    schema_id: str = Field(default="")
    machine_id: str = Field(
        default="", description="Cross-reference to rule.lineage_id"
    )
    paired_rule_file: str = Field(default="", description="Path to paired rule JSON")
    purpose_layer: str = Field(default="")
    runtime_prohibition: str = Field(default="")


class DirectivePolicy(BaseModel):
    """A per-rule directive policy document.

    Governance intent, guidance, examples, reasoning ONLY.
    MUST NOT be used for linting/evaluation at runtime.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    doctrine: DirectiveDoctrineMeta
    cross_layer_binding: dict[str, Any] = Field(default_factory=dict)
    contamination_guard: dict[str, Any] = Field(default_factory=dict)
    preamble: Preamble = Field(default_factory=Preamble)
    governance: Governance = Field(default_factory=Governance)
    definitions: Definitions = Field(default_factory=Definitions)
    principles: Principles = Field(default_factory=Principles)
    directives: Directives = Field(default_factory=Directives)
    sanctions: Sanctions = Field(default_factory=Sanctions)
    guidance: Guidance = Field(default_factory=Guidance)
    references: References = Field(default_factory=References)

    @property
    def machine_id(self) -> str:
        """Get the machine ID for cross-referencing."""
        return self.doctrine.machine_id

    @property
    def paired_rule_file(self) -> str:
        """Get the paired rule file path."""
        return self.doctrine.paired_rule_file
