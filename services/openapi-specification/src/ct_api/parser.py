"""OpenAPI parser (optional pyyaml)."""
from __future__ import annotations
import re
from pathlib import Path
from typing import Any
from .ir import OASDoc

try:
    import yaml
    HAS_YAML = True
except Exception:
    HAS_YAML = False


def parse_oas_file(path: str | Path) -> OASDoc:
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    data = None
    paths = []
    ops = []
    if HAS_YAML:
        try:
            data = yaml.safe_load(raw) or {}
            paths = list((data.get("paths") or {}).keys())
            for pth, methods in (data.get("paths") or {}).items():
                if isinstance(methods, dict):
                    for m in methods:
                        if m.lower() in ("get","post","put","patch","delete","options","head"):
                            ops.append(f"{m.upper()} {pth}")
        except Exception:
            pass
    if not paths:
        paths = re.findall(r'^\s+["\']?(/[^"\':\s]+)["\']?\s*:', raw, re.MULTILINE)
    return OASDoc(filename=str(p), source=raw, data=data, paths=paths, ops=ops)
