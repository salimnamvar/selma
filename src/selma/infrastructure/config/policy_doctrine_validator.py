"""YAML validation for policy doctrine documents.

Validates policy_doctrine.yaml and directive/policy/*.yaml files
using Pydantic v2 models. No JSON Schema validation needed for YAML
policy files since they contain no executable logic.

Schema contract: schema/policy_doctrine.yaml
Normative source: SPECIFICATION.md 8.2.4
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import cast

import yaml

from selma.domain.value_objects.result import Result
from selma.infrastructure.config.policy_doctrine_models import DirectivePolicy
from selma.infrastructure.config.policy_doctrine_models import PolicyDoctrine


def load_yaml_file(a_path: Path) -> Result[dict[str, Any]]:
    """Load a YAML file from disk.

    Preconditions:
        - a_path points to a valid YAML file.

    Postconditions:
        Returns Result.success with parsed dict, or Result.failure.

    Side Effects: None.
    Resource: Reads file from disk.
    Failure: Returns Failure on I/O error or invalid YAML.
    """
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
    """Validate policy doctrine YAML files using Pydantic v2.

    Two validation modes:
    1. validate_doctrine: validates the universal policy_doctrine.yaml
    2. validate_directive: validates a per-rule directive policy YAML

    No JSON Schema validation — policy files contain no executable logic.
    """

    def validate_doctrine(self, a_raw: dict[str, Any]) -> Result[PolicyDoctrine]:
        """Validate the universal policy doctrine document.

        Preconditions:
            - a_raw is a dict from policy_doctrine.yaml.

        Postconditions:
            Returns Result.success with PolicyDoctrine model, or Result.failure.

        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on validation errors.
        """
        try:
            model = PolicyDoctrine.model_validate(a_raw)
            return Result.success(model)
        except Exception as exc:
            return Result.failure(f"pydantic: {exc}")

    def validate_doctrine_file(self, a_path: Path) -> Result[PolicyDoctrine]:
        """Load and validate a policy doctrine YAML file.

        Preconditions:
            - a_path points to a valid YAML file.

        Postconditions:
            Returns Result.success with PolicyDoctrine model, or Result.failure.

        Side Effects: None.
        Resource: Reads file from disk.
        Failure: Returns Failure on I/O or validation errors.
        """
        load_result = load_yaml_file(a_path)
        if load_result.is_failure():
            return Result.failure(load_result.message)
        return self.validate_doctrine(load_result.unwrap())

    def validate_directive(self, a_raw: dict[str, Any]) -> Result[DirectivePolicy]:
        """Validate a per-rule directive policy document.

        Preconditions:
            - a_raw is a dict from directive/policy/*.yaml.

        Postconditions:
            Returns Result.success with DirectivePolicy model, or Result.failure.

        Side Effects: None.
        Resource: None.
        Failure: Returns Failure on validation errors.
        """
        try:
            model = DirectivePolicy.model_validate(a_raw)
            return Result.success(model)
        except Exception as exc:
            return Result.failure(f"pydantic: {exc}")

    def validate_directive_file(self, a_path: Path) -> Result[DirectivePolicy]:
        """Load and validate a directive policy YAML file.

        Preconditions:
            - a_path points to a valid YAML file.

        Postconditions:
            Returns Result.success with DirectivePolicy model, or Result.failure.

        Side Effects: None.
        Resource: Reads file from disk.
        Failure: Returns Failure on I/O or validation errors.
        """
        load_result = load_yaml_file(a_path)
        if load_result.is_failure():
            return Result.failure(load_result.message)
        return self.validate_directive(load_result.unwrap())
