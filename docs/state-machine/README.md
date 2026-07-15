# Selma — Canonical State Machine Architecture

**Contract version:** 8.2.4  
**Authority hierarchy:** `SPECIFICATION.md` > C4 architecture > User stories > Architect judgment  
**Constraint:** Zero `note` blocks in any `.puml` file (encode guards/actors on transitions; ownership in this README)

> C4 describes *what boxes exist and how they communicate*.  
> This directory describes *how state evolves inside those boxes*.  
> Read both with `docs/spec/SPECIFICATION.md` for the full behavioral contract.

---

## Catalog

| File | Machine | Spec authority | Normative? | C4 state authority |
| :--- | :--- | :--- | :---: | :--- |
| `selma_finding_lifecycle.puml` | Finding Lifecycle | §3.1 | **Yes** | Lifecycle Finder |
| `selma_directive_lifecycle.puml` | Directive Lifecycle | §2.2, §2.2.4, §2.3 | Extracted | Application Service + Directives Adapter |
| `selma_compilation_pipeline.puml` | Compilation / CG-IR | §2.4–§2.9, §3.4–§3.5 | Extracted | Hermetic Compiler |
| `selma_inspection_pipeline.puml` | Inspection Execution | §2.10–§2.13, §3.3, §3.6–§3.7 | Extracted | Rule Inspector |
| `selma_conflict_resolution.puml` | Conflict Resolution | §2.15, §2.15.2 | Extracted | Conflict Resolver |
| `selma_architecture_certification.puml` | Architectural Certification | §9.9 AA-01…AA-07 | Extracted | Architectural Auditor |
| `selma_authorization.puml` | Capability Authorization | §3.2, §3.2.1 | Extracted | Application Service + domain gates |
| `selma_artifact_lifecycle.puml` | Artifact Lifecycle | §2.1, §2.6, §3.5–§3.6 | Extracted | Snapshots / Compiled Rules / Findings adapters |
| `selma_hlc_clock.puml` | HLC Event Ordering | §2.14 | **Detail view** | Lifecycle Finder / Event Store (no independent aggregate) |
| `selma_cgir_hash_chain.puml` | CG-IR Hash & Reuse | §2.6 | **Detail view** | Hermetic Compiler (zoom of Hash Nodes → Publish) |
| `selma_machine_interaction.puml` | Machine Interaction Overview | C4 + ownership | **Overview** | Cross-machine handoffs (not a lifecycle aggregate) |
| `common/sm_styles.puml` | Shared theme | — | — | — |

**Normative note:** The specification defines **one** explicit state machine (Finding FSM §3.1). All other machines are *extracted* from normative pipeline prose, capability gates, and concurrency rules. They must not invent behavior that contradicts the spec.

**Detail views:** HLC and CG-IR hash chain zoom algorithms owned by Finding/Event Store and Compilation; they are not independent aggregates.

### Validation

```bash
python scripts/validate_state_machines.py          # notes + capabilities + catalog
python scripts/validate_state_machines.py --plantuml  # + PlantUML syntax
```

---

## Ownership Matrix

| State Machine | Aggregate Owner | State Authority | Persistence Authority | Event Source |
| :--- | :--- | :--- | :--- | :--- |
| Finding Lifecycle | Finding | Lifecycle Finder | `event_store` via Findings & Audit Trail Adapter | Rule Inspector (create); actors via Application Service |
| Directive Lifecycle | Directive (lineage_id + execution_id) | Application Service + Directives Adapter | `directive_store` via Directives Adapter | Regulatory Official → Interface → App Service |
| Compilation / CG-IR | CG-IR Snapshot | Hermetic Compiler | `cgir_store` (CAS) via Compiled Rules Adapter | App Service on directive change / CI |
| Inspection Execution | Inspection run | Rule Inspector | `artifact_store` via Snapshots Adapter; findings → Lifecycle Finder | Compliance Rep / System → App Service |
| Conflict Resolution | Conflict / Conflict Artifact | Conflict Resolver | Artifacts in `artifact_store`; denials in `event_store` | Compiler, Rule Inspector, Official human review |
| Architectural Certification | Certification Artifact | Architectural Auditor | `artifact_store` via Snapshots Adapter | CI/CD → App Service |
| Capability Authorization | Cross-cutting (denial record) | Application Service + Lifecycle Finder / Conflict Resolver | `event_store` (denial audits) | All ingress |
| Artifact Lifecycle | Snapshot / Trace / Conflict / Cert / Event | Multi-writer write-once adapters | `artifact_store`, `cgir_store`, `event_store` | Producers above |
| HLC Event Ordering (detail) | *(none — mechanism)* | Shared event-envelope on Finding/Event Store | `event_store` (persisted pt, lc) | Every event append path |
| CG-IR Hash & Reuse (detail) | *(none — sub-stages of CG-IR Snapshot)* | Hermetic Compiler (Hash Nodes…Publish) | `cgir_store` CAS | Compile pipeline Hash stages |

