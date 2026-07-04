"""CL diagram parser (PlantUML class)."""
from __future__ import annotations

import re
from pathlib import Path

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.puml import load_basic_diagram, strip_puml_comments
from .ir import CLDiagram


CLASS_RE = re.compile(r'^\s*class\s+([A-Za-z0-9_]+)', re.IGNORECASE | re.MULTILINE)
ENUM_RE = re.compile(r'^\s*enum\s+([A-Za-z0-9_]+)', re.IGNORECASE | re.MULTILINE)


CL_TYPE_RE = re.compile(r"'?\s*@cl-type\s+(domain|runtime)", re.IGNORECASE)


def parse_cl_file(path: str | Path) -> CLDiagram:
    p = Path(path)
    basic = load_basic_diagram(p)
    cleaned = strip_puml_comments(basic.source)
    classes = CLASS_RE.findall(cleaned)
    enums = ENUM_RE.findall(cleaned)

    # Detect @cl-type from header (first 10 lines)
    cl_type = "domain"
    source_lines = basic.source.split("\n")
    for line in source_lines[:10]:
        m = CL_TYPE_RE.search(line)
        if m:
            cl_type = m.group(1).lower()
            break

    return CLDiagram(
        filename=str(p),
        title=basic.title,
        source=basic.source,
        classes=classes,
        enums=enums,
        notes=basic.notes,
        cl_type=cl_type,
    )