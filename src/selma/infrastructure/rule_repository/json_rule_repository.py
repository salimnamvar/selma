"""JSON rule repository — loads rules from JSON files.

Implements the RuleRepository port from the application layer.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from selma.application.ports.rule_repository_port import RuleRepository
from selma.domain.entities.rule import EvaluatorConfig
from selma.domain.entities.rule import RuleDefinition
from selma.domain.value_objects.result import Result
from selma.domain.value_objects.rule_id import RuleId
from selma.domain.value_objects.severity import Severity

_DEFAULT_RULES_DIR = Path("schema/rules")


class JsonRuleRepository(RuleRepository):
    """Load rules from JSON files in the schema/rules/ directory.

    Implements RuleRepository port. Caches loaded rules.
    """

    def __init__(self, a_rules_dir: Path | None = None) -> None:
        self._rules_dir = a_rules_dir or _DEFAULT_RULES_DIR
        self._cached_rules: tuple[RuleDefinition, ...] | None = None

    def find_all(
        self,
    ) -> Result[tuple[RuleDefinition, ...]]:
        """Retrieve all active rules.

        Preconditions: None.
        Postconditions: Returns Ok with tuple of all active rules.
        Side Effects: None.
        Resource: Reads JSON files on first call, then cached.
        Failure: Returns Failure on load error.
        """
        b_continue = True
        result: Result[tuple[RuleDefinition, ...]] = Result.failure("unreachable")

        if b_continue and self._cached_rules is not None:
            b_continue = False
            result = Result.success(self._cached_rules)

        if b_continue:
            load_result = self._load_all_rules()
            if b_continue and load_result.is_failure():
                b_continue = False
                result = Result.failure(load_result.message)
            if b_continue and load_result.is_success():
                self._cached_rules = load_result.value
                result = Result.success(load_result.unwrap())

        return result

    def find_by_id(self, a_id: RuleId) -> Result[RuleDefinition]:
        """Retrieve a rule by ID.

        Preconditions: None.
        Postconditions: Returns Ok with rule, or Failure if
        not found.
        Side Effects: None.
        Resource: None.
        Failure: Returns Failure if rule not found.
        """
        b_continue = True
        result: Result[RuleDefinition] = Result.failure("unreachable")
        all_rules_result = self.find_all()

        if b_continue and all_rules_result.is_failure():
            b_continue = False
            result = Result.failure(all_rules_result.message)
        if b_continue:
            found: RuleDefinition | None = None
            for rule in all_rules_result.unwrap():
                if b_continue and RuleId(rule.lineage_id) == a_id:
                    b_continue = False
                    found = rule
            if b_continue:
                result = Result.failure(f"Rule not found: {a_id}")
            if not b_continue and found is not None:
                result = Result.success(found)

        return result

    def find_by_codes(
        self, a_codes: tuple[str, ...]
    ) -> Result[tuple[RuleDefinition, ...]]:
        """Retrieve rules by code list.

        Preconditions: None.
        Postconditions: Returns Ok with matching rules.
        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on load error.
        """
        b_continue = True
        result: Result[tuple[RuleDefinition, ...]] = Result.failure("unreachable")
        all_rules_result = self.find_all()

        if b_continue and all_rules_result.is_failure():
            b_continue = False
            result = Result.failure(all_rules_result.message)
        if b_continue:
            codes_set = frozenset(a_codes)
            matched = tuple(
                rule
                for rule in all_rules_result.unwrap()
                if rule.lineage_id in codes_set or rule.id in codes_set
            )
            result = Result.success(matched)

        return result

    def _load_all_rules(
        self,
    ) -> Result[tuple[RuleDefinition, ...]]:
        """Load all JSON rule files from the rules directory."""
        b_continue = True
        result: Result[tuple[RuleDefinition, ...]] = Result.failure("unreachable")
        rules: list[RuleDefinition] = []

        if b_continue and not self._rules_dir.exists():
            b_continue = False
            result = Result.success(())

        if b_continue:
            json_files = sorted(self._rules_dir.glob("*.json"))
            for file_path in json_files:
                if b_continue:
                    load_result = self._load_rule_file(file_path)
                    if b_continue and load_result.is_failure():
                        b_continue = False
                        msg = f"Failed to load {file_path.name}: {load_result.message}"
                        result = Result.failure(msg)
                    if b_continue and load_result.is_success():
                        rules.extend(load_result.unwrap())

        if b_continue:
            result = Result.success(tuple(rules))

        return result

    def _load_rule_file(self, a_path: Path) -> Result[tuple[RuleDefinition, ...]]:
        """Load rules from a single JSON file.

        Supports both formats:
        - Individual rule object: {"lineage_id": "SC-001", ...}
        - Wrapped dataset: {"rules": [{"lineage_id": "SC-001", ...}]}
        """
        b_continue = True
        result: Result[tuple[RuleDefinition, ...]] = Result.failure("unreachable")

        try:
            data: dict[str, Any] = {}
            if b_continue:
                with a_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            if b_continue:
                raw_rules = data.get("rules", [])
                if not raw_rules and "lineage_id" in data:
                    raw_rules = [data]
                parsed: list[RuleDefinition] = []
                for raw_rule in raw_rules:
                    if b_continue:
                        parse_result = self._parse_rule(raw_rule)
                        if b_continue and parse_result.is_failure():
                            b_continue = False
                            result = Result.failure(parse_result.message)
                        if b_continue and parse_result.is_success():
                            parsed.append(parse_result.unwrap())
                if b_continue:
                    result = Result.success(tuple(parsed))
        except (OSError, json.JSONDecodeError) as e:
            result = Result.failure(str(e))

        return result

    def _parse_rule(self, a_raw: dict[str, Any]) -> Result[RuleDefinition]:
        """Parse a raw JSON rule dict into a RuleDefinition."""
        b_continue = True
        result: Result[RuleDefinition] = Result.failure("unreachable")

        lineage_id = a_raw.get("lineage_id", "")
        if b_continue and not lineage_id:
            b_continue = False
            result = Result.failure("Rule missing lineage_id")

        rule_id = a_raw.get("id", "")
        if b_continue and not rule_id:
            b_continue = False
            result = Result.failure("Rule missing id")

        rule_type = a_raw.get("type", "")
        if b_continue and not rule_type:
            b_continue = False
            result = Result.failure(f"Rule {lineage_id} missing type")

        message = a_raw.get("message", "")
        if b_continue and not message:
            b_continue = False
            result = Result.failure(f"Rule {lineage_id} missing message")

        evaluator_type = a_raw.get("evaluator_type", "")
        if b_continue and not evaluator_type:
            b_continue = False
            result = Result.failure(f"Rule {lineage_id} missing evaluator_type")

        evaluator_config = EvaluatorConfig()
        ec_raw = a_raw.get("evaluator_config", {})
        if b_continue:
            ec_result = self._parse_evaluator_config(ec_raw)
            if b_continue and ec_result.is_failure():
                b_continue = False
                msg = f"Rule {lineage_id}: {ec_result.message}"
                result = Result.failure(msg)
            if b_continue and ec_result.is_success():
                evaluator_config = ec_result.unwrap()

        status = a_raw.get("status", "active")
        created_at = a_raw.get("created_at", "")
        rationale = a_raw.get("rationale", "")
        remediation = a_raw.get("remediation", "")
        parameters = a_raw.get("parameters", {})
        depends_on = tuple(a_raw.get("depends_on", []))
        conflicts_with = tuple(a_raw.get("conflicts_with", []))

        weight_str = a_raw.get("weight", "medium")
        valid_weights = frozenset(
            {
                "critical",
                "high",
                "medium",
                "low",
                "informational",
            }
        )
        weight = (
            Severity(weight_str) if weight_str in valid_weights else Severity.MEDIUM
        )

        priority = a_raw.get("priority", "operational")

        if b_continue:
            rule = RuleDefinition(
                lineage_id=lineage_id,
                id=rule_id,
                rule_type=rule_type,
                message=message,
                evaluator_type=evaluator_type,
                evaluator_config=evaluator_config,
                weight=weight,
                priority=priority,
                status=status,
                created_at=created_at,
                rationale=rationale,
                remediation=remediation,
                parameters=parameters,
                depends_on=depends_on,
                conflicts_with=conflicts_with,
            )
            result = Result.success(rule)

        return result

    def _parse_evaluator_config(self, a_raw: dict[str, Any]) -> Result[EvaluatorConfig]:
        """Parse raw evaluator config dict into EvaluatorConfig."""
        b_continue = True
        result: Result[EvaluatorConfig] = Result.failure("unreachable")

        pattern = a_raw.get("pattern")
        flags = a_raw.get("flags")
        field = a_raw.get("field")
        operator = a_raw.get("operator")
        value = a_raw.get("value")
        threshold = a_raw.get("threshold")
        logic = a_raw.get("logic")
        target_node = a_raw.get("target_node")
        walk_nodes = tuple(a_raw.get("walk_nodes", []))
        conditions = tuple(a_raw.get("conditions", []))
        fc_raw: list[dict[str, str]] = a_raw.get("forbidden_calls", [])
        forbidden_calls = tuple(
            {
                "name": fc.get("name", ""),
                "module": fc.get("module", ""),
            }
            for fc in fc_raw
        )
        forbidden_functions = tuple(a_raw.get("forbidden_functions", []))
        resource_calls = tuple(a_raw.get("resource_calls", []))
        execute_methods = tuple(a_raw.get("execute_methods", []))
        sql_keywords = tuple(a_raw.get("sql_keywords", []))
        io_calls = tuple(a_raw.get("io_calls", []))
        check_first_arg = a_raw.get("check_first_arg", {})
        count = a_raw.get("count", {})
        message_template = a_raw.get("message_template", "")
        exempt_dunders = a_raw.get("exempt_dunders", True)
        exempt_generators = a_raw.get("exempt_generators", True)
        exempt_names = tuple(a_raw.get("exempt_names", []))
        max_lines = a_raw.get("max_lines", 60)

        sub_raw = a_raw.get("sub_evaluators", [])
        sub_evaluators: tuple[EvaluatorConfig, ...] = ()
        if sub_raw:
            parsed_subs: list[EvaluatorConfig] = []
            for sub_item in sub_raw:
                sub_result = self._parse_evaluator_config(sub_item)
                if b_continue and sub_result.is_failure():
                    b_continue = False
                    msg = f"Sub-evaluator: {sub_result.message}"
                    result = Result.failure(msg)
                if b_continue and sub_result.is_success():
                    parsed_subs.append(sub_result.unwrap())
            if b_continue:
                sub_evaluators = tuple(parsed_subs)

        if b_continue:
            config = EvaluatorConfig(
                pattern=pattern,
                flags=flags,
                target_field=field,
                operator=operator,
                value=value,
                threshold=threshold,
                logic=logic,
                sub_evaluators=sub_evaluators,
                target_node=target_node,
                walk_nodes=walk_nodes,
                conditions=conditions,
                forbidden_calls=forbidden_calls,
                forbidden_functions=forbidden_functions,
                resource_calls=resource_calls,
                execute_methods=execute_methods,
                sql_keywords=sql_keywords,
                io_calls=io_calls,
                check_first_arg=check_first_arg,
                count=count,
                message_template=message_template,
                exempt_dunders=exempt_dunders,
                exempt_generators=exempt_generators,
                exempt_names=exempt_names,
                max_lines=max_lines,
            )
            result = Result.success(config)

        return result

    def invalidate_cache(self) -> None:
        """Clear the cached rules."""
        self._cached_rules = None
