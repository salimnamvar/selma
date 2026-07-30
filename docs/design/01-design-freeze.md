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
| State machines linked to contracts | `docs/state-machine/README.md` catalog |
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

### Component ID reconciliation

Contracts sometimes use logical engine names; C4 uses component IDs.
Use this map everywhere:

| C4 component ID | Contract `owner_component` aliases | Role |
| :--- | :--- | :--- |
| `application_service` | `application_service` | Ingress, authz, orchestration |
| `hermetic_compiler` | `hermetic_compiler` | Compile-time CG-IR |
| `rule_inspector` | `rule_inspector` | Inspection pipeline |
| `conflict_resolver` | `conflict_resolver` | Conflict resolution |
| `lifecycle_finder` | `finding_fsm_engine` | Finding FSM + SoD gates |
| `finding_analyzer` | (analytics / guidance) | Read-only guidance + aggregates |
| `architectural_auditor` | `architectural_auditor` | AA-01…AA-07 |
| `directives_adapter` | `directives_adapter` | Directive store port impl |
| `compiled_rules_adapter` | `cgir_adapter` | CG-IR store port impl |
| `findings_audit_adapter` | `event_adapter` | Event store port impl |
| `snapshots_adapter` | `artifact_adapter` | Artifact store port impl |
| `target_adapter` | `target_adapter` | External target systems |

## Frozen principles (non-negotiable)

1. **Compile-time / runtime separation** — executable rule documents → CG-IR at compile time; never re-interpret prose policy for evaluation.
2. **Guidance only after findings** — policy doctrine documents in `directive_store` via `paired_policy_ref` / `DirectiveRepository.readPolicyDoctrine` for humans/AI; never for FSM transitions.
3. **Dual-document single store** — executable rule + policy doctrine co-versioned under one Directive; `directives_adapter` owns both; no separate policy-doctrine adapter; no external Governance Contracts corpus.
4. **One normative FSM** — Finding 10-state machine; other diagrams are extracted pipelines.
5. **Capability + SoD before mutation** — human edges gated; denials audit with no partial mutation.
6. **Immutable compiled/event/snapshot stores** — append-only or content-addressed.
7. **Domain-agnostic core** — language-specific detail only in `detection.adapters[]`.

## Open decisions (implementation may choose; design stays stable)

| ID | Topic | Constraint |
| :--- | :--- | :--- |
| OD-01 | Concrete DB for directive_store | Must support versioned rows + exclusive write lock semantics |
| OD-02 | CAS backend for cgir_store | Content-addressed by snapshot/node hash; immutable publish |
| OD-03 | Event log technology | Append-only, hash-chained events, HLC ordering |
| OD-04 | API framework | Application Service is single ingress; REST contract is behavioral |
| OD-05 | Multi-tenant isolation | Out of freeze scope unless contracts gain tenant invariants |

## Change control

After freeze, changes require:

1. Contract MAJOR/MINOR bump per `meta/versioning.yaml` when behavior changes.
2. Design doc PR updating the affected `docs/design/*` section.
3. C4 and state-machine updates if component ownership or edges change.

Cosmetic typo fixes in design docs do not unfreeze the model.
