#!/usr/bin/env python3
"""ODCS / CT-DATA Linter CLI.

Canonical: ~/.grok/tools/software-design/ct_data/odcs_lint.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).parent))

from ct_data.parser import parse_odcs_file
from ct_data.report import build_odcs_report
from ct_data.validator import validate_odcs


def find_yaml_files(paths: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        pp = Path(p)
        if pp.is_file() and pp.suffix.lower() in {".yaml", ".yml"}:
            files.append(pp)
        elif pp.is_dir():
            files.extend(sorted(pp.rglob("*.yaml")))
            files.extend(sorted(pp.rglob("*.yml")))
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description="ODCS/CT-DATA linter")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    files = find_yaml_files(args.paths)
    if not files:
        print("No yaml files.", file=sys.stderr)
        return 2

    reps = []
    tot = crit = 0
    for f in files:
        try:
            d = parse_odcs_file(f)
            vs = validate_odcs(d)
            r = build_odcs_report(d, vs)
            reps.append(r)
            tot += r.total_violations
            crit += r.critical
        except Exception as e:
            print(f"ERROR {f}: {e}", file=sys.stderr)
    if args.format == "json":
        print(json.dumps({"layer": "ct-data", "files": len(reps), "total": tot, "critical": crit, "reports": [json.loads(r.to_json()) for r in reps]}, indent=2))
    else:
        for r in reps:
            print(r.to_text())
            print("---")
        print(f"SUMMARY ct-data: {len(reps)} {tot}v {crit}c")
    return 1 if args.strict and tot else 0


if __name__ == "__main__":
    sys.exit(main())
