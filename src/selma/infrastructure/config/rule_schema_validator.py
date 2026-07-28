"""JSON Schema validation using jschon + Pydantic v2 for rule documents.

Provides two-layer validation:
1. jschon JSON Schema structural validation (2020-12)
2. Pydantic v2 semantic validation with typed models

Schema path MUST be provided — no hardcoded paths.
No module-level mutable state (SC-070).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jschon
from jschon.exc import JSONError as JschonJSONError

from selma.domain.value_objects.result import Result
from selma.infrastructure.config.rule_schema_models import Rule
from selma.infrastructure.config.rule_schema_models import RuleDataset


class RuleSchemaValidator:
    """Validate rule JSON with jschon JSON Schema then parse with Pydantic.

    Two-layer validation:
    1. jschon structural validation against rule_schema.json
    2. Pydantic semantic validation into typed models

    The schema path MUST be provided at construction time.
    All state is instance-level — no module-level globals (SC-070).
    """

    def __init__(
        self,
        a_schema_path: Path,
    ) -> None:
        self._schema_path = a_schema_path
        self._catalog = jschon.create_catalog("2020-12")
        self._schema: jschon.JSONSchema | None = None

    def _ensure_schema(self) -> Result[jschon.JSONSchema]:
        """Ensure the JSON Schema is loaded from disk.

        Preconditions:
            - self._schema_path points to a valid JSON Schema file.

        Postconditions:
            Returns Result.success with jschon schema, or Result.failure.

        Side Effects: Caches schema on self._schema.
        Resource: Reads file from disk on first call.
        Failure: Returns Failure on I/O error or invalid JSON.
        """
        b_continue = True
        result: Result[jschon.JSONSchema] = Result.failure("unreachable")

        if self._schema is not None:
            b_continue = False
            result = Result.success(self._schema)

        if b_continue:
            try:
                with self._schema_path.open("r", encoding="utf-8") as handle:
                    schema_dict = json.load(handle)
                if not isinstance(schema_dict, dict):
                    b_continue = False
                    result = Result.failure("rule schema root must be an object")
            except (OSError, json.JSONDecodeError) as exc:
                b_continue = False
                result = Result.failure(f"Failed to load rule schema: {exc}")

        if b_continue:
            try:
                self._schema = jschon.JSONSchema(
                    schema_dict,  # type: ignore[arg-type]
                    catalog=self._catalog,
                )
                result = Result.success(self._schema)
            except JschonJSONError as exc:
                result = Result.failure(f"Failed to create jschon schema: {exc}")

        return result

    def validate_document(self, a_raw: dict[str, Any]) -> Result[Rule]:
        """Validate a single rule document.

        Two-layer validation:
        1. jschon JSON Schema structural check
        2. Pydantic semantic check

        Preconditions:
            - a_raw is a dict representing a rule JSON document.

        Postconditions:
            Returns Result.success with Rule model, or Result.failure.

        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on schema or semantic validation errors.
        """
        b_continue = True
        result: Result[Rule] = Result.failure("unreachable")

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
        """Validate a wrapped rule dataset.

        Two-layer validation:
        1. jschon JSON Schema structural check
        2. Pydantic semantic check

        Preconditions:
            - a_raw is a dict with version, policy_contract_version,
              policy_contract_id, and rules fields.

        Postconditions:
            Returns Result.success with RuleDataset model, or Result.failure.

        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on schema or semantic validation errors.
        """
        b_continue = True
        result: Result[RuleDataset] = Result.failure("unreachable")

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
