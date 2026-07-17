"""Lifecycle definition — flat YAML-shaped intent for identity operations."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LifecycleDefinition(BaseModel):
    """Direct mapping of lifecycle definition field names."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    revision: str = Field(min_length=1, description="When to use revision")
    fork: str = Field(min_length=1, description="When to use fork")
    merge: str = Field(min_length=1, description="When to use merge")
    split: str = Field(min_length=1, description="When to use split")
    rename: str = Field(min_length=1, description="When to use rename")
    retire: str = Field(min_length=1, description="When to use retire")
    dag_intent: str = Field(min_length=1, description="Constraint on lineage ancestry graph structure")


