"""Fixing service — applies deterministic fixes to diagrams based on violations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from usecase_diagram.domain.entities.diagram import UCDiagram
from usecase_diagram.domain.entities.violation import Violation
from usecase_diagram.repository.diagrams import DiagramRepository


@dataclass
class FixResult:
    """Result of applying fixes to a diagram.

    Attributes:
        diagram (UCDiagram): The diagram that was fixed.
        fixes_applied (List[str]): List of fix descriptions.
        original_source (str): Original source before fixes.
    """

    diagram: UCDiagram = field(metadata={"description": "The diagram that was fixed"})
    fixes_applied: List[str] = field(
        default_factory=list, metadata={"description": "List of fix descriptions"}
    )
    original_source: str = field(
        default="", metadata={"description": "Original source before fixes"}
    )


class FixingService:
    """Applies deterministic fixes to use case diagrams.

    Attributes:
        _diagram_repo (DiagramRepository): Diagram data access.
    """

    def __init__(self, a_diagram_repo: DiagramRepository) -> None:
        """Initialize with a diagram repository.

        Args:
            a_diagram_repo (DiagramRepository): Diagram data access.
        """
        self._diagram_repo: DiagramRepository = a_diagram_repo

    def apply_fixes(
        self,
        a_diagram: UCDiagram,
        a_violations: List[Violation],
    ) -> FixResult:
        """Apply deterministic fixes based on violations.

        Args:
            a_diagram (UCDiagram): Diagram to fix.
            a_violations (List[Violation]): Violations to fix.

        Returns:
            FixResult: Result with applied fixes.
        """
        result: FixResult = FixResult(diagram=a_diagram, original_source=a_diagram.source)
        source: str = a_diagram.source

        for violation in a_violations:
            if violation.rule_id == "UC-004":
                source = self._fix_header(source, a_diagram)
                result.fixes_applied.append("UC-004: injected header block")

        return result

    def rewrite(self, a_source: str) -> str:
        """Rewrite diagram source after fixes.

        Args:
            a_source (str): Source text to rewrite.

        Returns:
            str: Rewritten source text.
        """
        result: str = a_source
        if not a_source.strip():
            result = "@startuml\n@enduml\n"
        return result

    def _fix_header(self, a_source: str, a_diagram: UCDiagram) -> str:
        """Inject a header block after @startuml.

        Args:
            a_source (str): Current source text.
            a_diagram (UCDiagram): Diagram with header info.

        Returns:
            str: Source with injected header block.
        """
        source: str = a_source
        if not source.strip():
            source = "@startuml\n@enduml\n"

        header_lines: List[str] = [
            f"' Title: {a_diagram.title}",
            "' C4 ID: ",
            "' Boundary: ",
            "' Purpose: ",
            "' Principle: ",
            "' Source: ",
            "' Entry: ",
            "",
        ]
        header_block: str = "\n".join(header_lines)

        result: str = header_block + "\n" + source
        if "@startuml" in source:
            parts: List[str] = source.split("@startuml", 1)
            after_start: str = parts[1]
            if not after_start.lstrip().startswith("\n"):
                after_start = "\n" + after_start
            result = parts[0] + "@startuml" + after_start + "\n" + header_block + after_start
        return result

    def _csr_layer_from_path(self, a_path_parts: Tuple[str, ...]) -> str:
        """Detect CSR layer from path parts.

        Args:
            a_path_parts (Tuple[str, ...]): Path components.

        Returns:
            str: Detected CSR layer name.
        """
        result: str = "unknown"
        for part in a_path_parts:
            lower: str = part.lower()
            if "controller" in lower or "api" in lower:
                result = "controller"
                break
            if "service" in lower:
                result = "service"
                break
            if "repository" in lower or "repo" in lower:
                result = "repository"
                break
        return result
