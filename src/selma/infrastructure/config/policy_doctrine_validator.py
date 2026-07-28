"""YAML validation for policy doctrine documents using domain models."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from typing import cast

import yaml

from selma.domain.entities.policy import DirectivePolicy
from selma.domain.entities.policy import PolicyDoctrine
from selma.domain.value_objects.result import Result

logger = logging.getLogger(__name__)


class PolicyDoctrineValidator:
    """Validate policy doctrine YAML into domain models."""

    @staticmethod
    def load_yaml_file(a_path: Path) -> Result[dict[str, Any]]:
        """Load a YAML file from disk into a dict."""
        b_continue = True
        result: Result[dict[str, Any]] = Result.failure("unreachable")
        data: object = None
        try:
            with a_path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle)
        except (OSError, yaml.YAMLError) as exc:
            b_continue = False
            msg = f"Failed to load YAML: {exc}"
            logger.exception(msg)
            result = Result.failure(msg)
        if b_continue and not isinstance(data, dict):
            b_continue = False
            msg = f"YAML root must be an object, got {type(data).__name__}"
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue:
            result = Result.success(cast("dict[str, Any]", data))
        return result

    def validate_doctrine(self, a_raw: dict[str, Any]) -> Result[PolicyDoctrine]:
        """Validate the universal policy doctrine document."""
        b_continue = True
        result: Result[PolicyDoctrine] = Result.failure("unreachable")
        model: PolicyDoctrine | None = None
        try:
            model = PolicyDoctrine.model_validate(a_raw)
        except Exception as exc:
            b_continue = False
            msg = f"pydantic: {exc}"
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and model is not None:
            result = Result.success(model)
        return result

    def validate_doctrine_file(self, a_path: Path) -> Result[PolicyDoctrine]:
        """Load and validate a policy doctrine YAML file."""
        b_continue = True
        result: Result[PolicyDoctrine] = Result.failure("unreachable")
        load_result = PolicyDoctrineValidator.load_yaml_file(a_path)
        if load_result.is_failure():
            b_continue = False
            msg = load_result.message
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue:
            result = self.validate_doctrine(load_result.unwrap())
        return result

    def validate_directive(self, a_raw: dict[str, Any]) -> Result[DirectivePolicy]:
        """Validate a per-rule directive policy document."""
        b_continue = True
        result: Result[DirectivePolicy] = Result.failure("unreachable")
        model: DirectivePolicy | None = None
        try:
            model = DirectivePolicy.model_validate(a_raw)
        except Exception as exc:
            b_continue = False
            msg = f"pydantic: {exc}"
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue and model is not None:
            result = Result.success(model)
        return result

    def validate_directive_file(self, a_path: Path) -> Result[DirectivePolicy]:
        """Load and validate a per-rule directive policy YAML file."""
        b_continue = True
        result: Result[DirectivePolicy] = Result.failure("unreachable")
        load_result = PolicyDoctrineValidator.load_yaml_file(a_path)
        if load_result.is_failure():
            b_continue = False
            msg = load_result.message
            logger.warning(msg)
            result = Result.failure(msg)
        if b_continue:
            result = self.validate_directive(load_result.unwrap())
        return result
