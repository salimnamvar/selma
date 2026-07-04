#!/usr/bin/env python3
"""C4 Linter CLI.

Canonical location: ~/.grok/tools/software-design/c4/c4_lint.py  (and ~/.claude equivalent)

Usage:
    python tools/software-design/c4/c4_lint.py docs/C4 docs/LOG
    python ~/.grok/tools/software-design/c4/c4_lint.py path/to/diagram.puml --format json --strict

This tool is bound to rules/software-design/c4.md and is invoked as part of
the C4 layer in skills/software-design (review, audit, cicd gates).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

# Allow running as script before package install
sys.path.insert(0, str(Path(__file__).parent))

from c4.ir import C4Diagram
from c4.parser import parse_file
from c4.report import build_report
from c4.validator import validate


def find_puml_files(paths: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        pp = Path(p)
        if pp.is_file() and pp.suffix.lower() in {".puml", ".plantuml"}:
            files.append(pp)
        elif pp.is_dir():
            files.extend(sorted(pp.rglob("*.puml")))
            files.extend(sorted(pp.rglob("*.plantuml")))
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="C4 PlantUML linter (canonical global tool)")
    parser.add_argument("paths", nargs="+", help="Files or directories containing .puml C4 diagrams")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any violations found")
    args = parser.parse_args()

    files = find_puml_files(args.paths)
    if not files:
        print("No .puml files found.", file=sys.stderr)
        return 2

    all_reports = []
    total_violations = 0
    total_critical = 0

    for f in files:
        try:
            diagram: C4Diagram = parse_file(str(f))
            violations = validate(diagram)
            report = build_report(diagram, violations)
            all_reports.append(report)
            total_violations += report.total_violations
            total_critical += report.critical
        except Exception as exc:
            print(f"ERROR parsing {f}: {exc}", file=sys.stderr)
            continue

    if args.format == "json":
        payload = {
            "files": len(all_reports),
            "total_violations": total_violations,
            "critical": total_critical,
            "reports": [r.to_dict() if hasattr(r, "to_dict") else json.loads(r.to_json()) for r in all_reports],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for r in all_reports:
            print(r.to_text())
            print("-" * 60)
        print(f"\nSUMMARY: {len(all_reports)} files, {total_violations} violations, {total_critical} critical")

    if args.strict and total_violations > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
