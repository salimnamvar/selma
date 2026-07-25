"""LintRequest DTO — input for the lint use case."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from selma.domain.value_objects.file_path import FilePath


@dataclass(frozen=True)
class LintRequest:
    """Input DTO for lint use case."""

    paths: tuple[FilePath, ...]
    exclude_codes: frozenset[str] = frozenset()
    codes: frozenset[str] = frozenset()
    format: str = "default"
    guide: bool = False
    skip_tools: bool = False
    skip_ast: bool = False
    only: str | None = None
