"""Tests for Directive and DirectiveCatalog aggregates."""

from selma.domain.aggregates.directive import Directive
from selma.domain.aggregates.directive import DirectiveCatalog
from selma.domain.entities.policy import DirectiveDoctrineMeta
from selma.domain.entities.policy import DirectivePolicy
from selma.domain.entities.policy import Directives
from selma.domain.entities.policy import Guidance
from selma.domain.entities.policy import SpecificDirective
from selma.domain.entities.rule import EvaluatorConfig
from selma.domain.entities.rule import Rule
from selma.domain.value_objects.enums import DeonticType
from selma.domain.value_objects.enums import Severity


def _rule() -> Rule:
    return Rule(
        lineage_id="SC-001",
        id="SC-001",
        type=DeonticType.OBLIGATION,
        message="Single exit point",
        evaluator_type="ast_walk",
        evaluator_config=EvaluatorConfig(),
        weight=Severity.CRITICAL,
    )


def test_directive_without_policy() -> None:
    """Test directive without policy."""
    d = Directive(rule=_rule(), policy=None)
    assert d.lineage_id == "SC-001"
    assert d.has_policy() is False
    assert d.reasoning_guidance() is None
    assert d.title == "Single exit point"


def test_directive_with_policy_guidance() -> None:
    """Test directive with policy guidance."""
    policy = DirectivePolicy(
        doctrine=DirectiveDoctrineMeta(
            name="sc-001",
            version="8.2.4",
            description="t",
            machine_id="SC-001",
        ),
        directives=Directives(
            specific_directives=(
                SpecificDirective(
                    type="Obligation",
                    description="one return",
                    machine_id="SC-001",
                    title="Single-Exit Point",
                ),
            )
        ),
        guidance=Guidance(
            reasoning="traceability",
            correct_example="ok",
            incorrect_example="bad",
        ),
    )
    d = Directive(rule=_rule(), policy=policy)
    assert d.title == "Single-Exit Point"
    g = d.reasoning_guidance()
    assert g is not None
    assert g.rationale == "traceability"
    assert g.correct_example == "ok"


def test_catalog_find() -> None:
    """Test catalog find."""
    catalog = DirectiveCatalog(directives=(Directive(rule=_rule()),))
    assert catalog.find_by_lineage_id("SC-001") is not None
    assert catalog.get_rule("SC-001") is not None
    assert len(catalog.list_active_rules()) == 1
