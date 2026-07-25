"""LintCompleted event — fired when linting of a file completes.

Uses Pydantic v2 BaseModel with frozen config.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict

from selma.domain.value_objects.file_path import FilePath


class LintCompleted(BaseModel):
    """Event: linting of a file completed."""

    model_config = ConfigDict(frozen=True)

    file_path: FilePath
    finding_count: int
    violation_count: int
    duration_ms: float
