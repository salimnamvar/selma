"""YAML validation for policy doctrine documents using domain models."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import cast

import yaml

from selma.domain.entities.policy import DirectivePolicy
from selma.domain.entities.policy import PolicyDoctrine
from selma.domain.value_objects.result import Result


def load_yaml_file(a_path: Path) -> Result[dict[str, Any]]:
    """Load a YAML file from disk into a dict."""
    try:
        with a_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        if not isinstance(data, dict):
            return Result.failure(
                f"YAML root must be an object, got {type(data).__name__}"
            )
        return Result.success(cast("dict[str, Any]", data))
    except (OSError, yaml.YAMLError) as exc:
        return Result.failure(f"Failed to load YAML: {exc}")


class PolicyDoctrineValidator:
    """Validate policy doctrine YAML into domain models."""

    def validate_doctrine(self, a_raw: dict[str, Any]) -> Result[PolicyDoctrine]:
        """Validate the universal policy doctrine document."""
        try:
            model = PolicyDoctrine.model_validate(a_raw)
            return Result.success(model)
        except Exception as exc:
            return Result.failure(f"pydantic: {exc}")

    def validate_doctrine_file(self, a_path: Path) -> Result[PolicyDoctrine]:
        """Load and validate a policy doctrine YAML file."""
        b_continue = True
        result: Result[PolicyDoctrine] = Result.failure("unreachable")
        load_result = load_yaml_file(a_path)
        if load_result.is_failure():
            b_continue = False
            result = Result.failure(load_result.message)
        if b_continue:
            result = self.validate_doctrine(load_result.unwrap())
        return result

    def validate_directive(self, a_raw: dict[str, Any]) -> Result[DirectivePolicy]:
        """Validate a per-rule directive policy document."""
        try:
            model = DirectivePolicy.model_validate(a_raw)
            return Result.success(model)
        except Exception as exc:
            return Result.failure(f"pydantic: {exc}")

    def validate_directive_file(self, a_path: Path) -> Result[DirectivePolicy]:
        """Load and validate a per-rule directive policy YAML file."""
        b_continue = True
        result: Result[DirectivePolicy] = Result.failure("unreachable")
        load_result = load_yaml_file(a_path)
        if load_result.is_failure():
            b_continue = False
            result = Result.failure(load_result.message)
        if b_continue:
            result = self.validate_directive(load_result.unwrap())
        return result
