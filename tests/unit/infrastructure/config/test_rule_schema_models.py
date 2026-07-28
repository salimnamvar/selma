"""Tests for rule_schema_models — Pydantic v2 models for rule_schema.json."""

from selma.domain.value_objects.enums import Severity
from selma.infrastructure.config.rule_schema_models import ComparisonOperator
from selma.infrastructure.config.rule_schema_models import CompositeEvaluatorConfig
from selma.infrastructure.config.rule_schema_models import ConflictResolution
from selma.infrastructure.config.rule_schema_models import ConflictStrategy
from selma.infrastructure.config.rule_schema_models import DeonticType
from selma.infrastructure.config.rule_schema_models import EvaluatorConfigEntry
from selma.infrastructure.config.rule_schema_models import EvaluatorType
from selma.infrastructure.config.rule_schema_models import FieldCheckEvaluatorConfig
from selma.infrastructure.config.rule_schema_models import Lineage
from selma.infrastructure.config.rule_schema_models import LineageOperation
from selma.infrastructure.config.rule_schema_models import LogicOp
from selma.infrastructure.config.rule_schema_models import PriorityLevel
from selma.infrastructure.config.rule_schema_models import RegexEvaluatorConfig
from selma.infrastructure.config.rule_schema_models import Rule
from selma.infrastructure.config.rule_schema_models import RuleDataset
from selma.infrastructure.config.rule_schema_models import RuleStatus
from selma.infrastructure.config.rule_schema_models import Scope
from selma.infrastructure.config.rule_schema_models import TargetType
from selma.infrastructure.config.rule_schema_models import ThresholdEvaluatorConfig


class TestEnums:
    """Enum value behavior."""

    def test_deontic_type_values(self) -> None:
        assert DeonticType.OBLIGATION == "obligation"
        assert DeonticType.PROHIBITION == "prohibition"
        assert DeonticType.PERMISSION == "permission"

    def test_rule_status_values(self) -> None:
        assert RuleStatus.DRAFT == "draft"
        assert RuleStatus.ACTIVE == "active"
        assert RuleStatus.DEPRECATED == "deprecated"
        assert RuleStatus.SUPERSEDED == "superseded"

    def test_evaluator_type_values(self) -> None:
        assert EvaluatorType.REGEX == "regex"
        assert EvaluatorType.FIELD_CHECK == "field_check"
        assert EvaluatorType.THRESHOLD == "threshold"
        assert EvaluatorType.COMPOSITE == "composite"

    def test_severity_values(self) -> None:
        assert Severity.CRITICAL == "critical"
        assert Severity.HIGH == "high"
        assert Severity.MEDIUM == "medium"
        assert Severity.LOW == "low"
        assert Severity.INFORMATIONAL == "informational"

    def test_priority_level_values(self) -> None:
        assert PriorityLevel.CONSTITUTIONAL == "constitutional"
        assert PriorityLevel.STATUTORY == "statutory"
        assert PriorityLevel.REGULATORY == "regulatory"
        assert PriorityLevel.OPERATIONAL == "operational"
        assert PriorityLevel.ADVISORY == "advisory"


class TestRegexEvaluatorConfig:
    """Regex evaluator config behavior."""

    def test_creation(self) -> None:
        config = RegexEvaluatorConfig(pattern="test.*pattern")
        assert config.pattern == "test.*pattern"
        assert config.flags == ""

    def test_with_flags(self) -> None:
        config = RegexEvaluatorConfig(pattern="test", flags="ims")
        assert config.flags == "ims"

    def test_frozen(self) -> None:
        config = RegexEvaluatorConfig(pattern="test")
        assert hasattr(config, "__pydantic_fields__")


class TestFieldCheckEvaluatorConfig:
    """Field check evaluator config behavior."""

    def test_creation(self) -> None:
        config = FieldCheckEvaluatorConfig(
            field="name",
            operator=ComparisonOperator.EQ,
            value="test",
        )
        assert config.field == "name"
        assert config.operator == ComparisonOperator.EQ
        assert config.value == "test"


class TestThresholdEvaluatorConfig:
    """Threshold evaluator config behavior."""

    def test_creation(self) -> None:
        config = ThresholdEvaluatorConfig(
            field="count",
            operator="gt",
            threshold=10.0,
        )
        assert config.field == "count"
        assert config.operator == "gt"
        assert config.threshold == 10.0


class TestCompositeEvaluatorConfig:
    """Composite evaluator config behavior."""

    def test_creation_with_sub_evaluators(self) -> None:
        sub = EvaluatorConfigEntry(
            evaluator_type=EvaluatorType.REGEX,
            evaluator_config=RegexEvaluatorConfig(pattern="test"),
        )
        config = CompositeEvaluatorConfig(
            logic=LogicOp.AND,
            sub_evaluators=(sub,),
        )
        assert config.logic == LogicOp.AND
        assert len(config.sub_evaluators) == 1

    def test_not_logic_max_one(self) -> None:
        sub = EvaluatorConfigEntry(
            evaluator_type=EvaluatorType.REGEX,
            evaluator_config=RegexEvaluatorConfig(pattern="test"),
        )
        config = CompositeEvaluatorConfig(
            logic=LogicOp.NOT,
            sub_evaluators=(sub,),
        )
        assert config.logic == LogicOp.NOT
        assert len(config.sub_evaluators) == 1


