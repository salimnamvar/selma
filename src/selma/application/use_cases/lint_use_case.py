"""LintUseCase — main application service for linting files.

Orchestrates: parse -> evaluate -> report
"""

from __future__ import annotations

import ast
import logging

from selma.application.dto.lint_request import LintRequest
from selma.application.dto.lint_response import LintResponse
from selma.application.ports.evaluator_port import RuleEvaluator
from selma.application.ports.parser_port import SourceCodeParser
from selma.application.ports.reporter_port import FindingReporter
from selma.application.ports.rule_repository_port import RuleRepository
from selma.domain.entities.finding import Finding
from selma.domain.entities.rule import RuleDefinition
from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.result import Result
from selma.domain.value_objects.severity import Severity

logger = logging.getLogger(__name__)


class LintUseCase:
    """Application service: orchestrate linting process.

    Dependencies are injected via constructor (Dependency Inversion).
    """

    def __init__(
        self,
        a_parser: SourceCodeParser,
        a_rule_repository: RuleRepository,
        a_evaluator: RuleEvaluator,
        a_reporter: FindingReporter | None = None,
    ) -> None:
        self._parser = a_parser
        self._rule_repository = a_rule_repository
        self._evaluator = a_evaluator
        self._reporter = a_reporter

    def execute(self, a_request: LintRequest) -> Result[LintResponse]:
        """Execute the lint use case.

        Orchestrates: load rules → parse files → evaluate → collect findings

        Preconditions:
            - a_request.paths is non-empty.
            - Parser and rule repository are available.

        Postconditions:
            Returns Ok with LintResponse containing findings.

        Side Effects: Reads files, evaluates rules.
        Resource: File handles, subprocess handles.
        Failure: Returns Failure on critical error.
        """
        b_continue = True
        result: Result[LintResponse] = Result.failure("unreachable")

        rules_result = self._load_rules(a_request)
        if rules_result.is_failure():
            b_continue = False
            result = Result.failure(f"Failed to load rules: {rules_result.message}")

        all_findings: list[Finding] = []
        if b_continue:
            rules = rules_result.unwrap()
            for path in a_request.paths:
                file_result = self._lint_file(path, rules, a_request)
                if file_result.is_success():
                    all_findings.extend(file_result.unwrap())

        if b_continue:
            response = LintResponse(
                findings=tuple(all_findings),
                summary=f"Found {len(all_findings)} issues",
                has_errors=any(f.is_violation for f in all_findings),
            )
            if self._reporter is not None:
                report_result = self._reporter.report(response.findings)
                if report_result.is_failure():
                    result = Result.failure(
                        f"Reporting failed: {report_result.message}"
                    )
                else:
                    result = Result.success(response)
            else:
                result = Result.success(response)
        return result

    def _load_rules(self, a_request: LintRequest) -> Result[tuple[RuleDefinition, ...]]:
        """Load and filter rules based on request."""
        b_continue = True
        result: Result[tuple[RuleDefinition, ...]] = Result.failure("unreachable")

        if a_request.codes:
            b_continue = False
            result = self._rule_repository.find_by_codes(tuple(a_request.codes))

        all_rules_result: Result[tuple[RuleDefinition, ...]] = Result.failure(
            "Rules not yet loaded"
        )
        if b_continue:
            all_rules_result = self._rule_repository.find_all()
            if all_rules_result.is_failure():
                b_continue = False
                result = all_rules_result

        if b_continue:
            rules = all_rules_result.unwrap()
            if a_request.exclude_codes:
                rules = tuple(
                    r for r in rules if r.lineage_id not in a_request.exclude_codes
                )
            if a_request.only:
                rules = tuple(r for r in rules if r.evaluator_type == a_request.only)
            result = Result.success(rules)
        return result

    def _lint_file(
        self,
        a_path: FilePath,
        a_rules: tuple[RuleDefinition, ...],
        a_request: LintRequest,
    ) -> Result[list[Finding]]:
        """Lint a single file against all rules.

        FIXED: P0.4 — Each rule is isolated in try/except.
        """
        b_continue = True
        result: Result[list[Finding]] = Result.failure("unreachable")

        parse_result = self._parser.parse(a_path)
        if parse_result.is_failure():
            b_continue = False
            result = Result.failure(f"Failed to parse {a_path}: {parse_result.message}")

        tree: ast.AST
        findings: list[Finding] = []
        if b_continue:
            tree = parse_result.unwrap()
            for rule in a_rules:
                try:
                    rule_findings = self._evaluate_rule(rule, tree, a_path)
                    findings.extend(rule_findings)
                except Exception as exc:
                    logger.warning(
                        "Rule %s failed on %s: %s", rule.lineage_id, a_path, exc
                    )
                    findings.append(
                        Finding(
                            rule_id=rule.lineage_id,
                            file=str(a_path),
                            line=0,
                            col=0,
                            message=f"Internal rule error: {exc}",
                            severity=Severity.LOW,
                            filepath=str(a_path),
                        )
                    )
        if b_continue:
            result = Result.success(findings)
        return result

    def _evaluate_rule(
        self,
        a_rule: RuleDefinition,
        a_tree: ast.AST,
        a_path: FilePath,
    ) -> list[Finding]:
        """Evaluate a single rule against an AST.

        Delegates to ASTInterpreter for actual evaluation.
        """
        findings: list[Finding] = []

        eval_result = self._evaluator.evaluate(
            a_tree=a_tree,
            a_rule=a_rule,
            a_file_path=str(a_path),
        )
        if eval_result.is_success():
            raw_findings = eval_result.unwrap()
            if a_rule.guidance is not None:
                findings = [
                    finding.model_copy(update={"guidance": a_rule.guidance})
                    if finding.guidance is None
                    else finding
                    for finding in raw_findings
                ]
            else:
                findings = raw_findings
        return findings
