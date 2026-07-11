"""Identity Lifecycle Intent Value Objects.

When to use each identity lifecycle operation.
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from pydantic import Field, model_validator

from domain.base import DomainValueObject
from domain.enums import IdentityOperation
from domain.identifiers import GovernanceText


class LifecycleOperationIntent(DomainValueObject):
    """Guidance for a single identity lifecycle operation.

    Attributes:
        operation (IdentityOperation): Lifecycle operation.
        guidance (GovernanceText): When to use this operation.
    """

    operation: IdentityOperation = Field(description="Lifecycle operation")
    guidance: GovernanceText = Field(description="When to use this operation")


class IdentityLifecycleIntent(DomainValueObject):
    """Describes when to use each identity lifecycle operation.

    Attributes:
        operations (Tuple[LifecycleOperationIntent, ...]): Per-operation guidance.
        dag_intent (GovernanceText): Constraint on lineage ancestry graph structure.
    """

    operations: Tuple[LifecycleOperationIntent, ...] = Field(description="Guidance for each lifecycle operation")
    dag_intent: GovernanceText = Field(description="Constraint on lineage ancestry graph structure")

    @model_validator(mode="before")
    @classmethod
    def _normalize_flat_yaml(cls, a_data: Any) -> Any:
        """Normalize flat YAML keys into structured operations.

        Args:
            a_data (Any): Raw input mapping or structured form.

        Returns:
            Any: Structured mapping with operations list.
        """
        result: Any = a_data
        if isinstance(a_data, dict):
            raw: Dict[str, Any] = dict(a_data)  # type: ignore[arg-type]
            if "operations" in raw:
                result = raw
            else:
                operation_keys: FrozenSet[str] = frozenset(operation.value for operation in IdentityOperation)
                operations: List[Dict[str, str]] = []
                for key in IdentityOperation:
                    if key.value not in raw:
                        continue
                    guidance: str = str(raw[key.value])
                    operations.append({"operation": key.value, "guidance": guidance})
                remaining: Dict[str, Any] = {key: value for key, value in raw.items() if key not in operation_keys}
                remaining["operations"] = operations
                result = remaining
        return result

    @model_validator(mode="after")
    def check_complete_and_unique(self) -> IdentityLifecycleIntent:
        """Require exactly one guidance entry per IdentityOperation.

        Returns:
            IdentityLifecycleIntent: Validated instance.

        Raises:
            ValueError: If operations are missing or duplicated.
        """
        result: IdentityLifecycleIntent = self
        present: List[IdentityOperation] = [item.operation for item in self.operations]
        if len(present) != len(set(present)):
            raise ValueError("Duplicate lifecycle operations are not allowed")
        missing: Set[IdentityOperation] = set(IdentityOperation) - set(present)
        if missing:
            names: List[str] = sorted(operation.value for operation in missing)
            raise ValueError(f"Missing lifecycle operation guidance: {names}")
        return result

    def guidance_for(self, a_operation: IdentityOperation) -> GovernanceText:
        """Return authoring guidance for the given lifecycle operation.

        Args:
            a_operation (IdentityOperation): Lifecycle operation.

        Returns:
            GovernanceText: Guidance text for the operation.

        Raises:
            KeyError: If no guidance exists for the operation.
        """
        found: Optional[GovernanceText] = None
        for item in self.operations:
            if item.operation == a_operation:
                found = item.guidance
                break
        if found is None:
            msg: str = f"No guidance for operation {a_operation}"
            raise KeyError(msg)
        result: GovernanceText = found
        return result

    def supported_operations(self) -> FrozenSet[IdentityOperation]:
        """Return the set of operations covered by this intent.

        Returns:
            FrozenSet[IdentityOperation]: Supported operations.
        """
        result: FrozenSet[IdentityOperation] = frozenset(item.operation for item in self.operations)
        return result
