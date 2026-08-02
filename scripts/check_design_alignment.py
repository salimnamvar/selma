#!/usr/bin/env python3
"""Validate Selma design docs against docs/standards (C4 registry + contract schema).

Design freeze version SSoT
--------------------------
  docs/standards/VERSION          — sole writable design_contract_version
  docs/standards/CHANGELOG.md     — human history (Keep a Changelog)
  All other occurrences are stamps and must equal VERSION.

  python scripts/check_design_alignment.py           # verify
  python scripts/check_design_alignment.py --fix    # rewrite stamps from VERSION

Exit 0 if clean; non-zero if errors. Warnings print but do not fail by default
unless --strict.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
STANDARDS = DOCS / "standards"
VERSION_PATH = STANDARDS / "VERSION"
REGISTRY_PATH = STANDARDS / "c4_registry.yaml"
CONTRACT_SCHEMA_PATH = STANDARDS / "contract.schema.json"
CONTRACTS_DIR = DOCS / "spec" / "contracts"
API_DIR = DOCS / "api"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Stamp patterns (design line only — not product schema_version fields)
RE_CONTRACT_DCV = re.compile(
    r'^(design_contract_version:\s*)(["\']?)(\d+\.\d+\.\d+)\2',
    re.M,
)
RE_PUML_CONTRACT = re.compile(
    r"(Contract:\s*)(?:design_contract_version\s+)?(\d+\.\d+\.\d+)",
)
RE_MD_DCV_BACKTICK = re.compile(
    r"(design_contract_version[:\*]*\s*[`*]*)(\d+\.\d+\.\d+)([`*]*)",
    re.I,
)
RE_OPENAPI_INFO_VERSION = re.compile(
    r"(?m)^(\s*version:\s*)([\"']?)(\d+\.\d+\.\d+)\2",
)


def load_design_version() -> str:
    if not VERSION_PATH.is_file():
        print(f"ERROR missing SSoT {VERSION_PATH.relative_to(ROOT)}", file=sys.stderr)
        sys.exit(2)
    raw = VERSION_PATH.read_text(encoding="utf-8").strip()
    # allow optional trailing comment / blank lines: first non-empty token
    line = raw.splitlines()[0].strip() if raw else ""
    if "#" in line:
        line = line.split("#", 1)[0].strip()
    if not SEMVER_RE.match(line):
        print(
            f"ERROR {VERSION_PATH.relative_to(ROOT)}: expected MAJOR.MINOR.PATCH, got {line!r}",
            file=sys.stderr,
        )
        sys.exit(2)
    return line


def load_registry() -> dict:
    with REGISTRY_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def collect_peer_ids(reg: dict) -> set[str]:
    ids: set[str] = set()
    peers = reg.get("peers", {})
    for group in peers.values():
        for item in group or []:
            ids.add(item["id"])
    return ids


def _write_if_changed(path: Path, new_text: str, rel: Path, messages: list[str], label: str) -> None:
    old = path.read_text(encoding="utf-8")
    if old != new_text:
        path.write_text(new_text, encoding="utf-8")
        messages.append(f"{rel}: {label}")


def fix_registry_stamp(design_version: str, messages: list[str]) -> None:
    text = REGISTRY_PATH.read_text(encoding="utf-8")
    new, n = RE_CONTRACT_DCV.subn(
        rf'\1"{design_version}"',
        text,
        count=1,
    )
    if n:
        _write_if_changed(
            REGISTRY_PATH, new, REGISTRY_PATH.relative_to(ROOT), messages, "stamped design_contract_version"
        )
    elif f'design_contract_version: "{design_version}"' not in text and (
        f"design_contract_version: '{design_version}'" not in text
    ):
        # try unquoted
        new2, n2 = re.subn(
            r"^(design_contract_version:\s*)(\d+\.\d+\.\d+)",
            rf'\1"{design_version}"',
            text,
            count=1,
            flags=re.M,
        )
        if n2:
            _write_if_changed(
                REGISTRY_PATH,
                new2,
                REGISTRY_PATH.relative_to(ROOT),
                messages,
                "stamped design_contract_version",
            )


def fix_contract_file(path: Path, design_version: str, messages: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)
    if "design_contract_version:" in text:
        new, n = RE_CONTRACT_DCV.subn(rf'\1"{design_version}"', text, count=1)
        if n and new != text:
            path.write_text(new, encoding="utf-8")
            messages.append(f"{rel}: stamped design_contract_version")
        return
    new, n = re.subn(
        r"(schema_version:\s*[\"']?\d+\.\d+\.\d+[\"']?\s*\n)",
        rf'\1design_contract_version: "{design_version}"\n',
        text,
        count=1,
    )
    if n:
        path.write_text(new, encoding="utf-8")
        messages.append(f"{rel}: injected design_contract_version")
    else:
        messages.append(f"{rel}: could not inject design_contract_version")


def fix_puml_file(path: Path, design_version: str, messages: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)

    def repl_header(m: re.Match[str]) -> str:
        return f"{m.group(1)}{design_version}"

    def repl_style(m: re.Match[str]) -> str:
        return f"{m.group(1)}{design_version}{m.group(3)}"

    new = RE_PUML_CONTRACT.sub(repl_header, text)
    # styles: ' Contract: design_contract_version 1.1.0 (docs/standards/...)
    new = re.sub(
        r"(Contract:\s*design_contract_version\s+)\d+\.\d+\.\d+(\s*)",
        rf"\g<1>{design_version}\2",
        new,
    )
    if new != text:
        path.write_text(new, encoding="utf-8")
        messages.append(f"{rel}: stamped Contract header")


def fix_markdown_stamps(path: Path, design_version: str, messages: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)

    def repl(m: re.Match[str]) -> str:
        return f"{m.group(1)}{design_version}{m.group(3)}"

    new = RE_MD_DCV_BACKTICK.sub(repl, text)
    # design_contract_version[`:*\s]+VERSION  — covers:
    #   design_contract_version: `1.1.0`
    #   design_contract_version 1.1.0
    #   `design_contract_version` 1.1.0  (backtick closes name before version)
    new = re.sub(
        r"(design_contract_version)([`:\*\s]+)(\d+\.\d+\.\d+)",
        rf"\g<1>\g<2>{design_version}",
        new,
        flags=re.I,
    )
    # Contract: 1.1.0 in markdown schema docs
    new = re.sub(
        r"(Contract:\s*)(\d+\.\d+\.\d+)",
        rf"\g<1>{design_version}",
        new,
    )
    # Exactly `1.1.0` until the design line — in diagram_header.schema.md
    new = re.sub(
        r"(Exactly `)(\d+\.\d+\.\d+)(` until the design line)",
        rf"\g<1>{design_version}\3",
        new,
    )
    # Contract **1.1.0** prose
    new = re.sub(
        r"(Contract\s+\*\*)(\d+\.\d+\.\d+)(\*\*)",
        rf"\g<1>{design_version}\3",
        new,
    )
    if new != text:
        path.write_text(new, encoding="utf-8")
        messages.append(f"{rel}: stamped design_contract_version mentions")


def fix_openapi(path: Path, design_version: str, messages: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)
    # Only the first top-level info.version (after "info:")
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    in_info = False
    info_indent: int | None = None
    done = False
    changed = False
    for line in lines:
        if done:
            out.append(line)
            continue
        if re.match(r"^info:\s*$", line):
            in_info = True
            info_indent = 0
            out.append(line)
            continue
        if in_info and not done:
            m = re.match(r"^(\s*)version:\s*([\"']?)(\d+\.\d+\.\d+)\2\s*$", line)
            if m:
                out.append(f'{m.group(1)}version: "{design_version}"\n')
                if m.group(3) != design_version:
                    changed = True
                done = True
                continue
            # left info block
            if line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                in_info = False
        out.append(line)
    new = "".join(out)
    if changed or (done and new != text):
        # also stamp "Contract **1.1.0**" in description if present
        new2 = re.sub(
            r"(Contract\s+\*\*)(\d+\.\d+\.\d+)(\*\*)",
            rf"\g<1>{design_version}\3",
            new,
        )
        if new2 != text:
            path.write_text(new2, encoding="utf-8")
            messages.append(f"{rel}: stamped info.version / design line prose")


def apply_fixes(design_version: str) -> list[str]:
    messages: list[str] = []
    fix_registry_stamp(design_version, messages)

    for path in sorted(CONTRACTS_DIR.rglob("*.yaml")):
        fix_contract_file(path, design_version, messages)

    for path in DOCS.rglob("*.puml"):
        fix_puml_file(path, design_version, messages)

    # Markdown stamps under docs/ (standards templates + section READMEs + root docs README)
    for path in DOCS.rglob("*.md"):
        # Keep a Changelog retains historical versions — never rewrite
        if path.name == "CHANGELOG.md" and path.parent == STANDARDS:
            continue
        fix_markdown_stamps(path, design_version, messages)

    openapi = API_DIR / "openapi.yaml"
    if openapi.is_file():
        fix_openapi(openapi, design_version, messages)

    return messages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Rewrite all design_contract_version stamps from docs/standards/VERSION",
    )
    parser.add_argument(
        "--fix-contracts",
        action="store_true",
        help="Deprecated alias for --fix (contracts + all stamps)",
    )
    args = parser.parse_args()
    do_fix = args.fix or args.fix_contracts

    design_version = load_design_version()

    if do_fix:
        for msg in apply_fixes(design_version):
            print(f"FIX   {msg}")

    reg = load_registry()
    reg_ver = str(reg.get("design_contract_version") or "")
    errors: list[str] = []
    warnings: list[str] = []

    if reg_ver != design_version:
        errors.append(
            f"{REGISTRY_PATH.relative_to(ROOT)}: design_contract_version "
            f"{reg_ver!r} != VERSION {design_version} "
            f"(edit VERSION only, then run with --fix)"
        )

    allowed_owners = set(reg.get("allowed_owner_components") or [])
    forbidden = set(reg.get("forbidden_ids") or [])
    peer_ids = collect_peer_ids(reg)

    # --- Contract front-matter ------------------------------------------------
    schema = json.loads(CONTRACT_SCHEMA_PATH.read_text(encoding="utf-8"))
    owner_enum = set(schema["properties"]["owner_component"]["oneOf"][1]["enum"])

    # schema must not pin a const to a stale version (pattern-only)
    dcv_schema = schema.get("properties", {}).get("design_contract_version", {})
    if "const" in dcv_schema:
        errors.append(
            f"{CONTRACT_SCHEMA_PATH.relative_to(ROOT)}: design_contract_version "
            f"must use pattern (not const) so VERSION remains the sole SSoT"
        )

    for path in sorted(CONTRACTS_DIR.rglob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            errors.append(f"{path.relative_to(ROOT)}: not a mapping")
            continue
        rel = path.relative_to(ROOT)
        for req in ("contract_id", "schema_version", "description"):
            if req not in data:
                errors.append(f"{rel}: missing required field {req}")

        cid = data.get("contract_id")
        if cid and not re.match(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$", str(cid)):
            errors.append(f"{rel}: invalid contract_id {cid!r}")

        sv = data.get("schema_version")
        if sv and not re.match(r"^\d+\.\d+\.\d+$", str(sv)):
            errors.append(f"{rel}: invalid schema_version {sv!r}")

        owner = data.get("owner_component", data.get("owner", "__missing__"))
        if owner == "__missing__":
            errors.append(f"{rel}: missing owner_component (or owner for meta)")
        elif owner is None:
            if not str(path).endswith(("authority.yaml", "versioning.yaml")):
                warnings.append(f"{rel}: owner_component is null (meta only expected)")
        elif owner not in allowed_owners and owner not in owner_enum:
            errors.append(f"{rel}: owner_component {owner!r} not in C4 allowed set")

        dcv = data.get("design_contract_version")
        if dcv is None:
            errors.append(
                f"{rel}: missing design_contract_version (run with --fix)"
            )
        elif str(dcv) != design_version:
            errors.append(
                f"{rel}: design_contract_version {dcv!r} != VERSION {design_version}"
            )

    # --- Forbidden IDs in docs (scan) -----------------------------------------
    scan_roots = [
        DOCS / "spec",
        DOCS / "c4-model",
        DOCS / "state",
        DOCS / "sequence",
        DOCS / "activity",
        DOCS / "usecase",
        DOCS / "class",
        DOCS / "package",
        DOCS / "erd",
        DOCS / "deployment",
        DOCS / "api",
        DOCS / "schema",
    ]
    for root in scan_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in {".yaml", ".yml", ".md", ".puml", ".json"}:
                continue
            if "standards" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            rel = path.relative_to(ROOT)
            for bad in forbidden:
                if bad not in text:
                    continue
                for i, line in enumerate(text.splitlines(), 1):
                    if bad not in line:
                        continue
                    lower = line.lower()
                    if any(
                        k in lower
                        for k in (
                            "must not",
                            "must not be",
                            "no separate",
                            "forbidden",
                            "not a",
                            "removed",
                            "never",
                            "there must not",
                            "not named",
                            "not present",
                            "do not",
                            "does not",
                            "cannot",
                            "prohibits",
                            "prohibited",
                            "(forbidden)",
                        )
                    ):
                        continue
                    errors.append(f"{rel}:{i}: forbidden id {bad!r}: {line.strip()[:100]}")

    # --- PlantUML Contract headers --------------------------------------------
    for path in DOCS.rglob("*.puml"):
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT)
        if path.name.endswith("_styles.puml"):
            # styles may note the design line
            m = re.search(
                r"Contract:\s*(?:design_contract_version\s+)?([0-9]+\.[0-9]+\.[0-9]+)",
                text,
            )
            if m and m.group(1) != design_version:
                errors.append(
                    f"{rel}: Contract {m.group(1)} != VERSION {design_version}"
                )
            continue
        m = re.search(r"Contract:\s*([0-9]+\.[0-9]+\.[0-9]+)", text)
        if m:
            if m.group(1) != design_version:
                errors.append(
                    f"{rel}: Contract {m.group(1)} != VERSION {design_version}"
                )
        else:
            if path.parent.name != "common":
                warnings.append(f"{rel}: missing Contract: header field")

        if "event_store.yaml" in text:
            errors.append(f"{rel}: stale source event_store.yaml → finding_events_store.yaml")

    # --- Section README / standards markdown stamps ---------------------------
    md_stamp_re = re.compile(
        r"design_contract_version[:\*\s`]+(\d+\.\d+\.\d+)",
        re.I,
    )
    for path in DOCS.rglob("*.md"):
        # CHANGELOG may mention historical versions — skip version equality there
        if path.name == "CHANGELOG.md" and path.parent == STANDARDS:
            continue
        if path.name == "VERSION":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT)
        for m in md_stamp_re.finditer(text):
            if m.group(1) != design_version:
                # allow explicit historical notes
                line_start = text.rfind("\n", 0, m.start()) + 1
                line_end = text.find("\n", m.end())
                line = text[line_start : line_end if line_end != -1 else None]
                lower = line.lower()
                if any(
                    k in lower
                    for k in (
                        "superseded",
                        "historical",
                        "was ",
                        "formerly",
                        "previous",
                        "deprecated",
                        "old ",
                    )
                ):
                    continue
                errors.append(
                    f"{rel}: design_contract_version stamp {m.group(1)} "
                    f"!= VERSION {design_version}"
                )

        # diagram header schema: Contract: X.Y.Z examples
        if path.name == "diagram_header.schema.md":
            for m in re.finditer(r"Contract:\s*(\d+\.\d+\.\d+)", text):
                if m.group(1) != design_version:
                    errors.append(
                        f"{rel}: Contract example {m.group(1)} != VERSION {design_version}"
                    )

    # --- Package aliases must not appear as C4 peer IDs -----------------------
    forbidden_c4 = set(reg.get("forbidden_c4_peer_ids") or [])
    c4_dir = DOCS / "c4-model"
    if c4_dir.exists() and forbidden_c4:
        for path in c4_dir.rglob("*.puml"):
            text = path.read_text(encoding="utf-8", errors="replace")
            rel = path.relative_to(ROOT)
            for bad in forbidden_c4:
                patterns = [
                    rf"\bComponent\(\s*{re.escape(bad)}\b",
                    rf"\bContainer\(\s*{re.escape(bad)}\b",
                    rf"\bContainerDb\(\s*{re.escape(bad)}\b",
                    rf"\bSystem\(\s*{re.escape(bad)}\b",
                    rf"\bRel\(\s*{re.escape(bad)}\b",
                    rf",\s*{re.escape(bad)}\s*,",
                ]
                for pat in patterns:
                    if re.search(pat, text):
                        errors.append(
                            f"{rel}: forbidden C4 peer id {bad!r} "
                            f"(use package alias mapping in c4_registry package_aliases)"
                        )
                        break

    # --- docs/schema SSoT mirrored at repo root schema/ -----------------------
    docs_schema = DOCS / "schema"
    root_schema = ROOT / "schema"
    for name in ("rule_schema.json", "policy_doctrine.yaml"):
        dpath = docs_schema / name
        rpath = root_schema / name
        if not dpath.is_file():
            errors.append(f"docs/schema/{name}: missing (design SSoT)")
            continue
        if not rpath.is_file():
            errors.append(
                f"schema/{name}: missing mirror of docs/schema/{name} "
                f"(copy from docs/schema after edits)"
            )
            continue
        if dpath.read_bytes() != rpath.read_bytes():
            errors.append(
                f"schema/{name}: out of sync with docs/schema/{name} "
                f"(docs/schema is SSoT — copy to schema/ in the same change)"
            )

    # --- API openapi version (design line stamp) ------------------------------
    openapi = API_DIR / "openapi.yaml"
    if openapi.exists():
        ot = openapi.read_text(encoding="utf-8")
        # info.version only
        info_ver = None
        in_info = False
        for line in ot.splitlines():
            if re.match(r"^info:\s*$", line):
                in_info = True
                continue
            if in_info:
                m = re.match(r"^\s+version:\s*[\"']?([0-9]+\.[0-9]+\.[0-9]+)", line)
                if m:
                    info_ver = m.group(1)
                    break
                if line.strip() and not line[0].isspace():
                    break
        if info_ver is None:
            errors.append("docs/api/openapi.yaml: missing info.version")
        elif info_ver != design_version:
            errors.append(
                f"docs/api/openapi.yaml info.version {info_ver} != VERSION {design_version}"
            )
        for path_key in (
            "/directives/{lineage_id}",
            "/inspections",
            "/findings/{finding_id}",
            "/artifacts",
        ):
            if path_key not in ot:
                errors.append(f"docs/api/openapi.yaml: missing path key {path_key}")
        for bad_path in ("/certifications", "/conflicts"):
            if re.search(rf"^\s*{re.escape(bad_path)}\s*:", ot, re.M):
                errors.append(f"docs/api/openapi.yaml: freestanding peer path {bad_path}")

    # --- Report ---------------------------------------------------------------
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")

    print(
        f"\nSummary: {len(errors)} error(s), {len(warnings)} warning(s); "
        f"peers={len(peer_ids)} design_contract_version={design_version} "
        f"(SSoT: docs/standards/VERSION)"
    )
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
