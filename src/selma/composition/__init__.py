"""Composition root — wires all dependencies together."""

from __future__ import annotations

from pathlib import Path

from selma.application.ports.parser_port import SourceCodeParser
from selma.application.ports.reporter_port import FindingReporter
from selma.application.ports.rule_repository_port import RuleRepository
from selma.application.use_cases.lint_use_case import LintUseCase
from selma.infrastructure.evaluators.ast_interpreter import ASTInterpreter
from selma.infrastructure.parsers.python_ast_parser import PythonAstParser
from selma.infrastructure.reporters import DefaultReporter
from selma.infrastructure.reporters import GccReporter
from selma.infrastructure.reporters import JsonReporter
from selma.infrastructure.rule_repository.json_rule_repository import JsonRuleRepository


class Container:
    """Dependency injection container.

    Wires all layers together. This is the ONLY place that knows
    about concrete implementations.
    """

    def __init__(self) -> None:
        self._parser = PythonAstParser()
        self._evaluator = ASTInterpreter()
        self._default_reporter = DefaultReporter()
        self._json_reporter = JsonReporter()
        self._gcc_reporter = GccReporter()
        self._guidance_reporter = JsonReporter(a_guide=True)

    def get_lint_use_case(
        self,
        a_rule_repository: RuleRepository,
    ) -> LintUseCase:
        """Get a configured LintUseCase with explicit repository."""
        return LintUseCase(
            a_parser=self._parser,
            a_rule_repository=a_rule_repository,
            a_evaluator=self._evaluator,
        )

    def get_lint_use_case_with_defaults(
        self,
        a_rules_dir: Path,
        a_schema_path: Path,
        a_policy_dir: Path | None = None,
    ) -> LintUseCase:
        """Get a configured LintUseCase with default rule repository.

        a_rules_dir and a_schema_path MUST be provided from config.
        a_policy_dir is optional and used only for human guidance/examples.
        """
        rule_repository = JsonRuleRepository(
            a_rules_dir=a_rules_dir,
            a_schema_path=a_schema_path,
            a_policy_dir=a_policy_dir,
        )
        return self.get_lint_use_case(a_rule_repository=rule_repository)

    def get_parser(self) -> SourceCodeParser:
        return self._parser

    def get_reporter(self, a_format: str) -> FindingReporter:
        reporters: dict[str, FindingReporter] = {
            "default": self._default_reporter,
            "json": self._json_reporter,
            "gcc": self._gcc_reporter,
            "guidance": self._guidance_reporter,
        }
        return reporters.get(a_format, self._default_reporter)
