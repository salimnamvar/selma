#!/usr/bin/env python3
"""RoD-CSR-SQ Linter CLI.

Validates sequence diagrams against the unified rod-csr-sq rule.
Checks CSR layer compliance, RoD method/resource patterns, and SQ structure.

Usage:
    python ~/.claude/tools/selma/rod_csr_sq/rod_csr_sq_lint.py docs/SQ --format text --strict
    python ~/.claude/tools/selma/rod_csr_sq/rod_csr_sq_lint.py docs/SQ/some.puml --format json

Bound to rules/selma/rod-csr-sq.md and invoked by selma skill.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).parent))

from rod_csr_sq.parser import parse_rod_csr_sq
from rod_csr_sq.report import build_rod_csr_sq_report
from rod_csr_sq.validator import validate_rod_csr_sq


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
    parser = argparse.ArgumentParser(
        description="RoD-CSR-SQ unified linter (validates CSR + RoD + SQ in sequence diagrams)"
    )
    parser.add_argument("paths", nargs="+", help="Files or directories")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on any violations")
    parser.add_argument("--csr-only", action="store_true", help="Check only CSR rules")
    parser.add_argument("--rod-only", action="store_true", help="Check only RoD rules")
    parser.add_argument("--sq-only", action="store_true", help="Check only SQ structure rules")
    args = parser.parse_args()

    files = find_puml_files(args.paths)
    if not files:
        print("No .puml files found.", file=sys.stderr)
        return 2

    all_reports = []
    total = 0
    crit = 0

    for f in files:
        # Skip common/ shared include files — they are not standalone diagrams
        if "common" in f.parts:
            continue
        try:
            d = parse_rod_csr_sq(str(f))
            violations = validate_rod_csr_sq(d)

            # Filter violations based on flags
            if args.csr_only:
                violations = [v for v in violations if v.rule_id.startswith("RCSR")]
            elif args.rod_only:
                violations = [v for v in violations if v.rule_id.startswith("RROD")]
            elif args.sq_only:
                violations = [v for v in violations if v.rule_id.startswith("RSQ")]

            rep = build_rod_csr_sq_report(d, violations)
            all_reports.append(rep)
            total += rep.total_violations
            crit += rep.critical
        except Exception as exc:
            print(f"ERROR parsing {f}: {exc}", file=sys.stderr)
            continue

    if args.format == "json":
        payload = {
            "layer": "rod_csr_sq",
            "files": len(all_reports),
            "total_violations": total,
            "critical": crit,
            "reports": [json.loads(r.to_json()) for r in all_reports],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for r in all_reports:
            print(r.to_text())
            print("-" * 60)
        print(f"\nSUMMARY: {len(all_reports)} files, {total} violations, {crit} critical")

    if args.strict and crit > 0:
        return 1
    if args.strict and total > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
