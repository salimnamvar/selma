"""Tests for InspectSourceUseCase."""

from __future__ import annotations

import ast
from typing import Any

import pytest

from selma.application.dto.inspect_request import InspectRequest
from selma.application.ports.directive_repository_port import DirectiveRepository
from selma.application.ports.evaluator_port import RuleEvaluator
from selma.application.ports.parser_port import SourceParser
from selma.application.use_cases.inspect_source import InspectSourceUseCase
from selma.domain.aggregates.directive import Directive
from selma.domain.aggregates.directive import DirectiveCatalog
from selma.domain.entities.finding import Finding
from selma.domain.entities.policy import DirectivePolicy
from selma.domain.entities.rule import EvaluatorConfig
from selma.domain.entities.rule import Rule
from selma.domain.value_objects.enums import DeonticType
from selma.domain.value_objects.enums import PriorityLevel
from selma.domain.value_objects.enums import RuleStatus
from selma.domain.value_objects.enums import Severity
from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.result import Result
from selma.domain.value_objects.rule_id import RuleId


def _make_rule(a_lineage_id: str = "SC-001") -> Rule:
    return Rule(
        lineage_id=a_lineage_id,
        id=a_lineage_id,
        type=DeonticType.OBLIGATION,
        message="Test rule",
        evaluator_type="ast_node_match",
        evaluator_config=EvaluatorConfig(),
        weight=Severity.MEDIUM,
        priority=PriorityLevel.OPERATIONAL,
        status=RuleStatus.ACTIVE,
    )


def _make_catalog(*a_rules: Rule) -> DirectiveCatalog:
    return DirectiveCatalog(
        directives=tuple(Directive(rule=rule, policy=None) for rule in a_rules)
    )


class _MockParser(SourceParser):
    def __init__(self, a_result: Result[Any] | None = None) -> None:
        self._result = a_result or Result.success(ast.parse("x = 1"))

    async def parse(self, a_path: FilePath) -> Result[Any]:
        return self._result

    async def parse_source(
        self, a_source: str, a_filename: str = "<string>"
    ) -> Result[Any]:
        return self._result


class _MockRepository(DirectiveRepository):
    def __init__(self, a_catalog: Result[DirectiveCatalog] | None = None) -> None:
        # Do not use `or` — failure Result is falsy via __bool__.
        if a_catalog is None:
            self._catalog: Result[DirectiveCatalog] = Result.success(DirectiveCatalog())
        else:
            self._catalog = a_catalog

    async def list_catalog(self) -> Result[DirectiveCatalog]:
        return self._catalog

    async def list_active_rules(self) -> Result[tuple[Rule, ...]]:
        if self._catalog.is_failure():
            return Result.failure(self._catalog.message)
        return Result.success(self._catalog.unwrap().list_active_rules())

    async def find_by_lineage_id(self, a_id: RuleId) -> Result[Directive]:
        return Result.failure("Not implemented")

    async def find_by_codes(
        self, a_codes: tuple[str, ...]
    ) -> Result[tuple[Directive, ...]]:
        if self._catalog.is_failure():
            return Result.failure(self._catalog.message)
        return Result.success(self._catalog.unwrap().find_by_codes(a_codes))

    async def get_policy(self, a_id: RuleId) -> Result[DirectivePolicy]:
        return Result.failure("Not implemented")

    async def get_rule(self, a_id: RuleId) -> Result[Rule]:
        return Result.failure("Not implemented")


class _MockEvaluator(RuleEvaluator):
    def __init__(self, a_findings: list[Finding] | None = None) -> None:
        self._findings = a_findings or []

    async def evaluate(
        self,
        a_tree: ast.AST,
        a_rule: Rule,
        a_file_path: str = "",
    ) -> Result[list[Finding]]:
        return Result.success(self._findings)


@pytest.mark.asyncio
async def test_successful_execution_no_findings() -> None:
    """Test successful execution no findings."""
    use_case = InspectSourceUseCase(
        a_parser=_MockParser(),
        a_directive_repository=_MockRepository(),
        a_evaluator=_MockEvaluator(),
    )
    result = await use_case.execute(InspectRequest(paths=(FilePath("/src/main.py"),)))
    assert result.is_success()
    assert result.unwrap().finding_count == 0


@pytest.mark.asyncio
async def test_successful_execution_with_findings() -> None:
    """Test successful execution with findings."""
    finding = Finding(
        rule_id="SC-001",
        file="/src/main.py",
        line=10,
        message="Test finding",
        severity=Severity.HIGH,
        filepath="/src/main.py",
    )
    use_case = InspectSourceUseCase(
        a_parser=_MockParser(),
        a_directive_repository=_MockRepository(
            a_catalog=Result.success(_make_catalog(_make_rule()))
        ),
        a_evaluator=_MockEvaluator(a_findings=[finding]),
    )
    result = await use_case.execute(InspectRequest(paths=(FilePath("/src/main.py"),)))
    assert result.is_success()
    assert result.unwrap().finding_count == 1
    assert result.unwrap().has_errors is True


@pytest.mark.asyncio
async def test_catalog_load_failure() -> None:
    """Test catalog load failure."""
    use_case = InspectSourceUseCase(
        a_parser=_MockParser(),
        a_directive_repository=_MockRepository(
            a_catalog=Result.failure("DB connection error")
        ),
        a_evaluator=_MockEvaluator(),
    )
    result = await use_case.execute(InspectRequest(paths=(FilePath("/src/main.py"),)))
    assert result.is_failure()
    assert "Failed to load directives" in result.message


@pytest.mark.asyncio
async def test_exclude_codes_filtering() -> None:
    """Test exclude codes filtering."""
    use_case = InspectSourceUseCase(
        a_parser=_MockParser(),
        a_directive_repository=_MockRepository(
            a_catalog=Result.success(
                _make_catalog(_make_rule("SC-001"), _make_rule("SC-002"))
            )
        ),
        a_evaluator=_MockEvaluator(),
    )
    result = await use_case.execute(
        InspectRequest(
            paths=(FilePath("/src/main.py"),),
            exclude_codes=frozenset({"SC-001"}),
        )
    )
    assert result.is_success()
