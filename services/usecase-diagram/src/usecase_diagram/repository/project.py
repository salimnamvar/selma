"""Project repository — builds project context from C4, README, SQ, and entity files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from usecase_diagram.domain.entities.diagram import UCDiagram
from usecase_diagram.repository.diagrams import DiagramRepository

C4_COMPONENT_RE = re.compile(r'component\s+"([^"]+)"')
C4_PERSON_RE = re.compile(r'(?:person|actor)\s+"([^"]+)"')
C4_SYSTEM_EXT_RE = re.compile(r'system_extern\w*\s+"([^"]+)"')
C4_CONTAINER_RE = re.compile(r'container\s+"([^"]+)"')
UC_ID_RE = re.compile(r"([A-Z]{2,12}-\d{2,})")
HEADER_FIELD_RE = re.compile(r"'\s*(\w[\w\s]*):\s*(.*)")


@dataclass
class TraceRow:
    """A row from the README traceability table."""

    uc_id: str
    title: str
    sq_ref: str = ""


@dataclass
class ProjectContext:
    """Aggregated project context for cross-layer validation."""

    project_root: Path
    uc_root: Path
    diagrams: list[UCDiagram] = field(default_factory=list)
    c4_components: list[str] = field(default_factory=list)
    c4_persons: list[str] = field(default_factory=list)
    c4_system_exts: list[str] = field(default_factory=list)
    c4_containers: list[str] = field(default_factory=list)
    readme_rows: list[TraceRow] = field(default_factory=list)
    sq_uc_ids: list[str] = field(default_factory=list)
    all_uc_ids: list[str] = field(default_factory=list)
    domain_verbs: list[str] = field(default_factory=list)


class ProjectRepository:
    """Builds ProjectContext by scanning C4, README, SQ, and entity files."""

    def __init__(self, project_root: Path, uc_root: Path | None = None) -> None:
        self._root = project_root
        self._uc_root = uc_root or project_root / "docs" / "UC"
        self._diagram_repo = DiagramRepository()

    def build_context(self) -> ProjectContext:
        """Assemble the full project context."""
        diagrams = self._load_diagrams()
        all_uc_ids = [uc["id"] for d in diagrams for uc in d.usecases if uc.get("id")]

        ctx = ProjectContext(
            project_root=self._root,
            uc_root=self._uc_root,
            diagrams=diagrams,
            all_uc_ids=all_uc_ids,
        )

        ctx.c4_components, ctx.c4_persons, ctx.c4_system_exts, ctx.c4_containers = (
            self._load_c4_inventory()
        )
        ctx.readme_rows = self._load_readme_inventory()
        ctx.sq_uc_ids = self._load_sq_inventory()
        ctx.domain_verbs = self._load_entities_verbs()

        return ctx

    def _load_diagrams(self) -> list[UCDiagram]:
        files = self._diagram_repo.discover(self._uc_root)
        return [self._diagram_repo.parse(f) for f in files]

    def _load_c4_inventory(self) -> tuple[list[str], list[str], list[str], list[str]]:
        components, persons, systems, containers = [], [], [], []
        c4_dir = self._root / "docs" / "C4"
        if not c4_dir.exists():
            return components, persons, systems, containers
        for puml in c4_dir.glob("*.puml"):
            text = puml.read_text(encoding="utf-8")
            components.extend(C4_COMPONENT_RE.findall(text))
            persons.extend(C4_PERSON_RE.findall(text))
            systems.extend(C4_SYSTEM_EXT_RE.findall(text))
            containers.extend(C4_CONTAINER_RE.findall(text))
        return components, persons, systems, containers

    def _load_readme_inventory(self) -> list[TraceRow]:
        rows: list[TraceRow] = []
        readme = self._uc_root / "README.md"
        if not readme.exists():
            return rows
        text = readme.read_text(encoding="utf-8")
        for line in text.splitlines():
            m = re.search(r"(UC-\d+[-\w]*)\s*\|", line)
            if m:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 2:
                    rows.append(TraceRow(uc_id=parts[0], title=parts[1]))
        return rows

    def _load_sq_inventory(self) -> list[str]:
        ids: list[str] = []
        sq_dir = self._root / "docs" / "SQ"
        if not sq_dir.exists():
            return ids
        for puml in sq_dir.rglob("*.puml"):
            text = puml.read_text(encoding="utf-8")
            ids.extend(UC_ID_RE.findall(text))
        return list(set(ids))

    def _load_entities_verbs(self) -> list[str]:
        verbs: list[str] = []
        entities_file = self._root / "docs" / "entities.md"
        if not entities_file.exists():
            return verbs
        text = entities_file.read_text(encoding="utf-8")
        for line in text.splitlines():
            m = re.match(r"^#+\s+(\w+)", line)
            if m:
                verbs.append(m.group(1).upper())
        return verbs
