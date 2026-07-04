"""ERD diagram parser (PlantUML IE)."""
from __future__ import annotations

import re
from pathlib import Path

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.puml import load_basic_diagram, strip_puml_comments
from .ir import ERDDiagram


ENTITY_RE = re.compile(r'entity\s+["\']?([A-Za-z0-9_]+)["\']?', re.IGNORECASE)
REL_RE = re.compile(r'\|\|--o\{|\.\.>|\|\|-\||--', re.IGNORECASE)


def parse_erd_file(path: str | Path) -> ERDDiagram:
    p = Path(path)
    basic = load_basic_diagram(p)
    cleaned = strip_puml_comments(basic.source)
    ents = [m.group(1) for m in ENTITY_RE.finditer(cleaned)]
    rels = [m.group(0) for m in REL_RE.finditer(cleaned)]
    return ERDDiagram(
        filename=str(p),
        title=basic.title,
        source=basic.source,
        entities=ents,
        relationships=rels,
        notes=basic.notes,
    )