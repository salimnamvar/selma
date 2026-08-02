# Selma — Entity-Relationship Diagrams

> **Design standard:** [`../standards/`](../standards/README.md) · **C4 registry:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)  
> **design_contract_version:** `1.3.0` · Structural SSoT: [`../c4-model/`](../c4-model/README.md)  
> **View ownership:** [`../standards/view_concerns.md`](../standards/view_concerns.md) (ERD row)

## Answers

*What durable tables and relationships does each C4 `*_store` hold?*

ERD owns **storage structure** only: entities, columns, keys, enum domains, and
mutability stereotypes. Normative locking, retention prose, FSM transition
tables, and capability catalogs live under [`../spec/contracts/`](../spec/contracts/)
and are **not** restated as diagram notes.

## Catalog

| File | Diagram ID | C4 store ID | Owner repository | Storage model |
| :--- | :--- | :--- | :--- | :--- |
| `erd_001_directives_store.puml` | ERD-001 | `directives_store` | `directives_repository` | PostgreSQL · mutable dual documents · compile outbox |
| `erd_002_compiled_rules_store.puml` | ERD-002 | `compiled_rules_store` | `compiled_rules_repository` | Content-addressed · immutable snapshots · lineage head index |
| `erd_003_finding_events_store.puml` | ERD-003 | `finding_events_store` | `finding_events_repository` | Append-only log · hybrid logical clock · projections |
| `erd_004_artifacts_store.puml` | ERD-004 | `artifacts_store` | `artifacts_repository` | Object store · write-once + conflict versioning |

Contract filenames under `spec/contracts/data_stores/` match C4 store IDs
(`directives_store.yaml`, `compiled_rules_store.yaml`, `finding_events_store.yaml`,
`artifacts_store.yaml`).

## Shared maintenance layer

| File | Role |
| :--- | :--- |
| `common/erd_styles.puml` | CA palette include + entity/package skinparams + `$ERD_*` color aliases |
| `common/erd_identities.puml` | Diagram titles/IDs, C4 store peers, table name macros, product terms, stereotypes |

**Include order:** `erd_styles.puml` → `erd_identities.puml` → body.

**Headers (required):** `Title`, `Source`, `C4`, `Package`, `Contract` (= `docs/standards/VERSION`).

**Join key:** C4 store peer IDs from the registry — identical strings to package
`ST_*`, deployment data-zone nodes, and class infrastructure store targets.

**Cross-store links:** content hashes and opaque IDs only (no foreign keys drawn
across failure domains). Pointers such as `head_snapshot_hash` and
`paired_policy_ref` are documented as columns, not multi-store relationships.

**No PlantUML `note` blocks.** Encode mutability with stereotypes
(`<<mutable>>`, `<<append_only>>`, `<<immutable>>`, `<<write_once>>`,
`<<projection>>`, `<<outbox>>`, `<<secondary_index>>`, `<<content_addressed>>`,
`<<system_of_record>>`). Constraints appear as `<<PK>>` / `<<FK>>` /
`<<unique>>` attribute markers and enum entities.

## Alignment map (ERD ↔ other views)

| ERD concern | Aligns with | Does not own |
| :--- | :--- | :--- |
| Table/column shape | Domain aggregates & value objects ([`../class/`](../class/README.md)); store contracts | Class method signatures |
| Outbox columns (`worker_id`, `lease_expires_at`, status enum) | Compilation / directive store contracts; state machine 003 pipeline drain | Locking algorithm narrative |
| `fsm_state` / disposition on projections | Finding lifecycle contracts; class `Finding` / `FindingProjection` | Transition **edges** (state view) |
| Hybrid logical clock columns + `RetiredNodes` | Finding events store + state machine 009 | Deployment PVC sizing |
| Lineage head index | Compiled rules store `lineage_head_index`; directives `head_snapshot_hash` | CAS publish linearization prose |
| Artifact types | Ports: Inspection / Finding / Certification artifact ports (package + class) | Pipeline stage inventory as process (activity/state) |
| Enum domains | Domain enums in class; lifecycle contracts | Actor goal catalogs (use case) |

## Modeling state-machine triggers and guards in ERD

State diagrams own **graphs** (states, edges, guards, actions). ERD owns **facts**
those graphs read and write. Never redraw transitions on an ERD.

