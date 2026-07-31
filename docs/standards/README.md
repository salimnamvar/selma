# Selma — Design Standards

Investigation stays correct only if every artifact uses the **same IDs, ownership,
and version line**. This directory is the **checkable schema** for that discipline.

| Artifact | Role |
| :--- | :--- |
| [`c4_registry.yaml`](c4_registry.yaml) | Canonical C4 IDs, non-peers, API resource surface, forbidden aliases |
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
| Diagram headers | **Header schema** | checker warns on `Contract:` ≠ 1.1.0 and stale sources |

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

## Design contract version

**`design_contract_version: 1.1.0`** is shared by:

- C4 PlantUML headers
- `docs/api/openapi.yaml` `info.version` (API surface revision may track this)
- Spec contracts field `design_contract_version`
- Diagram headers `Contract: 1.1.0`

Bump only with coordinated C4 + registry + contract schema enum updates.
