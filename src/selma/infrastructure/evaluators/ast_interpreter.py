"""ASTInterpreter — main engine that dispatches JSON rules to evaluator strategies."""

from __future__ import annotations

import ast
import logging
from typing import Any

from selma.domain.entities.finding import Finding
from selma.domain.value_objects.result import Result
from selma.domain.value_objects.severity import Severity
from selma.infrastructure.evaluators.ast_call_check import AstCallCheckEvaluator
from selma.infrastructure.evaluators.ast_context_check import AstContextCheckEvaluator
from selma.infrastructure.evaluators.ast_module_check import AstModuleCheckEvaluator
from selma.infrastructure.evaluators.ast_node_match import AstNodeMatchEvaluator
from selma.infrastructure.evaluators.ast_scope_check import AstScopeCheckEvaluator
from selma.infrastructure.evaluators.ast_walk import AstWalkEvaluator
from selma.infrastructure.evaluators.base import EvaluatorBase

logger = logging.getLogger(__name__)

_EVALUATOR_MAP: dict[str, type[EvaluatorBase]] = {
    "ast_walk": AstWalkEvaluator,
    "ast_node_match": AstNodeMatchEvaluator,
    "ast_scope_check": AstScopeCheckEvaluator,
    "ast_call_check": AstCallCheckEvaluator,
    "ast_context_check": AstContextCheckEvaluator,
    "ast_module_check": AstModuleCheckEvaluator,
}


class ASTInterpreter:
    """Interpret JSON rule definitions against Python AST.

    The interpreter reads the evaluator_type from a rule dict,
    looks up the corresponding evaluator strategy, and delegates
    evaluation to it.
    """

    def __init__(self) -> None:
        self._evaluators: dict[str, EvaluatorBase] = {}
        for name, cls in _EVALUATOR_MAP.items():
            self._evaluators[name] = cls()

    def evaluate(
        self,
        a_tree: ast.AST,
        a_rule: dict[str, Any],
        a_file_path: str = "",
        a_source_code: str = "",
    ) -> Result[list[Finding]]:
        """Evaluate a single rule against an AST.

        Preconditions:
            - a_tree is a valid parsed AST.
            - a_rule is a dict loaded from a JSON rule file.
            - a_file_path is the file path for findings.

        Postconditions:
            Returns Result.success(list[Finding]) or Result.failure(...).

        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on unknown evaluator type.
        """
        b_continue = True
        result: Result[list[Finding]] = Result.failure("unreachable")
        evaluator_type = a_rule.get("evaluator_type", "")
        config = a_rule.get("evaluator_config", {})
        if b_continue and evaluator_type not in self._evaluators:
            b_continue = False
            logger.warning("Unknown evaluator type: %s", evaluator_type)
            result = Result.failure(f"Unknown evaluator type: {evaluator_type}")
        if b_continue:
            evaluator = self._evaluators[evaluator_type]
            try:
                findings = evaluator.evaluate(a_tree, config, a_rule, a_source_code)
                enriched = self._enrich_findings(findings, a_file_path, a_rule)
                result = Result.success(enriched)
            except Exception as exc:
                logger.warning("Evaluator %s failed: %s", evaluator_type, exc)
                b_continue = False
                result = Result.failure(f"Evaluator error: {exc}")
        return result

    def evaluate_many(
        self,
        a_tree: ast.AST,
        a_rules: list[dict[str, Any]],
        a_file_path: str = "",
        a_source_code: str = "",
    ) -> Result[list[Finding]]:
        """Evaluate multiple rules against an AST.

        Preconditions:
            - a_tree is a valid parsed AST.
            - a_rules is a list of rule dicts.

        Postconditions:
            Returns Result.success with all findings merged.

        Side Effects: None.
        Resource: None.
        Failure: Never fails — skips invalid rules.
        """
        b_continue = True
        all_findings: list[Finding] = []
        for rule in a_rules:
            eval_result = self.evaluate(a_tree, rule, a_file_path, a_source_code)
            if b_continue and eval_result.is_success():
                all_findings.extend(eval_result.unwrap())
        result = Result.success(all_findings)
        return result

    @staticmethod
    def _enrich_findings(
        a_findings: list[Finding],
        a_file_path: str,
        a_rule: dict[str, Any],
    ) -> list[Finding]:
        """Enrich findings with file path and severity from rule."""
        b_continue = True
        enriched: list[Finding] = []
        if b_continue and not a_findings:
            b_continue = False
            enriched = []
        if b_continue:
            severity = Severity.MEDIUM
            weight = a_rule.get("weight", "medium")
            try:
                severity = Severity(weight)
            except ValueError:
                severity = Severity.MEDIUM
            for finding in a_findings:
                enriched.append(
                    Finding(
                        rule_id=finding.rule_id,
                        file=a_file_path,
                        line=finding.line,
                        col=finding.col,
                        message=finding.message,
                        severity=severity,
                        guidance=finding.guidance,
                        filepath=a_file_path,
                    )
                )
        return enriched
