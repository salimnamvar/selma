"""Audit trail value object.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.3
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict

from domain.directive_graph.scalars import ActorId
from domain.directive_graph.scalars import UtcTimestamp


class AuditTrail(BaseModel):
    """Authorship and approval metadata for a directive or dataset.

    Attributes:
        authored_by (ActorId | None): Actor who created the directive.
        approved_by (ActorId | None): Actor who approved the directive.
        approved_at (UtcTimestamp | None): UTC timestamp of approval.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    authored_by: ActorId | None = None
    approved_by: ActorId | None = None
    approved_at: UtcTimestamp | None = None
