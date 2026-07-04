"""PlantUML utilities — loading and parsing .puml files."""

from __future__ import annotations

import re
from pathlib import Path


def load_basic_diagram(filepath: Path) -> str:
    """Load a PlantUML file and return its raw text content."""
    return filepath.read_text(encoding="utf-8")


def strip_comments(source: str) -> str:
    """Remove PlantUML comments from source text."""
    lines = []
    in_multiline = False
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("'"):
            continue
        if stripped.startswith("/*"):
            in_multiline = True
            continue
        if in_multiline:
            if "*/" in stripped:
                in_multiline = False
            continue
        lines.append(line)
    return "\n".join(lines)


def extract_startuml_body(source: str) -> str:
    """Extract content between @startuml and @enduml."""
    match = re.search(r"@startuml.*?\n(.*?)@enduml", source, re.DOTALL)
    if match:
        return match.group(1)
    return source
