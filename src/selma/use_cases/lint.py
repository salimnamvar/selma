"""Lint orchestrator for Selma."""

import hashlib
from pathlib import Path

from selma.core.entities.finding import Finding
from selma.core.entities.finding import Weight
from selma.core.entities.rule import Rule
from selma.core.evaluators.composite import CompositeEvaluator
from selma.core.evaluators.field_check import FieldCheckEvaluator
from selma.core.evaluators.regex_eval import RegexEvaluator
from selma.core.evaluators.script import ScriptEvaluator
from selma.core.evaluators.threshold import ThresholdEvaluator
from selma.core.ports.cache_port import AbstractCache
from selma.core.ports.parser_port import AbstractParser


class LintOrchestrator:
    """Orchestrates the linting process."""

    def __init__(
        self,
        rules: list[dict],
        parser: AbstractParser,
        cache: AbstractCache | None = None,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            rules: List of rule dictionaries.
            parser: Parser implementation.
            cache: Optional cache implementation.
        """
        self.rules = [Rule(**rule) for rule in rules]
        self.parser = parser
        self.cache = cache
        self.evaluators = self._create_evaluators()

    def _create_evaluators(self) -> dict[str, object]:
        """Create evaluator instances."""
        field_check = FieldCheckEvaluator()
        regex = RegexEvaluator()
        threshold = ThresholdEvaluator()
        script = ScriptEvaluator()

        return {
            "field_check": field_check,
            "regex": regex,
            "threshold": threshold,
            "composite": CompositeEvaluator(
                {
                    "field_check": field_check,
                    "regex": regex,
                    "threshold": threshold,
                    "script": script,
                },
            ),
            "script": script,
        }

    def lint(self, paths: list[Path]) -> list[Finding]:
        """Lint the given files.

        Args:
            paths: List of file paths to lint.

        Returns:
            List of findings.
        """
        findings: list[Finding] = []

        for path in paths:
            if not path.exists():
                continue

            # Check cache
            if self.cache:
                content = path.read_text(encoding="utf-8")
                file_hash = hashlib.sha256(content.encode()).hexdigest()
                document = self.cache.get(file_hash)
                if document is None:
                    document = self.parser.extract(path, ["lines", "declarations"])
                    self.cache.put(file_hash, document)
            else:
                document = self.parser.extract(path, ["lines", "declarations"])

            # Evaluate rules against declarations
            declarations = document.layers.get("declarations", [])
            for decl in declarations:
                for rule in self.rules:
                    findings.extend(self._evaluate_rule(rule, decl, document.file))

        return findings

    def _evaluate_rule(
        self,
        rule: Rule,
        declaration: object,
        file_path: str,
    ) -> list[Finding]:
        """Evaluate a rule against a declaration."""
        evaluator = self.evaluators.get(rule.evaluator_type)
        if not evaluator:
            return []

        # Convert declaration to dict for evaluator
        if hasattr(declaration, "model_dump"):
            data = declaration.model_dump()
        else:
            data = dict(declaration) if declaration else {}

        config = rule.evaluator_config.model_dump(exclude_none=True)

        if evaluator.evaluate(config, data):
            return [
                Finding(
                    rule_id=rule.id,
                    file=file_path,
                    line=data.get("line", 0),
                    message=rule.message,
                    weight=Weight(rule.weight)
                    if rule.weight in Weight.__members__.values()
                    else Weight.MEDIUM,
                ),
            ]

        return []
