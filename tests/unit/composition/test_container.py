"""Tests for Container — composition root wiring."""

from pathlib import Path

from selma.application.ports.rule_repository_port import RuleRepository
from selma.application.use_cases.lint_use_case import LintUseCase
from selma.composition import Container
from selma.domain.entities.rule import RuleDefinition
from selma.domain.value_objects.result import Result
from selma.domain.value_objects.rule_id import RuleId
from selma.infrastructure.parsers.python_ast_parser import PythonAstParser
from selma.infrastructure.reporters import DefaultReporter
from selma.infrastructure.reporters import GccReporter
from selma.infrastructure.reporters import JsonReporter


class _NullRepo(RuleRepository):
    """Null repository for testing."""

    def find_all(self) -> Result[tuple[RuleDefinition, ...]]:
        return Result.success(())

    def find_by_id(self, a_id: RuleId) -> Result[RuleDefinition]:
        return Result.failure("Not implemented")

    def find_by_codes(
        self, a_codes: tuple[str, ...]
    ) -> Result[tuple[RuleDefinition, ...]]:
        return Result.success(())


class TestContainerInit:
    """Container initialization behavior."""

    def test_creates_parser(self) -> None:
        """Container should create a PythonAstParser."""
        container = Container()
        assert isinstance(container.get_parser(), PythonAstParser)

    def test_creates_evaluator(self) -> None:
        """Container should have an ASTInterpreter evaluator."""
        container = Container()
        # Verify evaluator works by creating a use case
        use_case = container.get_lint_use_case(a_rule_repository=_NullRepo())
        assert isinstance(use_case, LintUseCase)

    def test_creates_reporters(self) -> None:
        """Container should create all reporter types."""
        container = Container()
        assert isinstance(container.get_reporter("default"), DefaultReporter)
        assert isinstance(container.get_reporter("json"), JsonReporter)
        assert isinstance(container.get_reporter("gcc"), GccReporter)
        assert isinstance(container.get_reporter("guidance"), JsonReporter)

    def test_unknown_format_returns_default(self) -> None:
        """Container should return default reporter for unknown format."""
        container = Container()
        assert isinstance(container.get_reporter("unknown"), DefaultReporter)


class TestContainerGetLintUseCase:
    """Container.get_lint_use_case behavior."""

    def test_returns_lint_use_case(self) -> None:
        """get_lint_use_case should return a LintUseCase."""
        container = Container()
        use_case = container.get_lint_use_case(a_rule_repository=_NullRepo())
        assert isinstance(use_case, LintUseCase)

    def test_get_lint_use_case_with_defaults(self) -> None:
        """get_lint_use_case_with_defaults should create repo from rules dir."""
        container = Container()
        rules_dir = Path.home() / ".selma" / "rules"
        schema_path = Path.home() / ".selma" / "schema" / "rule_schema.json"
        use_case = container.get_lint_use_case_with_defaults(
            a_rules_dir=rules_dir,
            a_schema_path=schema_path,
            a_policy_dir=None,
        )
        assert isinstance(use_case, LintUseCase)
