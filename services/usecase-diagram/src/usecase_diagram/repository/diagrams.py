"""Diagram repository — reads and writes PlantUML use case diagram files."""

from __future__ import annotations

import re
from pathlib import Path

from usecase_diagram.domain.entities.diagram import UCDiagram
from usecase_diagram.utils.puml import (
    extract_startuml_body,
    load_basic_diagram,
    strip_comments,
)

FILENAME_TO_GROUP: dict[str, str] = {
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

    def discover(self, root: Path, pattern: str = "uc_*.puml") -> list[Path]:
        """Discover all use case diagram files under root."""
        return sorted(root.rglob(pattern))

    def read_source(self, filepath: Path) -> str:
        """Read raw PlantUML source from a file."""
        return load_basic_diagram(filepath)

    def parse(self, filepath: Path) -> UCDiagram:
        """Parse a PlantUML file into a UCDiagram intermediate representation."""
        source = load_basic_diagram(filepath)
        clean = strip_comments(source)
        body = extract_startuml_body(clean)

        filename = filepath.stem
        group = FILENAME_TO_GROUP.get(filename, filename.upper())

        header = self._parse_header(body)
        title = header.get("Title", filename)
        usecases = self._parse_usecases(body)
        actors = self._parse_actors(body)
        associations = self._parse_associations(body, actors)
        relations = self._parse_relations(body)
        has_boundary = "rectangle" in body or "package" in body or "node" in body

        return UCDiagram(
            filename=filepath.name,
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

    def write(self, filepath: Path, source: str) -> None:
        """Write PlantUML source to a file."""
        filepath.write_text(source, encoding="utf-8")

    def _parse_header(self, body: str) -> dict[str, str]:
        header: dict[str, str] = {}
        for match in HEADER_FIELD_RE.finditer(body):
            key = match.group(1).strip()
            value = match.group(2).strip()
            header[key] = value
        return header

    def _parse_usecases(self, body: str) -> list[dict]:
        uc_re = re.compile(r'(?:usecase|use\s+case)\s+"([^"]+)"')
        usecases: list[dict] = []
        for match in uc_re.finditer(body):
            full = match.group(1)
            uc_id, title, description = self._split_title_description(full)
            usecases.append({
                "id": uc_id,
                "title": title,
                "description": description,
                "full": full,
            })
        return usecases

    def _parse_actors(self, body: str) -> list[str]:
        actors: list[str] = []
        for match in ACTOR_RE.finditer(body):
            actors.append(match.group(1))
        return actors

    def _parse_associations(self, body: str, actors: list[str]) -> list[dict]:
        assoc_re = re.compile(r'"([^"]+)"\s*-->.*?"([^"]+)"')
        associations: list[dict] = []
        for match in assoc_re.finditer(body):
            source = match.group(1)
            target = match.group(2)
            associations.append({"source": source, "target": target})
        return associations

    def _parse_relations(self, body: str) -> list[dict]:
        rel_re = re.compile(r'"([^"]+)"\s*\.\.>\s*"([^"]+)"\s*:\s*<<(\w+)>>')
        relations: list[dict] = []
        for match in rel_re.finditer(body):
            relations.append({
                "source": match.group(1),
                "target": match.group(2),
                "stereotype": match.group(3),
            })
        return relations

    @staticmethod
    def _split_title_description(full: str) -> tuple[str, str, str]:
        """Split 'UC-01: VERB Noun -- Description' into (id, title, description)."""
        if " -- " in full:
            left, description = full.split(" -- ", 1)
        else:
            left, description = full, ""

        if ":" in left:
            uc_id, title = left.split(":", 1)
            return uc_id.strip(), title.strip(), description.strip()

        return "", left.strip(), description.strip()
