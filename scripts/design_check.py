#!/usr/bin/env python3
"""Design Integrity Check — consolidated cross-domain battery.

Runs all cross-domain checks as a single composite gate.
Exits non-zero if any CRITICAL check fails.

Usage:
    python design_check.py /path/to/project --strict
    python design_check.py /path/to/project --format json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple


TOOLS_DIR = Path(__file__).resolve().parent.parent


class CheckResult(NamedTuple):
    name: str
    passed: bool
    severity: str  # critical, high, info
    detail: str


def run_linter(script: str, args: list[str], cwd: Path) -> tuple[bool, str]:
    """Run a linter script and return (passed, output)."""
    script_path = TOOLS_DIR / script
    if not script_path.exists():
        return False, f"Script not found: {script_path}"
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout.strip() or result.stderr.strip()
        passed = result.returncode == 0
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT: linter exceeded 120s"
    except Exception as e:
        return False, f"ERROR: {e}"


def run_grep(pattern: str, path: str, cwd: Path) -> tuple[bool, str]:
    """Run a grep check. Passes if grep finds zero matches."""
    try:
        result = subprocess.run(
            ["grep", "-rn", pattern, path],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        # grep returns 0 when matches found, 1 when no matches, 2 on error
        if result.returncode == 0:
            return False, f"Found {len(result.stdout.splitlines())} matches:\n{result.stdout[:500]}"
        elif result.returncode == 1:
            return True, "No matches found"
        else:
            return False, f"grep error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT: grep exceeded 30s"
    except Exception as e:
        return False, f"ERROR: {e}"


def run_plantuml_render_check(docs_dir: Path) -> CheckResult:
    """Check that all .puml files can be parsed (basic syntax check)."""
    puml_files = list(docs_dir.rglob("*.puml"))
    if not puml_files:
        return CheckResult("PlantUML files exist", False, "critical", "No .puml files found in docs/")
    
    # Basic syntax check: every @startuml must have @enduml
    errors = []
    for f in puml_files:
        try:
            content = f.read_text()
            starts = content.count("@startuml")
            ends = content.count("@enduml")
            if starts != ends:
                errors.append(f"{f.relative_to(docs_dir)}: {starts} @startuml vs {ends} @enduml")
        except Exception as e:
            errors.append(f"{f.relative_to(docs_dir)}: read error - {e}")
    
    if errors:
        return CheckResult(
            "PlantUML syntax", False, "critical",
            f"{len(errors)} files with unclosed @startuml:\n" + "\n".join(errors[:10])
        )
    return CheckResult("PlantUML syntax", True, "critical", f"{len(puml_files)} files OK")


def run_all_checks(project_dir: Path) -> list[CheckResult]:
    """Run the full design integrity check battery."""
    results: list[CheckResult] = []
    docs_dir = project_dir / "docs"

    if not docs_dir.exists():
        results.append(CheckResult("docs/ exists", False, "critical", "No docs/ directory found"))
        return results

    # 1. PlantUML syntax check
    results.append(run_plantuml_render_check(docs_dir))

    # 2. C4: Component_Ext forbidden
    c4_dir = docs_dir / "C4"
    if c4_dir.exists():
        passed, detail = run_grep(r"Component_Ext", "docs/C4/", project_dir)
        results.append(CheckResult("C4: No Component_Ext (AU-01)", passed, "critical", detail))
    else:
        results.append(CheckResult("C4: No Component_Ext (AU-01)", False, "critical", "docs/C4/ not found"))

    # 3. C4: SIM-01 exception for large overviews
    if c4_dir.exists():
        large_files = []
        for f in sorted(c4_dir.glob("*.puml")):
            content = f.read_text()
            # Count elements: Person, System, Container, Component, Boundary, System_Ext
            element_count = sum(1 for line in content.splitlines()
                              if line.strip().startswith(("Person(", "System(", "Container(", "Component(", "Boundary(", "System_Ext(")))
            if element_count > 12:
                has_exception = "SIM-01 EXCEPTION" in content
                if not has_exception:
                    large_files.append(f"{f.name} ({element_count} elements, no SIM-01 EXCEPTION header)")
        if large_files:
            results.append(CheckResult(
                "C4: SIM-01 exception headers (AU-02)", False, "critical",
                f"{len(large_files)} files >12 elements without exception header:\n" + "\n".join(large_files)
            ))
        else:
            results.append(CheckResult("C4: SIM-01 exception headers (AU-02)", True, "critical", "All files compliant"))
    else:
        results.append(CheckResult("C4: SIM-01 exception headers (AU-02)", False, "critical", "docs/C4/ not found"))

    # 4. UC: No same-group internal components as actors (UC-02 / UC-010)
    uc_dir = docs_dir / "UC"
    if uc_dir.exists():
        passed, detail = run_grep(
            r"actor.*Router\|actor.*Orchestrator\|actor.*Handler\|actor.*ServerRouter\|actor.*AgentOrchestrator",
            "docs/UC/",
            project_dir,
        )
        results.append(CheckResult("UC: No internal actors (UC-010)", passed, "critical", detail))
    else:
        results.append(CheckResult("UC: No internal actors (AU-03)", False, "critical", "docs/UC/ not found"))

    # 5. SM: Transition Coverage Table exists in README
    sm_readme = docs_dir / "SM" / "README.md"
    if sm_readme.exists():
        content = sm_readme.read_text()
        has_coverage_table = "Transition Coverage" in content or "Coverage Table" in content or "| From State" in content
        results.append(CheckResult(
            "SM: Transition Coverage Table (AU-04)", has_coverage_table, "critical",
            "Found" if has_coverage_table else "MISSING: No Transition Coverage Table in docs/SM/README.md"
        ))
    else:
        results.append(CheckResult("SM: Transition Coverage Table (AU-04)", False, "critical", "docs/SM/README.md not found"))

    # 6. SM labels are UC IDs (no human-readable labels)
    sm_dir = docs_dir / "SM"
    if sm_dir.exists():
        passed = True
        violations = []
        for f in sorted(sm_dir.rglob("*.puml")):
            content = f.read_text()
            for line in content.splitlines():
                stripped = line.strip()
                if "-->" in stripped and "[" not in stripped:
                    # Check if label contains non-UC-ID text
                    if ":" in stripped:
                        label = stripped.split(":")[-1].strip().strip('"')
                        if label and not label.startswith("[") and not label.upper().startswith(tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")):
                            pass  # Could be a valid transition label
                        # Check for human-readable text (more than just UC-ID)
                        if label and " " in label and "[" not in label and "state" not in label.lower():
                            violations.append(f"{f.name}: {stripped.strip()}")
        if violations:
            results.append(CheckResult(
                "SM: Labels are UC IDs", False, "critical",
                f"Human-readable labels found:\n" + "\n".join(violations[:5])
            ))
        else:
            results.append(CheckResult("SM: Labels are UC IDs", True, "critical", "All labels valid"))
    else:
        results.append(CheckResult("SM: Labels are UC IDs", False, "critical", "docs/SM/ not found"))

    # 7. Run existing service checks if available
    lint_checks = [
        ("State Machine Diagram", "services/state-machine-diagram/sm_lint.py", ["docs/SM", "--strict"]),
        ("Sequence Diagram", "services/sequence-diagram/sq_lint.py", ["docs/SQ", "--strict"]),
        ("Resource-Oriented Design", "services/resource-oriented-design/rod_csr_sq_lint.py", ["docs/SQ", "--strict"]),
    ]
    for name, script, args in lint_checks:
        passed, detail = run_linter(script, args, project_dir)
        results.append(CheckResult(name, passed, "high" if not passed else "info", detail))

    # 8. Cross-layer naming consistency check
    passed, detail = run_linter(
        "scripts/cross_layer_naming_check.py",
        [str(docs_dir), "--strict"],
        project_dir,
    )
    results.append(CheckResult("Cross-layer naming consistency", passed, "high", detail))

    return results


def format_text_report(results: list[CheckResult]) -> str:
    """Format results as human-readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("DESIGN INTEGRITY CHECK")
    lines.append("=" * 60)
    lines.append("")

    critical_failures = [r for r in results if not r.passed and r.severity == "critical"]
    high_failures = [r for r in results if not r.passed and r.severity == "high"]
    info_failures = [r for r in results if not r.passed and r.severity == "info"]
    passed_checks = [r for r in results if r.passed]

    if critical_failures:
        lines.append(f"CRITICAL FAILURES ({len(critical_failures)}):")
        lines.append("-" * 40)
        for r in critical_failures:
            lines.append(f"  ❌ {r.name}")
            for d in r.detail.split("\n"):
                lines.append(f"     {d}")
        lines.append("")

    if high_failures:
        lines.append(f"HIGH FAILURES ({len(high_failures)}):")
        lines.append("-" * 40)
        for r in high_failures:
            lines.append(f"  ⚠️  {r.name}")
            for d in r.detail.split("\n"):
                lines.append(f"     {d}")
        lines.append("")

    if info_failures:
        lines.append(f"INFO ({len(info_failures)}):")
        for r in info_failures:
            lines.append(f"  ℹ️  {r.name}: {r.detail[:120]}")
        lines.append("")

    lines.append(f"PASSED ({len(passed_checks)}):")
    for r in passed_checks:
        lines.append(f"  ✅ {r.name}")

    lines.append("")
    lines.append("=" * 60)
    if critical_failures:
        lines.append(f"RESULT: ❌ BLOCKED — {len(critical_failures)} CRITICAL failures")
    elif high_failures:
        lines.append(f"RESULT: ⚠️  PASSED WITH WARNINGS — {len(high_failures)} HIGH issues")
    else:
        lines.append("RESULT: ✅ ALL CHECKS PASSED")
    lines.append("=" * 60)
    return "\n".join(lines)


def format_json_report(results: list[CheckResult]) -> str:
    """Format results as JSON."""
    payload = {
        "checks": [
            {
                "name": r.name,
                "passed": r.passed,
                "severity": r.severity,
                "detail": r.detail,
            }
            for r in results
        ],
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r.passed),
            "failed_critical": sum(1 for r in results if not r.passed and r.severity == "critical"),
            "failed_high": sum(1 for r in results if not r.passed and r.severity == "high"),
            "blocked": any(not r.passed and r.severity == "critical" for r in results),
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Design Integrity Check — consolidated cross-domain battery"
    )
    parser.add_argument(
        "project_dir", nargs="?", default=".",
        help="Project root directory (default: current dir)"
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero on ANY failure (including HIGH)")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists():
        print(f"Directory not found: {project_dir}", file=sys.stderr)
        return 2

    results = run_all_checks(project_dir)

    if args.format == "json":
        print(format_json_report(results))
    else:
        print(format_text_report(results))

    # Determine exit code
    critical_failures = any(not r.passed and r.severity == "critical" for r in results)
    high_failures = any(not r.passed and r.severity == "high" for r in results)

    if critical_failures:
        return 1
    if args.strict and high_failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
