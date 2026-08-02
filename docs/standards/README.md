# Selma — Design Standards

Investigation stays correct only if every artifact uses the **same IDs, ownership,
and version line**. This directory is the **checkable schema** for that discipline.

| Artifact | Role |
| :--- | :--- |
| [`VERSION`](VERSION) | **Sole SSoT** for design freeze SemVer (one line; only place the number lives) |
| [`CHANGELOG.md`](CHANGELOG.md) | Design-line history (Keep a Changelog; historical SemVer allowed) |
| [`common/ca_palette.puml`](common/ca_palette.puml) | **Sole SSoT** for Clean Architecture MACRO layer + MICRO concern colors |
| [`common/README.md`](common/README.md) | Palette mapping for C4 / package / class / deployment / state |
| [`c4_registry.yaml`](c4_registry.yaml) | Canonical C4 IDs, non-peers, API resource surface, forbidden aliases (no version stamp) |
| [`view_concerns.md`](view_concerns.md) | Exclusive ownership matrix for C4 / package / deployment / state (no principle duplication) |
| [`contract.schema.json`](contract.schema.json) | Front-matter schema for `docs/spec/contracts/**/*.yaml` |
| [`diagram_header.schema.md`](diagram_header.schema.md) | Required PlantUML header fields |
| [`section_readme.template.md`](section_readme.template.md) | Required section README shape |
| [`../../scripts/check_design_alignment.py`](../../scripts/check_design_alignment.py) | Automated alignment gate |

## Authority order (investigation)

1. **Behavior** — `docs/spec/contracts/` (what MUST happen)
2. **Data shape** — `docs/schema/` + `docs/api/schemas/` (structure)
3. **Structure** — `docs/c4-model/` + `c4_registry.yaml` (who exists)
4. **HTTP surface** — `docs/api/openapi.yaml` (Redocly lint)
5. **Behavior views** — state / sequence / activity / use case (must not contradict 1–4)
6. **Implementation views** — class / package / ERD / deployment

## Tooling standards

| Concern | Standard | How to check |
| :--- | :--- | :--- |
| OpenAPI + wire schemas | **Redocly** (`docs/api/redocly.yaml`) | `cd docs/api && npx @redocly/cli lint openapi.yaml` |
| Spec contract front-matter | **JSON Schema** (`contract.schema.json`) | `python scripts/check_design_alignment.py` |
| C4 IDs in contracts/diagrams/prose | **Registry** (`c4_registry.yaml`) | same checker (forbidden IDs + owner enum) |
| Design freeze version | **`VERSION`** only | checker rejects embedded SemVer; diagrams redirect to path |
| Diagram headers | **Header schema** | `Contract: docs/standards/VERSION` (path redirect) |

## Naming principles (strict)

From C4 Clean Architecture postfixes:

| Kind | ID pattern | Example |
| :--- | :--- | :--- |
| Store | `{resource}_store` | `directives_store` |
| Use-case cluster | `{resource\|process}_application` | `compilation_application` |
| Store adapter | `{resource}_repository` | `finding_events_repository` |
| External adapter | `{external}_gateway` | `target_sources_gateway` |
| Gate | `api` | `api` |
| Package module | `{resource}_{layer}` | `directives_domain` |

Dependency rule:

```text
clients → api → *_application → *_repository | *_gateway → *_store | externals
```

## Non-peers (never C4 boxes)

- Domain service `ResolveConflict` (`conflicts_domain`; used by compile + inspect packages)
- Application port `DenialAuditPort` (consumer: `api`; implementer: `finding_events_repository`)
- Offline/CI `certification_tool`
- Findings guidance / aggregate **read models** (not engines); doctrine by `paired_policy_ref` revision
- Optional CI/CD, audit export, remediation ticketing

### Package aliases (not C4 peer IDs)

| Package | C4 peer |
| :--- | :--- |
| `compiled_rules_application` | `compilation_application` |
| `compiled_rules_infrastructure` | `compiled_rules_repository` |

See `package_aliases` in [`c4_registry.yaml`](c4_registry.yaml).

## Design contract version (single source of truth)

Pattern: **one version file holds the number**; every diagram and document **redirects**
to that path. CI **rejects embedded SemVer** for the design freeze line.

| Role | Location | Editable? |
| :--- | :--- | :--- |
| **Authority (SemVer)** | [`VERSION`](VERSION) | **Yes — only here** |
| History | [`CHANGELOG.md`](CHANGELOG.md) | Yes (with every bump; historical SemVer OK) |
| Diagram redirect | PlantUML `Contract: docs/standards/VERSION` | Path only — never `Contract: 1.2.0` |
| Section redirect | README `design_contract_version: docs/standards/VERSION` | Path only |
| API redirect | `openapi.yaml` `info.version: "docs/standards/VERSION"` | Path only |
| Registry / contracts | **no** `design_contract_version` field | Omit |

### Workflow

1. Change any design content under `docs/` as needed.
2. If the change should move the freeze line, edit **`VERSION` once** (SemVer; see CHANGELOG bump table).
3. Add a CHANGELOG entry under `[Unreleased]` or the new version section.
4. Ensure redirects (not stamps):

```bash
python scripts/check_design_alignment.py --fix   # rewrite any leftover SemVer stamps → path redirects
python scripts/check_design_alignment.py --strict
```

5. Optional publish tag: `design/vX.Y.Z` (tag reads from `VERSION`).

### What is *not* the design freeze line

| Field | Meaning |
| :--- | :--- |
| Contract `schema_version` | Shape of that contract **file body** (may differ by file) |
| Rule/policy dataset `version` | Product/runtime data revision |
| Per-diagram embedded SemVer | **Forbidden** — redirect with `Contract: docs/standards/VERSION` |

Bump policy and history: [`CHANGELOG.md`](CHANGELOG.md).
