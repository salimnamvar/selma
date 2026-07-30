# 02 — DDD Model

## Ubiquitous language (core terms)

| Term | Meaning |
| :--- | :--- |
| **Directive** | Human-authored governance unit; dual documents: executable rule + policy doctrine |
| **Lineage ID** | Immutable root identity (`^[A-Z]{2,5}-\d{3}[A-Z]?$`); Machine ID in policy tables |
| **Execution ID** | Active node identity; equals lineage on create; changes on fork/merge/split |
| **CG-IR** | Compiled Control Graph Intermediate Representation; immutable snapshot |
| **Detection** | Strategy + specs + adapters that evaluate a target (`detection` / `detection_spec`) |
| **Deontic** | Obligation modality (`must`, `must_not`, …) on subject + predicate |
| **Finding** | Evaluation outcome under lifecycle FSM; not a free-form lint string alone |
| **Disposition** | Semantic resolution alongside FSM state (`valid`, `invalid`, `waived`, …) |
| **Paired policy ref** | Link from executable rule to guidance doctrine (runtime guidance only) |
| **Capability** | Atomic authorization unit (e.g. `finding.waive`) |
| **SoD** | Segregation of duties: creator cannot waive; evidence submitter cannot approve |

## Bounded contexts

```
┌─────────────────────┐     ┌──────────────────────┐
│ Governance Authoring│     │ Compilation          │
│ (directives, lineage│────▶│ (hermetic, CG-IR,    │
│  policy pairing)    │     │  portability gates)  │
└─────────────────────┘     └──────────┬───────────┘
                                       │ publishes
                                       ▼
┌─────────────────────┐     ┌──────────────────────┐
│ Inspection          │◀────│ Compiled Rules       │
│ (targets, pipeline, │     │ (immutable snapshots)│
│  findings birth)    │     └──────────────────────┘
└──────────┬──────────┘
           │ creates findings
           ▼
┌─────────────────────┐     ┌──────────────────────┐
│ Finding Lifecycle   │────▶│ Authorization        │
│ (FSM, SoD, events,  │     │ (capabilities, roles)│
│  guidance reads)    │     │  C4: api             │
└──────────┬──────────┘     └──────────────────────┘
           │ guidance_only → directives_repository
           ▼
┌─────────────────────┐     ┌──────────────────────┐
│ Guidance read model │     │ Certification        │
│ (findings + doctrine│     │ (AA-01…AA-07)        │
│  — not a C4 peer)   │     │ offline/CI tool only │
└─────────────────────┘     └──────────────────────┘
```

| Bounded context | Primary aggregates | C4 owners | Contracts |
| :--- | :--- | :--- | :--- |
| **Governance Authoring** | DirectiveGraph, Directive | `api`, `directives_repository` · modules `directives_domain` / `directives_application` | `directive/*` |
| **Compilation** | CompilationJob, CgIrSnapshot | `compilation` · `compiled_rules_*` modules | `compilation/*` |
| **Inspection** | InspectionSnapshot, Target | `inspection` · `inspections_*` modules | `inspection/*` |
| **Finding Lifecycle** | Finding | `findings` · `findings_*` modules | `finding_lifecycle/*` |
| **Conflict** | ConflictArtifact | domain service `ResolveConflict` (used by `compilation` / `inspection` / `findings`; **not** a C4 component) | `conflict/*` |
| **Authorization** | ActorCapabilityGrant (or session claims) | `api` | `authorization/*` |
| **Guidance** | GuidanceView (read model) | `findings` + `directives_repository` (`guidance_only`); not a freestanding engine | policy schema + finding guidance |
| **Certification** | CertificationRun | offline/CI `certification_tool` (writes `artifacts`; **not** an in-process C4 peer) | `certification/gates.yaml` |

Contexts communicate via **application orchestration** and **immutable store contracts**, not by sharing mutable entities across package boundaries.

## Aggregates

See: [`../class/`](../class/) for aggregate structure, value objects, entities, and invariants.

| Aggregate | Bounded Context | Contract |
| :--- | :--- | :--- |
| Directive | Governance Authoring | `directive/identity`, `lifecycle`, `amendment` |
| CgIrSnapshot | Compilation | `compilation/pipeline`, `hermetic_boundary`, `data_stores/compiled_rules` → C4 `compiled_rules` |
| InspectionSnapshot | Inspection | `inspection/pipeline`, `finding_contract`, `data_stores/artifacts` → C4 `artifacts` |
| Finding | Finding Lifecycle | `finding_lifecycle/*`, `data_stores/finding_events` → C4 `finding_events` |
| ConflictArtifact | Conflict | `conflict/detection`, `precedence` |
| CertificationRun | Certification | `certification/gates.yaml` |

**Dual document:** The Directive aggregate **stores** both an executable rule document (`rule_schema`) and a policy doctrine document (`policy_doctrine`) in C4 store `directives`, linked by `paired_policy_ref` and co-versioned per revision. Doctrine is **not** used for evaluation; only the executable document compiles to CG-IR.

## Domain services (stateless rules)

| Service | Responsibility | Context | Layer |
| :--- | :--- | :--- | :--- |
| `LineageService` | fork/merge/split identity rules, DAG depth | Governance | domain |
| `DetectionDiscriminator` | strategy ↔ active `*_spec` + adapters | Compilation | domain |
| `ResolveConflict` | multi-factor precedence algorithm | Conflict | domain |
| `FindingFsm` | transition table + SoD predicates | Finding Lifecycle | domain |
| `ScopeMatcher` | applicability / specificity scoring | Inspection / Conflict | domain |
| `GuidanceResolver` | load doctrine by `paired_policy_ref` | Guidance | application |
| `CapabilityGate` | cap check + denial audit | Authorization | application |

## Domain events (summary)

See [06-domain-events-and-stores.md](06-domain-events-and-stores.md) for full schemas.

| Event | Aggregate | Append target |
| :--- | :--- | :--- |
| `FindingCreated` | Finding | `finding_events` |
| `DispositionChanged` | Finding | `finding_events` |
| `FindingClosed` | Finding | `finding_events` |
| `CapabilityDenied` | (security audit) | `finding_events` |
| `CgIrPublished` | CgIrSnapshot | provenance / `compiled_rules` metadata |
| `InspectionCompleted` | InspectionSnapshot | `artifacts` |
| `ConflictEscalated` | ConflictArtifact | `artifacts` |
| `CertificationCompleted` | CertificationRun | `artifacts` |

## Anti-corruption notes

| External / adjacent | Translation |
| :--- | :--- |
| Policy doctrine document (in `directives`) | Guidance read model only via Directives Repository; never mutates Finding FSM |
| External Git/package rule trees | Not part of architecture; instances authored in Selma into `directives` only |
| Legacy lint “Finding” (file:line:code) | Map to inspection location + message fields; identity is `finding_id` + control binding |
| Language adapters | Live only under `detection.adapters[]`; core stays universal |
| CI/CD | Triggers auditor; does not write directives or findings |

## Aggregate transaction boundaries

| Use case family | Aggregate(s) in one TX | Notes |
| :--- | :--- | :--- |
| Directive mutate + compile | Directive write lock; then CompilationJob | Compile may be async but publish is atomic CAS |
| Inspect target | InspectionSnapshot create; FindingCreated events | Findings open via FSM auto-transition |
| FSM transition | Single Finding | Capability/SoD before append |
| Conflict review | ConflictArtifact | May advise only for cross-lineage |
