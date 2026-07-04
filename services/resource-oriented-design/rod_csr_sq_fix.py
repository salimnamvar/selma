#!/usr/bin/env python3
"""RoD-CSR-SQ Fixer CLI.

Auto-fixes common violations in sequence diagrams per rod-csr-sq.md.

Usage:
    python ~/.claude/tools/software-design/rod_csr_sq/rod_csr_sq_fix.py docs/SQ --dry-run
    python ~/.claude/tools/software-design/rod_csr_sq/rod_csr_sq_fix.py docs/SQ/some.puml

Bound to rules/software-design/rod-csr-sq.md and invoked by software-design skill.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable


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


def fix_intro_note_add_returns(content: str) -> str:
    """Add Returns section to intro note if missing."""
    if "returns:" in content.lower() or "Returns:" in content:
        return content

    # Find intro note (note over ... with Scope:)
    intro_pattern = re.compile(
        r'(note\s+over\s+[^:]+:\s*\n(?:.*?\n)*?.*?Scope:\s*.*?\n)'
        r'((?:.*?\n)*?)'
        r'(end\s+note)',
        re.IGNORECASE,
    )

    def add_returns(match):
        before = match.group(1)
        middle = match.group(2)
        end = match.group(3)
        if "returns:" not in middle.lower():
            returns_line = "  Returns:        200 OK on success; 400/404/500 on failure\n"
            return before + middle + returns_line + end
        return match.group(0)

    return intro_pattern.sub(add_returns, content)


def fix_summary_note_add_failure(content: str) -> str:
    """Add Failure field to summary note if missing."""
    if "failure:" in content.lower():
        return content

    summary_pattern = re.compile(
        r'(note\s+over\s+[^:]+:\s*\n(?:.*?\n)*?.*?Flow:\s*.*?\n)'
        r'((?:.*?\n)*?)'
        r'(end\s+note)',
        re.IGNORECASE,
    )

    def add_failure(match):
        before = match.group(1)
        middle = match.group(2)
        end = match.group(3)
        if "failure:" not in middle.lower():
            failure_line = "  Failure:        {HTTP} {STATUS} — {condition}\n"
            return before + middle + failure_line + end
        return match.group(0)

    return summary_pattern.sub(add_failure, content)


def fix_add_activation_bars(content: str) -> str:
    """Add activation bars if missing."""
    if re.search(r'\bactivate\b', content, re.IGNORECASE):
        return content

    # Find first message arrow and add activate after it
    arrow_pattern = re.compile(r'(\w+)\s*->\s*(\w+)\s*:', re.IGNORECASE)
    m = arrow_pattern.search(content)
    if m:
        target = m.group(2)
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if arrow_pattern.search(line) and target in line:
                # Insert activate after the arrow line
                indent = len(line) - len(line.lstrip())
                activate_line = ' ' * indent + f'activate {target}'
                lines.insert(i + 1, activate_line)
                break
        content = '\n'.join(lines)

    return content


FIXERS = {
    "RSQ-003": fix_intro_note_add_returns,
    "RSQ-004": fix_summary_note_add_failure,
    "RSQ-005": fix_summary_note_add_failure,
    "RSQ-006": fix_add_activation_bars,
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="RoD-CSR-SQ auto-fixer (applies safe structural fixes)"
    )
    parser.add_argument("paths", nargs="+", help="Files or directories")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    parser.add_argument("--rules", nargs="*", help="Only fix specific rule IDs (e.g., RSQ-003)")
    args = parser.parse_args()

    files = find_puml_files(args.paths)
    if not files:
        print("No .puml files found.", file=sys.stderr)
        return 2

    fixed_count = 0
    for f in files:
        content = f.read_text()
        original = content

        for rule_id, fixer in FIXERS.items():
            if args.rules and rule_id not in args.rules:
                continue
            content = fixer(content)

        if content != original:
            fixed_count += 1
            if args.dry_run:
                print(f"WOULD FIX: {f}")
            else:
                f.write_text(content)
                print(f"FIXED: {f}")

    print(f"\n{'Would fix' if args.dry_run else 'Fixed'}: {fixed_count} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