### C4 mapping gaps (accepted)

| Gap | Mitigation in this model |
| :--- | :--- |
| No dedicated Directive FSM component | Application Service + Directives Adapter own status transitions |
| No capability registry component | Authorization FSM is cross-cutting; matrix lives in §3.2 |
| Inspection status not a separate store | Process FSM; durable outcome is snapshot + findings |
| Artifact multi-writer | Write-once semantics + content addressing |

---

## Transition Matrices

### 1. Finding Lifecycle (normative §3.1)

| From | To | Command | Actor | Capability / Guard | Event |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `[*]` | Created | evaluation outcome Fail/Partial/NeedsReview | System (Rule Inspector) | — | `FindingCreated` |
| Created | Open | automatic | System | — | `DispositionChanged` |
| Open | Acknowledged | `finding.acknowledge` | Compliance Representative | `finding.acknowledge` | `DispositionChanged` |
| Open | Dismissed | `finding.dismiss` | Regulatory Official | `finding.dismiss` | `DispositionChanged` (invalid) |
| Open | Waived | `finding.waive` | Regulatory Official | `finding.waive` + **SoD-1** | `DispositionChanged` (waived) |
| Acknowledged | Evidence Submitted | `evidence.submit` | Compliance Representative | `evidence.submit` | `DispositionChanged` |
| Evidence Submitted | Pending Verification | automatic | System | — | `DispositionChanged` |
| Pending Verification | Verified | `finding.approve_remediation` | Regulatory Official | `finding.approve_remediation` + **SoD-2** | `DispositionChanged` |
| Pending Verification | Rejected | `finding.reject_remediation` | Regulatory Official | `finding.reject_remediation` | `DispositionChanged` |
| Rejected | Open | `finding.reopen` (+ comments) | Regulatory Official | **`finding.reject_remediation`** (S-14c binding) | `DispositionChanged` |
| Verified | Closed | automatic | System | — | `FindingClosed` |
| Waived | Closed | automatic | System | — | `FindingClosed` |

**Terminal:** `Dismissed`, `Closed`  
**Pre-terminal:** `Verified`, `Waived` (system auto-close only)  
**Forbidden:** human-triggered Close; any transition from Dismissed; Closed reopen without new finding  
**SoD-1:** actor ∉ `creator_provenance` for `finding.control_id`  
**SoD-2:** actor ≠ evidence submitter for this finding  
**Deny semantics:** 403 · FSM unchanged · **no** success event · denial audit only  
**Command vs capability:** §3.1 command name is `finding.reopen`; gating capability is `finding.reject_remediation` per User Stories **S-14c** (Q-02 resolved).  
**Extension point (not modeled):** `finding.supersede` — optional per §2.13.1; capability exists in matrix; no edge in normative 10-state FSM (Q-03).

### 2. Directive Lifecycle

| From | To | Command | Actor | Capability | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `[*]` | Draft | `directive.create` | Official | `directive.create` | lineage_id = Machine ID; execution_id = lineage_id |
| Draft | Draft | `directive.modify` | Official | `directive.modify` | revision; same IDs |
| Draft | Active | publish + compile success | Official + System | `directive.modify` | new CG-IR snapshot |
| Active | Active | `directive.modify` | Official | `directive.modify` | incremental compile |
| Active | Deprecated | `directive.retire` | Official | `directive.retire` | CG-IR nodes marked deprecated |
| Active | Superseded | supersede | Official | `directive.modify` | `superseded_by` required |
| Active | Fork/Merge/Split spawn | fork / merge / split | Official | `directive.fork` / `directive.merge` / **`directive.fork` (split)** | parent → Deprecated |
| spawn | **Draft** | materialize children | System | — | new execution_id; publish via Draft→Active |
| Deprecated | Draft | `directive.restore` | Official | `directive.restore` | must recompile to Active |

**Split gating (Q-01 resolved):** S-26 `directive.split` is gated by existing **`directive.fork`** for v8.2.4 (spec matrix has no `directive.split` row). A future SPEC amendment may add a distinct row; until then the fork gate is permanent for this contract version.

