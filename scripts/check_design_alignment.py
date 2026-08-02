#!/usr/bin/env python3
"""Validate Selma design docs against docs/standards (C4 registry + contract schema).

Design freeze version SSoT
--------------------------
  docs/standards/VERSION          — sole place that holds the SemVer freeze line
  docs/standards/CHANGELOG.md     — human history (historical SemVer allowed)

  Everywhere else MUST redirect to docs/standards/VERSION — never embed
  design_contract SemVer (X.Y.Z) in diagrams, footers, README banners,
  contract front-matter, registry, or OpenAPI info.version.

  Redirect forms:
    PlantUML:   ' Contract:  docs/standards/VERSION
    Markdown:   design_contract_version: `docs/standards/VERSION`
    OpenAPI:    info.version: "docs/standards/VERSION"

  python scripts/check_design_alignment.py           # verify
  python scripts/check_design_alignment.py --fix    # rewrite redirects (no SemVer stamps)

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
VERSION_REF = "docs/standards/VERSION"
REGISTRY_PATH = STANDARDS / "c4_registry.yaml"
CONTRACT_SCHEMA_PATH = STANDARDS / "contract.schema.json"
CONTRACTS_DIR = DOCS / "spec" / "contracts"
API_DIR = DOCS / "api"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
SEMVER_TOKEN = re.compile(r"\b\d+\.\d+\.\d+\b")

# Design freeze must never appear as embedded SemVer outside VERSION / CHANGELOG
RE_EMBEDDED_DCV = re.compile(
    r"design_contract_version\s*[:=]?\s*[`\"']?\d+\.\d+\.\d+",
    re.I,
)
RE_PUML_CONTRACT_SEMVER = re.compile(
    r"Contract:\s*(?:design_contract_version\s+)?\d+\.\d+\.\d+",
)
RE_PUML_CONTRACT_REF = re.compile(
    r"Contract:\s*docs/standards/VERSION\b",
)
RE_FOOTER_CONTRACT_SEMVER = re.compile(
    r"footer[^\n]*Contract\s+\d+\.\d+\.\d+",
    re.I,
)
RE_MD_DCV_SEMVER = re.compile(
    r"design_contract_version[:\*\s`]+[`\"']?\d+\.\d+\.\d+",
    re.I,
)
RE_OPENAPI_INFO_SEMVER = re.compile(
    r"(?m)^(\s*version:\s*)([\"']?)(\d+\.\d+\.\d+)\2",
)
RE_OPENAPI_INFO_REF = re.compile(
    r'(?m)^(\s*version:\s*)(["\']?)docs/standards/VERSION\2',
)


def load_design_version() -> str:
    if not VERSION_PATH.is_file():
        print(f"ERROR missing SSoT {VERSION_PATH.relative_to(ROOT)}", file=sys.stderr)
        sys.exit(2)
    raw = VERSION_PATH.read_text(encoding="utf-8").strip()
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


def fix_registry(messages: list[str]) -> None:
    text = REGISTRY_PATH.read_text(encoding="utf-8")
    new = re.sub(
        r"^design_contract_version:\s*[\"']?\d+\.\d+\.\d+[\"']?[^\n]*\n",
        "",
        text,
        flags=re.M,
    )
    _write_if_changed(
        REGISTRY_PATH, new, REGISTRY_PATH.relative_to(ROOT), messages, "removed design_contract_version stamp"
    )


def fix_contract_file(path: Path, messages: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)
    new = re.sub(
        r"^design_contract_version:\s*[\"']?\d+\.\d+\.\d+[\"']?\s*\n",
        "",
        text,
        flags=re.M,
    )
    if new != text:
        path.write_text(new, encoding="utf-8")
        messages.append(f"{rel}: removed design_contract_version stamp")


def fix_puml_file(path: Path, messages: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)
    new = re.sub(
        r"(Contract:\s*)(?:design_contract_version\s+)?\d+\.\d+\.\d+(\s*(?:\([^)]*\))?)",
        rf"\1{VERSION_REF}",
        text,
    )
    new = re.sub(
        r"(footer[^\n]*?)Contract\s+\d+\.\d+\.\d+",
        rf"\1{VERSION_REF}",
        new,
    )
    new = re.sub(
        r"(Contract\s+)\d+\.\d+\.\d+(\s*·)",
        rf"\1{VERSION_REF}\2",
        new,
    )
    new = new.replace(f"{VERSION_REF}'", VERSION_REF)
    if new != text:
        path.write_text(new, encoding="utf-8")
        messages.append(f"{rel}: redirected Contract to {VERSION_REF}")


def fix_markdown(path: Path, messages: list[str]) -> None:
    if path.name == "CHANGELOG.md" and path.parent == STANDARDS:
        return
    if path.name == "VERSION":
        return
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)
    new = re.sub(
        r"(design_contract_version)([`:\*\s]+)(\d+\.\d+\.\d+)",
        rf"\g<1>\g<2>{VERSION_REF}",
        text,
        flags=re.I,
    )
    new = re.sub(
        r"(Contract:\s*)(\d+\.\d+\.\d+)",
        rf"\g<1>{VERSION_REF}",
        new,
    )
    new = re.sub(
        r"(Contract\s+\*\*)(\d+\.\d+\.\d+)(\*\*)",
        rf"\g<1>{VERSION_REF}\3",
        new,
    )
    if new != text:
        path.write_text(new, encoding="utf-8")
        messages.append(f"{rel}: redirected design_contract_version to {VERSION_REF}")


def fix_openapi(path: Path, messages: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT)
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    in_info = False
    done = False
    changed = False
    for line in lines:
        if done:
            out.append(line)
            continue
        if re.match(r"^info:\s*$", line):
            in_info = True
            out.append(line)
            continue
        if in_info and not done:
            m = re.match(r"^(\s*)version:\s*.*$", line)
            if m:
                out.append(f'{m.group(1)}version: "{VERSION_REF}"\n')
                if line.strip() != f'version: "{VERSION_REF}"':
                    changed = True
                done = True
                continue
            if line.strip() and not line[0].isspace():
                in_info = False
        out.append(line)
    new = "".join(out)
    new = re.sub(
        r"C4 Contract \*\*\d+\.\d+\.\d+\*\*",
        f"C4 design freeze ({VERSION_REF})",
        new,
    )
    if new != text or changed:
        path.write_text(new, encoding="utf-8")
        messages.append(f"{rel}: redirected info.version to {VERSION_REF}")


def apply_fixes() -> list[str]:
    messages: list[str] = []
    fix_registry(messages)
    for path in sorted(CONTRACTS_DIR.rglob("*.yaml")):
        fix_contract_file(path, messages)
    for path in DOCS.rglob("*.puml"):
        fix_puml_file(path, messages)
    for path in DOCS.rglob("*.md"):
        fix_markdown(path, messages)
    openapi = API_DIR / "openapi.yaml"
    if openapi.is_file():
        fix_openapi(openapi, messages)
    return messages


def _line_of(text: str, pos: int) -> str:
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    return text[start : end if end != -1 else None]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument(
        "--fix",
        action="store_true",
        help=f"Rewrite design version refs to redirect to {VERSION_REF} (no SemVer stamps)",
    )
    parser.add_argument(
        "--fix-contracts",
        action="store_true",
        help="Deprecated alias for --fix",
    )
    args = parser.parse_args()
    do_fix = args.fix or args.fix_contracts

    design_version = load_design_version()

    if do_fix:
        for msg in apply_fixes():
            print(f"FIX   {msg}")

    reg = load_registry()
    errors: list[str] = []
    warnings: list[str] = []

    if "design_contract_version" in reg:
        errors.append(
            f"{REGISTRY_PATH.relative_to(ROOT)}: must not embed design_contract_version "
            f"(redirect to {VERSION_REF} only; remove the field)"
        )

    allowed_owners = set(reg.get("allowed_owner_components") or [])
    forbidden = set(reg.get("forbidden_ids") or [])
    peer_ids = collect_peer_ids(reg)

    # --- Contract front-matter ------------------------------------------------
    schema = json.loads(CONTRACT_SCHEMA_PATH.read_text(encoding="utf-8"))
    owner_enum = set(schema["properties"]["owner_component"]["oneOf"][1]["enum"])

    dcv_schema = schema.get("properties", {}).get("design_contract_version", {})
    if dcv_schema and "const" in dcv_schema:
        errors.append(
            f"{CONTRACT_SCHEMA_PATH.relative_to(ROOT)}: design_contract_version "
            f"must not use const (VERSION is sole SSoT)"
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

        if "design_contract_version" in data:
            errors.append(
                f"{rel}: must not embed design_contract_version "
                f"(use {VERSION_REF} only; remove the field)"
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

    # --- PlantUML: Contract redirects; forbid SemVer design stamps ------------
    for path in DOCS.rglob("*.puml"):
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT)
        if RE_PUML_CONTRACT_SEMVER.search(text):
            errors.append(
                f"{rel}: embeds SemVer in Contract header — use '{VERSION_REF}' only"
            )
        if RE_FOOTER_CONTRACT_SEMVER.search(text):
            errors.append(
                f"{rel}: embeds SemVer in footer Contract — use '{VERSION_REF}' only"
            )
        # non-common diagrams should declare Contract redirect
        if path.parent.name != "common" and not path.name.endswith("_styles.puml"):
            if "Contract:" in text and not RE_PUML_CONTRACT_REF.search(text):
                # allow files that mention Contract only in prose without header
                if re.search(r"(?m)^'\s*Contract:", text):
                    errors.append(
                        f"{rel}: Contract header must be '{VERSION_REF}' "
                        f"(got non-redirect form)"
                    )
            elif "Contract:" not in text and path.suffix == ".puml":
                # orchestrator diagrams
                if path.name.startswith(
                    (
                        "cd_",
                        "erd_",
                        "uc_",
                        "seq_",
                        "act_",
                        "dep_",
                        "pkg_",
                        "c4_",
                        "state_machine_",
                    )
                ):
                    warnings.append(f"{rel}: missing Contract: header field")

    # --- Markdown: no design SemVer stamps (except CHANGELOG / VERSION) -------
    for path in DOCS.rglob("*.md"):
        if path.name == "CHANGELOG.md" and path.parent == STANDARDS:
            continue
        if path.name == "VERSION":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT)
        for m in RE_MD_DCV_SEMVER.finditer(text):
            line = _line_of(text, m.start())
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
                    "e.g.",
                    "example",
                )
            ):
                continue
            errors.append(
                f"{rel}: embeds design_contract SemVer stamp — redirect to {VERSION_REF}"
            )

        if path.name == "diagram_header.schema.md":
            if RE_PUML_CONTRACT_SEMVER.search(text):
                errors.append(
                    f"{rel}: example Contract must redirect to {VERSION_REF}, not SemVer"
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

    # --- API openapi version must redirect to VERSION -------------------------
    openapi = API_DIR / "openapi.yaml"
    if openapi.exists():
        ot = openapi.read_text(encoding="utf-8")
        info_ver = None
        in_info = False
        for line in ot.splitlines():
            if re.match(r"^info:\s*$", line):
                in_info = True
                continue
            if in_info:
                m = re.match(r"^\s+version:\s*[\"']?([^\"'\s]+)[\"']?", line)
                if m:
                    info_ver = m.group(1)
                    break
                if line.strip() and not line[0].isspace():
                    break
        if info_ver is None:
            errors.append("docs/api/openapi.yaml: missing info.version")
        elif info_ver != VERSION_REF:
            errors.append(
                f"docs/api/openapi.yaml info.version {info_ver!r} must be "
                f'"{VERSION_REF}" (redirect; SemVer lives only in VERSION)'
            )
        if RE_OPENAPI_INFO_SEMVER.search(ot):
            errors.append(
                f"docs/api/openapi.yaml: embeds SemVer in info.version — use {VERSION_REF}"
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
        f"(SSoT: {VERSION_REF}; embeds forbidden)"
    )
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
