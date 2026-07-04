#!/usr/bin/env python3
"""C4 Auto-Fix CLI.

Canonical location: ~/.grok/tools/software-design/c4/c4_fix.py  (and ~/.claude equivalent)

Applies deterministic fixes and writes corrected PlantUML.

Usage:
    python ~/.grok/tools/software-design/c4/c4_fix.py docs/LOG --in-place
    python tools/software-design/c4/c4_fix.py docs/C4/c4_mdl_context.puml --stdout --diff

Always run after edits to C4 diagrams. Integrated with software-design skill
for the C4 layer (review + cicd gates).
"""
from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).parent))

from c4.fixer import apply_fixes
from c4.parser import parse_file
from c4.report import build_report
from c4.rewriter import rewrite_diagram
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
    parser = argparse.ArgumentParser(description="C4 PlantUML auto-fixer (canonical global tool)")
    parser.add_argument("paths", nargs="+", help="Files or directories")
    parser.add_argument("--in-place", "-i", action="store_true", help="Write fixes back to original files")
    parser.add_argument("--stdout", action="store_true", help="Print corrected PlantUML to stdout (first file only)")
    parser.add_argument("--diff", action="store_true", help="Show unified diff of changes")
    parser.add_argument("--report-json", action="store_true", help="Also emit violation report JSON")
    args = parser.parse_args()

    files = find_puml_files(args.paths)
    if not files:
        print("No .puml files found for the given path(s).", file=sys.stderr)
        return 2

    any_changed = False

    for f in files:
        try:
            original_text = f.read_text(encoding="utf-8")
            diagram = parse_file(str(f))
            violations = validate(diagram)

            if not violations:
                if args.stdout:
                    # Still emit the diagram (identical to original) for agent "only corrected output" mode
                    print(original_text, end="")
                    return 0
                if args.diff:
                    continue
                print(f"[clean] {f}")
                continue

            fix_result = apply_fixes(diagram, violations)
            corrected = rewrite_diagram(fix_result.diagram)

            changed = corrected != original_text
            any_changed = any_changed or changed

            if args.report_json:
                report = build_report(fix_result.diagram, violations)
                print(json.dumps({
                    "file": str(f),
                    "fixes": fix_result.fixes_applied,
                    "report": json.loads(report.to_json()),
                }, indent=2))

            if args.stdout:
                # only first file when using stdout — always emit a (possibly identical) corrected form
                print(corrected, end="")
                return 0

            if args.diff and changed:
                diff = difflib.unified_diff(
                    original_text.splitlines(keepends=True),
                    corrected.splitlines(keepends=True),
                    fromfile=f"before/{f.name}",
                    tofile=f"after/{f.name}",
                )
                sys.stdout.writelines(diff)

            if args.in_place and changed:
                f.write_text(corrected, encoding="utf-8")
                print(f"[fixed] {f}  (violations={len(violations)}, applied={len(fix_result.fixes_applied)})")
            elif not args.diff and not args.stdout:
                print(f"[would-fix] {f}  violations={len(violations)} fixes={len(fix_result.fixes_applied)}")

        except Exception as exc:
            print(f"ERROR on {f}: {exc}", file=sys.stderr)
            continue

    return 0 if not any_changed or args.in_place or args.stdout else 0


if __name__ == "__main__":
    sys.exit(main())