| FSM element | ERD modeling pattern | Not on ERD |
| :--- | :--- | :--- |
| **Trigger** (named event on edge) | Append-only event row · outbox status change · new revision/version row · write-once artifact | Transition inventory |
| **Guard** `[predicate]` | Queryable column, enum domain, or projection denormalization of stream facts | Predicate expression text |
| **Action** `/ effect()` | Column write co-committed with the trigger row (same store TX when possible) | Procedural algorithm |
| **Capability** `[capability: …]` | Denial audit event only (`CapabilityDenied` / `SoDDenied`) | Role/capability matrix |
| **Lock / lease** | Lease columns on outbox (`worker_id`, `lease_expires_at`); not DB lock graphs | FOR SHARE / FIFO narrative |
| **Ephemeral pipeline stage** | Optional stage row in trace tables when audit needs it; not a second FSM table | In-memory gate order |

### Per state machine → store facts

| State machine | Primary store | Triggers become | Guards need (columns) |
| :--- | :--- | :--- | :--- |
| **001 Finding lifecycle** | `finding_events_store` | `Events.event_type` + `trigger_command` + `from_fsm_state`/`to_fsm_state` + `atomic_batch_id` | `FindingProjections.fsm_state`, `creator_provenance`, `evidence_submitter`, `last_reopen_comments`, disposition enum |
| **002 Directive lifecycle** | `directives_store` | revision `change_trigger`, status write, `LineageOperations` | `status`, `superseded_by_execution_id`, `head_snapshot_hash` (publish), `restore_from_revision` |
| **003 Compilation** | `directives_store` outbox + `compiled_rules_store` | `CompileRequests.status` transitions; snapshot publish | `status`, lease expiry, `published_snapshot_hash`, `failure_class`; CAS existence by hash |
| **004 Inspection** | `artifacts_store` | snapshot status; `PipelineTraces` rows | `skipped_nodes` (partial vs completed), `evaluate_retry_count`, pin hashes |
| **005 Conflict** | `artifacts_store` (+ frozen CG-IR read) | conflict artifact version rows | `lineage_id_a/b` (same/different lineage), `binding_status`, `cg_ir_snapshot_hash`, `requires_human_action`; cascade inputs on `Nodes` (`priority_level`, `authored_at`, `lineage_id`) |
| **006 Certification** | `artifacts_store` | `CertificationRuns.status`; per-gate artifacts | run status; `pass_fail` per `gate_id` |
| **007 Authorization** | `finding_events_store` (denials only) | `CapabilityDenied` / `SoDDenied` events | No grant table — matrix is contract; denials are the durable side-effect |
| **008 Artifact lifecycle** | `artifacts_store` / CAS | write-once publish; conflict version archive | content hash identity; `binding_status=archived` |
| **009 Hybrid logical clock** | `finding_events_store` | HLC fields on every event; watermark upsert | `HybridLogicalClockState`, `RetiredNodes`, event HLC tuple monotonicity |
| **010 Hash composition** | `compiled_rules_store` | node/edge/snapshot hash columns | `semantic_hash` / `presentation_hash` / snapshot hash; `compiled_at` excluded from identity |
| **011 Interaction** | cross-store pointers only | outbox enqueue, pin hash, finding birth, artifact write | no multi-store FK edges |

### Guard classes (what ERD refuses)

| Guard class | Examples | Durable model |
| :--- | :--- | :--- |
| **State predicate** | `fsm_state ∈ {Open,…}`, `status=active` | Enum column on head/projection |
| **Provenance / SoD** | `actorNotInCreatorProvenance`, `actorNotEvidenceSubmitter` | Projection fields + stream SoR |
| **Content / pin** | `hermeticCompileSuccess`, `sameHashAndFrozenEnv` | `head_snapshot_hash`, CAS PK, pin columns |
| **Identity scope** | `sameLineageId`, `supersededByActiveOrDraftId` | lineage columns; successor id + status |
| **Batch atomicity** | `atomicWithTriggerBatch` | `Events.atomic_batch_id` |
| **Clock fence** | `pvcCorruptedOrLost`, non-decreasing HLC | `RetiredNodes`, watermark table |
| **Capability** | `[capability: finding.waive]` | **Not a table** — evaluated at `api`; failure may append denial event |
| **Runtime lock** | `writeLockHeldOrWritePending` | Process/DB lock; outbox may record `failure_class=lock_deferred` |

### Atomic batches (INV-FL-020)

Human trigger + system auto-successor (e.g. `WaiverGranted` + `FindingClosed`) share one
`atomic_batch_id` on multiple `Events` rows in a single DB transaction. The projection
applies only after the full batch commits. ERD models the batch key; state owns which
edges are atomic.

## Rendering

```bash
# Single file
plantuml docs/erd/erd_001_directives_store.puml

# All ERDs
plantuml docs/erd/erd_00*.puml
```

## Check

```bash
python scripts/check_design_alignment.py
```
