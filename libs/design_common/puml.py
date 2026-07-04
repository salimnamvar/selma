"""Shared PlantUML utilities for design layer linters (UC, SM, SQ, ERD, CL).

Provides:
- strip_comments
- extract_title
- extract_notes
- find_macro_calls (generic)
- basic structure scan
- header block detection helpers

Used by per-layer parsers. Keep minimal deps (stdlib only).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


def strip_puml_comments(text: str) -> str:
    """Strip PlantUML ' comments. Keep structure lines count stable for simple cases."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("'"):
            lines.append("")
            continue
        # remove trailing ' comment unless in URL or inside quotes
        in_quote = False
        out = []
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == '"':
                in_quote = not in_quote
                out.append(ch)
                i += 1
                continue
            if not in_quote and ch == "'" and "://" not in line[max(0, i-8):i+3]:
                break
            out.append(ch)
            i += 1
        lines.append("".join(out).rstrip())
    return "\n".join(lines)


TITLE_RE = re.compile(r"^\s*title\s+(.+)$", re.IGNORECASE | re.MULTILINE)
START_RE = re.compile(r"@startuml(?:\s+(.+))?", re.IGNORECASE)
END_RE = re.compile(r"@enduml", re.IGNORECASE)


def extract_title(text: str) -> str:
    m = TITLE_RE.search(text)
    if m:
        return m.group(1).strip().strip('"')
    # fallback first non-empty after startuml
    for line in text.splitlines():
        s = line.strip()
        if s and not s.startswith(("@", "'", "!", "skin", "title")) and not s.startswith("note"):
            return s[:80]
    return ""


def extract_notes(text: str) -> list[dict[str, Any]]:
    """Extract note blocks. Very lightweight."""
    notes = []
    # note over ... end note
    pat = re.compile(
        r"note\s+(?:over|as)\s+([^\n:]+?)(?:\s*:\s*([^\n]+?))?\s*\n(.*?)\s*end\s*note",
        re.IGNORECASE | re.DOTALL,
    )
    for m in pat.finditer(text):
        notes.append({
            "target": m.group(1).strip(),
            "title": (m.group(2) or "").strip(),
            "content": m.group(3).strip(),
        })
    return notes


MACRO_CALL_RE = re.compile(r"^\s*(?P<macro>[A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE)


def find_macro_calls(text: str) -> list[dict[str, Any]]:
    """Return list of top level macro invocations with rough args string."""
    calls = []
    for m in MACRO_CALL_RE.finditer(text):
        start = m.end() - 1  # position of (
        macro = m.group("macro")
        args_str, _ = _extract_balanced(text, start)
        calls.append({"macro": macro, "args": args_str})
    return calls


def _extract_balanced(text: str, start_idx: int) -> tuple[str, int]:
    """Extract inside balanced () ."""
    depth = 1
    i = start_idx + 1
    buf = []
    in_str = False
    while i < len(text) and depth > 0:
        ch = text[i]
        if ch == '"' and (i == 0 or text[i-1] != '\\'):
            in_str = not in_str
        if not in_str:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    break
        buf.append(ch)
        i += 1
    return "".join(buf), i


def has_header_block(text: str, required_markers: Iterable[str]) -> bool:
    """Check if a structured header comment block containing the markers is present near top."""
    # Look for the common ' Header ... pattern used across layers
    head = text[:2000]
    for marker in required_markers:
        if marker.lower() not in head.lower():
            return False
    return True


@dataclass
class BasicDiagram:
    """Lightweight IR shared by non-C4 layers."""
    filename: str
    title: str = ""
    source: str = ""
    notes: list[dict] = field(default_factory=list)
    macros: list[dict] = field(default_factory=list)
    elements: list[dict] = field(default_factory=list)  # layer fills this
    level_hints: list[str] = field(default_factory=list)


def load_basic_diagram(path: str | Path) -> BasicDiagram:
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    cleaned = strip_puml_comments(raw)
    title = extract_title(cleaned)
    notes = extract_notes(cleaned)
    macros = find_macro_calls(cleaned)
    return BasicDiagram(
        filename=str(p),
        title=title,
        source=raw,
        notes=notes,
        macros=macros,
    )
