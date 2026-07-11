"""Lifecycle guidance — when to use each identity operation (intent only)."""

from __future__ import annotations

from functools import cached_property
from typing import Any, Self

from pydantic import Field, model_validator

from domain.base import DomainValueObject, IndexedLookupMixin
from domain.enums import IdentityOperation
from domain.identifiers import GovernanceText


class LifecycleOperationGuidance(DomainValueObject):
    """Governance intent for a single identity lifecycle operation."""

    operation: IdentityOperation = Field(description="Lifecycle operation")
    guidance: GovernanceText = Field(description="When and how to use this operation")

    @property
    def id(self) -> IdentityOperation:
        """Stable identifier for collection indexing."""
        return self.operation


class LifecycleGuidance(
    DomainValueObject,
    IndexedLookupMixin[IdentityOperation, LifecycleOperationGuidance],
):
    """Describes when to use each identity lifecycle operation.

    Modeled as an operation→guidance registry (not enum-coupled fields) so new
    operations can be added without reshaping the class. YAML flat maps are
    adapted in :meth:`from_flat_dict`.
    """

    operations: tuple[LifecycleOperationGuidance, ...] = Field(
        min_length=1,
        description="Guidance entries keyed by operation",
    )
    dag_intent: GovernanceText = Field(
        description="Constraint on lineage ancestry graph structure"
    )

    @model_validator(mode="after")
    def _validate_operations(self) -> Self:
        present = {entry.operation for entry in self.operations}
        missing = set(IdentityOperation) - present
        if missing:
            raise ValueError(
                f"Lifecycle guidance missing operations: {sorted(op.value for op in missing)}"
            )
        if len(present) != len(self.operations):
            raise ValueError("Lifecycle guidance contains duplicate operations")
        return self

    @cached_property
    def _index(self) -> dict[IdentityOperation, LifecycleOperationGuidance]:
        return {entry.operation: entry for entry in self.operations}

    def get_guidance(self, key: IdentityOperation) -> str:
        """Return guidance text for the given operation."""
        return self.require(key).guidance

    @classmethod
    def from_flat_dict(cls, data: dict[str, Any]) -> LifecycleGuidance:
        """Adapt policy_doctrine.yaml flat operation keys into this model."""
        if "dag_intent" not in data:
            raise ValueError("lifecycle_definition requires 'dag_intent'")
        operations: list[dict[str, Any]] = []
        for key, value in data.items():
            if key == "dag_intent":
                continue
            operations.append({"operation": key, "guidance": value})
        return cls.model_validate({"operations": operations, "dag_intent": data["dag_intent"]})
