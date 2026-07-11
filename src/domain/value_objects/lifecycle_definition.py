"""Lifecycle definition — flat YAML-shaped intent for identity operations."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from domain.enums import IdentityOperation


class LifecycleDefinition(BaseModel):
    """Direct mapping of policy_doctrine.yaml ``lifecycle_definition`` field names."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    revision: str = Field(min_length=1, description="When to use revision")
    fork: str = Field(min_length=1, description="When to use fork")
    merge: str = Field(min_length=1, description="When to use merge")
    split: str = Field(min_length=1, description="When to use split")
    rename: str = Field(min_length=1, description="When to use rename")
    retire: str = Field(min_length=1, description="When to use retire")
    dag_intent: str = Field(min_length=1, description="Constraint on lineage ancestry graph structure")

    def get_lifecycle_definition(self, operation: IdentityOperation) -> str:
        """Return lifecycle text for ``operation``.

        ``IdentityOperation`` values match the flat YAML field names on this model
        (``revision``, ``fork``, ``merge``, etc.); ``dag_intent`` is not an operation.
        """
        return getattr(self, operation.value)
