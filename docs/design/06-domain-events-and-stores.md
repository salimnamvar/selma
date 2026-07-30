# 06 — Domain Events & Stores

## Store roles (frozen)

| C4 store ID | Mutability | Writer components | Reader components |
| :--- | :--- | :--- | :--- |
| `directives` | Mutable versioned dual documents | `directives_repository` via directive use cases / `api` | `compilation.readExecutable` (read lock), `findings.readPolicyDoctrine` (guidance_only), queries |
| `compiled_rules` | Immutable CAS | `compiled_rules_repository` via `compilation` | `inspection`, `findings` (provenance), conflict domain service |
| `finding_events` | Append-only | `finding_events_repository` via `findings` + `api` denials | `findings` reads, queries |
| `artifacts` | Write-once objects | `artifacts_repository` via `inspection` / `findings` / cert tool | queries |

## Finding event stream

Normative types (from `finding_lifecycle/transitions` + finding_events contract):

### FindingCreated

| Field | Notes |
| :--- | :--- |
| `event_id` | UUID |
| `finding_id` | stable ID |
| `event_type` | `FindingCreated` |
| `timestamp` | ISO 8601 UTC Z |
| `logical_clock` | HLC |
| `actor` | `system` / inspector |
| `payload` | control/node binding, inspection_id, severity, paired_policy_ref, location |
| `event_hash` | SHA-256 canonical payload |

FSM effect: Created → Open (automatic).

### DispositionChanged

Emitted on every human or automatic transition that changes state/disposition.

Payload includes: `from_state`, `to_state`, `disposition`, `capability`, `comments?`, `evidence_ref?`.

### FindingClosed

Terminal close from Verified or Waived (system). Dismissed is terminal without requiring a separate close event if modeled as terminal disposition—implementations must match contract event_schema list.

### CapabilityDenied

Security audit event: attempted action, actor, capability, reason (`segregation of duties violation` | `missing capability`), **no state mutation**.

## HLC ordering

- Every append carries `logical_clock`.
- Total order for a stream is HLC then `event_id` tie-break.
- Detail machine: `state-machine/selma_hlc_clock.puml`.
- Contract: `data_stores/event_store.yaml`.

## CG-IR hash events / provenance

Not necessarily in finding event stream; recorded at publish:

- `frozen_env_hash`, `engine_version`, `directive_graph_version`
- `cg_ir_snapshot_hash`, node/edge hashes
- `creator_provenance` per node (excluded from node_body hash)

Detail: `selma_cgir_hash_chain.puml`, `compilation/pipeline.yaml`.

## Inspection artifacts

`InspectionSnapshot` fields (design):

- `target_hash`, `ruleset_version` / snapshot hash, `frozen_env_hash`, `engine_version`
- `pipeline_trace`, `skipped_nodes`, `system_state_hash`
- finding IDs or embedded finding summaries

## Conflict artifacts

- Within-lineage unresolvable → requires human action  
- Cross-lineage → advisory (`binding_status=advisory`) without rewriting findings  

Stored in `artifacts`; never silently dropped.

## Guidance payload (not an event source of truth)

Guidance resolved by the `findings` use-case cluster is a **read model** field on query responses:

- `reasoning`, `remediation_strategy`, `remediation_steps`, domain examples  
- Source: policy doctrine in `directives` via `paired_policy_ref` and `DirectiveRepository.readPolicyDoctrine`  
- Must not be required for FSM transition validity  

## Replication

Adapters may push to `optional_export`:

- finding events  
- inspection snapshots  
- certification artifacts  

Replication is best-effort relative to local append success; local immutability wins.

## Consistency model

| Path | Model |
| :--- | :--- |
| Directive write + compile | Write lock on directive graph; publish CAS snapshot |
| Inspection | Read snapshot of CG-IR; write-once inspection artifact |
| Finding transition | Single-stream append with optimistic concurrency on stream version / HLC |
| Analytics | Eventual read models allowed; never feedback into CG-IR without human directive change |
