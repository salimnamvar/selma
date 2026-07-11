"""Shared Pydantic config for domain models."""

from __future__ import annotations

from pydantic import ConfigDict

VO_CONFIG = ConfigDict(
    frozen=True,
    extra="forbid",
    populate_by_name=True,
)