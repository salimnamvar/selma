"""Tests for QueryDirectiveUseCase."""

from __future__ import annotations

import pytest

from selma.application.dto.query_request import QueryKind
from selma.application.dto.query_request import QueryRequest
from selma.application.ports.directive_repository_port import DirectiveRepository
from selma.application.use_cases.query_directive import QueryDirectiveUseCase
from selma.domain.aggregates.directive import Directive
from selma.domain.aggregates.directive import DirectiveCatalog
from selma.domain.entities.policy import DirectiveDoctrineMeta
from selma.domain.entities.policy import DirectivePolicy
from selma.domain.entities.policy import Guidance
from selma.domain.entities.rule import EvaluatorConfig
from selma.domain.entities.rule import Rule
from selma.domain.value_objects.enums import DeonticType
from selma.domain.value_objects.enums import Severity
from selma.domain.value_objects.result import Result
from selma.domain.value_objects.rule_id import RuleId


def _rule() -> Rule:
    return Rule(
        lineage_id="SC-001",
        id="SC-001",
        type=DeonticType.OBLIGATION,
        message="Single exit",
        evaluator_type="ast_walk",
        evaluator_config=EvaluatorConfig(),
        weight=Severity.CRITICAL,
    )


def _policy() -> DirectivePolicy:
    return DirectivePolicy(
        doctrine=DirectiveDoctrineMeta(
            name="sc-001",
            version="8.2.4",
            description="test",
            machine_id="SC-001",
        ),
        guidance=Guidance(
            reasoning="Multiple exits hide control flow",
            correct_example="return result",
            incorrect_example="return early",
        ),
    )


class _Repo(DirectiveRepository):
    def __init__(self) -> None:
        self._catalog = DirectiveCatalog(
            directives=(Directive(rule=_rule(), policy=_policy()),)
        )

    async def list_catalog(self) -> Result[DirectiveCatalog]:
        return Result.success(self._catalog)

    async def list_active_rules(self) -> Result[tuple[Rule, ...]]:
        return Result.success(self._catalog.list_active_rules())

    async def find_by_lineage_id(self, a_id: RuleId) -> Result[Directive]:
        d = self._catalog.find_by_lineage_id(a_id.value)
        if d is None:
            return Result.failure("missing")
        return Result.success(d)

    async def find_by_codes(
        self, a_codes: tuple[str, ...]
    ) -> Result[tuple[Directive, ...]]:
        return Result.success(self._catalog.find_by_codes(a_codes))

    async def get_policy(self, a_id: RuleId) -> Result[DirectivePolicy]:
        d = self._catalog.find_by_lineage_id(a_id.value)
        if d is None or d.policy is None:
            return Result.failure("missing")
        return Result.success(d.policy)

    async def get_rule(self, a_id: RuleId) -> Result[Rule]:
        d = self._catalog.find_by_lineage_id(a_id.value)
        if d is None:
            return Result.failure("missing")
        return Result.success(d.rule)


@pytest.mark.asyncio
async def test_list_directives() -> None:
    """Test list directives."""
    uc = QueryDirectiveUseCase(a_directive_repository=_Repo())
    result = await uc.execute(QueryRequest(kind=QueryKind.LIST))
    assert result.is_success()
    assert result.unwrap().items
    assert result.unwrap().items[0]["lineage_id"] == "SC-001"


@pytest.mark.asyncio
async def test_guidance_query() -> None:
    """Test guidance query."""
    uc = QueryDirectiveUseCase(a_directive_repository=_Repo())
    result = await uc.execute(
        QueryRequest(kind=QueryKind.GUIDANCE, lineage_id="SC-001")
    )
    assert result.is_success()
    guidance = result.unwrap().payload.get("guidance")
    assert guidance is not None
    assert "control flow" in guidance["rationale"]


@pytest.mark.asyncio
async def test_missing_id() -> None:
    """Test missing id."""
    uc = QueryDirectiveUseCase(a_directive_repository=_Repo())
    result = await uc.execute(QueryRequest(kind=QueryKind.POLICY, lineage_id=""))
    assert result.is_failure()
