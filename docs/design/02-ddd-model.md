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

### Directive (Governance Authoring)

- **Root:** `Directive` (execution identity)
- **Invariants:** lineage immutable; status transitions per `directive/lifecycle`; metadata non-executable
- **Value objects:** `LineageId`, `ExecutionId`, `DeonticModality`, `Subject`, `Predicate`, `DetectionSpec`, `PairedPolicyRef`, `Applicability`, `Priority`
- **Entities:** `DirectiveRevision` (history), optional `LineageOperation` record (fork/merge/split)
- **Repository:** `DirectiveRepository` (port) → directives adapter
- **Contract:** `directive/identity`, `lifecycle`, `amendment`

**Dual document:** The aggregate **references** policy doctrine by `paired_policy_ref` but does **not** embed executable evaluation logic from YAML.

### CgIrSnapshot (Compilation)

- **Root:** `CgIrSnapshot` identified by `cg_ir_snapshot_hash`
- **Entities:** `ControlNode`, `DependencyEdge`
- **Value objects:** `NodeHash` (semantic + presentation), `EdgeHash`, `FrozenEnvHash`, `Provenance`
- **Invariants:** immutability after publish; deterministic hash; no policy doctrine load at compile
- **Repository:** `CgIrRepository` → compiled rules adapter
- **Contract:** `compilation/pipeline`, `hermetic_boundary`, `data_stores/cgir_store`

### InspectionSnapshot (Inspection)

- **Root:** `InspectionSnapshot`
- **Value objects:** `Target`, `TargetHash`, `PipelineTrace`, `SkippedNode`, `SystemStateHash`
- **Entities:** born `Finding` drafts (or finding IDs) handed to lifecycle context
- **Invariants:** point-in-time consistency; pure detection evaluators
- **Repository:** `ArtifactRepository` (snapshots) → snapshots adapter
- **Contract:** `inspection/pipeline`, `finding_contract`, `data_stores/artifact_store`

### Finding (Finding Lifecycle)

- **Root:** `Finding`
- **State:** exactly one of 10 FSM states
- **Value objects:** `FindingId`, `Disposition`, `Severity`, `EvidenceRef`, `GuidancePayload` (populated post-hoc)
- **Invariants:** legal transitions only; capability + SoD; system-only close from Verified/Waived
- **Domain events:** `FindingCreated`, `DispositionChanged`, `FindingClosed` (+ denial audit events)
- **Repository:** state reconstructed from **event store** (event-sourced) or projection + append
- **Contract:** `finding_lifecycle/*`, `data_stores/event_store`

### ConflictArtifact (Conflict)

- **Root:** `ConflictArtifact`
- **Value objects:** `ConflictKind` (within-lineage vs cross-lineage advisory), `BindingStatus`, `ResolutionTrace`
- **Invariants:** deterministic resolution for frozen CG-IR; human path for unresolvable
- **Contract:** `conflict/detection`, `precedence`

### CertificationRun (Certification)

- **Root:** `CertificationRun`
- **Entities:** `GateResult` (AA-01…AA-07)
- **Invariants:** all gates pass for production-grade certification; gate-ID traceability
- **Contract:** `certification/gates.yaml`

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
| Policy doctrine YAML | Guidance read model only; never mutates Finding FSM |
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
