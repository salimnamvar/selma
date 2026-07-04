"""ERD rewriter."""
from __future__ import annotations

from .ir import ERDDiagram


def rewrite_erd(diagram: ERDDiagram) -> str:
    if diagram.source:
        return diagram.source
    return "@startuml\ntitle ER\n@enduml\n"
