"""Scope and scope filter value objects.

Reference: .tmp/Architecture/DOMAIN_ARCHITECTURE.md §2.3
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from domain.directive_graph.enums import FilterOperator
from domain.directive_graph.enums import TargetType


class ScopeFilter(BaseModel):
    """A single applicability predicate on target metadata or content.

    Attributes:
        field (str): Path within target metadata or content.
        operator (FilterOperator): Comparison semantics.
        value (Any): Value to compare against.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    field: str = Field(min_length=1, description="Path within target metadata or content.")
    operator: FilterOperator
    value: Any


class Scope(BaseModel):
    """Structured applicability context for a directive.

    Replaces the deprecated bare ``target`` string field. Used for
    deterministic scope filtering and specificity scoring per
    SPECIFICATION.md §2.8.2.

    Attributes:
        target_type (TargetType): Kind of content the directive applies to.
        domain (str | None): Regulatory or business domain.
        jurisdiction (str | None): Legal or operational jurisdiction.
        filters (tuple[ScopeFilter, ...]): Additional applicability predicates.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    target_type: TargetType
    domain: str | None = None
    jurisdiction: str | None = None
    filters: tuple[ScopeFilter, ...] = ()