### 3. Compilation / CG-IR

| Stage order | On fail |
| :--- | :--- |
| Requested → Queued → Acquire Read Lock → Schema → Complexity → Portability → Discriminator → Lineage → Hash Nodes → Hash Edges → Conflict Map → Snapshot Hash → Policy Assert (AA-02) → Publish CAS → Release Lock → Completed | **Failed** · release lock · no partial CG-IR · Directive Graph unchanged |

**Gate ordering ADR:** Spec requires Schema then Complexity before CG-IR generation (§2.9). Portability → Discriminator → Lineage → Hash is extracted engineering order (logged in decision log).

### 4. Inspection Execution

| Stage order | Terminal |
| :--- | :--- |
| Submitted → Ingress → Normalize → Classify → Select Controls → Evaluate → Aggregate → Report | Completed \| Partial \| Failed |

Ingress deny → no snapshot. Stage faults → typed findings (except Dependency skip). Fatal CG-IR corruption → Failed. Timeout retry: `[retry_count < max_retries]`, max 3, default 0.

### 5. Conflict Resolution

Within-lineage cascade: Explicit override → Compatible overrides → Priority (lower number wins) → Specificity → Recency → Conflict Artifact (human `conflict.resolve`).  
Cross-lineage: advisory artifact only; never mutates findings/CG-IR.

### 6. Architectural Certification

Triggered → Collecting Evidence → Validating AA-01…AA-07 → Passed → Certified → Archived  
Any gate fail → Failed → Remediation Required → new CI run (no domain mutation).

### 7. Capability Authorization

RequestReceived → IdentityVerified → CapabilityEvaluated → [SoDEvaluated] → StageGateChecked → Allowed  
Any fail → Denied → DenialAudited → DomainUnchanged.

### 8. Artifact Lifecycle

Building → Validated → Published → Active Reference → Superseded Reference → Archived.  
**Extended state:** `replicated: bool` (self-transitions on Published / Active / Superseded when async audit replicate fires).  
Reject build → no durable artifact.

### 9–10. Detail views (Q-04 resolved)

| Machine | Purpose | Relationship |
| :--- | :--- | :--- |
| HLC | Per-node (pt, lc) advance / receive / partition reconcile | Event-envelope mechanism; not a durable aggregate |
| CG-IR Hash Chain | Dual-hash → reuse decision → snapshot hash → CAS dedup | Zoom of Compilation Hash Nodes → Publish CAS |

---

## Event Catalog

### Finding stream (normative §2.14)

| Event type | When | Key payload |
| :--- | :--- | :--- |
| `FindingCreated` | Birth at inspection Report | finding_id, lineage_id, control_id, inspection_id, fsm_state=`Created`, severity, outcome, confidence, evidence, reasoning |
| `DispositionChanged` | Any successful FSM edge | previous/new disposition, previous/new fsm_state, reason optional |
| `FindingClosed` | Verified/Waived → Closed | final_disposition, final_fsm_state, closure_reason optional |

**Envelope (all events):** `event_id`, `timestamp` (UTC), `logical_clock` (HLC), `actor`, `event_hash` = SHA-256(canonical_json without hash).

### Denial audit (not a success transition)

```
{ actor, capability, action, outcome: "denied", timestamp, reason }
```

### Extracted domain events (non-normative names; implementable)

| Domain | Event / artifact | Identity |
| :--- | :--- | :--- |
| Directive | DirectiveCreated / Revised / Published / Retired / Forked / Merged / Split / Restored / ChildrenSpawned | lineage_id + execution_id |
| Compilation | CompileRequested … CgIrPublished / CompileGateFailed | request_id + cg_ir_snapshot_hash |
| Inspection | InspectionSubmitted … InspectionCompleted / Partial / Failed | inspection_id + system_state_hash |
| Conflict | ConflictResolvedBinding / ConflictArtifactOpened / Resolved | artifact_id + pair ids |
| Certification | CertificationTriggered … Sealed / Failed | run_id + AA gate report |
| Authorization | AuthzAllowed / AuthzDenied / AuthzDenialAudited | actor + capability |
| Artifact | ArtifactPublished / Replicated / Archived | content hash or object id |
| HLC | HlcTupleEmitted / HlcReconciled | node_id + (pt, lc) |

---

## Security Model

