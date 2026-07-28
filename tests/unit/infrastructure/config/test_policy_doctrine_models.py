"""Tests for policy_doctrine_models — Pydantic v2 models for policy_doctrine.yaml."""

from selma.domain.value_objects.enums import DeonticType
from selma.infrastructure.config.policy_doctrine_models import ConflictResolutionBinding
from selma.infrastructure.config.policy_doctrine_models import ContentType
from selma.infrastructure.config.policy_doctrine_models import CrossLayerBinding
from selma.infrastructure.config.policy_doctrine_models import DirectiveDoctrineMeta
from selma.infrastructure.config.policy_doctrine_models import DirectivePolicy
from selma.infrastructure.config.policy_doctrine_models import DirectiveTerm
from selma.infrastructure.config.policy_doctrine_models import DoctrineMeta
from selma.infrastructure.config.policy_doctrine_models import DocumentSection
from selma.infrastructure.config.policy_doctrine_models import FieldLegality
from selma.infrastructure.config.policy_doctrine_models import Guidance
from selma.infrastructure.config.policy_doctrine_models import PriorityCategory
from selma.infrastructure.config.policy_doctrine_models import PriorityLevelDefinition
from selma.infrastructure.config.policy_doctrine_models import SanctionRow
from selma.infrastructure.config.policy_doctrine_models import Sanctions
from selma.infrastructure.config.policy_doctrine_models import SpecificDirective
from selma.infrastructure.config.policy_doctrine_models import WritingPrinciple


class TestDoctrineMeta:
    """Doctrine metadata behavior."""

    def test_creation(self) -> None:
        meta = DoctrineMeta(
            name="test-doctrine",
            version="8.2.4",
            description="Test",
            spec_version="8.2.4",
            schema_version="8.2.4",
            schema_id="universal-rule-schema",
        )
        assert meta.name == "test-doctrine"
        assert meta.version == "8.2.4"


class TestFieldLegality:
    """Field legality model behavior."""

    def test_creation(self) -> None:
        fl = FieldLegality(
            policy_layer="Descriptive only",
            schema_layer="Executable fields only",
            spec_layer="System behavior",
        )
        assert fl.policy_layer == "Descriptive only"


class TestCrossLayerBinding:
    """Cross-layer binding model behavior."""

    def test_creation(self) -> None:
        crb = ConflictResolutionBinding(
            policy_layer="intent",
            schema_layer="override",
            spec_layer="algorithm",
            precedence="explicit → computed",
        )
        clb = CrossLayerBinding(
            normative_source="SPECIFICATION.md",
            policy_purpose="governance",
            schema_purpose="structural",
            enforcement="compile-time",
            conflict_resolution_binding=crb,
            runtime_prohibition="MUST NOT be read at runtime",
            field_legality=FieldLegality(
                policy_layer="descriptive",
                schema_layer="executable",
                spec_layer="behavior",
            ),
        )
        assert clb.normative_source == "SPECIFICATION.md"


class TestWritingPrinciple:
    """Writing principle behavior."""

    def test_creation(self) -> None:
        wp = WritingPrinciple(
            id="WP-001",
            title="Precision",
            description="Use exact language",
        )
        assert wp.id == "WP-001"


class TestPriorityLevelDefinition:
    """Priority level definition behavior."""

    def test_creation(self) -> None:
        pl = PriorityLevelDefinition(
            category=PriorityCategory.CONSTITUTIONAL,
            rank=1,
            title="Constitutional",
            description="Core principles",
        )
        assert pl.rank == 1
        assert pl.category == PriorityCategory.CONSTITUTIONAL


class TestDocumentSection:
    """Document section behavior."""

    def test_prose_section(self) -> None:
        section = DocumentSection(
            id="preamble",
            title="Preamble",
            required=True,
            content_type=ContentType.PROSE,
            guidance="Explain the need",
        )
        assert section.required is True
        assert section.content_type == ContentType.PROSE

    def test_table_section(self) -> None:
        section = DocumentSection(
            id="definitions",
            title="Definitions",
            required=True,
            content_type=ContentType.TABLE,
            columns=("Term", "Definition", "Exclusion"),
        )
        assert len(section.columns) == 3


class TestDirectiveTerm:
    """Directive term behavior."""

    def test_creation(self) -> None:
        term = DirectiveTerm(
            term="Machine ID",
            definition="Immutable lineage identifier",
            exclusion="Not an execution ID",
        )
        assert term.term == "Machine ID"


class TestSpecificDirective:
    """Specific directive behavior."""

    def test_creation(self) -> None:
        directive = SpecificDirective(
            type=DeonticType.OBLIGATION,
            description="Every function SHALL validate inputs",
            machine_id="SC-009",
            title="Input Validation",
        )
        assert directive.type == DeonticType.OBLIGATION
        assert directive.machine_id == "SC-009"


class TestSanctionRow:
    """Sanction row behavior."""

    def test_creation(self) -> None:
        row = SanctionRow(
            violation_context="Multiple exit points",
            enforcement_action="Machine lint finding",
            remediation_path="Use b_continue pattern",
        )
        assert row.violation_context == "Multiple exit points"


class TestGuidance:
    """Guidance behavior."""

    def test_creation(self) -> None:
        guidance = Guidance(
            reasoning="Multiple exits create invisible flow",
            correct_example="def f(): ...",
            incorrect_example="def f(): return ... return ...",
            exceptions="Dunder methods exempt",
        )
        assert guidance.reasoning != ""
        assert guidance.correct_example != ""


class TestDirectivePolicy:
    """Directive policy behavior."""

    def test_minimal_creation(self) -> None:
        policy = DirectivePolicy(
            doctrine=DirectiveDoctrineMeta(
                name="sc-001",
                version="8.2.4",
                description="Single exit",
                machine_id="SC-001",
                paired_rule_file="directive/rule/sc001_single_exit.json",
            ),
        )
        assert policy.machine_id == "SC-001"
        assert policy.paired_rule_file == "directive/rule/sc001_single_exit.json"

    def test_full_creation(self) -> None:
        policy = DirectivePolicy(
            doctrine=DirectiveDoctrineMeta(
                name="sc-104",
                version="8.2.4",
                description="No eval/exec",
                machine_id="SC-104",
            ),
            guidance=Guidance(
                reasoning="eval() executes arbitrary code",
                correct_example="ast.literal_eval()",
                incorrect_example="eval(a_value)",
            ),
            sanctions=Sanctions(
                rows=(
                    SanctionRow(
                        violation_context="Forbidden eval/exec",
                        enforcement_action="Machine lint",
                        remediation_path="Use safe alternative",
                    ),
                ),
            ),
        )
        assert policy.machine_id == "SC-104"
        assert policy.guidance.reasoning != ""
        assert len(policy.sanctions.rows) == 1
