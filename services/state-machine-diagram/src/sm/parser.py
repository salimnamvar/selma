"""SM diagram parser (PlantUML state)."""
from __future__ import annotations

import re
from pathlib import Path

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.puml import load_basic_diagram, strip_puml_comments
from .ir import SMDiagram


STATE_RE = re.compile(r"state\s+([A-Z0-9_]+)", re.IGNORECASE)
TRANS_RE = re.compile(r"([A-Z0-9_]+)\s*-->\s*([A-Z0-9_]+)", re.IGNORECASE)


def parse_sm_file(path: str | Path) -> SMDiagram:
    p = Path(path)
    basic = load_basic_diagram(p)
    cleaned = strip_puml_comments(basic.source)

    states = []
    for m in STATE_RE.finditer(cleaned):
        name = m.group(1).upper()
        if name not in ("[*]", "HIDDEN"):
            states.append({"name": name})

    trans = []
    for m in TRANS_RE.finditer(cleaned):
        trans.append({"from": m.group(1).upper(), "to": m.group(2).upper()})

    return SMDiagram(
        filename=str(p),
        title=basic.title,
        source=basic.source,
        states=states,
        transitions=trans,
        notes=basic.notes,
    )