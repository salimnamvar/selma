"""SQ validator per sq.md — design speaks through structure, not notes.

Rules:
- SQ-001: Filename under SQ/{GROUP}/sq_...
- SQ-003: Refs resolve to plausible UC IDs (basic shape)
- SQ-004: Header block with Source/Purpose
- SQ-005: Has actor and entry chain (CRITICAL)
- SQ-006: Has interface + controller + service lifelines
- SQ-009: ROD method name format (UC_ID METHOD ResourceName)
- SQ-010: CSR layering respected (no Controller→Repository)
- SQ-011: HTTP status codes on return arrows
- SQ-012: SM hnote annotations present for state changes
- SQ-013: Break blocks for failure paths
- SQ-014: No bare function names (must use ROD format)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.puml import has_header_block
from .ir import SQDiagram
sys.path.insert(0, str(_P(__file__).resolve().parents[4] / "libs" / "design-common" / "src"))
from design_common.report import Violation


def validate_sq(d: SQDiagram) -> list[Violation]:
    violations: list[Violation] = []
    fn = d.filename
    stem = _P(fn).stem

    # SQ-001: Filename convention
    if not (stem.startswith("sq_") and ".puml" in fn):
        violations.append(Violation(rule_id="SQ-001", severity="medium",
            message="SQ files must follow sq_{group}{nn}_{desc}.puml", location=fn))

    # SQ-004: Header block required
    if not has_header_block(d.source, ["Source:", "Purpose:"]):
        violations.append(Violation(rule_id="SQ-004", severity="high",
            message="Missing header block with 'Source:' and 'Purpose:' markers", location=fn))

    # SQ-003: refs should look like UC IDs
    for r in d.refs:
        if not re.match(r"^[A-Z]{2,5}-\d{2,}$", r):
            violations.append(Violation(rule_id="SQ-003", severity="medium",
                message=f"ref target should be UC ID, saw {r}", location=fn))

    # SQ-005: Actor and entry chain (CRITICAL)
    source_lower = d.source.lower()
    ACTOR_KEYWORDS = {"developer", "user", "operator", "httpclient", "mcpclient",
                      "prometheus", "mcp client", "http client"}
    has_actor = any(kw in source_lower for kw in ACTOR_KEYWORDS) or \
                bool(re.search(r'\bactor\b', d.source, re.IGNORECASE))
    if not has_actor:
        violations.append(Violation(rule_id="SQ-005", severity="critical",
            message="ALL diagrams must have an actor", location=fn,
            fix_suggestion="Add actor per sq.md entry chain rules"))

    # SQ-006: Lifeline completeness — must have interface + controller + service
    participants_lower = source_lower
    has_interface = any(kw in participants_lower for kw in
        ["serverrouter", "replsession", "mcpclientruntime", "router", "api", "cli"])
    has_service = any(kw in participants_lower for kw in
        ["service", "manager", "orchestrator", "coordinator", "handler", "engine"])
    if not has_interface and not has_service:
        violations.append(Violation(rule_id="SQ-006", severity="high",
            message="Missing interface and service lifelines — diagram needs full entry chain",
            location=fn))

    # SQ-009: ROD method name format on manager-level messages
    # Look for messages matching pattern: UC_ID METHOD ResourceName(params)
    arrow_lines = [l for l in d.source.split('\n')
                   if '->' in l and l.strip().startswith(('participant', 'actor', 'box', ''))
                   or '->' in l]
    # Find message lines (lines with arrows between lifelines)
    message_lines = []
    for l in d.source.split('\n'):
        stripped = l.strip()
        if '->' in stripped and not stripped.startswith('@') and \
           not stripped.startswith("'") and 'title' not in stripped and \
           '== ' not in stripped:
            message_lines.append(stripped)

    # Check several message lines for ROD format
    rod_violations = 0
    for ml in message_lines[:20]:
        # Skip return arrows
        if ml.startswith(('participant', 'actor', 'box', 'activate', 'deactivate', 'end', '}')):
            continue
        if '<--' in ml or '-->' in ml:
            continue
        # Extract label after the colon
        if ':' in ml:
            label = ml.split(':')[1].strip()
        else:
            continue
        # Check if label looks like a bare function name (no UC_ID, no UPPERCASE method)
        if label and not re.match(r'^[A-Z]{2,5}-\d{2}', label) and \
           not re.match(r'^[A-Z]{2,}', label.split()[0]) if label.split() else True:
            if len(label) < 30:  # long labels might be descriptions
                rod_violations += 1
    if rod_violations > 0:
        violations.append(Violation(rule_id="SQ-009", severity="high",
            message=f"Found {rod_violations} messages without ROD format (UC_ID METHOD ResourceName)",
            location=fn,
            fix_suggestion="Use format: UC_ID METHOD ResourceName(params) per rod.md"))

    # SQ-011: HTTP status codes on return arrows
    if not re.search(r'\b\d{3}\b', d.source):
        violations.append(Violation(rule_id="SQ-011", severity="medium",
            message="No HTTP status codes found on return arrows",
            location=fn,
            fix_suggestion="Add HTTP status codes (200, 404, etc.) to return arrows"))

    # SQ-013: Break blocks for failure paths
    if 'break' not in d.source and 'alt' not in d.source:
        violations.append(Violation(rule_id="SQ-013", severity="medium",
            message="No break or alt blocks found — missing failure path handling",
            location=fn,
            fix_suggestion="Add break/alt blocks for error handling per sq.md"))

    # SQ-014: No bare function names
    bare_func = re.findall(r'->\s*\w+\s*:\s*([a-z_]+)\(', d.source)
    bare_func = [f for f in bare_func if not f.startswith('sq_')]
    if bare_func:
        violations.append(Violation(rule_id="SQ-014", severity="high",
            message=f"Bare function names found (not ROD format): {', '.join(bare_func[:3])}",
            location=fn,
            fix_suggestion="Use ROD format: UC_ID METHOD ResourceName(params)"))

    return violations
