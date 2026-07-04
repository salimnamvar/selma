#!/usr/bin/env python3
"""SM Linter CLI.

Canonical location: ~/.grok/tools/selma/sm/sm_lint.py  (and ~/.claude)

Usage:
    python ~/.grok/tools/selma/sm/sm_lint.py docs/SM --strict

Bound to rules/selma/sm.md .
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).parent))

from sm.parser import parse_sm_file
from sm.report import build_sm_report
from sm.validator import validate_sm


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
    parser = argparse.ArgumentParser(description="SM PlantUML linter (canonical global tool)")
    parser.add_argument("paths", nargs="+", help="Files or directories")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    files = find_puml_files(args.paths)
    if not files:
        print("No .puml files found.", file=sys.stderr)
        return 2

    all_reports = []
    total = 0
    crit = 0

    for f in files:
        try:
            d = parse_sm_file(str(f))
            violations = validate_sm(d)
            rep = build_sm_report(d, violations)
            all_reports.append(rep)
            total += rep.total_violations
            crit += rep.critical
        except Exception as exc:
            print(f"ERROR parsing {f}: {exc}", file=sys.stderr)
            continue

    if args.format == "json":
        payload = {"layer": "sm", "files": len(all_reports), "total_violations": total, "critical": crit,
                   "reports": [json.loads(r.to_json()) for r in all_reports]}
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for r in all_reports:
            print(r.to_text())
            print("-" * 60)
        print(f"\nSUMMARY: {len(all_reports)} files, {total} violations, {crit} critical")

    if args.strict and total > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
