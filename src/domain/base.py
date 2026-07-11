"""Shared base for immutable domain models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DomainValueObject(BaseModel):
    """Immutable, strict value-object base for the governance domain."""

    model_config = ConfigDict(frozen=True, extra="forbid")