| Rule | Enforcement |
| :--- | :--- |
| Capability matrix §3.2 | Before every mutating transition |
| SoD-1 Creator ≠ Waiver | `finding.waive` at Lifecycle Finder |
| SoD-2 Submitter ≠ Approver | `finding.approve_remediation` at Lifecycle Finder |
| Hard deny | No partial mutation; no compensating events |
| Policy runtime prohibition | Compile PolicyAssert + cert AA-02 |
| Mediated feedback | Analytics never write CG-IR or drive Finding FSM |
| AI agents | Same matrix; actor = agent ID; full audit |
| Delegation | **Not supported** in v8.2.x |

### Capability matrix (authoritative §3.2) — diagram must not invent rows

| Capability | Official | Compliance | System |
| :--- | :---: | :---: | :---: |
| `directive.create` | ✅ | ❌ | ❌ |
| `directive.modify` | ✅ | ❌ | ❌ |
| `directive.retire` | ✅ | ❌ | ❌ |
| `directive.fork` | ✅ | ❌ | ❌ |
| `directive.merge` | ✅ | ❌ | ❌ |
| `directive.restore` | ✅ | ❌ | ❌ |
| `inspection.submit` | ❌ | ✅ | ✅ |
| `inspection.reinspect` | ❌ | ✅ | ❌ |
| `finding.view` | ✅ | ✅ | ✅ |
| `finding.acknowledge` | ❌ | ✅ | ❌ |
| `finding.dismiss` | ✅ | ❌ | ❌ |
| `finding.waive` | ✅ | ❌ | ❌ |
| `finding.approve_remediation` | ✅ | ❌ | ❌ |
| `finding.reject_remediation` | ✅ | ❌ | ❌ |
| `evidence.submit` | ❌ | ✅ | ❌ |
| `finding.supersede` | ✅ | ❌ | ❌ |
| `analytics.view` | ✅ | ✅ | ✅ |
| `conflict.resolve` | ✅ | ❌ | ❌ |

**Operation → capability bindings (not extra matrix rows):**

| Operation / command | Gating capability | Authority |
| :--- | :--- | :--- |
| `directive.split` (S-26) | `directive.fork` | Spec matrix has no split row (Q-01) |
| `finding.reopen` (§3.1 / S-14c) | `finding.reject_remediation` | User Stories S-14c (Q-02) |

---

## Concurrency Model

| Domain | Strategy |
| :--- | :--- |
| Directive Graph | Write lock exclusive for mutations; read lock for compilation; writer-preference FIFO; no lock-type inversion |
| CG-IR publish | Atomic all-or-nothing; content-addressed dedup |
| Finding FSM | Optimistic concurrency on projection version; conflict → 409 |
| Inspection | One pipeline instance per inspection_id; reinspect = new instance |
| Conflict human resolve | Optimistic on artifact version; capability-gated |
| Certification | Isolated by run_id / commit SHA |
| HLC | Per-node exclusive advance of (pt, lc); total order reconstructed on merge |
| Artifact CAS | Content-addressed put is idempotent |

---

## Artifact Retention (§3.5)

| Artifact type | Default retention | Notes |
| :--- | :--- | :--- |
| CG-IR snapshots / node objects | Indefinite | CAS; no delete |
| Finding events | Indefinite | Append-only HLC stream |
| Inspection snapshots | Configurable (default 7 years) | Pruned after retention |
| Pipeline traces | Configurable (default 1 year) | Pruned after retention |
| Conflict / certification artifacts | Per policy; archive path modeled | Write-once |
| audit_platform replica | Append-only async | Not source of mutation |

---

## Specification Mapping

| Spec section | Machine |
| :--- | :--- |
| §2.2 Identity lifecycle | Directive Lifecycle |
| §2.2.2 Deterministic merge | Directive Lifecycle |
| §2.2.3 Lineage DAG | Compilation LineageValidate |
| §2.2.4 Deprecation / supersession | Directive Lifecycle |
| §2.4 Transformation pipeline | Compilation + Inspection |
| §2.6 Dual-hash / snapshot | Compilation + CG-IR Hash Chain |
| §2.6–§2.9 CG-IR / evaluators | Compilation |
| §2.14 HLC / events | Finding + HLC |
| §2.15 Conflict resolution | Conflict Resolution |
| §3.1 Finding FSM | Finding Lifecycle |
| §3.2 Capability model | Authorization |
| §3.3 Fault taxonomy | Inspection |
| §3.4 Compilation concurrency | Compilation |
| §3.5 Storage / retention | Artifact Lifecycle |
| §3.6–§3.7 Inspection snapshot / stages | Inspection |
| §9.9 Architectural audit gates | Architectural Certification |

---

## User Story Mapping

