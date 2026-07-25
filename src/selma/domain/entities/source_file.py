"""SourceFile entity — represents a source file being linted.

Has identity (FilePath), carries metadata.
Uses Pydantic v2 BaseModel with frozen config.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict

from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.source_hash import SourceHash


class SourceFile(BaseModel):
    """A source file being linted."""

    model_config = ConfigDict(frozen=True)

    path: FilePath
    hash: SourceHash
    language: str = "python"
    content: str = ""

    @property
    def extension(self) -> str:
        return self.path.extension
