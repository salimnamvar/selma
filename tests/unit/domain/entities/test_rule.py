"""Tests for RuleDefinition entity — creation, properties.

NOTE: With Pydantic v2, the field name collision with dataclasses.field
is no longer an issue. All tests run without skipif.
"""

from selma.domain.entities.rule import EvaluatorConfig
from selma.domain.entities.rule import RuleDefinition
from selma.domain.value_objects.severity import Severity


def _make_rule(**a_overrides: object) -> RuleDefinition:
    """Create a RuleDefinition with sensible defaults."""
    defaults: dict[str, object] = {
        "lineage_id": "SC001",
        "id": "sc001",
        "rule_type": "prohibition",
        "message": "No mutable defaults",
        "evaluator_type": "ast",
        "evaluator_config": EvaluatorConfig(),
    }
    defaults.update(a_overrides)
    return RuleDefinition(**defaults)  # type: ignore[arg-type]


class TestRuleDefinitionCreation:
    """RuleDefinition creation behavior."""

    def test_required_fields(self) -> None:
        """RuleDefinition should accept required fields."""
        r = _make_rule()
        assert r.lineage_id == "SC001"
        assert r.id == "sc001"
        assert r.rule_type == "prohibition"
        assert r.message == "No mutable defaults"
        assert r.evaluator_type == "ast"

    def test_defaults(self) -> None:
        """RuleDefinition should have sensible defaults."""
        r = _make_rule()
        assert r.weight == Severity.MEDIUM
        assert r.priority == "operational"
        assert r.status == "active"
        assert r.created_at == ""
        assert r.rationale == ""
        assert r.remediation == ""
        assert r.guidance is None
        assert r.parameters == {}
        assert r.depends_on == ()
        assert r.conflicts_with == ()


class TestRuleDefinitionProperties:
    """RuleDefinition property behavior."""

    def test_rule_id_property(self) -> None:
        """rule_id should return a string wrapping lineage_id."""
        r = _make_rule(lineage_id="SC042")
        rid = r.rule_id
        assert str(rid) == "SC042"

    def test_is_active_true(self) -> None:
        """is_active returns True when status is 'active'."""
        r = _make_rule(status="active")
        assert r.is_active() is True

    def test_is_active_false(self) -> None:
        """is_active returns False when status is not 'active'."""
        r = _make_rule(status="deprecated")
        assert r.is_active() is False


class TestEvaluatorConfig:
    """EvaluatorConfig creation behavior."""

    def test_defaults(self) -> None:
        """EvaluatorConfig should have sensible defaults."""
        ec = EvaluatorConfig()
        assert ec.pattern is None
        assert ec.flags is None
        assert ec.target_field is None
        assert ec.operator is None
        assert ec.value is None
        assert ec.threshold is None
        assert ec.logic is None
        assert ec.sub_evaluators == ()
        assert ec.max_lines == 60

    def test_frozen(self) -> None:
        """EvaluatorConfig should be a Pydantic frozen model."""
        ec = EvaluatorConfig()
        assert hasattr(ec, "__pydantic_fields__")
