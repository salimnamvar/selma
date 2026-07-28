"""Composition root — wires all dependencies together."""

from __future__ import annotations

from pathlib import Path

from selma.application.ports.directive_repository_port import DirectiveRepository
from selma.application.ports.reporter_port import FindingReporter
from selma.application.use_cases.inspect_source import InspectSourceUseCase
from selma.application.use_cases.query_directive import QueryDirectiveUseCase
from selma.infrastructure.evaluators.ast_interpreter import ASTInterpreter
from selma.infrastructure.parsers.python_ast_parser import PythonAstParser
from selma.infrastructure.reporters import DefaultReporter
from selma.infrastructure.reporters import GccReporter
from selma.infrastructure.reporters import JsonReporter
from selma.infrastructure.rule_repository.json_rule_repository import JsonRuleRepository


class Container:
    """Dependency injection container.

    The only place that knows concrete infrastructure implementations.
    """

    def __init__(self) -> None:
        self._parser = PythonAstParser()
        self._evaluator = ASTInterpreter()
        self._default_reporter = DefaultReporter()
        self._json_reporter = JsonReporter()
        self._gcc_reporter = GccReporter()
        self._guidance_reporter = JsonReporter(a_guide=True)

    def get_directive_repository(
        self,
        a_rules_dir: Path,
        a_schema_path: Path,
        a_policy_dir: Path | None = None,
    ) -> DirectiveRepository:
        """Build a filesystem directive repository."""
        return JsonRuleRepository(
            a_rules_dir=a_rules_dir,
            a_schema_path=a_schema_path,
            a_policy_dir=a_policy_dir,
        )

    def get_inspect_use_case(
        self,
        a_directive_repository: DirectiveRepository,
        a_reporter: FindingReporter | None = None,
    ) -> InspectSourceUseCase:
        """Wire InspectSourceUseCase with explicit repository."""
        return InspectSourceUseCase(
            a_parser=self._parser,
            a_directive_repository=a_directive_repository,
            a_evaluator=self._evaluator,
            a_reporter=a_reporter,
        )

    def get_inspect_use_case_with_defaults(
        self,
        a_rules_dir: Path,
        a_schema_path: Path,
        a_policy_dir: Path | None = None,
    ) -> InspectSourceUseCase:
        """Wire InspectSourceUseCase with filesystem defaults."""
        repository = self.get_directive_repository(
            a_rules_dir=a_rules_dir,
            a_schema_path=a_schema_path,
            a_policy_dir=a_policy_dir,
        )
        return self.get_inspect_use_case(
            a_directive_repository=repository,
            a_reporter=self._default_reporter,
        )

    def get_query_use_case(
        self,
        a_directive_repository: DirectiveRepository,
    ) -> QueryDirectiveUseCase:
        """Wire QueryDirectiveUseCase."""
        return QueryDirectiveUseCase(a_directive_repository=a_directive_repository)

    def get_query_use_case_with_defaults(
        self,
        a_rules_dir: Path,
        a_schema_path: Path,
        a_policy_dir: Path | None = None,
    ) -> QueryDirectiveUseCase:
        """Wire QueryDirectiveUseCase with filesystem defaults."""
        repository = self.get_directive_repository(
            a_rules_dir=a_rules_dir,
            a_schema_path=a_schema_path,
            a_policy_dir=a_policy_dir,
        )
        return self.get_query_use_case(a_directive_repository=repository)

    def get_reporter(self, a_format: str) -> FindingReporter:
        """Resolve a reporter by format name."""
        reporters: dict[str, FindingReporter] = {
            "default": self._default_reporter,
            "json": self._json_reporter,
            "gcc": self._gcc_reporter,
            "guidance": self._guidance_reporter,
        }
        return reporters.get(a_format, self._default_reporter)
