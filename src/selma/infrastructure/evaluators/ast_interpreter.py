"""ASTInterpreter — dispatches executable rules to evaluator strategies."""

from __future__ import annotations

import ast
import asyncio
import logging
from typing import Any

from selma.application.ports.evaluator_port import RuleEvaluator
from selma.domain.entities.finding import Finding
from selma.domain.entities.rule import Rule
from selma.domain.value_objects.enums import Severity
from selma.domain.value_objects.result import Result
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


class ASTInterpreter(RuleEvaluator):
    """Interpret domain Rule objects against Python AST."""

    def __init__(self) -> None:
        self._evaluators: dict[str, EvaluatorBase] = {}
        for name, cls in _EVALUATOR_MAP.items():
            self._evaluators[name] = cls()

    async def evaluate(
        self,
        a_tree: ast.AST,
        a_rule: Rule,
        a_file_path: str = "",
        a_source_code: str = "",
    ) -> Result[list[Finding]]:
        """Evaluate a single rule against an AST (CPU-bound via to_thread)."""
        return await asyncio.to_thread(
            self._evaluate_sync,
            a_tree,
            a_rule,
            a_file_path,
            a_source_code,
        )

    def _evaluate_sync(
        self,
        a_tree: ast.AST,
        a_rule: Rule,
        a_file_path: str = "",
        a_source_code: str = "",
    ) -> Result[list[Finding]]:
        """Blocking evaluation for one rule."""
        b_continue = True
        result: Result[list[Finding]] = Result.failure("unreachable")
        evaluator_type = a_rule.evaluator_type
        config = a_rule.evaluator_config.model_dump()
        if b_continue and evaluator_type not in self._evaluators:
            b_continue = False
            logger.warning("Unknown evaluator type: %s", evaluator_type)
            result = Result.failure(f"Unknown evaluator type: {evaluator_type}")
        if b_continue:
            evaluator = self._evaluators[evaluator_type]
            try:
                rule_dict: dict[str, Any] = {
                    "evaluator_type": a_rule.evaluator_type,
                    "evaluator_config": config,
                    "weight": a_rule.weight.value,
                    "lineage_id": a_rule.lineage_id,
                    "message": a_rule.message,
                    "parameters": a_rule.parameters,
                }
                eval_result = evaluator.evaluate(
                    a_tree, config, rule_dict, a_source_code
                )
                if eval_result.is_success():
                    enriched = self._enrich_findings(
                        eval_result.unwrap(), a_file_path, rule_dict
                    )
                    result = Result.success(enriched)
                else:
                    result = Result.failure(eval_result.message)
            except Exception as exc:
                logger.warning("Evaluator %s failed: %s", evaluator_type, exc)
                b_continue = False
                result = Result.failure(f"Evaluator error: {exc}")
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
            weight = str(a_rule.get("weight", "medium"))
            valid_weights = {member.value for member in Severity}
            if weight in valid_weights:
                severity = Severity(weight)
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
