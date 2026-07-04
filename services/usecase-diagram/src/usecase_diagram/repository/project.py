"""Project repository — builds project context from C4, README, SQ, and entity files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

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
    """A row from the README traceability table.

    Attributes:
        uc_id (str): Use case identifier.
        title (str): Use case title.
        sq_ref (str): Software quality reference.
    """

    uc_id: str = field(metadata={"description": "Use case identifier"})
    title: str = field(metadata={"description": "Use case title"})
    sq_ref: str = field(default="", metadata={"description": "Software quality reference"})


@dataclass
class ProjectContext:
    """Aggregated project context for cross-layer validation.

    Attributes:
        project_root (Path): Root path of the project.
        uc_root (Path): Root path of use case diagrams.
        diagrams (List[UCDiagram]): Parsed diagram list.
        c4_components (List[str]): C4 component names.
        c4_persons (List[str]): C4 person/actor names.
        c4_system_exts (List[str]): C4 external system names.
        c4_containers (List[str]): C4 container names.
        readme_rows (List[TraceRow]): README traceability rows.
        sq_uc_ids (List[str]): Use case IDs referenced in SQ diagrams.
        all_uc_ids (List[str]): All use case IDs across diagrams.
        domain_verbs (List[str]): Verbs extracted from entity files.
    """

    project_root: Path = field(metadata={"description": "Root path of the project"})
    uc_root: Path = field(metadata={"description": "Root path of use case diagrams"})
    diagrams: List[UCDiagram] = field(
        default_factory=list, metadata={"description": "Parsed diagram list"}
    )
    c4_components: List[str] = field(
        default_factory=list, metadata={"description": "C4 component names"}
    )
    c4_persons: List[str] = field(
        default_factory=list, metadata={"description": "C4 person/actor names"}
    )
    c4_system_exts: List[str] = field(
        default_factory=list, metadata={"description": "C4 external system names"}
    )
    c4_containers: List[str] = field(
        default_factory=list, metadata={"description": "C4 container names"}
    )
    readme_rows: List[TraceRow] = field(
        default_factory=list, metadata={"description": "README traceability rows"}
    )
    sq_uc_ids: List[str] = field(
        default_factory=list, metadata={"description": "Use case IDs in SQ diagrams"}
    )
    all_uc_ids: List[str] = field(
        default_factory=list, metadata={"description": "All use case IDs"}
    )
    domain_verbs: List[str] = field(
        default_factory=list, metadata={"description": "Verbs from entity files"}
    )


class ProjectRepository:
    """Builds ProjectContext by scanning C4, README, SQ, and entity files.

    Attributes:
        _root (Path): Project root directory.
        _uc_root (Path): Use case diagrams root directory.
        _diagram_repo (DiagramRepository): Diagram data access.
    """

    def __init__(self, a_project_root: Path, a_uc_root: Optional[Path] = None) -> None:
        """Initialize with project root and optional UC root override.

        Args:
            a_project_root (Path): Project root directory.
            a_uc_root (Optional[Path]): UC root or None for default.
        """
        self._root: Path = a_project_root
        self._uc_root: Path = a_uc_root or a_project_root / "docs" / "UC"
        self._diagram_repo: DiagramRepository = DiagramRepository()

    def build_context(self) -> ProjectContext:
        """Assemble the full project context.

        Returns:
            ProjectContext: Aggregated project context.
        """
        diagrams: List[UCDiagram] = self._load_diagrams()
        all_uc_ids: List[str] = [
            uc["id"] for d in diagrams for uc in d.usecases if uc.get("id")
        ]

        ctx: ProjectContext = ProjectContext(
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

    def _load_diagrams(self) -> List[UCDiagram]:
        """Load all use case diagrams from the UC root.

        Returns:
            List[UCDiagram]: Parsed diagram list.
        """
        files: List[Path] = self._diagram_repo.discover(self._uc_root)
        result: List[UCDiagram] = [self._diagram_repo.parse(f) for f in files]
        return result

    def _load_c4_inventory(self) -> Tuple[List[str], List[str], List[str], List[str]]:
        """Load C4 inventory from .puml files.

        Returns:
            Tuple of (components, persons, systems, containers).
        """
        components: List[str] = []
        persons: List[str] = []
        systems: List[str] = []
        containers: List[str] = []
        c4_dir: Path = self._root / "docs" / "C4"
        if c4_dir.exists():
            for puml in c4_dir.glob("*.puml"):
                text: str = puml.read_text(encoding="utf-8")
                components.extend(C4_COMPONENT_RE.findall(text))
                persons.extend(C4_PERSON_RE.findall(text))
                systems.extend(C4_SYSTEM_EXT_RE.findall(text))
                containers.extend(C4_CONTAINER_RE.findall(text))
        return components, persons, systems, containers

    def _load_readme_inventory(self) -> List[TraceRow]:
        """Load traceability rows from the README.

        Returns:
            List[TraceRow]: Parsed traceability rows.
        """
        rows: List[TraceRow] = []
        readme: Path = self._uc_root / "README.md"
        if readme.exists():
            text: str = readme.read_text(encoding="utf-8")
            for line in text.splitlines():
                m = re.search(r"(UC-\d+[-\w]*)\s*\|", line)
                if m:
                    parts: List[str] = [p.strip() for p in line.split("|")]
                    if len(parts) >= 2:
                        rows.append(TraceRow(uc_id=parts[0], title=parts[1]))
        return rows

    def _load_sq_inventory(self) -> List[str]:
        """Load use case IDs referenced in SQ diagrams.

        Returns:
            List[str]: Deduplicated use case ID list.
        """
        ids: List[str] = []
        sq_dir: Path = self._root / "docs" / "SQ"
        if sq_dir.exists():
            for puml in sq_dir.rglob("*.puml"):
                text: str = puml.read_text(encoding="utf-8")
                ids.extend(UC_ID_RE.findall(text))
        result: List[str] = list(set(ids))
        return result

    def _load_entities_verbs(self) -> List[str]:
        """Load domain verbs from the entities file.

        Returns:
            List[str]: Uppercase verb strings.
        """
        verbs: List[str] = []
        entities_file: Path = self._root / "docs" / "entities.md"
        if entities_file.exists():
            text: str = entities_file.read_text(encoding="utf-8")
            for line in text.splitlines():
                m = re.match(r"^#+\s+(\w+)", line)
                if m:
                    verbs.append(m.group(1).upper())
        return verbs
