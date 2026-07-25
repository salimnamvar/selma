from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Violation:
    filepath: str
    line: int
    col: int
    code: str
    message: str
    severity: str = "error"

    def __str__(self) -> str:
        return f"{self.filepath}:{self.line}:{self.col}: {self.severity}: {self.message} ({self.code})"
