#!/usr/bin/env python3
"""Cross-diagram rule enforcement tool.

Validates PlantUML/Mermaid diagrams against design rules:
- UC <<include>> arrow directions (base → included)
- UC <<extend>> arrow directions (extension → base)
- SQ actor as first lifeline for UC-level diagrams
- Cross-cutting concerns use ref frames
- SM state colors with hex notation
- Required headers in all diagrams

Usage:
    python scripts/diagram_linter.py [dir] [--strict]
    python scripts/diagram_linter.py docs/ --format json
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
from typing import List


def lint_usecase(file: Path) -> List[str]:
    """Validate Use Case diagram rules."""
    errors = []
    try:
        content = file.read_text()
    except UnicodeDecodeError:
        return errors

    # Rule: Include direction base → included
    includes = re.findall(r"(\w[\w\s]*?)\s*-->.*<<include>>\s*(\w[\w\s]*?)(?:\s*|$)", content)
    for base, inc in includes:
        base, inc = base.strip(), inc.strip()
        # Check if reverse direction exists
        if re.search(rf"{re.escape(inc)}\s*-->.*<<include>>\s*{re.escape(base)}", content):
            errors.append(f"UC-001: Reverse <<include>> arrow detected between {base} and {inc}")

    # Rule: Extend direction extension → base
    extends = re.findall(r"(\w[\w\s]*?)\s*-->.*<<extend>>\s*(\w[\w\s]*?)(?:\s*|$)", content)
    for ext, base in extends:
        ext, base = ext.strip(), base.strip()
        # Check if reverse direction exists
        if re.search(rf"{re.escape(base)}\s*-->.*<<extend>>\s*{re.escape(ext)}", content):
            errors.append(f"UC-002: Reverse <<extend>> arrow detected between {ext} and {base}")

    # Rule: System boundary must exist
    if "rectangle" not in content.lower() and "package" not in content.lower():
        if "usecase" in content.lower():
            errors.append("UC-003: No system boundary (rectangle/package) found in use case diagram")

    return errors


def lint_sequence(file: Path) -> List[str]:
    """Validate Sequence Diagram rules."""
    errors = []
    try:
        content = file.read_text()
    except UnicodeDecodeError:
        return errors

    # Rule: Actor/User should be first lifeline for UC-level diagrams
    lifelines = re.findall(r"^(actor|participant)\s+(\S+)", content, re.MULTILINE | re.IGNORECASE)
    if lifelines:
        first_type, first_name = lifelines[0]
        # Check if this is a UC-level diagram (has UC ID in title or notes)
        has_uc_id = bool(re.search(r"[A-Z]{2,}-\d{2}", content))
        if has_uc_id and first_type.lower() == "actor":
            # Actor is fine for UC-level
            pass
        elif has_uc_id and "User" not in first_name and "Developer" not in first_name:
            errors.append(f"SQ-001: First lifeline should be Actor/User for UC-level diagram, got: {first_name}")

    # Rule: alt/opt/loop/par blocks must be balanced with end
    block_openers = len(re.findall(r"\b(alt|opt|loop|par|seq)\b", content))
    # Only count standalone "end" (not "end note", "end skinparam", etc.)
    end_count = len(re.findall(r"^\s*end\s*$", content, re.MULTILINE))
    if block_openers > 0 and end_count != block_openers:
        errors.append(f"SQ-002: Mismatched block/end blocks ({block_openers} openers, {end_count} end)")

    # Rule: Required header comment
    if "Title:" not in content and "title " not in content.lower():
        errors.append("SQ-004: Missing title in sequence diagram")

    # Rule: ref frames for cross-cutting
    if "OBS" in content or "AGT-15" in content or "HK" in content:
        if "ref" not in content.lower():
            errors.append("SQ-005: Cross-cutting concerns (OBS/SAF/HK) should use ref frames")

    return errors


def lint_state_machine(file: Path) -> List[str]:
    """Validate State Machine rules."""
    errors = []
    try:
        content = file.read_text()
    except UnicodeDecodeError:
        return errors

    # Rule: Hex colors on states
    states = re.findall(r'state\s+"(\w+)"\s+as\s+\w+\s+#(\w{6})', content)
    if not states:
        states = re.findall(r"state\s+(\w+)\s+#(\w{6})", content)

    if not states and "state " in content.lower():
        errors.append("SM-001: No state definitions with hex colors found")

    # Rule: Check for duplicate colors
    colors = [color for _, color in states]
    if len(colors) != len(set(colors)):
        errors.append("SM-002: Duplicate hex colors found in state definitions")

    # Rule: Initial state
    if "[*]" not in content and "-->" not in content:
        errors.append("SM-003: No initial state transition found")

    return errors


def lint_c4(file: Path) -> List[str]:
    """Validate C4 diagram rules."""
    errors = []
    try:
        content = file.read_text()
    except UnicodeDecodeError:
        return errors

    # Rule: LAYOUT_LEFT_RIGHT on context diagrams
    if "context" in file.stem.lower():
        if "LAYOUT_LEFT_RIGHT" not in content:
            errors.append("C4-001: Context diagrams must use LAYOUT_LEFT_RIGHT()")

    # Rule: Required header
    if "Title:" not in content:
        errors.append("C4-002: Missing structured header (Title/Boundary/Purpose)")

    # Rule: Pinned C4-PlantUML version
    if "!include" in content and "C4-PlantUML" in content:
        if "/master/" in content or "/main/" in content:
            errors.append("C4-003: C4-PlantUML include should pin to a specific version tag, not master/main")

    return errors


def lint_file(file: Path) -> List[str]:
    """Route file to appropriate linter based on name/path."""
    name = file.stem.lower()
    parent = file.parent.name.lower()

    if "usecase" in name or "uc" in parent:
        return lint_usecase(file)
    elif "sequence" in name or "sq" in parent:
        return lint_sequence(file)
    elif "state" in name or "sm" in parent:
        return lint_state_machine(file)
    elif "c4" in name or "c4" in parent:
        return lint_c4(file)
    else:
        # Try all linters
        errors = []
        errors.extend(lint_usecase(file))
        errors.extend(lint_sequence(file))
        errors.extend(lint_state_machine(file))
        errors.extend(lint_c4(file))
        return errors


def find_diagram_files(paths: List[Path]) -> List[Path]:
    """Find all PlantUML and Markdown files that might contain diagrams."""
    files = []
    for p in paths:
        if p.is_file():
            if p.suffix.lower() in {".puml", ".plantuml", ".md"}:
                files.append(p)
        elif p.is_dir():
            files.extend(sorted(p.rglob("*.puml")))
            files.extend(sorted(p.rglob("*.plantuml")))
            # Also check markdown files for embedded diagrams
            for md in p.rglob("*.md"):
                try:
                    content = md.read_text()
                    if "@startuml" in content or "```mermaid" in content:
                        files.append(md)
                except UnicodeDecodeError:
                    continue
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="Cross-diagram rule enforcement")
    parser.add_argument("paths", nargs="*", default=["."], help="Files or directories to lint")
    parser.add_argument("--strict", action="store_true", help="Strict mode (fail on any issue)")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    files = find_diagram_files([Path(p) for p in args.paths])
    if not files:
        print("No diagram files found.", file=sys.stderr)
        return 2

    all_violations = {}
    total_errors = 0

    for f in files:
        errors = lint_file(f)
        if errors:
            all_violations[str(f)] = errors
            total_errors += len(errors)

    if args.format == "json":
        import json

        print(json.dumps({"violations": all_violations, "total": total_errors}))
    else:
        if all_violations:
            print(f"[DIAGRAM-LINTER] Found {total_errors} violations across {len(all_violations)} files:")
            for file, errors in all_violations.items():
                print(f"\n  {file}:")
                for e in errors:
                    print(f"    - {e}")
        else:
            print("[DIAGRAM-LINTER] All diagram checks passed.")

    if total_errors > 0 and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
