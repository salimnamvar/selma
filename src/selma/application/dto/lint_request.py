"""LintRequest DTO — input for the lint use case.

Uses Pydantic v2 BaseModel with frozen config.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict

from selma.domain.value_objects.file_path import FilePath


class LintRequest(BaseModel):
    """Input DTO for lint use case."""

    model_config = ConfigDict(frozen=True)

    paths: tuple[FilePath, ...]
    exclude_codes: frozenset[str] = frozenset()
    codes: frozenset[str] = frozenset()
    format: str = "default"
    guide: bool = False
    skip_tools: bool = False
    skip_ast: bool = False
    only: str | None = None
