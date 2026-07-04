#!/usr/bin/env python3
"""ODCS/CT-DATA Auto-Fix CLI."""
from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).parent))

from ct_data.fixer import apply_odcs_fixes
from ct_data.parser import parse_odcs_file
from ct_data.rewriter import rewrite_odcs
from ct_data.validator import validate_odcs


def find_yaml(paths: Iterable[str]) -> list[Path]:
    fs = []
    for p in paths:
        pp = Path(p)
        if pp.is_file() and pp.suffix.lower() in {".yaml", ".yml"}:
            fs.append(pp)
        elif pp.is_dir():
            fs.extend(sorted(pp.rglob("*.yaml") + list(pp.rglob("*.yml"))))
    return fs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--in-place", "-i", action="store_true")
    ap.add_argument("--stdout", action="store_true")
    ap.add_argument("--diff", action="store_true")
    args = ap.parse_args()

    files = find_yaml(args.paths)
    if not files:
        print("no files", file=sys.stderr)
        return 2
    for f in files:
        try:
            orig = f.read_text(encoding="utf-8")
            d = parse_odcs_file(f)
            vs = validate_odcs(d)
            if not vs:
                if args.stdout:
                    print(orig, end="")
                    return 0
                print(f"[clean] {f}")
                continue
            fr = apply_odcs_fixes(d, vs)
            corr = rewrite_odcs(fr.doc)
            ch = corr != orig
            if args.stdout:
                print(corr, end="")
                return 0
            if args.diff and ch:
                sys.stdout.writelines(difflib.unified_diff(orig.splitlines(keepends=True), corr.splitlines(keepends=True), fromfile="before", tofile="after"))
            if args.in_place and ch:
                f.write_text(corr, encoding="utf-8")
                print(f"[fixed] {f}")
            elif not args.diff:
                print(f"[would-fix] {f}")
        except Exception as e:
            print(f"ERR {f}: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
