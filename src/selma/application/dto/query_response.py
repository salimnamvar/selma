"""Query response DTO — catalog answers for reasoning sessions."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class QueryResponse(BaseModel):
    """Structured answer from the directive catalog."""

    model_config = ConfigDict(frozen=True)

    kind: str
    summary: str = ""
    items: tuple[dict[str, Any], ...] = ()
    payload: dict[str, Any] = Field(default_factory=dict)
