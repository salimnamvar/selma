"""SQ rewriter."""
from __future__ import annotations

from .ir import SQDiagram


def rewrite_sq(diagram: SQDiagram) -> str:
    if diagram.source:
        return diagram.source
    return "@startuml\ntitle SQ\n@enduml\n"
