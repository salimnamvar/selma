"""LintCompleted event — fired when linting of a file completes."""

from __future__ import annotations

from dataclasses import dataclass

from selma.domain.value_objects.file_path import FilePath


@dataclass(frozen=True)
class LintCompleted:
    """Event: linting of a file completed."""

    file_path: FilePath
    finding_count: int
    violation_count: int
    duration_ms: float
