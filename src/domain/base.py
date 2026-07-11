"""Domain Model Base.

Shared immutable base for governance domain value objects.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DomainValueObject(BaseModel):
    """Immutable value-object base with strict validation and alias support."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )
