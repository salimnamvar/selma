# Selma — Unified User Stories

**Project:** Selma — Rule Regularity Platform  
**Version:** 17.0  
**Date:** 2026-07-05  
**Status:** Final  

> **Note:** Selma is domain-agnostic. It can serve financial compliance, environmental standards, organizational governance, software engineering, or any other regulatory domain.

---

## Core Architecture

```
┌─────────────────────────────┐
│   1. Directive Graph        │
│   (source-of-truth spec)    │
└──────────────┬──────────────┘
               │ compile (hermetic boundary)
               ▼
┌─────────────────────────────┐
│   2. Compiled Control DAG   │
│   (= CG-IR snapshot)        │
└──────────────┬──────────────┘
               │ evaluate (pure functions)
               ▼
┌─────────────────────────────┐
│   3. Finding Event Stream   │
│   - Append-only events      │
│   - Read-only analytics     │
│   - Mediated feedback       │
└──────────────┬──────────────┘
               │ serialize
               ▼
┌─────────────────────────────┐
│   4. Execution Artifacts    │
│   - Inspection snapshots    │
│   - System state hashes     │
│   - Pipeline traces         │
└─────────────────────────────┘
```

---

## Canonical Identity

One directive has ONE identifier across all layers:

| Layer | Field | Example |
| :--- | :--- | :--- |
| Policy Doctrine | `Machine ID` | `TRAF-001` |
| Rule Schema | `rule.id` | `TRAF-001` |
| CG-IR | `node.directive_id` | `TRAF-001` |
| Finding | `finding.control_id` → node | `TRAF-001` |

**Invariant:** `Machine ID` = `rule.id` = `node.directive_id`.

### Identity Lifecycle

| Operation | New ID Required | Description |
| :--- | :--- | :--- |
| **Revision** | No | Changes within same semantic intent |
| **Fork** | Yes (two new IDs) | One directive splits into two distinct directives |
| **Merge** | Yes (one new ID) | Two directives combine into one |
| **Split** | Yes (new IDs for each) | One directive restructured into multiple |
| **Rename** | No | Display name changes, semantic intent unchanged |
| **Retire** | No | Status = deprecated; ID never reused |

**Lineage Tracking:** Fork/merge/split operations record parent IDs in the `lineage` field.

---

## Key Concepts

| Concept | Definition |
| :--- | :--- |
| **Directive Graph** | Human-authored source-of-truth. Structured, versioned, diffable. |
| **CG-IR Snapshot** | Immutable, content-addressed DAG instance. Compilation creates new snapshots. |
| **Finding Event Stream** | Append-only audit log with event hashes. Read-only analytics. |
| **Execution Artifacts** | Immutable inspection snapshots, pipeline traces, system state hashes. |
| **Hermetic Compilation** | Frozen environment (engine, model, prompts, toolchain, OS) ensures reproducibility. |
| **Control Node** | CG-IR node with pure evaluator, scope, severity, dependencies. |
| **Evaluator** | Pure function: no IO, no randomness. Types: regex, field_check, threshold, composite. |
| **Context Object** | Strict schema: target_metadata, domain_constants, finding_aggregates. Read-only. |
| **Target** | Strict schema: target_id, target_type, content_hash, submitted_at, content, metadata. |
| **Incremental Compilation** | Reuses unchanged subgraph; output is always a new immutable snapshot. |
| **Mediated Feedback** | Analytics → human → directive change → recompile. No direct finding → CG-IR. |
| **Conflict Resolution Mapping** | Deterministic operators: priority ranking, specificity scoring, timestamp comparison. |
| **Deterministic Serialization** | Canonical JSON with sorted keys, ISO 8601 UTC, SHA-256 hashing. |
| **Version Resolution** | `system_state_hash = f(directive_version, cg_ir_hash, frozen_env, engine, target_hash)` |
| **Identity Immutability** | Once assigned, Machine IDs are never reused. Deprecated IDs persist in audit trail. |

---

## Actors

### Regulatory Official (Human or AI Agent)

| Attribute | Description |
| :--- | :--- |
| **Acts On Behalf Of** | The Regulatory Authority |
| **Role** | Rule Author & Governance Owner |
| **Responsibilities** | Create, modify, retire, fork, merge, split directives. Review consistency, audits, versions. Review remediation evidence. Authorize finding dispositions. Review analytics, drive mediated feedback. |
| **AI Agent Constraint** | Same permissions as humans. All actions audit-logged with actor identity. Segregation of duties applies equally. |

### Compliance Representative (Human or System)

