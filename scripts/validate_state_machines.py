#!/usr/bin/env python3
"""Validate docs/state-machine catalog against doctrine authoring rules.

Checks (design-time, STM-054 intent):
  - No PlantUML note blocks (project rule; STM-036 via header/README)
  - Required STM-034 header fields present
  - Non-initial transitions carry a named trigger (STM-015)
  - No ``event: none`` labels
  - Catalog files listed in README
  - Optional PlantUML syntax render when --plantuml is set

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
README = SM_DIR / "README.md"

REQUIRED_HEADER_KEYS = (
    "Compliance:",
    "Documentation tier:",
    "Purpose:",
    "Initial:",
    "Terminal:",
    "Event set:",
    "Unhandled-event policy:",
    "Event naming paradigm:",
)

# Overview / shared style are not full lifecycle machines
EXEMPT_FROM_FULL_HEADER = {
    "common/sm_styles.puml",
}

NOTE_RE = re.compile(r"(?im)^\s*(note\b|end note\b)")
EVENT_NONE_RE = re.compile(r"(?i)event:\s*none")
TRANSITION_RE = re.compile(
    r"(?m)^(?P<indent>\s*)"
    r"(?P<lhs>(?:\[\*\])|(?:[A-Za-z_][\w]*))"
    r"\s*-->\s*"
    r"(?P<rhs>(?:\[\*\])|(?:[A-Za-z_][\w]*))"
    r"(?:\s*:\s*(?P<label>.+))?$"
)
INTERNAL_RE = re.compile(
    r"(?m)^(?P<indent>\s*)(?P<state>[A-Za-z_][\w]*)\s*:\s*(?P<label>.+)$"
)
STATE_DECL_RE = re.compile(
    r"(?m)^\s*state\s+(?:\"[^\"]+\"\s+as\s+)?(?P<name>[A-Za-z_][\w]*)"
)


def catalog_puml_files() -> list[Path]:
    files = sorted(SM_DIR.glob("*.puml"))
    styles = SM_DIR / "common" / "sm_styles.puml"
    if styles.exists():
        files.append(styles)
    return files


def rel(path: Path) -> str:
    return str(path.relative_to(SM_DIR)).replace("\\", "/")


def check_notes(path: Path, text: str, errors: list[str]) -> None:
    for i, line in enumerate(text.splitlines(), 1):
        if NOTE_RE.search(line):
            # Allow mention of "note" only inside comments that ban them
            stripped = line.strip()
            if stripped.startswith("'"):
                continue
            errors.append(f"{rel(path)}:{i}: forbidden note block (project rule / STM-036 companion)")


def check_header(path: Path, text: str, errors: list[str]) -> None:
    r = rel(path)
    if r in EXEMPT_FROM_FULL_HEADER:
        return
    for key in REQUIRED_HEADER_KEYS:
        if key not in text:
            errors.append(f"{r}: missing STM-034 header field `{key}`")


def check_event_none(path: Path, text: str, errors: list[str]) -> None:
    for i, line in enumerate(text.splitlines(), 1):
        if EVENT_NONE_RE.search(line) and not line.strip().startswith("'"):
            errors.append(f"{rel(path)}:{i}: forbidden `event: none` (STM-015)")


def _label_has_trigger(label: str | None) -> bool:
    if not label:
        return False
    # First segment before \n should contain a non-empty name (often <b>Name</b>)
    first = label.split("\\n")[0].strip()
    # Strip HTML-ish bold tags
    first = re.sub(r"</?b>", "", first, flags=re.I).strip()
    if not first or first.lower() in {"terminal", "sink", "none"}:
        return False
    # Reject pure capability-only first lines without a past-tense-ish token
    if first.startswith("[") and first.endswith("]"):
        return False
    return True


def check_transitions(path: Path, text: str, errors: list[str]) -> None:
    r = rel(path)
    if r in EXEMPT_FROM_FULL_HEADER:
        return
    if "machine_interaction" in path.name:
        # Overview still needs labels; checked below
        pass

    for m in TRANSITION_RE.finditer(text):
        lhs = m.group("lhs")
        label = m.group("label")
        line_no = text[: m.start()].count("\n") + 1
        # Initial pseudostate transitions may omit a trigger (STM-015 carve-out)
        if lhs == "[*]":
            continue
        if not _label_has_trigger(label):
            errors.append(
                f"{r}:{line_no}: unlabeled non-initial transition "
                f"{lhs} --> {m.group('rhs')} (STM-015)"
            )


def check_readme_catalog(errors: list[str]) -> None:
    if not README.exists():
        errors.append("docs/state-machine/README.md missing")
        return
    body = README.read_text(encoding="utf-8")
    for path in SM_DIR.glob("*.puml"):
        name = path.name
        if name not in body:
            errors.append(f"README catalog missing entry for `{name}`")


def check_capabilities_not_invented(errors: list[str]) -> None:
    """Lightweight scan: capability guards must match known SPEC matrix tokens."""
    known = {
        "directive.create",
        "directive.modify",
        "directive.retire",
        "directive.fork",
        "directive.merge",
        "directive.restore",
        "inspection.submit",
        "inspection.reinspect",
        "finding.view",
        "finding.acknowledge",
        "finding.dismiss",
        "finding.waive",
        "finding.approve_remediation",
        "finding.reject_remediation",
        "evidence.submit",
        "finding.supersede",
        "analytics.view",
        "conflict.resolve",
    }
    cap_re = re.compile(r"capability:\s*([a-z_.]+(?:\s*\|\s*[a-z_.]+)*)")
    for path in SM_DIR.glob("*.puml"):
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            if line.strip().startswith("'"):
                continue
            for m in cap_re.finditer(line):
                for cap in re.split(r"\s*\|\s*", m.group(1)):
                    if cap and cap not in known:
                        errors.append(
                            f"{rel(path)}:{i}: unknown capability `{cap}` "
                            f"(must exist in SPEC §3.2)"
                        )


def run_plantuml(errors: list[str]) -> None:
    jar_candidates = [
        ROOT / ".tmp" / "tools" / "plantuml.jar",
        Path("/usr/share/plantuml/plantuml.jar"),
    ]
    jar = next((p for p in jar_candidates if p.exists()), None)
    plantuml_bin = None
    if jar is None:
        from shutil import which

        plantuml_bin = which("plantuml")
        if not plantuml_bin:
            errors.append(
                "PlantUML not found (.tmp/tools/plantuml.jar or plantuml on PATH); "
                "install or omit --plantuml"
            )
            return

    for path in SM_DIR.glob("*.puml"):
        if jar:
            cmd = ["java", "-jar", str(jar), "-checkonly", "-tpng", str(path)]
        else:
            cmd = [plantuml_bin, "-checkonly", "-tpng", str(path)]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(f"{rel(path)}: plantuml failed: {exc}")
            continue
        if proc.returncode != 0:
            msg = (proc.stderr or proc.stdout or "unknown error").strip()
            errors.append(f"{rel(path)}: plantuml check failed: {msg[:500]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plantuml",
        action="store_true",
        help="Also run PlantUML -checkonly on each diagram",
    )
    args = parser.parse_args(argv)

    if not SM_DIR.is_dir():
        print(f"ERROR: missing {SM_DIR}", file=sys.stderr)
        return 2

    errors: list[str] = []
    for path in catalog_puml_files():
        text = path.read_text(encoding="utf-8")
        check_notes(path, text, errors)
        check_header(path, text, errors)
        check_event_none(path, text, errors)
        check_transitions(path, text, errors)

    check_readme_catalog(errors)
    check_capabilities_not_invented(errors)

    if args.plantuml:
        run_plantuml(errors)

    if errors:
        print(f"validate_state_machines: {len(errors)} issue(s)\n")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("validate_state_machines: OK")
    print(f"  diagrams checked: {len(list(SM_DIR.glob('*.puml')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
