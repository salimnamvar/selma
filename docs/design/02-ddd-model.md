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
│ (FSM, SoD, events)  │     │ (capabilities, roles)│
└──────────┬──────────┘     └──────────────────────┘
           │ guidance_only
           ▼
┌─────────────────────┐     ┌──────────────────────┐
│ Guidance & Analytics│     │ Certification        │
│ (analyzer, doctrine)│     │ (AA-01…AA-07)        │
└─────────────────────┘     └──────────────────────┘
```

| Bounded context | Primary aggregates | C4 owners | Contracts |
| :--- | :--- | :--- | :--- |
| **Governance Authoring** | DirectiveGraph, Directive | `directives_adapter`, `application_service` | `directive/*` |
| **Compilation** | CompilationJob, CgIrSnapshot | `hermetic_compiler` | `compilation/*` |
| **Inspection** | InspectionSnapshot, Target | `rule_inspector` | `inspection/*` |
| **Finding Lifecycle** | Finding | `lifecycle_finder` | `finding_lifecycle/*` |
| **Conflict** | ConflictArtifact | `conflict_resolver` | `conflict/*` |
| **Authorization** | ActorCapabilityGrant (or session claims) | `application_service` | `authorization/*` |
| **Guidance & Analytics** | (read models) GuidanceView, AggregateReport | `finding_analyzer` | policy schema + inspection guidance |
| **Certification** | CertificationRun | `architectural_auditor` | `certification/gates.yaml` |

Contexts communicate via **application orchestration** and **immutable store contracts**, not by sharing mutable entities across package boundaries.

## Aggregates

See: [`../class-diagram/`](../class-diagram/) for aggregate structure, value objects, entities, and invariants.

| Aggregate | Bounded Context | Contract |
| :--- | :--- | :--- |
| Directive | Governance Authoring | `directive/identity`, `lifecycle`, `amendment` |
| CgIrSnapshot | Compilation | `compilation/pipeline`, `hermetic_boundary`, `data_stores/cgir_store` |
| InspectionSnapshot | Inspection | `inspection/pipeline`, `finding_contract`, `data_stores/artifact_store` |
| Finding | Finding Lifecycle | `finding_lifecycle/*`, `data_stores/event_store` |
| ConflictArtifact | Conflict | `conflict/detection`, `precedence` |
| CertificationRun | Certification | `certification/gates.yaml` |

**Dual document:** The Directive aggregate **stores** both an executable rule document (`rule_schema`) and a policy doctrine document (`policy_doctrine`) in `directive_store`, linked by `paired_policy_ref` and co-versioned per revision. Doctrine is **not** used for evaluation; only the executable document compiles to CG-IR.

## Domain services (stateless rules)

| Service | Responsibility | Context |
| :--- | :--- | :--- |
| `LineageService` | fork/merge/split identity rules, DAG depth | Governance |
| `DetectionDiscriminator` | strategy ↔ active `*_spec` + adapters | Compilation |
| `ResolveConflict` | multi-factor precedence algorithm | Conflict |
| `FindingFsm` | transition table + SoD predicates | Finding Lifecycle |
| `ScopeMatcher` | applicability / specificity scoring | Inspection / Conflict |
| `GuidanceResolver` | load doctrine by `paired_policy_ref` | Guidance |
| `CapabilityGate` | cap check + denial audit | Authorization |

## Domain events (summary)

See [06-domain-events-and-stores.md](06-domain-events-and-stores.md) for full schemas.

| Event | Aggregate | Append target |
| :--- | :--- | :--- |
| `FindingCreated` | Finding | event_store |
| `DispositionChanged` | Finding | event_store |
| `FindingClosed` | Finding | event_store |
| `CapabilityDenied` | (security audit) | event_store |
| `CgIrPublished` | CgIrSnapshot | provenance / cgir_store metadata |
| `InspectionCompleted` | InspectionSnapshot | artifact_store |
| `ConflictEscalated` | ConflictArtifact | artifact_store |
| `CertificationCompleted` | CertificationRun | artifact_store |

## Anti-corruption notes

| External / adjacent | Translation |
| :--- | :--- |
| Policy doctrine document (in directive_store) | Guidance read model only via Directives Adapter; never mutates Finding FSM |
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
