"""ODCS YAML parser (best effort, optional pyyaml)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .ir import ODCSDoc

try:
    import yaml  # type: ignore
    HAS_YAML = True
except Exception:
    HAS_YAML = False


def parse_odcs_file(path: str | Path) -> ODCSDoc:
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    data = None
    top = []
    if HAS_YAML:
        try:
            data = yaml.safe_load(raw) or {}
            top = list(data.keys()) if isinstance(data, dict) else []
        except Exception:
            pass
    if not top:
        # regex fallback
        for m in re.finditer(r'^([a-zA-Z0-9_]+)\s*:', raw, re.MULTILINE):
            top.append(m.group(1))
    return ODCSDoc(filename=str(p), source=raw, data=data, top_keys=top)
