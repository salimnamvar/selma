"""Validate rule JSON documents against a rule schema via jsonschema.

After structural validation, documents are parsed into Pydantic v2 models.
The schema path MUST be provided — no hardcoded paths.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from typing import cast

from jsonschema import Draft7Validator

from selma.domain.value_objects.result import Result
from selma.infrastructure.config.rule_schema_models import RuleDocumentModel


def load_rule_json_schema(a_schema_path: Path) -> Result[dict[str, Any]]:
    """Load the Draft-07 rule schema object from disk.

    Preconditions:
        - a_schema_path points to a valid JSON file.

    Postconditions:
        Returns Result.success with the schema dict, or Result.failure.

    Side Effects: None.
    Resource: Reads file from disk.
    Failure: Returns Failure on I/O error or invalid JSON.
    """
    b_continue = True
    result: Result[dict[str, Any]] = Result.failure("unreachable")
    try:
        with a_schema_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            b_continue = False
            result = Result.failure("rule schema root must be an object")
        if b_continue:
            result = Result.success(cast("dict[str, Any]", data))
    except (OSError, json.JSONDecodeError) as exc:
        result = Result.failure(f"Failed to load rule schema: {exc}")
    return result


class RuleSchemaValidator:
    """Validate rule JSON with jsonschema then parse with Pydantic.

    The schema path MUST be provided at construction time.
    """

    def __init__(
        self,
        a_schema_path: Path,
        a_schema: dict[str, Any] | None = None,
    ) -> None:
        self._schema_path = a_schema_path
        self._schema = a_schema
        self._validator: Draft7Validator | None = None

    def _ensure_validator(self) -> Result[Draft7Validator]:
        b_continue = True
        result: Result[Draft7Validator] = Result.failure("unreachable")
        if self._validator is not None:
            b_continue = False
            result = Result.success(self._validator)
        if b_continue and self._schema is None:
            schema_result = load_rule_json_schema(self._schema_path)
            if schema_result.is_failure():
                b_continue = False
                result = Result.failure(schema_result.message)
            if b_continue:
                self._schema = schema_result.unwrap()
        if b_continue and self._schema is not None:
            self._validator = Draft7Validator(self._schema)
            result = Result.success(self._validator)
        return result

    def validate_document(self, a_raw: dict[str, Any]) -> Result[RuleDocumentModel]:
        b_continue = True
        result: Result[RuleDocumentModel] = Result.failure("unreachable")
        validator_result = self._ensure_validator()
        if validator_result.is_failure():
            b_continue = False
            result = Result.failure(validator_result.message)
        if b_continue:
            validator = validator_result.unwrap()
            raw_errors = list(cast("Any", validator).iter_errors(a_raw))
            errors = sorted(raw_errors, key=lambda e: list(e.path))
            if errors:
                first = errors[0]
                path = ".".join(str(p) for p in first.path) or "<root>"
                b_continue = False
                result = Result.failure(f"jsonschema:{path}: {first.message}")
        if b_continue:
            try:
                model = RuleDocumentModel.model_validate(a_raw)
                result = Result.success(model)
            except Exception as exc:
                result = Result.failure(f"pydantic: {exc}")
        return result
