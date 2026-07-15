#!/usr/bin/env python3
"""Validate docs/state-machine PlantUML package against architecture gates.

Gates (Round-06 autonomous loop):
  1. Zero note / end note blocks in .puml files
  2. Every [capability: x] token exists in SPECIFICATION.md §3.2 matrix
  3. Required catalog files present
  4. Optional: PlantUML -checkonly if plantuml.jar or plantuml on PATH

Exit 0 on success; non-zero with diagnostics on failure.

Usage:
  python scripts/validate_state_machines.py
  python scripts/validate_state_machines.py --plantuml
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SM_DIR = ROOT / "docs" / "state-machine"
SPEC = ROOT / "docs" / "spec" / "SPECIFICATION.md"

REQUIRED_PUML = [
    "selma_finding_lifecycle.puml",
    "selma_directive_lifecycle.puml",
    "selma_compilation_pipeline.puml",
    "selma_inspection_pipeline.puml",
    "selma_conflict_resolution.puml",
    "selma_architecture_certification.puml",
    "selma_authorization.puml",
    "selma_artifact_lifecycle.puml",
    "selma_hlc_clock.puml",
    "selma_cgir_hash_chain.puml",
    "common/sm_styles.puml",
]

# Operation bindings that are NOT matrix rows (documented in README).
# command names may appear in labels; only [capability: x] is checked.
CAPABILITY_RE = re.compile(r"\[capability:\s*([^\]]+)\]")
MATRIX_CAP_RE = re.compile(
    r"\|\s*`((?:directive|finding|evidence|inspection|analytics|conflict)\.[a-z_]+)`\s*\|"
)
NOTE_RE = re.compile(r"(?m)^(?:\s*note\b|end note\b)")


def load_spec_capabilities() -> set[str]:
    text = SPEC.read_text(encoding="utf-8")
    return set(MATRIX_CAP_RE.findall(text))


def parse_capability_tokens(raw: str) -> list[str]:
    """Split compound labels like 'inspection.submit | inspection.reinspect'."""
    tokens: list[str] = []
    for part in re.split(r"[|·]", raw):
        part = part.strip()
        if not part:
            continue
        # first token if trailing prose
        tok = part.split()[0]
        if "." in tok:
            tokens.append(tok)
    return tokens


def check_notes() -> list[str]:
    errors: list[str] = []
    for path in sorted(SM_DIR.glob("*.puml")):
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            if NOTE_RE.match(line):
                errors.append(f"{path.relative_to(ROOT)}:{i}: forbidden note construct")
    return errors


def check_capabilities(matrix: set[str]) -> list[str]:
    errors: list[str] = []
    for path in sorted(SM_DIR.glob("*.puml")):
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            for m in CAPABILITY_RE.finditer(line):
                for tok in parse_capability_tokens(m.group(1)):
                    if tok not in matrix:
                        errors.append(
                            f"{path.relative_to(ROOT)}:{i}: "
                            f"capability {tok!r} not in SPEC §3.2 matrix"
                        )
    return errors


def check_required_files() -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_PUML:
        if not (SM_DIR / rel).exists():
            errors.append(f"missing required file: docs/state-machine/{rel}")
    return errors


def check_plantuml() -> list[str]:
    errors: list[str] = []
    jar = ROOT / ".tmp" / "tools" / "plantuml.jar"
    puml_files = sorted(SM_DIR.glob("*.puml"))
    cmd: list[str] | None = None
    if jar.is_file():
        cmd = ["java", "-jar", str(jar), "-checkonly", *[str(p) for p in puml_files]]
    else:
        from shutil import which

        if which("plantuml"):
            cmd = ["plantuml", "-checkonly", *[str(p) for p in puml_files]]
    if cmd is None:
        return ["plantuml not available (install plantuml or place jar at .tmp/tools/plantuml.jar)"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [f"plantuml failed: {exc}"]
    if proc.returncode != 0:
        errors.append(f"plantuml checkonly exit {proc.returncode}")
        if proc.stdout:
            errors.append(proc.stdout.strip()[:2000])
        if proc.stderr:
            errors.append(proc.stderr.strip()[:2000])
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plantuml",
        action="store_true",
        help="Also run PlantUML syntax check (requires plantuml or jar)",
    )
    args = parser.parse_args()

    if not SM_DIR.is_dir():
        print(f"ERROR: {SM_DIR} not found", file=sys.stderr)
        return 2
    if not SPEC.is_file():
        print(f"ERROR: {SPEC} not found", file=sys.stderr)
        return 2

    matrix = load_spec_capabilities()
    all_errors: list[str] = []
    all_errors.extend(check_required_files())
    all_errors.extend(check_notes())
    all_errors.extend(check_capabilities(matrix))
    if args.plantuml:
        all_errors.extend(check_plantuml())

    if all_errors:
        print("validate_state_machines: FAIL")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    print("validate_state_machines: PASS")
    print(f"  matrix capabilities loaded: {len(matrix)}")
    print(f"  puml files: {len(list(SM_DIR.glob('*.puml')))}")
    if args.plantuml:
        print("  plantuml checkonly: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
