# Design contract changelog

All notable changes to the **Selma design contract** (everything under `docs/`
that participates in investigation: standards, C4, spec contracts, schemas,
diagrams, OpenAPI) are recorded here.

This file follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Version numbers follow [Semantic Versioning](https://semver.org/).

## Single source of truth

| Role | Location |
| :--- | :--- |
| **Authoritative version** | [`VERSION`](VERSION) (one SemVer line; edit only here) |
| **Human history** | this file |
| **Machine ID registry** | [`c4_registry.yaml`](c4_registry.yaml) (`design_contract_version` is a **stamp** of `VERSION`) |
| **Alignment gate** | `python scripts/check_design_alignment.py` |

Stamps (contract front-matter, PlantUML `Contract:` headers, section README
banners, OpenAPI `info.version`) MUST equal `VERSION`. They are not independent
versions. After editing `VERSION`, run:

```bash
python scripts/check_design_alignment.py --fix
```

Do **not** invent per-diagram or per-document design versions.

## When to bump

| Bump | When |
| :--- | :--- |
| **MAJOR** | Breaking change to design meaning: rename/remove C4 peers, incompatible lifecycle/API/store contracts, authority order change that invalidates prior investigation |
| **MINOR** | Backward-compatible addition: new contract, optional field, new diagram that does not contradict existing meaning |
| **PATCH** | Clarifications, typo/layout fixes, non-normative prose, stamp/tooling hygiene with no semantic change |

**Any** material edit under the design tree that should be visible as a new
freeze line requires **one** bump of `VERSION` for the whole design — never a
partial version on a single section.

Tag freezes in git as `design/vX.Y.Z` when publishing a line (optional).

## [Unreleased]

## [1.2.0] — 2026-08-02

### Added

- **Use case view** exclusive ownership in [`view_concerns.md`](view_concerns.md):
  actor goals, ROD use-case groups, identity dual vs package/class/C4.
- Use-case shared `common/` maintenance layer: `uc_styles.puml` (CA palette),
  `uc_identities.puml`, `uc_section_*` per application / gate / offline group.
- `ValidateDirectiveDocuments` on package `compiled_rules_application` leaves
  (aligned with class + use case).

### Changed

- **UC-001…UC-008** rewritten to PascalCase ROD names identical to package
  application components and class `<<Use Case>>` types; pipeline stages and
  FSM state names removed from use-case ovals (state/activity own those).
- Use-case diagrams drop PlantUML `note` blocks and stop restating C4 paths,
  store mutability, capability catalogs, and segregation-of-duties tables.
- Use-case colors use [`common/ca_palette.puml`](common/ca_palette.puml) only
  (no invented hex in `uc_styles` / sections).
- Class interface use-case reference lists the full application catalog.
- Certification use cases include all nine gates (AA-01…AA-09).

### Added (prior)

- Design-wide version SSoT: `docs/standards/VERSION`, this changelog, and
  `check_design_alignment.py --fix` stamp propagation (big-project pattern:
  one version file, echoes checked in CI).

## [1.1.0]

### Added

- Shared design freeze line `1.1.0` across C4, spec contracts, diagram headers,
  section READMEs, and OpenAPI `info.version`.
- C4 registry, contract front-matter schema, and alignment checker.

### Notes

- Prior independent “document versions” are retired; only `schema_version` on
  individual contracts remains for **document body** shape, distinct from the
  design freeze line.
