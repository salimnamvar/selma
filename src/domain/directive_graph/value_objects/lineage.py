"""Lineage value object — records identity lifecycle operations.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.3
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from domain.directive_graph.enums import LineageOperation
from domain.directive_graph.scalars import ExecutionId
from domain.directive_graph.scalars import LineageId
from domain.directive_graph.scalars import UtcTimestamp


class Lineage(BaseModel):
    """Records a single identity lifecycle operation (fork, merge, or split).

    Required on ``Directive`` when the operation is ``fork``, ``merge``, or
    ``split``. NOT required for revision, rename, or retire.

    Invariants
    ----------
    - fork / split: ``len(parent_lineage_ids) == 1``
    - merge: ``len(parent_lineage_ids) == 2``
    - ``len(parent_execution_ids) == len(parent_lineage_ids)``

    Attributes:
        operation (LineageOperation): The kind of lifecycle operation.
        parent_lineage_ids (tuple[LineageId, ...]): Immutable root IDs of parents.
        parent_execution_ids (tuple[ExecutionId, ...]): Execution IDs of parents.
        timestamp (UtcTimestamp): UTC timestamp of the operation.
        reason (str | None): Optional human-readable explanation.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    operation: LineageOperation
    parent_lineage_ids: tuple[LineageId, ...] = Field(min_length=1)
    parent_execution_ids: tuple[ExecutionId, ...] = Field(min_length=1)
    timestamp: UtcTimestamp
    reason: str | None = None

    @model_validator(mode="after")
    def _validate_parent_cardinality(self) -> Lineage:
        """Enforce parent count rules per operation type.

        Raises:
            ValueError: If parent cardinality does not match the operation.
        """
        n_lineage = len(self.parent_lineage_ids)
        n_exec = len(self.parent_execution_ids)

        if self.operation in (LineageOperation.FORK, LineageOperation.SPLIT):
            if n_lineage != 1:
                raise ValueError(f"{self.operation} requires exactly 1 parent_lineage_id; got {n_lineage}")
        elif self.operation == LineageOperation.MERGE:
            if n_lineage != 2:
                raise ValueError(f"merge requires exactly 2 parent_lineage_ids; got {n_lineage}")

        if n_exec != n_lineage:
            raise ValueError(
                f"parent_execution_ids length ({n_exec}) must match " f"parent_lineage_ids length ({n_lineage})"
            )
        return self
