"""ConflictResolution value object.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.3
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from domain.directive_graph.enums import ConflictStrategy
from domain.directive_graph.scalars import DirectiveReference


class ConflictResolution(BaseModel):
    """Explicit conflict override for a directive.

    Takes precedence over the computed multi-factor resolution algorithm
    (SPECIFICATION.md §2.15).

    Invariants
    ----------
    - ``strategy == "defer_to"`` requires ``defer_to`` to be set.
    - ``strategy != "defer_to"`` requires ``defer_to`` to be ``None``.

    Attributes:
        strategy (ConflictStrategy): How to resolve conflicts involving this directive.
        defer_to (DirectiveReference | None): Target execution ID when deferring.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    strategy: ConflictStrategy
    defer_to: DirectiveReference | None = None

    @model_validator(mode="after")
    def _validate_defer_to_presence(self) -> ConflictResolution:
        """Enforce defer_to presence/absence rules.

        Raises:
            ValueError: If defer_to is missing for defer_to strategy, or
                present for a non-defer_to strategy.
        """
        if self.strategy == ConflictStrategy.DEFER_TO and self.defer_to is None:
            raise ValueError(
                "defer_to is required when strategy is 'defer_to'"
            )
        if self.strategy != ConflictStrategy.DEFER_TO and self.defer_to is not None:
            raise ValueError(
                f"defer_to must be None when strategy is '{self.strategy}'; "
                f"only valid with strategy='defer_to'"
            )
        return self
