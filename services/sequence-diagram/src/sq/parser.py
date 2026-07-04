"""SQ diagram parser (PlantUML sequence)."""
from __future__ import annotations

import re
from pathlib import Path

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.puml import load_basic_diagram, strip_puml_comments
from .ir import SQDiagram


PARTICIPANT_RE = re.compile(r'(?:participant|actor|boundary|control|entity|database)\s+["\']?([^"\']+)["\']?', re.IGNORECASE)
REF_RE = re.compile(r'ref\s+(?:over\s+)?[^:]+:\s*([A-Z]{2,5}-\d{2,})', re.IGNORECASE)
UC_ID_RE = re.compile(r"\b([A-Z]{2,5})-(\d{2,})\b")


def parse_sq_file(path: str | Path) -> SQDiagram:
    p = Path(path)
    basic = load_basic_diagram(p)
    cleaned = strip_puml_comments(basic.source)

    parts = [m.group(1).strip() for m in PARTICIPANT_RE.finditer(cleaned)]
    refs = []
    for m in REF_RE.finditer(cleaned):
        refs.append(m.group(1))
    # also capture bare IDs that look like UC
    for m in UC_ID_RE.finditer(cleaned):
        uid = f"{m.group(1)}-{m.group(2)}"
        if uid not in refs:
            refs.append(uid)

    return SQDiagram(
        filename=str(p),
        title=basic.title,
        source=basic.source,
        participants=parts,
        refs=refs,
        notes=basic.notes,
    )