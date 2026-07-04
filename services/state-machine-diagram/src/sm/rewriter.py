"""SM rewriter."""
from __future__ import annotations

from .ir import SMDiagram


def rewrite_sm(diagram: SMDiagram) -> str:
    if diagram.source:
        return diagram.source
    return "@startuml\n[*] --> UNSPECIFIED\n@enduml\n"
