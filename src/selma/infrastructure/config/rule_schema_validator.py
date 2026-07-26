"""Validate rule JSON documents against schema/rule_schema.json via jsonschema.

After structural validation, documents are parsed into Pydantic v2 models.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from typing import cast

from jsonschema import Draft7Validator

from selma.domain.value_objects.result import Result
from selma.infrastructure.config.rule_schema_models import RuleDocumentModel

_SCHEMA_CANDIDATES = (
    Path("schema/rule_schema.json"),
    Path(__file__).resolve().parents[4] / "schema" / "rule_schema.json",
    Path(__file__).resolve().parents[3] / "schema" / "rule_schema.json",
)


def resolve_rule_schema_path() -> Result[Path]:
    """Locate schema/rule_schema.json on disk."""
    b_continue = True
    result: Result[Path] = Result.failure("rule_schema.json not found")
    for candidate in _SCHEMA_CANDIDATES:
        if b_continue and candidate.is_file():
            b_continue = False
            result = Result.success(candidate)
    return result


def load_rule_json_schema() -> Result[dict[str, Any]]:
    """Load the Draft-07 rule schema object from disk."""
    b_continue = True
    result: Result[dict[str, Any]] = Result.failure("unreachable")
    path_result = resolve_rule_schema_path()
    if path_result.is_failure():
        b_continue = False
        result = Result.failure(path_result.message)
    if b_continue:
        path = path_result.unwrap()
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict):
                b_continue = False
                result = Result.failure("rule_schema.json root must be an object")
            if b_continue:
                result = Result.success(cast("dict[str, Any]", data))
        except (OSError, json.JSONDecodeError) as exc:
            result = Result.failure(f"Failed to load rule schema: {exc}")
    return result


class RuleSchemaValidator:
    """Validate rule JSON with jsonschema then parse with Pydantic."""

    def __init__(self, a_schema: dict[str, Any] | None = None) -> None:
        self._schema = a_schema
        self._validator: Draft7Validator | None = None

    def _ensure_validator(self) -> Result[Draft7Validator]:
        b_continue = True
        result: Result[Draft7Validator] = Result.failure("unreachable")
        if self._validator is not None:
            b_continue = False
            result = Result.success(self._validator)
        if b_continue and self._schema is None:
            schema_result = load_rule_json_schema()
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


def validate_rule_dict(a_raw: dict[str, Any]) -> Result[RuleDocumentModel]:
    """Validate one rule document dict against the project rule schema."""
    return RuleSchemaValidator().validate_document(a_raw)
