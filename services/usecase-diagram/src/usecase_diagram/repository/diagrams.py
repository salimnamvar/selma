"""Diagram repository — reads and writes PlantUML use case diagram files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from usecase_diagram.domain.entities.diagram import UCDiagram
from usecase_diagram.utils.puml import (
    extract_startuml_body,
    load_basic_diagram,
    strip_comments,
)

FILENAME_TO_GROUP: Dict[str, str] = {
    "uc_cli": "CLI",
    "uc_http": "HTTP",
    "uc_mcp": "MCP",
    "uc_agentctrl": "AGENTCTRL",
    "uc_task": "TASK",
    "uc_tool": "TOOL",
    "uc_session": "SESSION",
    "uc_config": "CONFIG",
    "uc_safety": "SAFETY",
    "uc_context": "CONTEXT",
    "uc_evaluation": "EVALUATION",
    "uc_editstrategy": "EDITSTRATEGY",
    "uc_sessionrepo": "SESSIONREPO",
    "uc_historyrepo": "HISTORYREPO",
    "uc_configrepo": "CONFIGREPO",
    "uc_wirelog": "WIRELOG",
    "uc_memory": "MEMORY",
    "uc_llm": "LLM",
    "uc_repointel": "REPOINTEL",
    "uc_git": "GIT",
    "uc_mcprepo": "MCPREPO",
    "uc_web": "WEB",
    "uc_fs": "FS",
    "uc_sandbox": "SANDBOX",
    "uc_overview": "ALL",
}

ACTOR_RE = re.compile(r'(?:actor|person)\s+"([^"]+)"')
HEADER_FIELD_RE = re.compile(r"'\s*(\w[\w\s]*):\s*(.*)")


class DiagramRepository:
    """Reads, parses, and writes PlantUML use case diagram files."""

    def discover(self, a_root: Path, a_pattern: str = "uc_*.puml") -> List[Path]:
        """Discover all use case diagram files under root.

        Args:
            a_root (Path): Root directory to search.
            a_pattern (str): Glob pattern for diagram files.

        Returns:
            List[Path]: Sorted list of matching file paths.
        """
        result: List[Path] = sorted(a_root.rglob(a_pattern))
        return result

    def read_source(self, a_filepath: Path) -> str:
        """Read raw PlantUML source from a file.

        Args:
            a_filepath (Path): Path to the PlantUML file.

        Returns:
            str: Raw source text.
        """
        result: str = load_basic_diagram(a_filepath)
        return result

    def parse(self, a_filepath: Path) -> UCDiagram:
        """Parse a PlantUML file into a UCDiagram intermediate representation.

        Args:
            a_filepath (Path): Path to the PlantUML file.

        Returns:
            UCDiagram: Parsed diagram representation.
        """
        source: str = load_basic_diagram(a_filepath)
        clean: str = strip_comments(source)
        body: str = extract_startuml_body(clean)

        filename: str = a_filepath.stem
        group: str = FILENAME_TO_GROUP.get(filename, filename.upper())

        header: Dict[str, str] = self._parse_header(body)
        title: str = header.get("Title", filename)
        usecases: List[Dict[str, Any]] = self._parse_usecases(body)
        actors: List[str] = self._parse_actors(body)
        associations: List[Dict[str, Any]] = self._parse_associations(body, actors)
        relations: List[Dict[str, Any]] = self._parse_relations(body)
        has_boundary: bool = "rectangle" in body or "package" in body or "node" in body

        result: UCDiagram = UCDiagram(
            filename=a_filepath.name,
            title=title,
            source=source,
            group=group,
            header=header,
            usecases=usecases,
            actors=[a if isinstance(a, str) else str(a) for a in actors],
            associations=associations,
            relations=relations,
            has_subject_boundary=has_boundary,
        )
        return result

    def write(self, a_filepath: Path, a_source: str) -> None:
        """Write PlantUML source to a file.

        Args:
            a_filepath (Path): Target file path.
            a_source (str): PlantUML source text to write.
        """
        a_filepath.write_text(a_source, encoding="utf-8")

    def _parse_header(self, a_body: str) -> Dict[str, str]:
        """Parse header fields from the diagram body.

        Args:
            a_body (str): Diagram body text.

        Returns:
            Dict[str, str]: Header key-value pairs.
        """
        header: Dict[str, str] = {}
        for match in HEADER_FIELD_RE.finditer(a_body):
            key: str = match.group(1).strip()
            value: str = match.group(2).strip()
            header[key] = value
        return header

    def _parse_usecases(self, a_body: str) -> List[Dict[str, Any]]:
        """Parse use case entries from the diagram body.

        Args:
            a_body (str): Diagram body text.

        Returns:
            List[Dict[str, Any]]: Parsed use case dictionaries.
        """
        uc_re = re.compile(r'(?:usecase|use\s+case)\s+"([^"]+)"')
        usecases: List[Dict[str, Any]] = []
        for match in uc_re.finditer(a_body):
            full: str = match.group(1)
            uc_id: str
            title: str
            description: str
            uc_id, title, description = self._split_title_description(full)
            usecases.append({
                "id": uc_id,
                "title": title,
                "description": description,
                "full": full,
            })
        return usecases

    def _parse_actors(self, a_body: str) -> List[str]:
        """Parse actor names from the diagram body.

        Args:
            a_body (str): Diagram body text.

        Returns:
            List[str]: Actor name strings.
        """
        actors: List[str] = []
        for match in ACTOR_RE.finditer(a_body):
            actors.append(match.group(1))
        return actors

    def _parse_associations(
        self, a_body: str, a_actors: List[str]
    ) -> List[Dict[str, Any]]:
        """Parse association entries from the diagram body.

        Args:
            a_body (str): Diagram body text.
            a_actors (List[str]): Known actor names.

        Returns:
            List[Dict[str, Any]]: Association dictionaries.
        """
        assoc_re = re.compile(r'"([^"]+)"\s*-->.*?"([^"]+)"')
        associations: List[Dict[str, Any]] = []
        for match in assoc_re.finditer(a_body):
            source: str = match.group(1)
            target: str = match.group(2)
            associations.append({"source": source, "target": target})
        return associations

    def _parse_relations(self, a_body: str) -> List[Dict[str, Any]]:
        """Parse relationship entries from the diagram body.

        Args:
            a_body (str): Diagram body text.

        Returns:
            List[Dict[str, Any]]: Relationship dictionaries.
        """
        rel_re = re.compile(r'"([^"]+)"\s*\.\.>\s*"([^"]+)"\s*:\s*<<(\w+)>>')
        relations: List[Dict[str, Any]] = []
        for match in rel_re.finditer(a_body):
            relations.append({
                "source": match.group(1),
                "target": match.group(2),
                "stereotype": match.group(3),
            })
        return relations

    @staticmethod
    def _split_title_description(a_full: str) -> Tuple[str, str, str]:
        """Split 'UC-01: VERB Noun -- Description' into components.

        Args:
            a_full (str): Full use case string.

        Returns:
            Tuple[str, str, str]: (uc_id, title, description).
        """
        left: str
        description: str
        if " -- " in a_full:
            left, description = a_full.split(" -- ", 1)
        else:
            left, description = a_full, ""

        uc_id: str = ""
        title: str = left.strip()
        if ":" in left:
            uc_id, title = left.split(":", 1)
            uc_id = uc_id.strip()
            title = title.strip()

        return uc_id, title, description.strip()
