"""Tests for LintUseCase — application service orchestration."""

import ast
from typing import Any

from selma.application.dto.lint_request import LintRequest
from selma.application.ports.evaluator_port import RuleEvaluator
from selma.application.ports.parser_port import SourceCodeParser
from selma.application.ports.rule_repository_port import RuleRepository
from selma.application.use_cases.lint_use_case import LintUseCase
from selma.domain.entities.finding import Finding
from selma.domain.entities.rule import EvaluatorConfig
from selma.domain.entities.rule import RuleDefinition
from selma.domain.value_objects.enums import DeonticType
from selma.domain.value_objects.enums import PriorityLevel
from selma.domain.value_objects.enums import RuleStatus
from selma.domain.value_objects.enums import Severity
from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.result import Result
from selma.domain.value_objects.rule_id import RuleId


class _MockParser(SourceCodeParser):
    """Mock parser for testing."""

    def __init__(self, a_result: Result[Any] | None = None) -> None:
        self._result = a_result or Result.success(None)

    def parse(self, a_path: FilePath) -> Result[Any]:
        return self._result

    def parse_source(self, a_source: str, a_filename: str = "<string>") -> Result[Any]:
        return self._result


class _MockRepository(RuleRepository):
    """Mock rule repository for testing."""

    def __init__(
        self,
        a_rules: Result[tuple[RuleDefinition, ...]] | None = None,
    ) -> None:
        self._rules = a_rules if a_rules is not None else Result.success(())

    def find_all(self) -> Result[tuple[RuleDefinition, ...]]:
        return self._rules

    def find_by_id(self, a_id: RuleId) -> Result[RuleDefinition]:
        return Result.failure("Not implemented")

    def find_by_codes(
        self, a_codes: tuple[str, ...]
    ) -> Result[tuple[RuleDefinition, ...]]:
        return self._rules


class _MockEvaluator(RuleEvaluator):
    """Mock evaluator for testing."""

    def __init__(self, a_findings: list[Finding] | None = None) -> None:
        self._findings = a_findings or []

    def evaluate(
        self,
        a_tree: ast.AST,
        a_rule: RuleDefinition,
        a_file_path: str = "",
    ) -> Result[list[Finding]]:
        return Result.success(self._findings)


def _make_rule(a_lineage_id: str = "SC001") -> RuleDefinition:
    """Create a RuleDefinition for testing."""
    return RuleDefinition(
        lineage_id=a_lineage_id,
        id=a_lineage_id,
        rule_type=DeonticType.OBLIGATION,
        message="Test rule",
        evaluator_type="ast_node_match",
        evaluator_config=EvaluatorConfig(),
        weight=Severity.MEDIUM,
        priority=PriorityLevel.OPERATIONAL,
        status=RuleStatus.ACTIVE,
    )


class TestLintUseCaseExecute:
    """LintUseCase.execute behavior."""

    def test_successful_execution_no_findings(self) -> None:
        """Execute should return success with empty findings."""
        use_case = LintUseCase(
            a_parser=_MockParser(),
            a_rule_repository=_MockRepository(),
            a_evaluator=_MockEvaluator(),
        )
        request = LintRequest(paths=(FilePath("/src/main.py"),))
        result = use_case.execute(request)

        assert result.is_success()
        response = result.unwrap()
        assert response.finding_count == 0
        assert response.has_errors is False

    def test_successful_execution_with_findings(self) -> None:
        """Execute should return findings from evaluator."""
        finding = Finding(
            rule_id="SC001",
            file="/src/main.py",
            line=10,
            col=0,
            message="Test finding",
            severity=Severity.HIGH,
            filepath="/src/main.py",
        )
        use_case = LintUseCase(
            a_parser=_MockParser(),
            a_rule_repository=_MockRepository(a_rules=Result.success((_make_rule(),))),
            a_evaluator=_MockEvaluator(a_findings=[finding]),
        )
        request = LintRequest(paths=(FilePath("/src/main.py"),))
        result = use_case.execute(request)

        assert result.is_success()
        response = result.unwrap()
        assert response.finding_count == 1
        assert response.has_errors is True

    def test_rule_load_failure(self) -> None:
        """Execute should return failure when rules fail to load."""
        use_case = LintUseCase(
            a_parser=_MockParser(),
            a_rule_repository=_MockRepository(
                a_rules=Result.failure("DB connection error")
            ),
            a_evaluator=_MockEvaluator(),
        )
        request = LintRequest(paths=(FilePath("/src/main.py"),))
        result = use_case.execute(request)

        assert result.is_failure()
        assert "Failed to load rules" in result.message

    def test_parse_failure_continues(self) -> None:
        """Execute should continue when a file fails to parse."""
        use_case = LintUseCase(
            a_parser=_MockParser(a_result=Result.failure("Syntax error")),
            a_rule_repository=_MockRepository(),
            a_evaluator=_MockEvaluator(),
        )
        request = LintRequest(paths=(FilePath("/src/bad.py"),))
        result = use_case.execute(request)

        assert result.is_success()
        response = result.unwrap()
        assert response.finding_count == 0

    def test_exclude_codes_filtering(self) -> None:
        """Execute should exclude rules by code."""
        rules = (
            _make_rule("SC001"),
            _make_rule("SC002"),
        )
        use_case = LintUseCase(
            a_parser=_MockParser(),
            a_rule_repository=_MockRepository(a_rules=Result.success(rules)),
            a_evaluator=_MockEvaluator(),
        )
        request = LintRequest(
            paths=(FilePath("/src/main.py"),),
            exclude_codes=frozenset({"SC001"}),
        )
        result = use_case.execute(request)

        assert result.is_success()

    def test_only_filter(self) -> None:
        """Execute should filter rules by evaluator type."""
        rules = (
            _make_rule("SC001"),
            _make_rule("SC002"),
        )
        use_case = LintUseCase(
            a_parser=_MockParser(),
            a_rule_repository=_MockRepository(a_rules=Result.success(rules)),
            a_evaluator=_MockEvaluator(),
        )
        request = LintRequest(
            paths=(FilePath("/src/main.py"),),
            only="ast_walk",
        )
        result = use_case.execute(request)

        assert result.is_success()

    def test_empty_paths(self) -> None:
        """Execute should handle empty paths."""
        use_case = LintUseCase(
            a_parser=_MockParser(),
            a_rule_repository=_MockRepository(),
            a_evaluator=_MockEvaluator(),
        )
        request = LintRequest(paths=())
        result = use_case.execute(request)

        assert result.is_success()
        response = result.unwrap()
        assert response.finding_count == 0
