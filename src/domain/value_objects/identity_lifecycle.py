"""Identity lifecycle intent value objects."""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from domain.base import DomainValueObject
from domain.enums import IdentityOperation
from domain.identifiers import GovernanceText

_OPERATION_KEYS = frozenset(op.value for op in IdentityOperation)


class LifecycleOperationIntent(DomainValueObject):
    """Guidance for a single identity lifecycle operation."""

    operation: IdentityOperation = Field(description="Lifecycle operation")
    guidance: GovernanceText = Field(description="When to use this operation")


class IdentityLifecycleIntent(DomainValueObject):
    """Describes when to use each identity lifecycle operation.

    Accepts the flat YAML form::

        revision: "..."
        fork: "..."
        ...
        dag_intent: "..."

    or a structured form with ``operations`` + ``dag_intent``.
    """

    operations: tuple[LifecycleOperationIntent, ...] = Field(description="Guidance for each lifecycle operation")
    dag_intent: GovernanceText = Field(description="Constraint on lineage ancestry graph structure")

    @model_validator(mode="before")
    @classmethod
    def _normalize_flat_yaml(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        raw: dict[str, Any] = dict(data)  # type: ignore[arg-type]
        if "operations" in raw:
            return raw

        operations: list[dict[str, str]] = []
        for key in IdentityOperation:
            if key.value not in raw:
                continue
            guidance = raw[key.value]
            operations.append({"operation": key.value, "guidance": str(guidance)})

        remaining: dict[str, Any] = {k: v for k, v in raw.items() if k not in _OPERATION_KEYS}
        remaining["operations"] = operations
        return remaining

    @model_validator(mode="after")
    def check_complete_and_unique(self) -> IdentityLifecycleIntent:
        """Require exactly one guidance entry per IdentityOperation."""
        present = [item.operation for item in self.operations]
        if len(present) != len(set(present)):
            raise ValueError("Duplicate lifecycle operations are not allowed")
        missing = set(IdentityOperation) - set(present)
        if missing:
            names = sorted(op.value for op in missing)
            raise ValueError(f"Missing lifecycle operation guidance: {names}")
        return self

    def guidance_for(self, operation: IdentityOperation) -> GovernanceText:
        """Return authoring guidance for the given lifecycle operation."""
        for item in self.operations:
            if item.operation == operation:
                return item.guidance
        msg = f"No guidance for operation {operation}"
        raise KeyError(msg)

    def supported_operations(self) -> frozenset[IdentityOperation]:
        """Return the set of operations covered by this intent."""
        return frozenset(item.operation for item in self.operations)
