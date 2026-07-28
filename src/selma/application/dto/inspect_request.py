"""Inspect request DTO — input for source inspection use case."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from selma.domain.value_objects.file_path import FilePath


class InspectRequest(BaseModel):
    """Request to inspect source paths against active directives."""

    model_config = ConfigDict(frozen=True)

    paths: tuple[FilePath, ...] = ()
    codes: frozenset[str] = Field(default_factory=frozenset)
    exclude_codes: frozenset[str] = Field(default_factory=frozenset)
    format: str = "default"
    guide: bool = False
    skip_tools: bool = False
    skip_ast: bool = False
    only: str = ""
    max_workers: int = 4
