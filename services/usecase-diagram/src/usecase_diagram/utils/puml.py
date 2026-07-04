"""PlantUML utilities — loading and parsing .puml files."""

from __future__ import annotations

import re
from pathlib import Path


def load_basic_diagram(a_filepath: Path) -> str:
    """Load a PlantUML file and return its raw text content.

    Args:
        a_filepath (Path): Path to the PlantUML file.

    Returns:
        str: Raw source text.
    """
    result: str = a_filepath.read_text(encoding="utf-8")
    return result


def strip_comments(a_source: str) -> str:
    """Remove PlantUML comments from source text.

    Args:
        a_source (str): PlantUML source text.

    Returns:
        str: Source text with comments removed.
    """
    lines: list[str] = []
    in_multiline: bool = False
    for line in a_source.splitlines():
        stripped: str = line.strip()
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
    result: str = "\n".join(lines)
    return result


def extract_startuml_body(a_source: str) -> str:
    """Extract content between @startuml and @enduml.

    Args:
        a_source (str): PlantUML source text.

    Returns:
        str: Content between @startuml and @enduml, or full source.
    """
    match = re.search(r"@startuml.*?\n(.*?)@enduml", a_source, re.DOTALL)
    result: str = match.group(1) if match else a_source
    return result