| Story | Machine | Binding |
| :--- | :--- | :--- |
| S-01 / S-02 / S-03 | Directive, Compilation | create / modify / retire |
| S-05 / S-28 | Conflict, Compilation | consistency + determinism |
| S-08 | Directive | restore |
| S-10 / S-15 / S-16 | Inspection | submit / reinspect / explain |
| S-11–S-14c | Finding | view + remediation path |
| S-19 / S-20 / S-26 | Directive | fork / merge / split |
| S-25 / S-29 | Finding | dismiss / waive |
| S-30 | Certification | AA gate report |
| S-32 / S-33 / S-34 | Authorization, Finding | SoD + capability gates |

---

## Color Legend

| Color | Meaning |
| :---: | :--- |
| Blue `#3B7DD8` | Persisted / stable state |
| Teal `#1B7A6E` | In-flight / system processing |
| Amber `#B9770E` | Pending human / capability gate / pre-terminal system wait |
| Green `#2C6E49` | Resolved positive |
| Red `#A93226` | Deny / error / fault |
| Grey `#4A4A4A` | Terminal sink |

---

## Rendering

Requires [PlantUML](https://plantuml.com/):

```bash
plantuml docs/state-machine/*.puml
# or
plantuml -tsvg docs/state-machine/*.puml
```

Shared styles: `common/sm_styles.puml` (included relatively from each diagram).

### Validation gate

```bash
# Must return zero matches
grep -rn "^note\|end note" docs/state-machine/*.puml
```

---

## Design Principles

1. **Specification dominance** — agent diagrams are proposals; §3.1 Finding FSM is non-negotiable.
2. **Compile-time / runtime separation** — policy and governance contracts never load at inspection/FSM/conflict runtime.
3. **Immutability** — CG-IR, finding events, inspection snapshots are append-only / write-once.
4. **Capability + SoD before mutation** — every human edge is gated.
5. **No silent failures** — typed findings, denial audits, or explicit abort states.
6. **Dual identity** — `lineage_id` immutable; `execution_id` changes only on fork/merge/split.
7. **Humans never close findings** — only System after Verified or Waived.
8. **No notes in diagrams** — all behavioral contract on states/transitions; ownership and rationale live in this README.
9. **No silent capability invention** — transition capabilities must exist in SPEC §3.2 (split uses `directive.fork`; reopen uses `finding.reject_remediation`).

---

## UML State Machine Conformance

Catalog machines are **behavioral** UML state machines (entity / process behavior), not protocol state machines. Notation and semantics follow UML statechart conventions:

| UML concept | How Selma applies it |
| :--- | :--- |
| Directed graph of states + transitions | PlantUML `state` diagrams; rounded states, arrow transitions |
| Initial pseudostate | Unlabeled `[*] --> …` on every machine (trigger-free start) |
| Final pseudostate | `… --> [*]` only for true sinks (no further legal edges) |
| Exactly one active simple state | Flat machines; no dual outgoing concurrency without extended state or regions |
| Trigger / guard / action | Labels: **trigger**, `[guard]`, `action: …`; capabilities are guards |
| Entry actions (Moore) | State bodies with `**entry** …` |
| Transition actions (Mealy) | `action:` / `event:` on edges |
| Extended state | Quantitative vars (e.g. `retry_count`, `replicated`, SoD provenance) + `[guards]` |
| Run-to-completion (RTC) | One aggregate processes one command/event to completion before the next |
| Hierarchical nesting | Used sparingly; pipelines are linear stages (valid flat FSMs) |
| Orthogonal regions | Prefer **extended state** when aspects co-vary (e.g. audit replication) rather than false XOR states |

**Intentionally not pure single-entity FSMs:**

| File | Role |
| :--- | :--- |
| `selma_machine_interaction.puml` | Cross-machine **overview** (handoffs), not one aggregate lifecycle |
| `selma_hlc_clock.puml` / `selma_cgir_hash_chain.puml` | **Detail views** of mechanisms owned by Finding/Event Store and Compilation |

**Transition label convention (UML-compatible multi-line form):**

```
trigger-name
actor: …
[capability: …] | [boolean guard]
action: …
event: DomainEvent
```

Guards use square brackets per UML. Same-trigger multi-edges must have non-overlapping guards (e.g. Authorization matrix PASS → SoD vs stage).

---

## Related Documents

- `docs/spec/SPECIFICATION.md` — normative behavior  
- `docs/spec/User_Stories.md` — story bindings  
- `docs/c4-model/` — structural architecture
