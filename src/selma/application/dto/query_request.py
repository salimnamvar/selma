"""Query request DTO — ask the directive catalog for reasoning."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel
from pydantic import ConfigDict


class QueryKind(StrEnum):
    """Kinds of catalog queries agents and humans may issue."""

    LIST = "list"
    POLICY = "policy"
    RULE = "rule"
    DIRECTIVE = "directive"
    GUIDANCE = "guidance"
    SEARCH = "search"


class QueryRequest(BaseModel):
    """Request to query the governance catalog."""

    model_config = ConfigDict(frozen=True)

    kind: QueryKind
    lineage_id: str = ""
    text: str = ""
    codes: tuple[str, ...] = ()
    limit: int = 50
