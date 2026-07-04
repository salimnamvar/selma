"""CL rewriter."""
from __future__ import annotations

from .ir import CLDiagram


def rewrite_cl(diagram: CLDiagram) -> str:
    if diagram.source:
        return diagram.source
    return "@startuml\ntitle CL\n@enduml\n"
