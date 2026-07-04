#!/usr/bin/env python3
"""Cross-Layer Naming Consistency Checker.

Validates that C4 component diagram names, UC filenames, and SQ directory names
use the same canonical group stem.

Usage:
    python scripts/cross_layer_naming_check.py /path/to/docs --format text
    python scripts/cross_layer_naming_check.py /path/to/docs --format json

Checks:
    - C4 component diagram stems ↔ UC filenames ↔ SQ directory names
    - Flags abbreviated SQ directories as violations
    - Reports missing mappings
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import NamedTuple

# Allow running as standalone script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "libs" / "design-common" / "src"))
from design_common.report import Violation


# Canonical mapping: abbreviation → canonical name
# Used to identify legacy abbreviated directories.
# All directories now use canonical C4 names; kept for backward compat.
ABBREVIATION_MAP = {
    "AC": "AgentController",
    "AGENT": "TaskService",
    "AGENTCONTROLLER": "AgentController",
    "AGT": "Agent",
    "API": "HTTPAdapter",
    "CFG": "ConfigRepository",
    "CLI": "CLI",
    "CONFIG": "ConfigRepository",
    "CONFIGREPOSITORY": "ConfigRepository",
    "CONTEXTGRAPH": "ContextService",
    "CONTEXTSERVICE": "ContextService",
    "CTX": "ContextService",
    "EDITSTRATEGY": "EditStrategyRepository",
    "EDITSTRATEGYREPOSITORY": "EditStrategyRepository",
    "EDT": "EditStrategyRepository",
    "EVALUATION": "EvaluationService",
    "EVALUATIONSERVICE": "EvaluationService",
    "EVL": "EvaluationService",
    "GIT": "GitRepository",
    "GITREPOSITORY": "GitRepository",
    "HK": "Hooks",
    "HOOKS": "Hooks",
    "HTTPADAPTER": "HTTPAdapter",
    "LLMREPOSITORY": "LLMRepository",
    "MCP": "MCPRepository",
    "MCPREPOSITORY": "MCPRepository",
    "MEM": "MemoryRepository",
    "MEMORY": "MemoryRepository",
    "MEMORYREPOSITORY": "MemoryRepository",
    "PLG": "Plugins",
    "PLUGINS": "Plugins",
    "PROVIDER": "LLMRepository",
    "PRV": "LLMRepository",
    "REPOINTELLIGENCE": "RepoIntelligenceRepository",
    "REPOINTELLIGENCEREPOSITORY": "RepoIntelligenceRepository",
    "RIM": "RepoIntelligenceRepository",
    "ROUTER": "LLMRepository",
    "RTG": "LLMRepository",
    "SAF": "SafetyService",
    "SAFETY": "SafetyService",
    "SAFETYSERVICE": "SafetyService",
    "SANDBOX": "SandboxRepository",
    "SANDBOXREPOSITORY": "SandboxRepository",
    "SBX": "SandboxRepository",
    "SESSION": "SessionService",
    "SESSIONSERVICE": "SessionService",
    "SSN": "SessionService",
    "TASKSERVICE": "TaskService",
    "TL": "ToolService",
    "TOOL": "ToolService",
    "TOOLSERVICE": "ToolService",
    "VCS": "GitRepository",
    "WIRELOG": "WireLogRepository",
    "WIRELOGREPOSITORY": "WireLogRepository",
    "WRL": "WireLogRepository",
}

# Reverse mapping: canonical name → abbreviation
CANONICAL_MAP = {v: k for k, v in ABBREVIATION_MAP.items()}


class NamingReport(NamedTuple):
    c4_stems: set[str]
    uc_stems: set[str]
    sq_dirs: set[str]
    violations: list[Violation]


def extract_c4_stems(docs_dir: Path) -> set[str]:
    """Extract group stems from C4 component diagram filenames."""
    c4_dir = docs_dir / "C4"
    if not c4_dir.exists():
        return set()

    stems = set()
    for f in c4_dir.glob("c4_nasim_component_*.puml"):
        # Extract stem: c4_nasim_component_agent → agent
        match = re.match(r"c4_nasim_component_(.+)\.puml", f.name)
        if match:
            stems.add(match.group(1))
    return stems


def extract_uc_stems(docs_dir: Path) -> set[str]:
    """Extract group stems from UC diagram filenames."""
    uc_dir = docs_dir / "UC"
    if not uc_dir.exists():
        return set()

    stems = set()
    for f in uc_dir.glob("uc_*.puml"):
        if f.name == "uc_overview.puml":
            continue
        # Extract stem: uc_agent → agent
        match = re.match(r"uc_(.+)\.puml", f.name)
        if match:
            stems.add(match.group(1))
    return stems


def extract_sq_dirs(docs_dir: Path) -> set[str]:
    """Extract directory names from SQ group directories."""
    sq_dir = docs_dir / "SQ"
    if not sq_dir.exists():
        return set()

    dirs = set()
    for d in sq_dir.iterdir():
        if d.is_dir() and d.name != "common":
            dirs.add(d.name)
    return dirs


def check_naming_consistency(docs_dir: Path) -> NamingReport:
    """Check cross-layer naming consistency."""
    c4_stems = extract_c4_stems(docs_dir)
    uc_stems = extract_uc_stems(docs_dir)
    sq_dirs = extract_sq_dirs(docs_dir)

    violations: list[Violation] = []

    # Check 1: SQ directories should use canonical names, not abbreviations
    # Skip directories where abbreviation equals canonical name (e.g., CLI, MCP)
    for sq_dir in sq_dirs:
        if sq_dir in ABBREVIATION_MAP:
            canonical = ABBREVIATION_MAP[sq_dir]
            if sq_dir == canonical:  # Already canonical (CLI, MCP)
                continue
            violations.append(Violation(
                rule_id="NAMING-001",
                severity="critical",
                message=f"SQ directory '{sq_dir}/' uses abbreviated code; should be '{canonical}/'",
                location=f"docs/SQ/{sq_dir}/",
                fix_suggestion=f"Rename directory to '{canonical}/' per sq.md File Naming rule",
            ))

    # Check 2: C4 stems ↔ UC stems consistency
    for c4_stem in c4_stems:
        if c4_stem not in uc_stems:
            violations.append(Violation(
                rule_id="NAMING-002",
                severity="high",
                message=f"C4 component '{c4_stem}' has no matching UC file 'uc_{c4_stem}.puml'",
                location=f"docs/C4/c4_nasim_component_{c4_stem}.puml",
                fix_suggestion=f"Create 'docs/UC/uc_{c4_stem}.puml' or verify UC exists with different stem",
            ))

    for uc_stem in uc_stems:
        if uc_stem not in c4_stems:
            violations.append(Violation(
                rule_id="NAMING-003",
                severity="high",
                message=f"UC file 'uc_{uc_stem}.puml' has no matching C4 component diagram",
                location=f"docs/UC/uc_{uc_stem}.puml",
                fix_suggestion=f"Create C4 component or verify C4 exists with different stem",
            ))

    # Check 3: SQ directories ↔ C4/UC stems
    # Map SQ dirs to canonical names for comparison
    sq_canonicals = set()
    for sq_dir in sq_dirs:
        if sq_dir in ABBREVIATION_MAP:
            sq_canonicals.add(ABBREVIATION_MAP[sq_dir].lower())
        else:
            sq_canonicals.add(sq_dir.lower())

    for c4_stem in c4_stems:
        if c4_stem not in sq_canonicals:
            violations.append(Violation(
                rule_id="NAMING-004",
                severity="high",
                message=f"C4 component '{c4_stem}' has no matching SQ directory",
                location=f"docs/C4/c4_nasim_component_{c4_stem}.puml",
                fix_suggestion=f"Create SQ directory '{ABBREVIATION_MAP.get(c4_stem.upper(), c4_stem.capitalize())}/' or verify SQ exists",
            ))

    return NamingReport(
        c4_stems=c4_stems,
        uc_stems=uc_stems,
        sq_dirs=sq_dirs,
        violations=violations,
    )


def format_text_report(report: NamingReport) -> str:
    """Format report as human-readable text."""
    lines = []
    lines.append("Cross-Layer Naming Consistency Report")
    lines.append("=" * 50)
    lines.append(f"C4 component stems: {len(report.c4_stems)}")
    lines.append(f"UC file stems:      {len(report.uc_stems)}")
    lines.append(f"SQ directories:     {len(report.sq_dirs)}")
    lines.append("")

    if report.violations:
        lines.append(f"VIOLATIONS: {len(report.violations)}")
        lines.append("-" * 50)
        for v in report.violations:
            lines.append(f"[{v.severity.upper():8s}] {v.rule_id}: {v.message}")
            lines.append(f"          Location: {v.location}")
            if v.fix_suggestion:
                lines.append(f"          Fix: {v.fix_suggestion}")
            lines.append("")
    else:
        lines.append("NO VIOLATIONS - all layers are consistent")

    # Summary tables
    lines.append("C4 Stems:")
    for s in sorted(report.c4_stems):
        lines.append(f"  - {s}")
    lines.append("")

    lines.append("UC Stems:")
    for s in sorted(report.uc_stems):
        lines.append(f"  - {s}")
    lines.append("")

    lines.append("SQ Directories:")
    for s in sorted(report.sq_dirs):
        canonical = ABBREVIATION_MAP.get(s, s)
        status = "⚠️ LEGACY" if s in ABBREVIATION_MAP else "✅ OK"
        lines.append(f"  - {s}/ → {canonical} {status}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cross-Layer Naming Consistency Checker"
    )
    parser.add_argument("docs_dir", help="Path to docs/ directory")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on any violations")
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    if not docs_dir.exists():
        print(f"Directory not found: {docs_dir}", file=sys.stderr)
        return 2

    report = check_naming_consistency(docs_dir)

    if args.format == "json":
        payload = {
            "c4_stems": sorted(report.c4_stems),
            "uc_stems": sorted(report.uc_stems),
            "sq_dirs": sorted(report.sq_dirs),
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "severity": v.severity,
                    "message": v.message,
                    "location": v.location,
                    "fix_suggestion": v.fix_suggestion,
                }
                for v in report.violations
            ],
            "total_violations": len(report.violations),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_text_report(report))

    if args.strict and report.violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