| Attribute | Description |
| :--- | :--- |
| **Acts On Behalf Of** | The Regulated Entity |
| **Role** | Compliance Seeker & Remediation Owner |
| **Responsibilities** | Submit targets for inspection. View findings, acknowledge, submit evidence, request reinspection. |
| **Non-Responsibilities** | Cannot create/modify/retire directives. Cannot waive findings. |

---

## Epic 1: Directive Lifecycle

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-01** | Regulatory Official | I want to submit a new directive. | **Given** I express a need. **When** Selma processes it. **Then** Selma assigns canonical ID, records in Directive Graph, compiles to CG-IR snapshot via hermetic boundary, performs structural review. **And** directive in "Draft" state with scope. | **P0** |
| **S-02** | Regulatory Official | I want to modify an existing directive. | **Given** I specify directive ID and change. **When** Selma processes it. **Then** Selma creates new revision, incrementally compiles to new CG-IR snapshot (reuses unchanged subgraph), re-assesses consistency, records provenance. **And** canonical ID unchanged. **And** new Ruleset Version. | **P0** |
| **S-03** | Regulatory Official | I want to retire a directive. | **Given** I specify directive to retire. **When** Selma processes it. **Then** Selma transitions to "Retired", records reason, marks CG-IR nodes deprecated, generates new snapshot. | **P1** |
| **S-19** | Regulatory Official | I want to fork a directive into two distinct directives. | **Given** I specify a directive and describe the split. **When** Selma processes it. **Then** Selma creates two new canonical IDs, records lineage (parent_ids = original ID, operation = fork), compiles both to CG-IR, deprecates original nodes. | **P1** |
| **S-20** | Regulatory Official | I want to merge two directives into one. | **Given** I specify two directives and describe the merge. **When** Selma processes it. **Then** Selma creates one new canonical ID, records lineage (parent_ids = both original IDs, operation = merge), compiles to CG-IR, deprecates both originals. | **P1** |

---

## Epic 2: Directive Governance

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-04** | Regulatory Official | I want to view all active requirements. | **Given** I request active requirements. **When** Selma processes it. **Then** Selma returns active directives and compiled nodes from current CG-IR snapshot. | **P0** |
| **S-05** | Regulatory Official | I want to inspect the regulatory set for conflicts. | **Given** I request consistency review. **When** Selma processes it. **Then** Selma assesses CG-IR, applies Conflict Resolution Mapping, issues report with Conflict Artifacts. | **P1** |
| **S-06** | Regulatory Official | I want a comprehensive audit. | **Given** I request full audit. **When** Selma processes it. **Then** Selma generates audit report with gaps, redundancies, remedial measures. | **P2** |
| **S-07** | Regulatory Official | I want to view revision and lineage history of any directive. | **Given** I request history. **When** Selma processes it. **Then** Selma provides full revision log with timestamps, originator, changes, and lineage (fork/merge/split operations). Canonical ID constant. | **P1** |
| **S-08** | Regulatory Official | I want to restore a directive to a previous revision. | **Given** I specify directive and target revision. **When** Selma processes it. **Then** Selma creates new revision copying target, recompiles to new CG-IR snapshot, records provenance. | **P1** |
| **S-09** | Regulatory Official | I want to preview impact before finalizing. | **Given** I request change. **When** Selma generates proposal. **Then** Selma shows current vs proposed CG-IR snapshots, requires confirmation. | **P2** |

---

## Epic 3: Inspection

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-10** | Compliance Representative | I want to submit a target for inspection. | **Given** I provide a target (conforming to target schema). **When** Selma processes it. **Then** Selma validates target schema, populates context (conforming to context schema), executes DAG pipeline, produces findings. **And** records inspection snapshot with: target_hash, ruleset_version, frozen_env_hash, engine_version, pipeline_trace, skipped_nodes, system_state_hash. **And** failed nodes → NeedsReview; others continue. **And** report is consistent point-in-time snapshot. | **P0** |
| **S-15** | Compliance Representative | I want to reinspect against latest directives. | **Given** I specify previously inspected target. **When** Selma processes it. **Then** Selma reads target (new hash), creates new inspection snapshot against current CG-IR, produces new Report. **And** original immutable. | **P1** |
| **S-16** | Compliance Representative | I want Selma to explain why a finding was raised. | **Given** I request explanation. **When** Selma processes it. **Then** Selma traverses causal chain (Finding → Control Node → Directive → Revision → Scope), highlights target portions, explains reasoning. | **P1** |

---