class TestScope:
    """Scope model behavior."""

    def test_defaults(self) -> None:
        scope = Scope()
        assert scope.target_type == TargetType.ANY
        assert scope.domain == ""
        assert scope.jurisdiction == ""
        assert scope.filters == ()

    def test_with_values(self) -> None:
        scope = Scope(
            target_type=TargetType.TEXT,
            domain="finance",
            jurisdiction="EU",
        )
        assert scope.target_type == TargetType.TEXT
        assert scope.domain == "finance"


class TestConflictResolution:
    """Conflict resolution model behavior."""

    def test_always_wins(self) -> None:
        cr = ConflictResolution(strategy=ConflictStrategy.ALWAYS_WINS)
        assert cr.strategy == ConflictStrategy.ALWAYS_WINS
        assert cr.defer_to is None

    def test_defer_to(self) -> None:
        cr = ConflictResolution(
            strategy=ConflictStrategy.DEFER_TO,
            defer_to="SC-002",
        )
        assert cr.defer_to == "SC-002"


class TestLineage:
    """Lineage model behavior."""

    def test_fork(self) -> None:
        lineage = Lineage(
            operation=LineageOperation.FORK,
            parent_lineage_ids=("SC-001",),
            parent_execution_ids=("SC-001",),
            timestamp="2026-07-25T00:00:00Z",
        )
        assert lineage.operation == LineageOperation.FORK
        assert len(lineage.parent_lineage_ids) == 1

    def test_merge(self) -> None:
        lineage = Lineage(
            operation=LineageOperation.MERGE,
            parent_lineage_ids=("SC-001", "SC-002"),
            parent_execution_ids=("SC-001", "SC-002"),
            timestamp="2026-07-25T00:00:00Z",
        )
        assert lineage.operation == LineageOperation.MERGE
        assert len(lineage.parent_lineage_ids) == 2


class TestRule:
    """Rule model behavior."""

    def _make_rule(self, **overrides: object) -> Rule:
        defaults: dict[str, object] = {
            "lineage_id": "SC-001",
            "id": "SC-001",
            "type": DeonticType.OBLIGATION,
            "message": "Test rule",
            "evaluator_type": EvaluatorType.REGEX,
            "evaluator_config": {"pattern": "test"},
            "status": RuleStatus.ACTIVE,
            "created_at": "2026-07-25T00:00:00Z",
        }
        defaults.update(overrides)
        return Rule.model_validate(defaults)

    def test_required_fields(self) -> None:
        rule = self._make_rule()
        assert rule.lineage_id == "SC-001"
        assert rule.id == "SC-001"
        assert rule.type == DeonticType.OBLIGATION
        assert rule.message == "Test rule"

    def test_defaults(self) -> None:
        rule = self._make_rule()
        assert rule.weight == Severity.MEDIUM
        assert rule.priority == PriorityLevel.OPERATIONAL
        assert rule.depends_on == ()
        assert rule.conflicts_with == ()

    def test_rule_id_property(self) -> None:
        rule = self._make_rule(lineage_id="SC-042")
        assert rule.rule_id == "SC-042"

    def test_is_active(self) -> None:
        rule = self._make_rule(status=RuleStatus.ACTIVE)
        assert rule.is_active() is True

    def test_is_not_active(self) -> None:
        rule = self._make_rule(status=RuleStatus.DEPRECATED)
        assert rule.is_active() is False

    def test_with_scope(self) -> None:
        rule = self._make_rule(
            scope={"target_type": "text", "domain": "finance"},
        )
        assert rule.scope is not None
        assert rule.scope.domain == "finance"

    def test_with_conflict_resolution(self) -> None:
        rule = self._make_rule(
            conflict_resolution={"strategy": "always_wins"},
        )
        assert rule.conflict_resolution is not None
        assert rule.conflict_resolution.strategy == ConflictStrategy.ALWAYS_WINS


class TestRuleDataset:
    """RuleDataset model behavior."""

    def test_creation(self) -> None:
        dataset = RuleDataset(
            version="8.2.4",
            policy_contract_version="8.2.4",
            rules=(
                Rule(
                    lineage_id="SC-001",
                    id="SC-001",
                    type=DeonticType.OBLIGATION,
                    message="Test",
                    evaluator_type=EvaluatorType.REGEX,
                    evaluator_config={"pattern": "test"},
                    status=RuleStatus.ACTIVE,
                    created_at="2026-07-25T00:00:00Z",
                ),
            ),
        )
        assert dataset.version == "8.2.4"
        assert len(dataset.rules) == 1
        assert dataset.policy_contract_id == "universal-policy-doctrine"
