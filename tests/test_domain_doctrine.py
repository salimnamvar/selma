"""Domain model tests aligned with policy_doctrine.yaml and audit invariants."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
from pydantic import ValidationError

from domain import (
    MAX_SECTION_DEPTH,
    REQUIRED_SECTION_IDS,
    ContentType,
    DocumentSection,
    DocumentStructure,
    FieldPath,
    IdentityOperation,
    MachineId,
    PolicyDoctrine,
    PriorityCategory,
    PriorityHierarchy,
    ProhibitedField,
    SemanticVersion,
    WritingPrinciple,
    WritingPrinciples,
)

# ── SemanticVersion ──────────────────────────────────────────────────────────


class TestSemanticVersion:
    def test_parse_string(self) -> None:
        version = SemanticVersion.from_string("8.2.4")
        assert version.major == 8
        assert version.minor == 2
        assert version.patch == 4
        assert str(version) == "8.2.4"

    def test_invalid_format(self) -> None:
        with pytest.raises(ValidationError):
            SemanticVersion.model_validate("1.2")

    def test_major_compatibility(self) -> None:
        a = SemanticVersion.from_string("8.2.4")
        b = SemanticVersion.from_string("8.0.0")
        c = SemanticVersion.from_string("9.0.0")
        assert a.is_compatible_with(b)
        assert not a.is_compatible_with(c)

    def test_ordering(self) -> None:
        assert SemanticVersion.from_string("1.0.0") < SemanticVersion.from_string("1.0.1")
        assert SemanticVersion.from_string("2.0.0") > SemanticVersion.from_string("1.9.9")


# ── Identifiers ──────────────────────────────────────────────────────────────


class TestIdentifiers:
    def test_machine_id_pattern(self) -> None:
        # Validated via FieldPath / doctrine fields; MachineId is Annotated[str].
        from pydantic import TypeAdapter

        adapter = TypeAdapter(MachineId)
        assert adapter.validate_python("AUTH-001") == "AUTH-001"
        with pytest.raises(ValidationError):
            adapter.validate_python("bad-id")

    def test_field_path_from_string(self) -> None:
        path = FieldPath.model_validate("rules[].lineage_id")
        assert path.collection == "rules"
        assert path.field == "lineage_id"
        assert str(path) == "rules[].lineage_id"

    def test_field_path_with_spaces(self) -> None:
        path = FieldPath.model_validate("CG-IR nodes[].directive_id")
        assert path.collection == "CG-IR nodes"
        assert path.field == "directive_id"


# ── Document sections ────────────────────────────────────────────────────────


class TestDocumentSection:
    def test_columns_forbidden_on_prose(self) -> None:
        with pytest.raises(ValidationError, match="columns"):
            DocumentSection(
                id="preamble",
                title="Preamble",
                content_type=ContentType.PROSE,
                columns=("A", "B"),
            )

    def test_max_depth_enforced(self) -> None:
        # Four nested levels (depth 4) exceeds MAX_SECTION_DEPTH (3).
        with pytest.raises(ValidationError, match="depth"):
            DocumentSection(
                id="a",
                title="A",
                content_type=ContentType.PROSE,
                children=(
                    DocumentSection(
                        id="b",
                        title="B",
                        content_type=ContentType.PROSE,
                        children=(
                            DocumentSection(
                                id="c",
                                title="C",
                                content_type=ContentType.PROSE,
                                children=(
                                    DocumentSection(
                                        id="d",
                                        title="D",
                                        content_type=ContentType.PROSE,
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            )

    def test_traverse_and_find(self) -> None:
        child = DocumentSection(
            id="specific_directives",
            title="Specific",
            content_type=ContentType.TABLE,
            columns=("Type", "Description"),
        )
        parent = DocumentSection(
            id="directives",
            title="Directives",
            content_type=ContentType.MIXED,
            children=(child,),
        )
        assert [s.id for s in parent.traverse()] == ["directives", "specific_directives"]
        assert parent.find("specific_directives") is child
        assert parent.find("missing") is None


class TestDocumentStructure:
    def _minimal_sections(self) -> tuple[DocumentSection, ...]:
        def prose(section_id: str, title: str) -> DocumentSection:
            return DocumentSection(
                id=section_id,
                title=title,
                content_type=ContentType.PROSE,
                guidance=f"Guidance for {title}",
            )

        return (
            prose("preamble", "Preamble"),
            prose("governance", "Governance"),
            DocumentSection(
                id="definitions",
                title="Definitions",
                content_type=ContentType.TABLE,
                columns=("Term", "Definition", "Exclusion"),
                guidance="Define terms",
            ),
            prose("principles", "Principles"),
            DocumentSection(
                id="directives",
                title="Directives",
                content_type=ContentType.MIXED,
                guidance="List obligations",
                children=(
                    DocumentSection(
                        id="specific_directives",
                        title="Specific Directives",
                        content_type=ContentType.TABLE,
                        columns=("Type", "Description", "Machine ID"),
                    ),
                    DocumentSection(
                        id="flexible_standards",
                        title="Flexible Standards",
                        content_type=ContentType.TABLE,
                        columns=("Description", "Machine ID"),
                    ),
                ),
            ),
            DocumentSection(
                id="sanctions",
                title="Sanctions",
                content_type=ContentType.TABLE,
                columns=("Violation", "Action", "Remediation"),
                guidance="Consequences",
            ),
        )

    def test_required_sections(self) -> None:
        sections = list(self._minimal_sections())
        sections = [s for s in sections if s.id != "preamble"]
        with pytest.raises(ValidationError, match="Missing required sections"):
            DocumentStructure(sections=tuple(sections))

    def test_duplicate_ids(self) -> None:
        sections = list(self._minimal_sections())
        sections.append(
            DocumentSection(
                id="preamble",
                title="Dup",
                content_type=ContentType.PROSE,
            )
        )
        with pytest.raises(ValidationError, match="Duplicate section ID"):
            DocumentStructure(sections=tuple(sections))

    def test_lookup(self) -> None:
        structure = DocumentStructure(sections=self._minimal_sections())
        assert structure.get("flexible_standards") is not None
        assert structure.get("nope") is None
        assert structure.all_section_ids() >= REQUIRED_SECTION_IDS


# ── Writing principles ───────────────────────────────────────────────────────


class TestWritingPrinciples:
    def test_unique_ids(self) -> None:
        principle = WritingPrinciple(
            id="WP-001",
            title="Precision",
            description="Use exact language",
        )
        with pytest.raises(ValidationError, match="Duplicate"):
            WritingPrinciples(principles=(principle, principle))

    def test_get(self) -> None:
        collection = WritingPrinciples(
            principles=(
                WritingPrinciple(id="WP-001", title="A", description="Alpha"),
                WritingPrinciple(id="WP-002", title="B", description="Beta"),
            )
        )
        assert collection.get("WP-001") is not None
        assert collection.get("WP-099") is None
        assert "WP-002" in collection
        assert len(collection) == 2


# ── Priority hierarchy ───────────────────────────────────────────────────────


def _full_priority_levels() -> list[dict[str, Any]]:
    titles = {
        PriorityCategory.CONSTITUTIONAL: "Constitutional",
        PriorityCategory.STATUTORY: "Statutory",
        PriorityCategory.REGULATORY: "Regulatory",
        PriorityCategory.OPERATIONAL: "Operational",
        PriorityCategory.ADVISORY: "Advisory",
    }
    return [
        {
            "id": category.value,
            "level": category.rank,
            "title": titles[category],
            "description": f"{titles[category]} rules",
            "examples": (f"Example for {category.value}",),
        }
        for category in PriorityCategory
    ]


class TestPriorityHierarchy:
    def test_complete_hierarchy(self) -> None:
        hierarchy = PriorityHierarchy.model_validate(
            {
                "description": "Authority levels",
                "levels": _full_priority_levels(),
                "conflict_resolution_intent": "Higher wins",
                "cross_layer_precedence": {
                    "normative_algorithm": "SPEC §2.15",
                    "structural_override": "conflict_resolution field",
                    "policy_role": "Declarative intent",
                    "order": "override → priority → specificity → recency",
                },
            }
        )
        assert hierarchy.get_level(PriorityCategory.CONSTITUTIONAL) is not None
        assert hierarchy.outranks(
            PriorityCategory.CONSTITUTIONAL,
            PriorityCategory.ADVISORY,
        )

    def test_missing_category_rejected(self) -> None:
        levels = _full_priority_levels()[:-1]
        with pytest.raises(ValidationError, match="missing categories"):
            PriorityHierarchy.model_validate(
                {
                    "description": "Authority levels",
                    "levels": levels,
                    "conflict_resolution_intent": "Higher wins",
                    "cross_layer_precedence": {
                        "normative_algorithm": "SPEC",
                        "structural_override": "schema",
                        "policy_role": "intent",
                        "order": "priority",
                    },
                }
            )

    def test_out_of_order_rejected(self) -> None:
        levels = _full_priority_levels()
        levels[0], levels[1] = levels[1], levels[0]
        with pytest.raises(ValidationError, match="expected"):
            PriorityHierarchy.model_validate(
                {
                    "description": "Authority levels",
                    "levels": levels,
                    "conflict_resolution_intent": "Higher wins",
                    "cross_layer_precedence": {
                        "normative_algorithm": "SPEC",
                        "structural_override": "schema",
                        "policy_role": "intent",
                        "order": "priority",
                    },
                }
            )


# ── YAML fidelity (normative document) ───────────────────────────────────────


class TestDoctrineFromYaml:
    def test_loads_normative_document(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.name == "universal-policy-doctrine"
        assert str(doctrine.version) == "8.2.4"
        assert doctrine.rule_contract_id == "universal-rule-schema"

    def test_version_compatibility(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.version.is_compatible_with(doctrine.spec_version)
        assert doctrine.version.is_compatible_with(doctrine.rule_contract_version)

    def test_cross_layer_binding_aliases(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.cross_layer_binding.policy_layer_purpose
        assert doctrine.cross_layer_binding.conflict_resolution_binding.schema_layer

    def test_conflict_resolution_binding_has_four_fields_only(self, doctrine: PolicyDoctrine) -> None:
        binding = doctrine.cross_layer_binding.conflict_resolution_binding
        data = binding.model_dump()
        assert set(data) == {"policy", "schema_layer", "spec", "precedence"}

    def test_cross_layer_precedence_on_priority_hierarchy(self, doctrine: PolicyDoctrine) -> None:
        precedence = doctrine.priority_hierarchy.cross_layer_precedence
        assert "SPECIFICATION.md" in precedence.normative_algorithm
        assert precedence.policy_role
        assert precedence.order

    def test_machine_id_exclusions_alias(self, doctrine: PolicyDoctrine) -> None:
        exclusions = doctrine.identity_resolution.machine_id_semantics.exclusions
        assert "execution ID" in exclusions
        assert "runtime lookup key" in exclusions

    def test_identity_lifecycle_uses_operations(self, doctrine: PolicyDoctrine) -> None:
        lifecycle = doctrine.identity_lifecycle
        assert lifecycle.supported_operations() == frozenset(IdentityOperation)
        assert "two distinct" in lifecycle.guidance_for(IdentityOperation.FORK).lower()
        assert "combine" in lifecycle.guidance_for(IdentityOperation.MERGE).lower()

    def test_versioning_intent_nested(self, doctrine: PolicyDoctrine) -> None:
        intent = doctrine.versioning_strategy.intent
        assert "Breaking" in intent.major or "breaking" in intent.major.lower()
        assert intent.minor
        assert intent.patch

    def test_writing_principles(self, doctrine: PolicyDoctrine) -> None:
        assert len(doctrine.writing_principles) == 5
        wp = doctrine.get_writing_principle("WP-001")
        assert wp is not None
        assert "Precision" in wp.title

    def test_sections_and_lookups(self, doctrine: PolicyDoctrine) -> None:
        assert {s.id for s in doctrine.sections} >= REQUIRED_SECTION_IDS
        directives = doctrine.get_section("directives")
        assert directives is not None
        assert doctrine.get_section("flexible_standards") is not None
        assert doctrine.get_section("specific_directives") is not None

    def test_contamination_guard(self, doctrine: PolicyDoctrine) -> None:
        guard = doctrine.contamination_guard
        assert guard.is_prohibited(ProhibitedField.PARAMETERS)
        assert guard.is_prohibited("evaluator_hint")
        assert not guard.is_prohibited("machine_id")
        assert ProhibitedField.LINEAGE in guard.as_field_set()

    def test_priority_outranks(self, doctrine: PolicyDoctrine) -> None:
        assert doctrine.priority_hierarchy.outranks(
            PriorityCategory.CONSTITUTIONAL,
            PriorityCategory.OPERATIONAL,
        )
        level = doctrine.get_priority_level(PriorityCategory.STATUTORY)
        assert level is not None
        assert level.level == 2

    def test_identity_field_paths(self, doctrine: PolicyDoctrine) -> None:
        resolution = doctrine.identity_resolution
        assert resolution.schema_lineage_location.field == "lineage_id"
        assert resolution.schema_execution_location.field == "id"

    def test_major_mismatch_rejected(self, doctrine_document: dict[str, Any]) -> None:
        doc = deepcopy(doctrine_document)
        doc["doctrine"]["spec_version"] = "9.0.0"
        with pytest.raises(ValidationError, match="MAJOR version mismatch"):
            PolicyDoctrine.from_document(doc)

    def test_schema_encoding_is_authoring_guidance_only(self, doctrine: PolicyDoctrine) -> None:
        flexible = doctrine.get_section("flexible_standards")
        assert flexible is not None
        assert flexible.schema_encoding is not None
        # Not executable configuration — prose guidance only.
        assert isinstance(flexible.schema_encoding, str)

    def test_section_depth_within_limit(self, doctrine: PolicyDoctrine) -> None:
        for section in doctrine.sections:
            assert section.max_depth() <= MAX_SECTION_DEPTH
