#!/usr/bin/env python3
"""Validate docs/state-machine catalog against doctrine authoring rules.

Checks (design-time, STM-054 intent):
  - No PlantUML note blocks (project rule; STM-036 via header/README)
  - Required STM-034 header fields present
  - Non-initial transitions carry a named trigger (STM-015)
  - No ``event: none`` labels
  - Catalog files listed in README
  - Capability guards exist in SPEC §3.2 matrix
  - STM-052 complexity caps (hard for Strict; report for Exploratory)
  - Composite states declare an initial substate (STM-026)
  - Optional PlantUML syntax render when --plantuml is set

Usage:
  python scripts/validate_state_machines.py
  python scripts/validate_state_machines.py --plantuml
  python scripts/validate_state_machines.py --metrics
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
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

# STM-052 Strict hard caps (doctrine Flexible Standards → hard under Strict)
MAX_STATES_STRICT = 20
MAX_TRANSITIONS_STRICT = 50
MAX_ORTHOGONAL_REGIONS = 2
MAX_NESTING_LEVELS = 3

NOTE_RE = re.compile(r"(?im)^\s*(note\b|end note\b)")
EVENT_NONE_RE = re.compile(r"(?i)event:\s*none")
TRANSITION_RE = re.compile(
    r"(?m)^(?P<indent>\s*)"
    r"(?P<lhs>(?:\[\*\])|(?:[A-Za-z_][\w]*))"
    r"\s*-->\s*"
    r"(?P<rhs>(?:\[\*\])|(?:[A-Za-z_][\w]*))"
    r"(?:\s*:\s*(?P<label>.+))?$"
)
STATE_DECL_RE = re.compile(
    r"(?m)^\s*state\s+(?:\"[^\"]+\"\s+as\s+)?(?P<name>[A-Za-z_][\w]*)"
)
INTERNAL_TRIGGER_RE = re.compile(
    r"(?m)^\s*(?P<state>[A-Za-z_][\w]*)\s*:\s*(?:<b>)?(?P<ev>[A-Za-z_][\w]*)"
)
COMPLIANCE_RE = re.compile(r"(?m)^\s*'\s*Compliance:\s*(?P<level>\w+)")
COMPOSITE_OPEN_RE = re.compile(
    r"(?m)^\s*state\s+(?:\"[^\"]+\"\s+as\s+)?(?P<name>[A-Za-z_][\w]*).*\{"
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
            stripped = line.strip()
            if stripped.startswith("'"):
                continue
            errors.append(
                f"{rel(path)}:{i}: forbidden note block "
                f"(project rule / STM-036 companion)"
            )


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
    first = label.split("\\n")[0].strip()
    first = re.sub(r"</?b>", "", first, flags=re.I).strip()
    if not first or first.lower() in {"terminal", "sink", "none"}:
        return False
    if first.startswith("[") and first.endswith("]"):
        return False
    return True


def check_transitions(path: Path, text: str, errors: list[str]) -> None:
    r = rel(path)
    if r in EXEMPT_FROM_FULL_HEADER:
        return

    for m in TRANSITION_RE.finditer(text):
        lhs = m.group("lhs")
        label = m.group("label")
        line_no = text[: m.start()].count("\n") + 1
        if lhs == "[*]":
            continue
        if not _label_has_trigger(label):
            errors.append(
                f"{r}:{line_no}: unlabeled non-initial transition "
                f"{lhs} --> {m.group('rhs')} (STM-015)"
            )


def check_composite_initials(path: Path, text: str, errors: list[str]) -> None:
    """STM-026: every composite with a body must define an initial substate."""
    r = rel(path)
    if r in EXEMPT_FROM_FULL_HEADER or "machine_interaction" in path.name:
        return

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("'"):
            i += 1
            continue
        m = COMPOSITE_OPEN_RE.search(line)
        if not m or not line.rstrip().endswith("{"):
            # multi-line open is rare; skip
            if m and "{" not in line:
                i += 1
                continue
            if not m:
                i += 1
                continue
        name = m.group("name")
        # Collect body until matching close brace at same indent-ish depth
        depth = 1
        body_lines: list[str] = []
        i += 1
        while i < len(lines) and depth > 0:
            bl = lines[i]
            # crude brace counting ignoring comments
            code = bl.split("'")[0]
            depth += code.count("{") - code.count("}")
            if depth > 0:
                body_lines.append(bl)
            i += 1
        body = "\n".join(body_lines)
        # Orthogonal regions: each region needs its own initial
        regions = re.split(r"(?m)^\s*--\s*$", body)
        for ri, region in enumerate(regions):
            if not STATE_DECL_RE.search(region) and "[*]" not in region:
                continue
            if not re.search(r"\[\*\]\s*-->", region):
                # Composites entered only via deep targets still need an initial
                # (doctrine STM-026). Orthogonal leaf regions always need one.
                label = f"region {ri}" if len(regions) > 1 else "body"
                errors.append(
                    f"{r}: composite `{name}` {label} missing "
                    f"initial substate `[*] --> …` (STM-026)"
                )
        continue  # i already advanced


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


@dataclass(frozen=True)
class DiagramMetrics:
    path: str
    compliance: str
    states: int
    transitions: int
    internal: int
    composites: int
    orthogonal_separators: int
    nesting_max: int


def measure(path: Path, text: str) -> DiagramMetrics:
    states = set(STATE_DECL_RE.findall(text))
    transitions = list(TRANSITION_RE.finditer(text))
    internal = list(INTERNAL_TRIGGER_RE.finditer(text))
    # Filter internal lines that are state body **entry** descriptions:
    # real internal transitions use : <b>Event or similar with past-tense event.
    # Keep all matches that look like EventName after colon with <b> in line.
    internal_count = 0
    for m in internal:
        line = text[m.start() : text.find("\n", m.start())]
        if "<b>" in line or re.search(r":\s*[A-Z][A-Za-z]+", line):
            # exclude pure description lines like `State : **entry**`
            if "**entry**" in line or "**allowed**" in line or "**forbidden**" in line:
                continue
            if "entry " in line.lower() and "event" not in line.lower():
                # still allow if bold event present
                if "<b>" not in line:
                    continue
            internal_count += 1

    composites = len(COMPOSITE_OPEN_RE.findall(text))
    orth = len(re.findall(r"(?m)^\s*--\s*$", text))
    # nesting: track brace depth after state opens
    depth = 0
    max_depth = 0
    for line in text.splitlines():
        if line.strip().startswith("'"):
            continue
        code = line.split("'")[0]
        if COMPOSITE_OPEN_RE.search(line) and "{" in code:
            depth += 1
            max_depth = max(max_depth, depth)
            # count only one open per line already in depth
            depth += code.count("{") - 1
            depth -= code.count("}")
            depth = max(depth, 0)
            continue
        depth += code.count("{") - code.count("}")
        depth = max(depth, 0)
        max_depth = max(max_depth, depth)

    cm = COMPLIANCE_RE.search(text)
    compliance = cm.group("level") if cm else "Unknown"
    return DiagramMetrics(
        path=rel(path),
        compliance=compliance,
        states=len(states),
        transitions=len(transitions) + internal_count,
        internal=internal_count,
        composites=composites,
        orthogonal_separators=orth,
        nesting_max=max_depth,
    )


def check_complexity(path: Path, text: str, errors: list[str], warnings: list[str]) -> DiagramMetrics:
    m = measure(path, text)
    if m.path in EXEMPT_FROM_FULL_HEADER or "machine_interaction" in path.name:
        return m

    over_states = m.states > MAX_STATES_STRICT
    over_trans = m.transitions > MAX_TRANSITIONS_STRICT
    over_orth = m.orthogonal_separators > MAX_ORTHOGONAL_REGIONS
    over_nest = m.nesting_max > MAX_NESTING_LEVELS

    msg_bits = []
    if over_states:
        msg_bits.append(f"states={m.states}>{MAX_STATES_STRICT}")
    if over_trans:
        msg_bits.append(f"transitions={m.transitions}>{MAX_TRANSITIONS_STRICT}")
    if over_orth:
        msg_bits.append(f"orthogonal={m.orthogonal_separators}>{MAX_ORTHOGONAL_REGIONS}")
    if over_nest:
        msg_bits.append(f"nesting={m.nesting_max}>{MAX_NESTING_LEVELS}")

    if not msg_bits:
        return m

    detail = ", ".join(msg_bits)
    if m.compliance == "Strict":
        errors.append(f"{m.path}: STM-052 Strict cap exceeded ({detail})")
    else:
        warnings.append(f"{m.path}: STM-052 soft guidance exceeded ({detail})")
    return m


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
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Print per-diagram complexity metrics (STM-052)",
    )
    args = parser.parse_args(argv)

    if not SM_DIR.is_dir():
        print(f"ERROR: missing {SM_DIR}", file=sys.stderr)
        return 2

    errors: list[str] = []
    warnings: list[str] = []
    metrics: list[DiagramMetrics] = []

    for path in catalog_puml_files():
        text = path.read_text(encoding="utf-8")
        check_notes(path, text, errors)
        check_header(path, text, errors)
        check_event_none(path, text, errors)
        check_transitions(path, text, errors)
        check_composite_initials(path, text, errors)
        if path.suffix == ".puml" and "sm_styles" not in path.name:
            metrics.append(check_complexity(path, text, errors, warnings))

    check_readme_catalog(errors)
    check_capabilities_not_invented(errors)

    if args.plantuml:
        run_plantuml(errors)

    if args.metrics or warnings or not errors:
        # always show brief metrics summary on success; full table with --metrics
        if args.metrics:
            print(
                f"{'diagram':42} {'lvl':11} {'st':>3} {'tr':>3} "
                f"{'int':>3} {'cmp':>3} {'orth':>4} {'nest':>4}"
            )
            for m in metrics:
                print(
                    f"{m.path:42} {m.compliance:11} {m.states:3} {m.transitions:3} "
                    f"{m.internal:3} {m.composites:3} {m.orthogonal_separators:4} "
                    f"{m.nesting_max:4}"
                )
            print(
                f"\nSTM-052 Strict caps: states≤{MAX_STATES_STRICT}, "
                f"transitions≤{MAX_TRANSITIONS_STRICT}, "
                f"orthogonal≤{MAX_ORTHOGONAL_REGIONS}, nesting≤{MAX_NESTING_LEVELS}"
            )

    if warnings:
        print(f"validate_state_machines: {len(warnings)} warning(s)\n")
        for w in warnings:
            print(f"  ! {w}")
        print()

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
