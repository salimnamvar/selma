"""SourceFile entity — represents a source file being linted.

Has identity (FilePath), carries metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.source_hash import SourceHash


@dataclass(frozen=True)
class SourceFile:
    """A source file being linted."""

    path: FilePath
    hash: SourceHash
    language: str = "python"
    content: str = ""

    @property
    def extension(self) -> str:
        return self.path.extension
