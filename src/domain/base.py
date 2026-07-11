"""Domain Model Base.

Shared immutable base for governance domain value objects.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DomainValueObject(BaseModel):
    """Immutable, strict value-object base for the governance domain."""

    model_config = ConfigDict(frozen=True, extra="forbid")
