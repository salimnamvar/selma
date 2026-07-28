"""Tests for composition Container."""

from pathlib import Path

from selma.application.ports.directive_repository_port import DirectiveRepository
from selma.application.use_cases.inspect_source import InspectSourceUseCase
from selma.application.use_cases.query_directive import QueryDirectiveUseCase
from selma.composition import Container
from selma.domain.aggregates.directive import Directive
from selma.domain.aggregates.directive import DirectiveCatalog
from selma.domain.entities.policy import DirectivePolicy
from selma.domain.entities.rule import Rule
from selma.domain.value_objects.result import Result
from selma.domain.value_objects.rule_id import RuleId


class _FakeRepo(DirectiveRepository):
    async def list_catalog(self) -> Result[DirectiveCatalog]:
        return Result.success(DirectiveCatalog())

    async def list_active_rules(self) -> Result[tuple[Rule, ...]]:
        return Result.success(())

    async def find_by_lineage_id(self, a_id: RuleId) -> Result[Directive]:
        return Result.failure("missing")

    async def find_by_codes(
        self, a_codes: tuple[str, ...]
    ) -> Result[tuple[Directive, ...]]:
        return Result.success(())

    async def get_policy(self, a_id: RuleId) -> Result[DirectivePolicy]:
        return Result.failure("missing")

    async def get_rule(self, a_id: RuleId) -> Result[Rule]:
        return Result.failure("missing")


class TestContainer:
    """Container wiring."""

    def test_inspect_use_case(self) -> None:
        c = Container()
        result = c.get_inspect_use_case(a_directive_repository=_FakeRepo())
        assert result.is_success()
        assert isinstance(result.unwrap(), InspectSourceUseCase)

    def test_query_use_case(self) -> None:
        c = Container()
        result = c.get_query_use_case(a_directive_repository=_FakeRepo())
        assert result.is_success()
        assert isinstance(result.unwrap(), QueryDirectiveUseCase)

    def test_reporter_default(self) -> None:
        c = Container()
        result = c.get_reporter("default")
        assert result.is_success()
        assert result.unwrap() is not None
        result = c.get_reporter("json")
        assert result.is_success()
        assert result.unwrap() is not None
        result = c.get_reporter("gcc")
        assert result.is_success()
        assert result.unwrap() is not None

    def test_directive_repository_type(self, tmp_path: Path) -> None:
        c = Container()
        schema = tmp_path / "schema.json"
        schema.write_text("{}")
        rules = tmp_path / "rules"
        rules.mkdir()
        result = c.get_directive_repository(
            a_rules_dir=rules,
            a_schema_path=schema,
        )
        assert result.is_success()
        assert result.unwrap() is not None
