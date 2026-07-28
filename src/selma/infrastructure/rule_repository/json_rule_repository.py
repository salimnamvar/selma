"""Filesystem directive repository — pairs rule JSON with policy YAML.

Implements DirectiveRepository and RuleRepository. Maps into domain only.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any
from typing import cast

from selma.application.ports.directive_repository_port import DirectiveRepository
from selma.domain.aggregates.directive import Directive
from selma.domain.aggregates.directive import DirectiveCatalog
from selma.domain.entities.policy import DirectivePolicy
from selma.domain.entities.rule import EvaluatorConfig
from selma.domain.entities.rule import Rule
from selma.domain.value_objects.result import Result
from selma.domain.value_objects.rule_id import RuleId
from selma.infrastructure.config.policy_doctrine_validator import (
    PolicyDoctrineValidator,
)
from selma.infrastructure.config.rule_schema_validator import RuleSchemaValidator

logger = logging.getLogger(__name__)


class JsonRuleRepository(DirectiveRepository):
    """Load directives from directive/rule and optional directive/policy."""

    def __init__(
        self,
        a_rules_dir: Path,
        a_schema_path: Path,
        a_policy_dir: Path | None = None,
    ) -> None:
        self._rules_dir = a_rules_dir
        self._policy_dir = a_policy_dir
        self._cached_catalog: DirectiveCatalog | None = None
        self._schema_validator = RuleSchemaValidator(a_schema_path=a_schema_path)
        self._policy_validator = PolicyDoctrineValidator()

    async def list_catalog(self) -> Result[DirectiveCatalog]:
        """Load the full directive catalog (cached)."""
        return await asyncio.to_thread(self._list_catalog_sync)

    async def list_active_rules(self) -> Result[tuple[Rule, ...]]:
        """List executable rules for inspection."""
        catalog_result = await self.list_catalog()
        if catalog_result.is_failure():
            return Result.failure(catalog_result.message)
        return Result.success(catalog_result.unwrap().list_active_rules())

    async def find_by_lineage_id(self, a_id: RuleId) -> Result[Directive]:
        """Find one directive by lineage id."""
        catalog_result = await self.list_catalog()
        if catalog_result.is_failure():
            return Result.failure(catalog_result.message)
        found = catalog_result.unwrap().find_by_lineage_id(a_id.value)
        if found is None:
            return Result.failure(f"Directive not found: {a_id}")
        return Result.success(found)

    async def find_by_codes(
        self, a_codes: tuple[str, ...]
    ) -> Result[tuple[Directive, ...]]:
        """Find directives matching codes."""
        catalog_result = await self.list_catalog()
        if catalog_result.is_failure():
            return Result.failure(catalog_result.message)
        return Result.success(catalog_result.unwrap().find_by_codes(a_codes))

    async def get_policy(self, a_id: RuleId) -> Result[DirectivePolicy]:
        """Get reasoning policy for a Machine ID."""
        directive_result = await self.find_by_lineage_id(a_id)
        if directive_result.is_failure():
            return Result.failure(directive_result.message)
        policy = directive_result.unwrap().policy
        if policy is None:
            return Result.failure(f"No policy for directive: {a_id}")
        return Result.success(policy)

    async def get_rule(self, a_id: RuleId) -> Result[Rule]:
        """Get executable rule for a Machine ID."""
        directive_result = await self.find_by_lineage_id(a_id)
        if directive_result.is_failure():
            return Result.failure(directive_result.message)
        return Result.success(directive_result.unwrap().rule)

    def invalidate_cache(self) -> None:
        """Clear the cached catalog."""
        self._cached_catalog = None

    def _list_catalog_sync(self) -> Result[DirectiveCatalog]:
        """Synchronous catalog load with cache."""
        b_continue = True
        result: Result[DirectiveCatalog] = Result.failure("unreachable")

        if self._cached_catalog is not None:
            b_continue = False
            result = Result.success(self._cached_catalog)

        if b_continue:
            load_result = self._load_catalog()
            if load_result.is_failure():
                b_continue = False
                msg = load_result.message
                logger.warning(msg)
                result = Result.failure(msg)
            if b_continue:
                self._cached_catalog = load_result.unwrap()
                result = Result.success(self._cached_catalog)

        return result

    def _load_catalog(self) -> Result[DirectiveCatalog]:
        """Load all rule JSON files and pair with policy YAML."""
        b_continue = True
        result: Result[DirectiveCatalog] = Result.failure("unreachable")
        directives: list[Directive] = []

        if b_continue and not self._rules_dir.exists():
            b_continue = False
            result = Result.success(DirectiveCatalog(directives=()))

        if b_continue:
            json_files = sorted(self._rules_dir.glob("*.json"))
            for file_path in json_files:
                if b_continue:
                    load_result = self._load_rule_file(file_path)
                    if load_result.is_failure():
                        b_continue = False
                        msg = f"Failed to load {file_path.name}: {load_result.message}"
                        logger.warning(msg)
                        result = Result.failure(msg)
                    if b_continue and load_result.is_success():
                        for rule in load_result.unwrap():
                            policy = self._load_policy_for_rule(file_path, rule)
                            directives.append(Directive(rule=rule, policy=policy))

        if b_continue:
            catalog = DirectiveCatalog(directives=tuple(directives))
            result = Result.success(catalog)

        return result

    def _load_rule_file(self, a_path: Path) -> Result[tuple[Rule, ...]]:
        """Load rules from a single JSON file."""
        b_continue = True
        result: Result[tuple[Rule, ...]] = Result.failure("unreachable")

        try:
            with a_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            raw_rules = data.get("rules", [])
            if not raw_rules and "lineage_id" in data:
                raw_rules = [data]
            parsed: list[Rule] = []
            for raw_rule in cast("list[object]", raw_rules):
                if b_continue and isinstance(raw_rule, dict):
                    parse_result = self._parse_rule(cast("dict[str, Any]", raw_rule))
                    if parse_result.is_failure():
                        b_continue = False
                        msg = parse_result.message
                        logger.warning(msg)
                        result = Result.failure(msg)
                    if b_continue and parse_result.is_success():
                        parsed.append(parse_result.unwrap())
            if b_continue:
                result = Result.success(tuple(parsed))
        except (OSError, json.JSONDecodeError) as exc:
            msg = str(exc)
            logger.warning(msg)
            result = Result.failure(msg)

        return result

    def _parse_rule(self, a_raw: dict[str, Any]) -> Result[Rule]:
        """Validate and normalize a rule document into domain Rule."""
        b_continue = True
        result: Result[Rule] = Result.failure("unreachable")
        raw = dict(a_raw)

        if "evaluator_config" in raw and isinstance(raw["evaluator_config"], dict):
            config_result = self._parse_evaluator_config(
                cast("dict[str, Any]", raw["evaluator_config"])
            )
            if config_result.is_failure():
                b_continue = False
                msg = config_result.message
                logger.warning(msg)
                result = Result.failure(msg)
            if b_continue:
                raw["evaluator_config"] = config_result.unwrap()

        if b_continue:
            validation = self._schema_validator.validate_document(raw)
            if validation.is_failure():
                b_continue = False
                msg = validation.message
                logger.warning(msg)
                result = Result.failure(msg)
            if b_continue:
                result = Result.success(validation.unwrap())

        return result

    def _load_policy_for_rule(
        self, a_rule_path: Path, a_rule: Rule
    ) -> DirectivePolicy | None:
        """Load paired policy YAML; never used for evaluation."""
        b_continue = True
        result: DirectivePolicy | None = None
        if b_continue and self._policy_dir is None:
            b_continue = False
        policy_path: Path | None = None
        if b_continue and self._policy_dir is not None:
            policy_path = self._policy_dir / f"{a_rule_path.stem}.yaml"
            if not policy_path.is_file():
                b_continue = False
                policy_path = None
        if b_continue and policy_path is not None:
            validated = self._policy_validator.validate_directive_file(policy_path)
            if validated.is_success():
                result = validated.unwrap()
        return result

    def _parse_evaluator_config(
        self,
        a_raw: dict[str, Any],
        a_depth: int = 0,
        a_max_depth: int = 32,
    ) -> Result[EvaluatorConfig]:
        """Parse raw evaluator config into domain EvaluatorConfig."""
        b_continue = True
        result: Result[EvaluatorConfig] = Result.failure("unreachable")

        if b_continue and a_depth >= a_max_depth:
            b_continue = False
            msg = f"Evaluator config nesting exceeds max depth {a_max_depth}"
            logger.warning(msg)
            result = Result.failure(msg)

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
                        logger.warning("Sub-evaluator: %s", sub_result.message)
                        result = Result.failure(f"Sub-evaluator: {sub_result.message}")
                        break
                    parsed_subs.append(sub_result.unwrap())
                if b_continue:
                    sub_evaluators = tuple(parsed_subs)

        if b_continue:
            known = {
                "pattern",
                "flags",
                "field",
                "operator",
                "value",
                "threshold",
                "logic",
                "sub_evaluators",
            }
            extras = {k: v for k, v in a_raw.items() if k not in known}
            config = EvaluatorConfig(
                pattern=a_raw.get("pattern"),
                flags=a_raw.get("flags"),
                field=a_raw.get("field"),
                operator=a_raw.get("operator"),
                value=a_raw.get("value"),
                threshold=a_raw.get("threshold"),
                logic=a_raw.get("logic"),
                sub_evaluators=sub_evaluators,
                **extras,
            )
            result = Result.success(config)

        return result
