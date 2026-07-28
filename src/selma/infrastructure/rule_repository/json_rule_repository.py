"""JSON rule repository — loads rules from JSON files.

Implements the RuleRepository port from the application layer.

Machine lint logic comes exclusively from directive/rule/*.json.
Optional policy YAML under directive/policy/ supplies human guidance
(examples, reasoning) only — never evaluator configuration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from typing import cast

import yaml

from selma.application.ports.rule_repository_port import RuleRepository
from selma.domain.entities.rule import EvaluatorConfig
from selma.domain.entities.rule import RuleDefinition
from selma.domain.value_objects.guidance import RuleGuidance
from selma.domain.value_objects.result import Result
from selma.domain.value_objects.rule_id import RuleId
from selma.infrastructure.config.rule_schema_models import Rule
from selma.infrastructure.config.rule_schema_validator import RuleSchemaValidator


class JsonRuleRepository(RuleRepository):
    """Load rules from JSON files from a configured rules directory.

    Implements RuleRepository port. Caches loaded rules.
    The rules directory and schema path MUST be provided — no hardcoded defaults.
    Optional policy_dir attaches guidance from paired YAML doctrines (not lint).
    """

    def __init__(
        self,
        a_rules_dir: Path,
        a_schema_path: Path,
        a_policy_dir: Path | None = None,
    ) -> None:
        self._rules_dir = a_rules_dir
        self._policy_dir = a_policy_dir
        self._cached_rules: tuple[RuleDefinition, ...] | None = None
        self._schema_validator = RuleSchemaValidator(a_schema_path=a_schema_path)

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
            active = tuple(rule for rule in rules if rule.is_active())
            result = Result.success(active)

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
                        parse_result = self._parse_rule(raw_rule, a_path)
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

    def _parse_rule(
        self, a_raw: dict[str, Any], a_rule_path: Path
    ) -> Result[RuleDefinition]:
        """Validate via jschon JSON Schema + Pydantic, then map to domain RuleDefinition."""
        b_continue = True
        result: Result[RuleDefinition] = Result.failure("unreachable")

        validation = self._schema_validator.validate_document(a_raw)
        if validation.is_failure():
            b_continue = False
            result = Result.failure(validation.message)

        if b_continue:
            document = validation.unwrap()
            mapped = self._map_document(document, a_rule_path)
            if mapped.is_failure():
                b_continue = False
                result = Result.failure(mapped.message)
            if b_continue:
                result = Result.success(mapped.unwrap())

        return result

    @staticmethod
    def _as_mapping(a_value: object) -> dict[str, object] | None:
        """Return a string-keyed mapping when the value is a dict."""
        b_continue = True
        result: dict[str, object] | None = None
        if b_continue and not isinstance(a_value, dict):
            b_continue = False
        if b_continue:
            raw = cast("dict[object, object]", a_value)
            result = {key: value for key, value in raw.items() if isinstance(key, str)}
        return result

    @staticmethod
    def _str_field(a_map: dict[str, object], a_key: str, a_default: str = "") -> str:
        """Read a map field as a string with a default."""
        value = a_map.get(a_key)
        if value is None:
            return a_default
        return str(value)

    def _load_policy_guidance(
        self, a_rule_path: Path, a_lineage_id: str, a_message: str
    ) -> RuleGuidance | None:
        """Load human guidance from paired policy YAML (never used for lint)."""
        b_continue = True
        result: RuleGuidance | None = None
        if b_continue and self._policy_dir is None:
            b_continue = False
        policy_path: Path | None = None
        if b_continue and self._policy_dir is not None:
            policy_path = self._policy_dir / f"{a_rule_path.stem}.yaml"
            if not policy_path.is_file():
                b_continue = False
                policy_path = None
        if b_continue and policy_path is not None:
            try:
                with policy_path.open("r", encoding="utf-8") as handle:
                    raw_obj: object = yaml.safe_load(handle)
                data = self._as_mapping(raw_obj)
                if data is None:
                    b_continue = False
                if b_continue and data is not None:
                    # Contamination guard: never accept machine evaluator fields
                    # as guidance carriers even if a bad policy file contains them.
                    for forbidden in (
                        "evaluator_type",
                        "evaluator_config",
                        "evaluator_hint",
                    ):
                        if forbidden in data:
                            b_continue = False
                if b_continue and data is not None:
                    guide_d = self._as_mapping(data.get("guidance")) or {}
                    title = a_lineage_id
                    directives = self._as_mapping(data.get("directives"))
                    if directives is not None:
                        specs_obj = directives.get("specific_directives")
                        if isinstance(specs_obj, list) and specs_obj:
                            specs_list = cast("list[object]", specs_obj)
                            first = self._as_mapping(specs_list[0])
                            if first is not None:
                                title = (
                                    self._str_field(first, "title")
                                    or self._str_field(first, "machine_id")
                                    or a_lineage_id
                                )
                    related: list[str] = []
                    related_raw = guide_d.get("related_machine_ids")
                    if isinstance(related_raw, list):
                        for item in cast("list[object]", related_raw):
                            related.append(str(item))
                    doctrine_section = ""
                    refs = self._as_mapping(data.get("references"))
                    if refs is not None:
                        doctrine_section = self._str_field(refs, "anchor_ref")
                    fix_instructions = ""
                    sanctions = self._as_mapping(data.get("sanctions"))
                    if sanctions is not None:
                        rows_obj = sanctions.get("rows")
                        if isinstance(rows_obj, list) and rows_obj:
                            rows_list = cast("list[object]", rows_obj)
                            first_row = self._as_mapping(rows_list[0])
                            if first_row is not None:
                                fix_instructions = self._str_field(
                                    first_row, "remediation_path"
                                )
                    if not fix_instructions:
                        fix_instructions = (
                            self._str_field(guide_d, "explanation") or a_message
                        )
                    result = RuleGuidance(
                        rule_code=a_lineage_id,
                        title=title,
                        description=self._str_field(guide_d, "explanation")
                        or a_message,
                        rationale=self._str_field(guide_d, "reasoning"),
                        severity="",
                        fix_instructions=fix_instructions,
                        correct_example=self._str_field(guide_d, "correct_example"),
                        anti_pattern=self._str_field(guide_d, "incorrect_example"),
                        related_rules=tuple(related),
                        doctrine_section=doctrine_section,
                        hints=(),
                    )
            except (OSError, yaml.YAMLError):
                result = None
        return result

    def _map_document(self, a_doc: Rule, a_rule_path: Path) -> Result[RuleDefinition]:
        """Map a validated Rule model to a domain RuleDefinition."""
        b_continue = True
        result: Result[RuleDefinition] = Result.failure("unreachable")

        ec_result = self._parse_evaluator_config(a_doc.evaluator_config)
        if ec_result.is_failure():
            b_continue = False
            result = Result.failure(ec_result.message)

        if b_continue:
            guidance = self._load_policy_guidance(
                a_rule_path=a_rule_path,
                a_lineage_id=a_doc.lineage_id,
                a_message=a_doc.message,
            )
            rule = RuleDefinition(
                lineage_id=a_doc.lineage_id,
                id=a_doc.id,
                rule_type=a_doc.type,
                message=a_doc.message,
                evaluator_type=str(a_doc.evaluator_type.value)
                if hasattr(a_doc.evaluator_type, "value")
                else str(a_doc.evaluator_type),
                evaluator_config=ec_result.unwrap(),
                weight=a_doc.weight,
                priority=a_doc.priority,
                status=a_doc.status,
                created_at=a_doc.created_at,
                rationale=a_doc.rationale,
                remediation=a_doc.remediation,
                guidance=guidance.model_dump() if guidance else None,
                parameters=dict(a_doc.parameters),
                depends_on=tuple(a_doc.depends_on),
                conflicts_with=tuple(a_doc.conflicts_with),
                anchor_ref=a_doc.anchor_ref,
                scope=a_doc.scope.model_dump() if a_doc.scope else None,
                conflict_resolution=a_doc.conflict_resolution.model_dump()
                if a_doc.conflict_resolution
                else None,
            )
            result = Result.success(rule)
        return result

    def _parse_evaluator_config(
        self,
        a_raw: dict[str, Any],
        a_depth: int = 0,
        a_max_depth: int = 32,
    ) -> Result[EvaluatorConfig]:
        """Parse raw evaluator config dict into EvaluatorConfig.

        Uses EvaluatorConfig's extra="allow" to accept any fields.
        a_depth / a_max_depth guard nested sub_evaluators (SC-114).
        """
        b_continue = True
        result: Result[EvaluatorConfig] = Result.failure("unreachable")

        if b_continue and a_depth >= a_max_depth:
            b_continue = False
            result = Result.failure(
                f"Evaluator config nesting exceeds max depth {a_max_depth}"
            )

        sub_evaluators: tuple[EvaluatorConfig, ...] = ()
        if b_continue:
            sub_raw: list[dict[str, Any]] = []
            raw_subs_obj: object = a_raw.get("sub_evaluators", [])
            if isinstance(raw_subs_obj, list):
                for item in cast("list[object]", raw_subs_obj):
                    if isinstance(item, dict):
                        sub_raw.append(cast("dict[str, Any]", item))

            if sub_raw:
                parsed_subs: list[EvaluatorConfig] = []
                for sub_item in sub_raw:
                    sub_result = self._parse_evaluator_config(
                        sub_item,
                        a_depth=a_depth + 1,
                        a_max_depth=a_max_depth,
                    )
                    if sub_result.is_failure():
                        b_continue = False
                        result = Result.failure(f"Sub-evaluator: {sub_result.message}")
                        break
                    parsed_subs.append(sub_result.unwrap())
                if b_continue:
                    sub_evaluators = tuple(parsed_subs)

        if b_continue:
            config = EvaluatorConfig(
                pattern=a_raw.get("pattern"),
                flags=a_raw.get("flags"),
                field=a_raw.get("field"),
                operator=a_raw.get("operator"),
                value=a_raw.get("value"),
                threshold=a_raw.get("threshold"),
                logic=a_raw.get("logic"),
                sub_evaluators=sub_evaluators,
                **{
                    k: v
                    for k, v in a_raw.items()
                    if k
                    not in {
                        "pattern",
                        "flags",
                        "field",
                        "operator",
                        "value",
                        "threshold",
                        "logic",
                        "sub_evaluators",
                    }
                },
            )
            result = Result.success(config)

        return result

    def invalidate_cache(self) -> None:
        """Clear the cached rules."""
        self._cached_rules = None
