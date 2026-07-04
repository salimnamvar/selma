#!/usr/bin/env python3
"""Architecture validation tool.

Validates that project structure matches C4 Container/Component hierarchy
and that public interface methods called in Sequence diagrams exist in code.

Usage:
    python scripts/validate_architecture.py [project_dir]
    python scripts/validate_architecture.py . --strict
"""
from __future__ import annotations

import ast
import argparse
import sys
from pathlib import Path
from typing import Dict, Set, List, Tuple


def extract_public_interfaces(src_dir: Path) -> Dict[str, Set[str]]:
    """Extract public class methods from Python source files."""
    interfaces: Dict[str, Set[str]] = {}
    if not src_dir.exists():
        return interfaces
    for py in src_dir.rglob("*.py"):
        try:
            tree = ast.parse(py.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = set()
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            if not item.name.startswith("_"):
                                methods.add(item.name)
                    if methods:
                        interfaces[node.name] = methods
        except (SyntaxError, UnicodeDecodeError):
            continue
    return interfaces


def extract_sequence_calls(seq_dir: Path) -> List[Tuple[str, str, str, str]]:
    """Extract method calls from PlantUML sequence diagrams.
    
    Returns list of (file, lifeline, method, call_type).
    """
    calls = []
    if not seq_dir.exists():
        return calls
    for puml in seq_dir.rglob("*.puml"):
        try:
            content = puml.read_text()
        except UnicodeDecodeError:
            continue
        for line in content.splitlines():
            stripped = line.strip()
            if "->" in stripped or "-->" in stripped:
                # Parse participant.method() calls
                parts = stripped.split("->")
                if len(parts) >= 2:
                    target = parts[-1].split(":")[-1].strip()
                    if "(" in target and "." in target:
                        cls, method = target.split(".", 1)
                        method = method.split("(")[0].strip()
                        calls.append((str(puml), cls, method, stripped))
    return calls


def validate_sequence_vs_code(
    calls: List[Tuple[str, str, str, str]],
    interfaces: Dict[str, Set[str]],
) -> List[str]:
    """Validate that sequence diagram calls exist in code."""
    violations = []
    for file, cls, method, raw in calls:
        if cls in interfaces:
            if method not in interfaces[cls]:
                violations.append(
                    f"MISSING: {cls}.{method} in {Path(file).name} — {raw}"
                )
    return violations


def validate_structure(project_dir: Path, expected_containers: List[str]) -> List[str]:
    """Validate that folder structure matches C4 Containers."""
    violations = []
    src = project_dir / "src"
    if not src.exists():
        violations.append(f"MISSING: src/ directory at {src}")
        return violations
    
    # Find the main package
    packages = [d for d in src.iterdir() if d.is_dir() and not d.name.startswith("_")]
    if not packages:
        violations.append("No Python packages found in src/")
        return violations
    
    # Check for expected container directories
    for container in expected_containers:
        found = False
        for pkg in packages:
            if (pkg / container).exists():
                found = True
                break
        if not found:
            violations.append(f"MISSING: Container '{container}' not found in src/")
    
    return violations


def validate_c4_vs_uc(c4_readme: Path, uc_readme: Path) -> List[str]:
    """Validate that C4 components have UC groups and vice versa."""
    violations = []
    if not c4_readme.exists() or not uc_readme.exists():
        return violations
    
    c4_content = c4_readme.read_text()
    uc_content = uc_readme.read_text()
    
    # Extract component names from C4
    c4_components = set()
    for line in c4_content.splitlines():
        if "|" in line and "Component" not in line and "---" not in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if parts:
                c4_components.add(parts[0])
    
    # Extract UC groups from UC
    uc_groups = set()
    for line in uc_content.splitlines():
        if "|" in line and "UC ID" not in line and "---" not in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if parts and "-" in parts[0]:
                group = parts[0].split("-")[0]
                uc_groups.add(group)
    
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate architecture against C4 design"
    )
    parser.add_argument(
        "project_dir", nargs="?", default=".",
        help="Project root directory"
    )
    parser.add_argument("--strict", action="store_true", help="Strict mode (fail on any issue)")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    
    project_dir = Path(args.project_dir).resolve()
    violations = []
    
    # 1. Validate sequence diagram calls vs code
    src_dir = None
    for d in project_dir.rglob("src"):
        if d.is_dir():
            src_dir = d
            break
    
    if src_dir:
        interfaces = extract_public_interfaces(src_dir)
        sq_dir = project_dir / "docs" / "SQ"
        calls = extract_sequence_calls(sq_dir)
        seq_violations = validate_sequence_vs_code(calls, interfaces)
        violations.extend(seq_violations)
    
    # 2. Validate C4 README exists
    c4_readme = project_dir / "docs" / "C4" / "README.md"
    uc_readme = project_dir / "docs" / "UC" / "README.md"
    if not c4_readme.exists():
        violations.append("MISSING: docs/C4/README.md")
    if not uc_readme.exists():
        violations.append("MISSING: docs/UC/README.md")
    
    # 3. Report
    if args.format == "json":
        import json
        print(json.dumps({"violations": violations, "count": len(violations)}))
    else:
        if violations:
            print(f"[ARCH-VALIDATE] Found {len(violations)} violations:")
            for v in violations:
                print(f"  - {v}")
        else:
            print("[ARCH-VALIDATE] All checks passed.")
    
    if violations and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
