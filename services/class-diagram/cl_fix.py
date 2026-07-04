#!/usr/bin/env python3
"""UC Auto-Fix CLI.

Canonical: ~/.grok/tools/selma/usecase-diagram/usecase_diagram_fix.py
"""
from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).parent))

from cl.fixer import apply_cl_fixes
from cl.parser import parse_cl_file
from cl.rewriter import rewrite_cl
from cl.validator import validate_cl


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
    parser = argparse.ArgumentParser(description="UC PlantUML auto-fixer")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--in-place", "-i", action="store_true")
    parser.add_argument("--stdout", action="store_true")
    parser.add_argument("--diff", action="store_true")
    args = parser.parse_args()

    files = find_puml_files(args.paths)
    if not files:
        print("No .puml files.", file=sys.stderr)
        return 2

    any_changed = False
    for f in files:
        try:
            original = f.read_text(encoding="utf-8")
            d = parse_cl_file(str(f))
            violations = validate_cl(d)
            if not violations:
                if args.stdout:
                    print(original, end="")
                    return 0
                if not args.diff:
                    print(f"[clean] {f}")
                continue
            fix_res = apply_cl_fixes(d, violations)
            corrected = rewrite_cl(fix_res.diagram)
            changed = corrected != original
            any_changed = any_changed or changed

            if args.stdout:
                print(corrected, end="")
                return 0
            if args.diff and changed:
                diff = difflib.unified_diff(
                    original.splitlines(keepends=True),
                    corrected.splitlines(keepends=True),
                    fromfile=f"before/{f.name}",
                    tofile=f"after/{f.name}",
                )
                sys.stdout.writelines(diff)
            if args.in_place and changed:
                f.write_text(corrected, encoding="utf-8")
                print(f"[fixed] {f}  applied={len(fix_res.fixes_applied)}")
            elif not args.diff and not args.stdout:
                print(f"[would-fix] {f}  violations={len(violations)}")
        except Exception as exc:
            print(f"ERROR {f}: {exc}", file=sys.stderr)
            continue
    return 0


if __name__ == "__main__":
    sys.exit(main())
