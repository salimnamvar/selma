"""InspectSourceUseCase — evaluate source against executable rules.

Orchestrates: load rules → parse files (concurrent) → evaluate → report.
Policy documents are never used for evaluation (runtime prohibition).
"""

from __future__ import annotations

import ast
import asyncio
import logging

from selma.application.dto.inspect_request import InspectRequest
from selma.application.dto.inspect_response import InspectResponse
from selma.application.ports.directive_repository_port import DirectiveRepository
from selma.application.ports.evaluator_port import RuleEvaluator
from selma.application.ports.parser_port import SourceParser
from selma.application.ports.reporter_port import FindingReporter
from selma.domain.aggregates.directive import Directive
from selma.domain.aggregates.directive import DirectiveCatalog
from selma.domain.entities.finding import Finding
from selma.domain.entities.rule import Rule
from selma.domain.value_objects.enums import Severity
from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.guidance import RuleGuidance
from selma.domain.value_objects.result import Result

logger = logging.getLogger(__name__)


class InspectSourceUseCase:
    """Application service: inspect source paths against the directive catalog."""

    def __init__(
        self,
        a_parser: SourceParser,
        a_directive_repository: DirectiveRepository,
        a_evaluator: RuleEvaluator,
        a_reporter: FindingReporter | None = None,
    ) -> None:
        self._parser = a_parser
        self._directive_repository = a_directive_repository
        self._evaluator = a_evaluator
        self._reporter = a_reporter

    async def execute(self, a_request: InspectRequest) -> Result[InspectResponse]:
        """Execute inspection.

        Preconditions:
            - Parser and directive repository are available.
        Postconditions:
            Returns Ok with InspectResponse containing findings.
        Side Effects: Reads files, evaluates rules.
        Resource: File handles.
        Failure: Returns Failure on critical error.
        """
        b_continue = True
        result: Result[InspectResponse] = Result.failure("unreachable")
        findings_tuple: tuple[Finding, ...] = ()
        report_text = ""

        catalog_result = await self._directive_repository.list_catalog()
        if catalog_result.is_failure():
            b_continue = False
            msg = f"Failed to load directives: {catalog_result.message}"
            logger.warning(msg)
            result = Result.failure(msg)

        rules: tuple[Rule, ...] = ()
        catalog: DirectiveCatalog | None = None
        if b_continue:
            catalog = catalog_result.unwrap()
            rules_result = self._filter_rules(catalog, a_request)
            if rules_result.is_failure():
                b_continue = False
                msg = rules_result.message
                logger.warning(msg)
                result = Result.failure(msg)
            if b_continue:
                rules = rules_result.unwrap()

        all_findings: list[Finding] = []
        if b_continue and a_request.paths:
            file_results = await asyncio.gather(
                *[self._inspect_file(path, rules, catalog) for path in a_request.paths]
            )
            for file_result in file_results:
                if file_result.is_success():
                    all_findings.extend(file_result.unwrap())

        if b_continue:
            findings_tuple = tuple(all_findings)
            if self._reporter is not None:
                report_result = await self._reporter.report(findings_tuple)
                if report_result.is_failure():
                    b_continue = False
                    msg = f"Reporting failed: {report_result.message}"
                    logger.warning(msg)
                    result = Result.failure(msg)
                if b_continue:
                    report_text = report_result.unwrap()
            if b_continue:
                response = InspectResponse(
                    findings=findings_tuple,
                    summary=f"Found {len(all_findings)} issues",
                    has_errors=any(f.is_violation for f in all_findings),
                    report_text=report_text,
                )
                result = Result.success(response)

        return result

    def _filter_rules(
        self,
        a_catalog: DirectiveCatalog,
        a_request: InspectRequest,
    ) -> Result[tuple[Rule, ...]]:
        """Select executable rules from the catalog for this request."""
        b_continue = True
        result: Result[tuple[Rule, ...]] = Result.failure("unreachable")
        rules: tuple[Rule, ...]

        if a_request.codes:
            matched = a_catalog.find_by_codes(tuple(a_request.codes))
            rules = tuple(d.rule for d in matched if d.is_active())
        else:
            rules = a_catalog.list_active_rules()

        if b_continue and a_request.exclude_codes:
            rules = tuple(
                r for r in rules if r.lineage_id not in a_request.exclude_codes
            )
        if b_continue and a_request.only:
            rules = tuple(r for r in rules if r.evaluator_type == a_request.only)
        if b_continue:
            result = Result.success(rules)
        return result

    async def _inspect_file(
        self,
        a_path: FilePath,
        a_rules: tuple[Rule, ...],
        a_catalog: DirectiveCatalog | None,
    ) -> Result[list[Finding]]:
        """Inspect a single file against all selected rules concurrently."""
        b_continue = True
        result: Result[list[Finding]] = Result.failure("unreachable")

        parse_result = await self._parser.parse(a_path)
        if parse_result.is_failure():
            b_continue = False
            logger.warning("Failed to parse %s: %s", a_path, parse_result.message)
            msg = f"Failed to parse {a_path}: {parse_result.message}"
            result = Result.failure(msg)

        if b_continue:
            tree = parse_result.unwrap()
            rule_results = await asyncio.gather(
                *[
                    self._evaluate_rule(rule, tree, a_path, a_catalog)
                    for rule in a_rules
                ]
            )
            findings: list[Finding] = []
            for rule_result in rule_results:
                findings.extend(rule_result)
            result = Result.success(findings)

        return result

    async def _evaluate_rule(
        self,
        a_rule: Rule,
        a_tree: ast.AST,
        a_path: FilePath,
        a_catalog: DirectiveCatalog | None,
    ) -> list[Finding]:
        """Evaluate one rule; attach policy guidance when available."""
        findings: list[Finding] = []
        try:
            eval_result = await self._evaluator.evaluate(
                a_tree=a_tree,
                a_rule=a_rule,
                a_file_path=str(a_path),
            )
            if eval_result.is_success():
                raw = eval_result.unwrap()
                guidance = self._guidance_for(a_rule.lineage_id, a_catalog)
                if guidance is not None:
                    findings = [
                        finding.model_copy(update={"guidance": guidance})
                        if finding.guidance is None
                        else finding
                        for finding in raw
                    ]
                else:
                    findings = raw
        except Exception as exc:
            logger.warning("Rule %s failed on %s: %s", a_rule.lineage_id, a_path, exc)
            findings = [
                Finding(
                    rule_id=a_rule.lineage_id,
                    file=str(a_path),
                    line=0,
                    col=0,
                    message=f"Internal rule error: {exc}",
                    severity=Severity.LOW,
                    filepath=str(a_path),
                )
            ]
        return findings

    @staticmethod
    def _guidance_for(
        a_lineage_id: str,
        a_catalog: DirectiveCatalog | None,
    ) -> RuleGuidance | None:
        """Project policy guidance for a rule id (reasoning only)."""
        b_continue = True
        result: RuleGuidance | None = None
        if b_continue and a_catalog is None:
            b_continue = False
        directive: Directive | None = None
        if b_continue and a_catalog is not None:
            directive = a_catalog.find_by_lineage_id(a_lineage_id)
            if directive is None:
                b_continue = False
        if b_continue and directive is not None:
            result = directive.reasoning_guidance()
        return result
