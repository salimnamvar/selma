# Selma Documentation

## What is Selma?

**Selma** is a domain-agnostic **rule regularity platform**. It turns dual-document
directives (executable rule + policy doctrine) into immutable compiled rules
(CG-IR), evaluates those rules against inspection targets, and manages findings
through a capability- and SoD-aware lifecycle with full audit trail and
post-finding guidance.

### Purpose

- Give regulated and regulatory parties a single system of record for **authoring**,
  **compiling**, **inspecting**, and **disposing** of compliance rules and findings
- Keep **evaluation** hermetically separated from **guidance** prose (doctrines never
  drive runtime checks)
- Provide an **API-first** product surface that clients (CLI, web, desktop, mobile)
  can use under explicit capabilities

### Core features

| Feature | C4 owners |
| :--- | :--- |
| Dual-document directive authoring and lifecycle | `directives_application` → `directives_repository` → `directives_store` |
| Hermetic compilation to immutable CG-IR | `compilation_application` → `compiled_rules_repository` → `compiled_rules_store` |
| Six-stage target inspection | `inspections_application` (+ optional `target_sources_gateway`) |
| Finding lifecycle, SoD, evidence, guidance | `findings_application` → `finding_events_repository` → `finding_events_store` |
| Write-once evidence and certification artifacts | `artifacts_repository` → `artifacts_store` |
| Capability / SoD gate at the edge | `api` (+ `clients`) |

**Not product peers:** CI/CD, long-term audit export, remediation ticketing.
Conflict resolution (`ResolveConflict`) and guidance are domain / findings
concerns. Certification (AA-01…AA-07) is offline/CI `certification_tool`.

## Design standards (mandatory)

All design work MUST follow [`standards/`](standards/README.md):

| Standard | Purpose | Check |
| :--- | :--- | :--- |
| [`standards/c4_registry.yaml`](standards/c4_registry.yaml) | Canonical C4 IDs, non-peers, API resources, forbidden aliases | `python scripts/check_design_alignment.py` |
| [`standards/contract.schema.json`](standards/contract.schema.json) | Spec contract front-matter | same |
| [`standards/diagram_header.schema.md`](standards/diagram_header.schema.md) | PlantUML headers (`Contract: 1.1.0`, C4, Source) | same |
| [`api/redocly.yaml`](api/redocly.yaml) | OpenAPI + wire schema lint | `cd docs/api && npx @redocly/cli lint openapi.yaml` |

**design_contract_version:** `1.1.0` (shared by C4, API `info.version`, contracts, diagram headers).

## Documentation map

| Area | Path | Role |
| :--- | :--- | :--- |
| **Design standards** | [`standards/`](standards/README.md) | Checkable ID/ownership schema |
| **Specification contracts** | [`spec/`](spec/README.md) | Normative behavior (`contracts/`) |
| **Schemas** | [`schema/`](schema/) | Rule + policy structure (v1.0.0) |
| **C4 architecture** | [`c4-model/`](c4-model/README.md) | **Structural SSoT** (context / container / component) |
| **State machines** | [`state/`](state/README.md) | FSMs and pipelines |
| **Use case diagrams** | [`usecase/`](usecase/README.md) | Actor / epic index |
| **Sequence diagrams** | [`sequence/`](sequence/README.md) | Resource workflow sequences |
| **Class diagrams** | [`class/`](class/README.md) | Domain / application / infrastructure |
| **Package diagrams** | [`package/`](package/README.md) | Clean Architecture packages |
| **ERDs** | [`erd/`](erd/README.md) | Four `*_store` resources |
| **Activity diagrams** | [`activity/`](activity/README.md) | Procedural swim-lane flows |
| **API** | [`api/`](api/README.md) | Modular OpenAPI (Redocly) |
| **Deployment** | [`deployment/`](deployment/README.md) | Topology aligned with C4 containers |
| **Project phases** | [`mindmap/`](mindmap/README.md) | Phase status |

## Authority (investigation order)

1. **`standards/`** — IDs, owners, version line (how we write design)
2. **`spec/contracts/`** — what the system MUST do
3. **`schema/`** — data shapes
4. **`c4-model/`** — structural architecture (peers only)
5. **`api/`** — HTTP surface (Redocly-valid)
6. Behavior views (`state`, `sequence`, `activity`, `usecase`) — must not contradict 2–5
7. Implementation views (`class`, `package`, `erd`, `deployment`) — map to C4 peers

### Canonical C4 IDs

See full registry: [`standards/c4_registry.yaml`](standards/c4_registry.yaml).

| Kind | Pattern | Examples |
| :--- | :--- | :--- |
| Use-case cluster | `*_application` | `directives_application`, `compilation_application`, `inspections_application`, `findings_application` |
| Driven store adapter | `*_repository` | `directives_repository`, `finding_events_repository` |
| Driven external adapter | `*_gateway` | `target_sources_gateway` |
| Store | `*_store` | `directives_store`, `compiled_rules_store`, `finding_events_store`, `artifacts_store` |
| Driving gate / clients | role tokens | `api`, `clients` |
| System / actors | role tokens | `selma`, `regulatory_official`, `compliance_representative` |

```
clients → api → *_application → *_repository | *_gateway → *_store | externals
```

## Implementation

Do not start coding from archives. Start from **contracts + C4 + standards**, then
state machines. Run `python scripts/check_design_alignment.py` and Redocly before
merging design changes.
