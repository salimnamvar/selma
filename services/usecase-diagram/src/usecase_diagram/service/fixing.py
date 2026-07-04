"""Fixing service — applies deterministic fixes to diagrams based on violations."""

from __future__ import annotations

from dataclasses import dataclass, field

from usecase_diagram.domain.entities.diagram import UCDiagram
from usecase_diagram.domain.entities.violation import Violation
from usecase_diagram.repository.diagrams import DiagramRepository


@dataclass
class FixResult:
    """Result of applying fixes to a diagram."""

    diagram: UCDiagram
    fixes_applied: list[str] = field(default_factory=list)
    original_source: str = ""


class FixingService:
    """Applies deterministic fixes to use case diagrams."""

    def __init__(self, diagram_repo: DiagramRepository) -> None:
        self._diagram_repo = diagram_repo

    def apply_fixes(
        self,
        diagram: UCDiagram,
        violations: list[Violation],
    ) -> FixResult:
        """Apply deterministic fixes based on violations."""
        result = FixResult(diagram=diagram, original_source=diagram.source)
        source = diagram.source

        for violation in violations:
            if violation.rule_id == "UC-004":
                source = self._fix_header(source, diagram)
                result.fixes_applied.append("UC-004: injected header block")

        return result

    def rewrite(self, source: str) -> str:
        """Rewrite diagram source after fixes."""
        if not source.strip():
            return "@startuml\n@enduml\n"
        return source

    def _fix_header(self, source: str, diagram: UCDiagram) -> str:
        """Inject a header block after @startuml."""
        if not source.strip():
            source = "@startuml\n@enduml\n"

        header_lines = [
            f"' Title: {diagram.title}",
            "' C4 ID: ",
            "' Boundary: ",
            "' Purpose: ",
            "' Principle: ",
            "' Source: ",
            "' Entry: ",
            "",
        ]
        header_block = "\n".join(header_lines)

        if "@startuml" in source:
            parts = source.split("@startuml", 1)
            after_start = parts[1]
            if not after_start.lstrip().startswith("\n"):
                after_start = "\n" + after_start
            return parts[0] + "@startuml" + after_start + "\n" + header_block + after_start

        return header_block + "\n" + source

    def _csr_layer_from_path(self, path_parts: tuple[str, ...]) -> str:
        """Detect CSR layer from path parts."""
        for part in path_parts:
            lower = part.lower()
            if "controller" in lower or "api" in lower:
                return "controller"
            if "service" in lower:
                return "service"
            if "repository" in lower or "repo" in lower:
                return "repository"
        return "unknown"
