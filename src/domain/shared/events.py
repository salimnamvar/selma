"""Base domain event type for all bounded contexts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar
from uuid import uuid4


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Immutable record of something that happened in the domain.

    Attributes:
        event_id: Unique identifier for this event instance.
        occurred_at: UTC timestamp when the event was raised.
        event_type: Short type name (overridden by subclasses via ClassVar).
    """

    event_type: ClassVar[str] = "domain_event"
    event_id: str
    occurred_at: str

    @staticmethod
    def _new_id() -> str:
        return str(uuid4())

    @staticmethod
    def _now_utc() -> str:
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