## Epic 4: Finding Management

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-11** | Compliance Representative | I want to view all findings. | **Given** I request findings. **When** Selma processes it. **Then** Selma returns findings with computed lifecycle_status, computed disposition, severity, inspection reference, control node. | **P0** |
| **S-12** | Compliance Representative | I want to acknowledge a finding. | **Given** I specify finding. **When** I acknowledge. **Then** Selma creates Remediation record, status "In Progress", records timestamp and actor. **And** event log unchanged. | **P1** |
| **S-13** | Compliance Representative | I want to submit remediation evidence. | **Given** I specify finding and evidence. **When** Selma processes it. **Then** Selma attaches evidence, status "Pending Verification", records submission. **And** event log unchanged. | **P1** |
| **S-14** | Regulatory Official | I want to review remediation evidence. | **Given** I request pending reviews. **When** Selma presents evidence. **Then** I approve (append FindingClosed) or reject (append DispositionChanged). **And** event log append-only with event_hash. | **P1** |

---

## Epic 5: Analytics & Mediated Feedback

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-17** | Regulatory Official | I want to view analytics on finding patterns. | **Given** I request analytics. **When** Selma processes it. **Then** Selma returns read-only aggregates: rates, severity distributions, recurrence, trends. **And** analytics never modify CG-IR. | **P1** |
| **S-18** | Regulatory Official | I want to propose a directive change based on analytics. | **Given** I review analytics and decide to change. **When** I submit via S-02. **Then** Selma records analytics provenance on directive revision. **And** follows standard path. | **P2** |

---

## Story Summary

| Epic | P0 | P1 | P2 | Total |
| :--- | :--- | :--- | :--- | :--- |
| Directive Lifecycle | 2 | 3 | 0 | **5** |
| Directive Governance | 1 | 3 | 1 | **5** |
| Inspection | 1 | 2 | 0 | **3** |
| Finding Management | 1 | 3 | 0 | **4** |
| Analytics & Mediated Feedback | 0 | 1 | 1 | **2** |
| **Total** | **5** | **12** | **2** | **19** |

---

## Traceability

| Principle | Stories |
| :--- | :--- |
| Canonical Identity + Lifecycle | S-01, S-02, S-03, S-19, S-20 |
| Incremental Compilation (new snapshots) | S-02, S-03, S-19, S-20 |
| Hermetic Reproducibility | S-10 |
| Inspection Consistency (point-in-time) | S-10 |
| State-Dependent Evaluation (strict context) | S-10 |
| Event-Sourced Findings (with hashes) | S-11, S-12, S-13, S-14 |
| Conflict Resolution Mapping | S-05 |
| Mediated Feedback | S-17, S-18 |
| DAG Execution with Failure Handling | S-10 |
| Declarative → Executable Logic | S-01, S-02 |
| Deterministic Serialization | S-10 |
| Version Forward-Only | All |

---

## System Invariants

| Invariant | Description |
| :--- | :--- |
| **Canonical Identity** | Machine ID = rule.id = directive_id across all layers |
| **Identity Immutability** | Once assigned, Machine IDs never reused |
| **Hermetic Compilation** | CG-IR reproducibility requires pinned frozen_env |
| **CG-IR Snapshot Immutability** | Once published, immutable; compilation creates new snapshots |
| **Finding Event Immutability** | Append-only; event_hash ensures integrity |
| **Inspection Immutability** | Completed snapshots never modified |
| **Inspector Snapshot Consistency** | Report is point-in-time; partial results explicitly marked |
| **Evaluator Purity** | Pure functions: no IO, no randomness |
| **DAG Acyclicity** | Enforced at compile time |
| **Segregation of Duties** | Directive creator ≠ Finding waiver |
| **Mediated Feedback** | No direct finding → CG-IR path |
| **Declarative Governance** | Policy describes intent; engine implements via Conflict Resolution Mapping |
| **Deterministic Serialization** | Canonical JSON with sorted keys for all hashing |
| **Event Ordering** | Strict total order by timestamp; ties by event_id |
| **Version Forward-Only** | No downgrades; legacy snapshots pinned to engine versions |
| **AI Actor Audit Equivalence** | AI agents have same permissions; all actions audit-logged |

---

## Internal View

| Engine | What It Does |
| :--- | :--- |
| **Directive Drafting Engine** | Natural language → Directive Graph entries |
| **Structural Compliance Reviewer** | Validates against schema and contamination rules |
| **Control Compilation Engine** | Directive Graph → CG-IR snapshot. Hermetic. Incremental. |
| **DAG Evaluation Engine** | Topological sort, parallel execution, strict context population, failure handling |
| **Conflict Resolution Engine** | Detects conflicts, applies Conflict Resolution Mapping, creates Conflict Artifacts |
| **Provenance Manager** | Tracks versions, revisions, lineage, frozen_env hashes, causal traceability |
| **Analytics Engine** | Read-only aggregates from Finding Event Stream. Feeds context. Never modifies CG-IR. |
