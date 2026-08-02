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
concerns. Certification (AA-01…AA-09) is offline/CI `certification_tool`.
Capability denials at `api` use application-owned **`DenialAuditPort`**
(implemented by `finding_events_repository`).

## Design standards (mandatory)

All design work MUST follow [`standards/`](standards/README.md):

| Standard | Purpose | Check |
| :--- | :--- | :--- |
| [`standards/VERSION`](standards/VERSION) | **Sole SSoT** for design freeze SemVer | `python scripts/check_design_alignment.py` |
| [`standards/CHANGELOG.md`](standards/CHANGELOG.md) | Design-line history | review with bumps |
| [`standards/c4_registry.yaml`](standards/c4_registry.yaml) | Canonical C4 IDs, non-peers, API resources, forbidden aliases | same checker |
| [`standards/view_concerns.md`](standards/view_concerns.md) | Exclusive ownership: C4 / package / deployment / state | design review |
| [`standards/contract.schema.json`](standards/contract.schema.json) | Spec contract front-matter | same checker |
| [`standards/diagram_header.schema.md`](standards/diagram_header.schema.md) | PlantUML headers (`Contract:` = `VERSION`, C4, Source) | same |
| [`api/redocly.yaml`](api/redocly.yaml) | OpenAPI + wire schema lint | `cd docs/api && npx @redocly/cli lint openapi.yaml` |

**design_contract_version:** `1.1.0` — stamp of [`standards/VERSION`](standards/VERSION) (C4, API `info.version`, contracts, diagram headers). Bump `VERSION` once, then `python scripts/check_design_alignment.py --fix`.

**Tenant model (v1):** single-tenant per deployment instance. Multi-tenancy is
out of scope; see [`c4-model/README.md`](c4-model/README.md) "Tenant model".

### Naming dual (C4 vs packages)

| Concept | C4 peer ID | Package prefix |
| :--- | :--- | :--- |
| Hermetic compile → CG-IR | `compilation_application` | `compiled_rules_application` / `compiled_rules_*` |

One concept, two names by design. Never invent a C4 peer `compiled_rules_application`.

## Documentation map

| Area | Path | Role |
| :--- | :--- | :--- |
| **Design standards** | [`standards/`](standards/README.md) | Checkable ID/ownership schema |
| **Specification contracts** | [`spec/`](spec/README.md) | Normative behavior (`contracts/`) |
| **Schemas** | [`schema/`](schema/) | Design SSoT for rule + policy structure (v1.0.0). Root `schema/` is a synced mirror for runtime paths. |
| **C4 architecture** | [`c4-model/`](c4-model/README.md) | **Structural SSoT** — *what* peers exist and how they depend |
| **State machines** | [`state/`](state/README.md) | FSMs and pipelines |
| **Use case diagrams** | [`usecase/`](usecase/README.md) | Actor / epic index |
| **Sequence diagrams** | [`sequence/`](sequence/README.md) | Resource workflow sequences |
| **Class diagrams** | [`class/`](class/README.md) | Types inside packages (domain / app / infra) |
| **Package diagrams** | [`package/`](package/README.md) | *How* code modules layer (CA rings, ports) |
| **ERDs** | [`erd/`](erd/README.md) | Four `*_store` resources |
| **Activity diagrams** | [`activity/`](activity/README.md) | Procedural swim-lane flows |
| **API** | [`api/`](api/README.md) | Modular OpenAPI (Redocly) |
| **Deployment** | [`deployment/`](deployment/README.md) | *Where* it runs (zones, TLS, failure domains, RPO) |

### Structural & state views (no concern overlap)

Full matrix: [`standards/view_concerns.md`](standards/view_concerns.md).

| Question | Authority | Owns 100% | Must not restate |
| :--- | :--- | :--- | :--- |
| What peers / containers / components exist? | [`c4-model/`](c4-model/README.md) | Peer IDs, dependency rule, boundaries | Package trees, zones/TLS/RPO, FSM tables, capability matrix |
| How are source modules and ports organized? | [`package/`](package/README.md) | `{resource}_{layer}`, ISP ports, module edges | Peer inventing, failure domains, normative FSM/lock text |
| Where do processes and data live in prod? | [`deployment/`](deployment/README.md) | Zones, TLS, HA, RPO/RTO, observability | Component use-case graph, package trees, domain algorithms |
| How does state evolve (FSMs / pipelines)? | [`state/`](state/README.md) | Extracted states/transitions from contracts | Peer inventing, packages, zones; product design principles (spec owns) |

Join key: **C4 peer IDs** from [`standards/c4_registry.yaml`](standards/c4_registry.yaml).
Behavior principles (authn, SoD, hermetic compile, dual-document, store mutability): **`spec/contracts/`** + **`schema/`** only — structural views link, never duplicate.

## Authority (investigation order)

1. **`standards/`** — IDs, owners, version line (how we write design)
2. **`spec/contracts/`** — what the system MUST do (behavior, locks, SoD, authz)
3. **`docs/schema/`** — data shapes (SSoT; root `schema/` mirror for product/runtime)
4. **`c4-model/`** — structural architecture (peers only)
5. **`api/`** — HTTP surface (Redocly-valid)
6. Behavior views (`state`, `sequence`, `activity`, `usecase`) — must not contradict 2–5
7. Implementation views (`class`, `package`, `erd`, `deployment`) — map to C4 peers

**Do not treat C4 alone as complete.** Authorization, hermetic locks, finding FSM,
and store contracts live under `spec/contracts/` and are mandatory before coding.
Structural-only reviews (C4 + package + deployment without standards/spec) will
under-report security and concurrency decisions that are already normative.

### Where common concerns are documented

| Concern | Primary authority |
| :--- | :--- |
| C4 peer IDs / non-peers | [`standards/c4_registry.yaml`](standards/c4_registry.yaml), [`c4-model/`](c4-model/README.md) |
| Authentication (JWT/OIDC) | [`spec/contracts/authorization/authentication.yaml`](spec/contracts/authorization/authentication.yaml) |
| Capability catalog / roles | [`spec/contracts/authorization/`](spec/contracts/authorization/) |
| JWT / HTTP security schemes | [`api/components/security.yaml`](api/components/security.yaml) |
| Denial audit at gate | C4 `DenialAuditPort` + [`spec/contracts/finding_lifecycle/sod_contract.yaml`](spec/contracts/finding_lifecycle/sod_contract.yaml) |
| Compile hermeticity + read locks | [`spec/contracts/compilation/`](spec/contracts/compilation/) |
| Guidance revision pinning | `paired_policy_ref` in [`spec/contracts/data_stores/directives_store.yaml`](spec/contracts/data_stores/directives_store.yaml) |
| RPO/RTO / TLS / composed recovery | [`deployment/`](deployment/README.md) |
| Package ↔ C4 map | [`package/`](package/README.md), [`class/`](class/README.md) |

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

Narrow exception: `api` → `DenialAuditPort` (implemented by `finding_events_repository`) for capability-denial audit only.

## Implementation

Do not start coding from archives. Start from **contracts + C4 + standards**, then
state machines. Run `python scripts/check_design_alignment.py` and Redocly before
merging design changes.
