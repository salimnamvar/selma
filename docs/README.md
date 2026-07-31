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

**Not product peers** (optional clients/exports only): CI/CD, long-term audit
export, remediation ticketing. Conflict resolution (`ResolveConflict`) and
guidance are domain / findings concerns, not freestanding engines. Certification
(AA-01…AA-07) is an offline/CI tool suite.

## Documentation map

| Area | Path | Role |
| :--- | :--- | :--- |
| **Specification contracts** | [`spec/`](spec/README.md) | Normative behavior (`contracts/`) |
| **Schemas** | [`schema/`](schema/) | Rule + policy structure (v1.0.0) |
| **C4 architecture** | [`c4-model/`](c4-model/README.md) | **Source of truth for structure** (context / container / component) |
| **State machines** | [`state/`](state/README.md) | FSMs and pipelines |
| **Use case diagrams** | [`usecase/`](usecase/README.md) | Actor / epic index (stories live in contracts) |
| **Sequence diagrams** | [`sequence/`](sequence/README.md) | Resource workflow sequences |
| **Class diagrams** | [`class/`](class/README.md) | Domain / application / infrastructure classes |
| **Package diagrams** | [`package/`](package/README.md) | Clean Architecture package layout |
| **ERDs** | [`erd/`](erd/README.md) | Four resource stores (`*_store`) |
| **Activity diagrams** | [`activity/`](activity/README.md) | Procedural swim-lane flows |
| **API** | [`api/`](api/README.md) | OpenAPI + resource schemas |
| **Deployment** | [`deployment/`](deployment/README.md) | Topology aligned with C4 containers |
| **Project phases** | [`mindmap/`](mindmap/README.md) | Phase status |

## Authority

1. `spec/contracts/` — what the system MUST do
2. `schema/` — data shapes
3. **`c4-model/`** — structural architecture (entity IDs, containers, components, stores)
4. `class/`, `package/` — implementation structure (packages, classes, use cases)
5. `state/` + other diagrams — behavior and detail views; must not contradict C4 or contracts

### Canonical C4 IDs (Clean Architecture layer postfixes)

Diagrams and design prose use identical IDs from
[`c4-model/README.md`](c4-model/README.md):

| Kind | Pattern | Examples |
| :--- | :--- | :--- |
| Use-case cluster | `*_application` | `directives_application`, `compilation_application`, `inspections_application`, `findings_application` |
| Driven store adapter | `*_repository` | `directives_repository`, `finding_events_repository` |
| Driven external adapter | `*_gateway` | `target_sources_gateway` |
| Store | `*_store` | `directives_store`, `compiled_rules_store`, `finding_events_store`, `artifacts_store` |
| Driving gate / clients | role tokens | `api`, `clients` |
| System / actors | role tokens | `selma`, `regulatory_official`, `compliance_representative` |

Dependency rule:

```
clients → api → *_application → *_repository | *_gateway → *_store | externals
```

## Implementation

Do not start coding from archives. Start from State Machines + contracts + C4.
