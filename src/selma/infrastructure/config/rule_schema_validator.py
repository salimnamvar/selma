"""JSON Schema validation using jschon + domain Pydantic models.

Structural validation (jschon) applies to pure schema evaluator types.
Language-specific engine types (ast_*) are validated with domain Pydantic only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from typing import cast

import jschon
from jschon.exc import JSONError as JschonJSONError

from selma.domain.entities.rule import Rule
from selma.domain.entities.rule import RuleDataset
from selma.domain.value_objects.enums import PureEvaluatorType
from selma.domain.value_objects.result import Result


class RuleSchemaValidator:
    """Validate rule JSON into domain Rule / RuleDataset models."""

    def __init__(self, a_schema_path: Path) -> None:
        self._schema_path = a_schema_path
        self._catalog = jschon.create_catalog("2020-12")
        self._schema: jschon.JSONSchema | None = None

    def _ensure_schema(self) -> Result[jschon.JSONSchema]:
        """Load and cache the JSON Schema from disk."""
        b_continue = True
        result: Result[jschon.JSONSchema] = Result.failure("unreachable")

        if self._schema is not None:
            b_continue = False
            result = Result.success(self._schema)

        schema_dict: dict[str, Any] | None = None
        if b_continue:
            try:
                with self._schema_path.open("r", encoding="utf-8") as handle:
                    loaded = json.load(handle)
                if not isinstance(loaded, dict):
                    b_continue = False
                    result = Result.failure("rule schema root must be an object")
                else:
                    schema_dict = cast("dict[str, Any]", loaded)
            except (OSError, json.JSONDecodeError) as exc:
                b_continue = False
                result = Result.failure(f"Failed to load rule schema: {exc}")

        if b_continue and schema_dict is not None:
            try:
                self._schema = jschon.JSONSchema(
                    schema_dict,  # type: ignore[arg-type]
                    catalog=self._catalog,
                )
                result = Result.success(self._schema)
            except JschonJSONError as exc:
                result = Result.failure(f"Failed to create jschon schema: {exc}")

        return result

    @staticmethod
    def _is_pure_evaluator_document(a_raw: dict[str, Any]) -> bool:
        """Return True when document uses only pure schema evaluator types."""
        b_continue = True
        result = False
        evaluator_type = a_raw.get("evaluator_type")
        if b_continue and not isinstance(evaluator_type, str):
            b_continue = False
            result = False
        if b_continue:
            pure = {member.value for member in PureEvaluatorType}
            result = str(evaluator_type) in pure
        return result

    def validate_document(self, a_raw: dict[str, Any]) -> Result[Rule]:
        """Validate a single rule document into a domain Rule.

        Pure evaluator types: jschon + Pydantic.
        Language extensions (ast_*): Pydantic domain model only.
        """
        b_continue = True
        result: Result[Rule] = Result.failure("unreachable")

        if b_continue and self._is_pure_evaluator_document(a_raw):
            schema_result = self._ensure_schema()
            if schema_result.is_failure():
                b_continue = False
                result = Result.failure(schema_result.message)
            if b_continue:
                schema = schema_result.unwrap()
                output = schema.evaluate(jschon.JSON(a_raw))
                if not output.valid:
                    errors = list(output.collect_errors())
                    msgs = [str(err) for err in errors[:5]]
                    b_continue = False
                    result = Result.failure(f"jschon: {'; '.join(msgs)}")

        if b_continue:
            try:
                model = Rule.model_validate(a_raw)
                result = Result.success(model)
            except Exception as exc:
                result = Result.failure(f"pydantic: {exc}")

        return result

    def validate_dataset(self, a_raw: dict[str, Any]) -> Result[RuleDataset]:
        """Validate a wrapped rule dataset into domain RuleDataset."""
        b_continue = True
        result: Result[RuleDataset] = Result.failure("unreachable")

        rules_obj = a_raw.get("rules")
        all_pure = True
        if isinstance(rules_obj, list):
            for item in cast("list[object]", rules_obj):
                if isinstance(item, dict) and not self._is_pure_evaluator_document(
                    cast("dict[str, Any]", item)
                ):
                    all_pure = False
                    break
        else:
            all_pure = False

        if b_continue and all_pure:
            schema_result = self._ensure_schema()
            if schema_result.is_failure():
                b_continue = False
                result = Result.failure(schema_result.message)
            if b_continue:
                schema = schema_result.unwrap()
                output = schema.evaluate(jschon.JSON(a_raw))
                if not output.valid:
                    errors = list(output.collect_errors())
                    msgs = [str(err) for err in errors[:5]]
                    b_continue = False
                    result = Result.failure(f"jschon: {'; '.join(msgs)}")

        if b_continue:
            try:
                model = RuleDataset.model_validate(a_raw)
                result = Result.success(model)
            except Exception as exc:
                result = Result.failure(f"pydantic: {exc}")

        return result
