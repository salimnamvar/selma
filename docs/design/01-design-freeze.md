# 01 — Design Freeze Status

**Status:** Complete (documentation freeze)
**Schema / contract version:** 1.0.0
**Date:** 2026-07-29

## Purpose

Lock the **target architecture** for Selma so Implementation can proceed
without redesigning bounded contexts, ports, or store ownership.

Design Freeze is a **docs artifact**, not a git tag on code. Implementation
may lag the freeze; gaps are tracked in [08-implementation-gap-map.md](08-implementation-gap-map.md).

## Entry criteria (all met)

| Criterion | Evidence |
| :--- | :--- |
| Normative behavioral source is contract tree | `docs/spec/contracts/` + `docs/spec/README.md` |
| Archives migrated to contract tree | All content migrated to `docs/spec/contracts/`; archives deleted |
| Universal schemas v1.0.0 | `rule_schema.json`, `policy_doctrine.yaml` |
| Dual-document directives (eval vs guidance) | C4 identities + meta/authority concern_split |
| State machines linked to contracts | `docs/state/README.md` catalog |
| Story IDs `US-DOMAIN-NNN` | Embedded in contracts |
| Interface contracts present | CLI / REST / TUI under `contracts/interfaces/` |
| Certification gates defined | `contracts/certification/gates.yaml` AA-01…AA-07 |

## Exit criteria (docs freeze)

| Criterion | Document |
| :--- | :--- |
| Bounded contexts and aggregates named | [02-ddd-model.md](02-ddd-model.md) |
| Ports defined with owners and stores | [03-ports-and-adapters.md](03-ports-and-adapters.md) |
| Package layout and dependency rules | [04-package-architecture.md](04-package-architecture.md) |
| Application use cases catalogued | [05-application-use-cases.md](05-application-use-cases.md) |
| Events and store semantics frozen | [06-domain-events-and-stores.md](06-domain-events-and-stores.md) |
| Component class surfaces sketched | [07-component-class-design.md](07-component-class-design.md) |
| Scaffold gaps explicit | [08-implementation-gap-map.md](08-implementation-gap-map.md) |

## Authority during Implementation

1. **Contracts** beat design docs if they diverge.
2. **Schemas** beat informal field names in design docs.
3. **Design docs** beat ad-hoc package choices in code.
4. **C4 IDs** are the canonical component names for ownership mapping.

### Component ID reconciliation (C4 1.1.0)

Resource-oriented C4 IDs are canonical. Legacy contract aliases map as follows:

| C4 ID | Legacy `owner_component` aliases | Role |
| :--- | :--- | :--- |
| `api` | `api` | Resource API gate, authz, orchestration |
| `compilation` | `compilation` | Compile executable docs → CG-IR |
| `inspection` | `inspection` | Inspection pipeline |
| `findings` | `lifecycle_finder`, `finding_fsm_engine`, `finding_analyzer` | Finding lifecycle, SoD, guidance reads |
| `directives_repository` | `directives_repository` | Directives store port |
| `compiled_rules_repository` | `compiled_rules_repository`, `cgir_adapter` | Compiled Rules store port |
| `finding_events_repository` | `finding_events_repository`, `event_adapter` | Finding Events store port |
| `artifacts_repository` | `artifacts_repository`, `artifact_adapter` | Artifacts store port |
| `target_sources_gateway` | `target_sources_gateway` | Optional Target Sources gateway |

**Not C4 components** (domain service / tool): `ResolveConflict` (legacy `conflict_resolver`, implementation owned by `compilation`/`inspection`/`findings`); AA certification suite (legacy `architectural_auditor`, run as offline/CI tool; results accessed via `api`).

| C4 store ID | Contract path (filename unchanged) |
| :--- | :--- |
| `directives` | `data_stores/directive_store.yaml` |
| `compiled_rules` | `data_stores/cgir_store.yaml` |
| `finding_events` | `data_stores/event_store.yaml` |
| `artifacts` | `data_stores/artifact_store.yaml` |

## Frozen principles (non-negotiable)

1. **Compile-time / runtime separation** — executable rule documents → CG-IR at compile time; never re-interpret prose policy for evaluation.
2. **Guidance only after findings** — policy doctrine in `directives` via `paired_policy_ref` / `DirectiveRepository.readPolicyDoctrine`; never for FSM transitions.
3. **Dual-document single store** — executable + doctrine co-versioned; `directives_repository` owns both; no external Governance Contracts corpus.
4. **One normative FSM** — Finding 10-state machine under `findings` component.
5. **Capability + SoD before mutation** — human edges gated; denials audit with no partial mutation.
6. **Four resource stores by mutability** — `directives` · `compiled_rules` · `finding_events` · `artifacts`.
7. **Domain-agnostic core** — language-specific detail only in `detection.adapters[]`.
8. **Slim C4** — optional Target Sources only as external system; CI/audit/remediation are not context peers.
9. **Two distinct roles** — `regulatory_official` and `compliance_representative` are not merged (SoD + authority split); see `authorization/role_matrix.yaml`.
10. **Module names `{resource}_{layer}`** and **ROD method names** (Verb+Resource) — see packages and ports design docs.

## Open decisions (implementation may choose; design stays stable)

| ID | Topic | Constraint |
| :--- | :--- | :--- |
| OD-01 | Concrete DB for `directives` | Versioned rows + exclusive write lock semantics |
| OD-02 | CAS backend for `compiled_rules` | Content-addressed by snapshot/node hash; immutable publish |
| OD-03 | Event log for `finding_events` | Append-only, hash-chained, HLC ordering |
| OD-04 | API framework | `api` is single ingress; REST is resource-oriented |
| OD-05 | Multi-tenant isolation | Out of freeze scope unless contracts gain tenant invariants |

## Change control

After freeze, changes require:

1. Contract MAJOR/MINOR bump per `meta/versioning.yaml` when behavior changes.
2. Design doc PR updating the affected `docs/design/*` section.
3. C4 and state-machine updates if component ownership or edges change.

Cosmetic typo fixes in design docs do not unfreeze the model.
