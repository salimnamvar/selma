"""Composition root — wires all dependencies together."""

from __future__ import annotations

from pathlib import Path

from selma.application.ports.event_publisher_port import EventPublisher
from selma.application.ports.rule_repository_port import RuleRepository
from selma.application.use_cases.lint_use_case import LintUseCase
from selma.infrastructure.evaluators.ast_interpreter import ASTInterpreter
from selma.infrastructure.parsers.python_ast_parser import PythonAstParser
from selma.infrastructure.reporters import DefaultReporter
from selma.infrastructure.reporters import GccReporter
from selma.infrastructure.reporters import JsonReporter
from selma.infrastructure.rule_repository.json_rule_repository import JsonRuleRepository
from selma.infrastructure.tool_runners.pylint_runner import PylintRunner
from selma.infrastructure.tool_runners.pyright_runner import PyrightRunner
from selma.infrastructure.tool_runners.ruff_runner import RuffCheckRunner
from selma.infrastructure.tool_runners.ruff_runner import RuffFormatRunner


class Container:
    """Dependency injection container.

    Wires all layers together. This is the ONLY place that knows
    about concrete implementations.
    """

    def __init__(self) -> None:
        self._parser = PythonAstParser()
        self._evaluator = ASTInterpreter()
        self._ruff_check = RuffCheckRunner()
        self._ruff_format = RuffFormatRunner()
        self._pylint = PylintRunner()
        self._pyright = PyrightRunner()
        self._default_reporter = DefaultReporter()
        self._json_reporter = JsonReporter()
        self._gcc_reporter = GccReporter()
        self._guidance_reporter = JsonReporter(a_guide=True)

    def get_lint_use_case(
        self,
        a_rule_repository: RuleRepository,
        a_event_publisher: EventPublisher | None = None,
    ) -> LintUseCase:
        """Get a configured LintUseCase with explicit repository."""
        return LintUseCase(
            a_parser=self._parser,
            a_rule_repository=a_rule_repository,
            a_evaluator=self._evaluator,
            a_event_publisher=a_event_publisher,
        )

    def get_lint_use_case_with_defaults(
        self,
        a_rules_dir: Path,
    ) -> LintUseCase:
        """Get a configured LintUseCase with default rule repository."""
        rule_repository = JsonRuleRepository(a_rules_dir=a_rules_dir)
        return self.get_lint_use_case(a_rule_repository=rule_repository)

    def get_parser(self) -> PythonAstParser:
        return self._parser

    def get_reporter(
        self, a_format: str
    ) -> DefaultReporter | JsonReporter | GccReporter:
        reporters = {
            "default": self._default_reporter,
            "json": self._json_reporter,
            "gcc": self._gcc_reporter,
            "guidance": self._guidance_reporter,
        }
        return reporters.get(a_format, self._default_reporter)

    def get_ruff_check(self) -> RuffCheckRunner:
        return self._ruff_check

    def get_ruff_format(self) -> RuffFormatRunner:
        return self._ruff_format

    def get_pylint(self) -> PylintRunner:
        return self._pylint

    def get_pyright(self) -> PyrightRunner:
        return self._pyright
