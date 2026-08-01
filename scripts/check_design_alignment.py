#!/usr/bin/env python3
"""Validate Selma design docs against docs/standards (C4 registry + contract schema).

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
REGISTRY_PATH = STANDARDS / "c4_registry.yaml"
CONTRACT_SCHEMA_PATH = STANDARDS / "contract.schema.json"
CONTRACTS_DIR = DOCS / "spec" / "contracts"
API_DIR = DOCS / "api"

DESIGN_VERSION = "1.1.0"


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    parser.add_argument(
        "--fix-contracts",
        action="store_true",
        help="Write design_contract_version into contract YAML files",
    )
    args = parser.parse_args()

    reg = load_registry()
    assert reg.get("design_contract_version") == DESIGN_VERSION
    allowed_owners = set(reg.get("allowed_owner_components") or [])
    forbidden = set(reg.get("forbidden_ids") or [])
    peer_ids = collect_peer_ids(reg)

    errors: list[str] = []
    warnings: list[str] = []

    # --- Contract front-matter ------------------------------------------------
    schema = json.loads(CONTRACT_SCHEMA_PATH.read_text(encoding="utf-8"))
    owner_enum = set(schema["properties"]["owner_component"]["oneOf"][1]["enum"])

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
            if args.fix_contracts:
                text = path.read_text(encoding="utf-8")
                # insert after schema_version line
                if "design_contract_version:" not in text:
                    text2, n = re.subn(
                        r"(schema_version:\s*[\"']?\d+\.\d+\.\d+[\"']?\s*\n)",
                        rf'\1design_contract_version: "{DESIGN_VERSION}"\n',
                        text,
                        count=1,
                    )
                    if n:
                        path.write_text(text2, encoding="utf-8")
                        warnings.append(f"{rel}: injected design_contract_version")
                    else:
                        errors.append(f"{rel}: could not inject design_contract_version")
            else:
                warnings.append(
                    f"{rel}: missing design_contract_version (run with --fix-contracts)"
                )
        elif str(dcv) != DESIGN_VERSION:
            errors.append(
                f"{rel}: design_contract_version {dcv!r} != {DESIGN_VERSION}"
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
    # Whole-word-ish matches for forbidden tokens
    for root in scan_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in {".yaml", ".yml", ".md", ".puml", ".json"}:
                continue
            # skip standards themselves and schema that document forbidden names
            if "standards" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            rel = path.relative_to(ROOT)
            for bad in forbidden:
                # allow mentions in MUST NOT / no separate / forbidden prose
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
        if "common" in path.parts and path.name.endswith("_styles.puml"):
            # styles: allow design line note
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT)
        # Skip pure style files without machines
        if path.name.endswith("_styles.puml"):
            continue
        m = re.search(r"Contract:\s*([0-9]+\.[0-9]+\.[0-9]+)", text)
        if m:
            if m.group(1) != DESIGN_VERSION:
                errors.append(
                    f"{rel}: Contract {m.group(1)} != design_contract_version {DESIGN_VERSION}"
                )
        else:
            # require for non-c4 identity includes? require for main diagrams
            if path.parent.name != "common":
                warnings.append(f"{rel}: missing Contract: header field")

        if "event_store.yaml" in text:
            errors.append(f"{rel}: stale source event_store.yaml → finding_events_store.yaml")

    # --- Package aliases must not appear as C4 peer IDs -----------------------
    # e.g. compiled_rules_application is a package prefix; C4 peer is compilation_application
    forbidden_c4 = set(reg.get("forbidden_c4_peer_ids") or [])
    c4_dir = DOCS / "c4-model"
    if c4_dir.exists() and forbidden_c4:
        for path in c4_dir.rglob("*.puml"):
            text = path.read_text(encoding="utf-8", errors="replace")
            rel = path.relative_to(ROOT)
            for bad in forbidden_c4:
                # Component(id, ...) or Container(id, ...) or bare peer-style Rel endpoints
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

    # --- API openapi version --------------------------------------------------
    openapi = API_DIR / "openapi.yaml"
    if openapi.exists():
        ot = openapi.read_text(encoding="utf-8")
        vm = re.search(r"version:\s*[\"']?([0-9]+\.[0-9]+\.[0-9]+)", ot)
        if vm and vm.group(1) != DESIGN_VERSION:
            warnings.append(
                f"docs/api/openapi.yaml version {vm.group(1)} != {DESIGN_VERSION}"
            )
        for path_key in (
            "/directives/{lineage_id}",
            "/inspections",
            "/findings/{finding_id}",
            "/artifacts",
        ):
            if path_key not in ot and path_key.replace("{", "").replace("}", "") not in ot:
                # paths are $ref'd; keys appear as-is in openapi.yaml
                if path_key not in ot:
                    errors.append(f"docs/api/openapi.yaml: missing path key {path_key}")
        for bad_path in ("/certifications", "/conflicts"):
            # only count top-level path keys
            if re.search(rf"^\s*{re.escape(bad_path)}\s*:", ot, re.M):
                errors.append(f"docs/api/openapi.yaml: freestanding peer path {bad_path}")

    # --- Report ---------------------------------------------------------------
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")

    print(
        f"\nSummary: {len(errors)} error(s), {len(warnings)} warning(s); "
        f"peers={len(peer_ids)} design_contract_version={DESIGN_VERSION}"
    )
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
