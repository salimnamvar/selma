"""Tests for Rule entity — creation, properties."""

from selma.domain.entities.rule import EvaluatorConfig
from selma.domain.entities.rule import Rule
from selma.domain.value_objects.enums import DeonticType
from selma.domain.value_objects.enums import PriorityLevel
from selma.domain.value_objects.enums import RuleStatus
from selma.domain.value_objects.enums import Severity


def _make_rule(**a_overrides: object) -> Rule:
    """Create a Rule with sensible defaults."""
    defaults: dict[str, object] = {
        "lineage_id": "SC-001",
        "id": "SC-001",
        "type": DeonticType.PROHIBITION,
        "message": "No mutable defaults",
        "evaluator_type": "ast_walk",
        "evaluator_config": EvaluatorConfig(),
    }
    defaults.update(a_overrides)
    return Rule(**defaults)  # type: ignore[arg-type]


class TestRuleCreation:
    """Rule creation behavior."""

    def test_required_fields(self) -> None:
        """Rule should accept required fields."""
        r = _make_rule()
        assert r.lineage_id == "SC-001"
        assert r.id == "SC-001"
        assert r.type == DeonticType.PROHIBITION
        assert r.message == "No mutable defaults"
        assert r.evaluator_type == "ast_walk"

    def test_defaults(self) -> None:
        """Rule should have sensible defaults."""
        r = _make_rule()
        assert r.weight == Severity.MEDIUM
        assert r.priority == PriorityLevel.OPERATIONAL
        assert r.status == RuleStatus.ACTIVE
        assert r.created_at == ""
        assert r.rationale == ""
        assert r.remediation == ""
        assert r.parameters == {}
        assert r.depends_on == ()
        assert r.conflicts_with == ()


class TestRuleProperties:
    """Rule property behavior."""

    def test_rule_id_property(self) -> None:
        """rule_id should return lineage_id."""
        r = _make_rule(lineage_id="SC-042", id="SC-042")
        assert r.rule_id == "SC-042"

    def test_is_active_true(self) -> None:
        """is_active returns True when status is ACTIVE."""
        r = _make_rule(status=RuleStatus.ACTIVE)
        assert r.is_active() is True

    def test_is_active_false(self) -> None:
        """is_active returns False when status is not ACTIVE."""
        r = _make_rule(status=RuleStatus.DEPRECATED)
        assert r.is_active() is False


class TestEvaluatorConfig:
    """EvaluatorConfig creation behavior."""

    def test_defaults(self) -> None:
        """EvaluatorConfig should have sensible defaults."""
        ec = EvaluatorConfig()
        assert ec.pattern is None
        assert ec.flags is None
        assert ec.field is None
        assert ec.operator is None
        assert ec.value is None
        assert ec.threshold is None
        assert ec.logic is None
        assert ec.sub_evaluators == ()

    def test_frozen(self) -> None:
        """EvaluatorConfig should be a Pydantic frozen model."""
        ec = EvaluatorConfig()
        assert hasattr(ec, "__pydantic_fields__")

    def test_extra_fields_allowed(self) -> None:
        """EvaluatorConfig should accept language-specific extra fields."""
        ec = EvaluatorConfig(
            walk_nodes=("Return",),
            message_template="test {name}",
            exempt_dunders=True,
        )
        assert ec.walk_nodes == ("Return",)
        assert ec.message_template == "test {name}"
        assert ec.exempt_dunders is True
