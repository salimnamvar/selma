# Selma — Unified User Stories

**Project:** Selma — Rule Regularity Platform  
**Version:** 20.0  
**Date:** 2026-07-05  
**Status:** Final  
**Normative Reference:** SPECIFICATION.md v8.1.0

> **Note:** Selma is domain-agnostic. It can serve financial compliance, environmental standards, organizational governance, software engineering, or any other regulatory domain.

---

## Cross-Layer Binding

| Layer | Document | Role |
| :--- | :--- | :--- |
| **Normative** | SPECIFICATION.md v8.1.0 | Defines system behavior, invariants, contracts |
| **Structural** | rule_schema.json v8.1.0 | JSON Schema encoding of spec invariants |
| **Governance** | policy_doctrine.yaml v8.1.0 | Declarative governance intent |
| **Behavioral** | User_Stories.md v20.0 | This document — behavioral contract |

**Rule:** Spec is normative; schema and policy MUST conform. Version MAJOR must match across all documents.

---

## Core Architecture

```
┌─────────────────────────────┐
│   1. Directive Graph        │
│   (source-of-truth spec)    │
└──────────────┬──────────────┘
               │ compile (hermetic boundary, read lock)
               ▼
┌─────────────────────────────┐
│   2. Compiled Control DAG   │
│   (= CG-IR snapshot)        │
│   Content-addressed store   │
└──────────────┬──────────────┘
               │ evaluate (pure functions)
               ▼
┌─────────────────────────────┐
│   3. Finding Event Stream   │
│   - Append-only events      │
│   - HLC-ordered             │
│   - Finding FSM             │
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

## Dual Identity Model

| ID Type | Purpose | Mutability | Format |
| :--- | :--- | :--- | :--- |
| **Lineage ID** | Immutable root for audit trail | Never changes | `^[A-Z][A-Z0-9]+-[0-9]+$` |
| **Execution ID** | Active node identity for compilation | Changes on fork/merge/split | `^[A-Z][A-Z0-9]+-[0-9]+(-[A-Z0-9]+)*$` |

| Layer | Lineage ID Field | Execution ID Field |
| :--- | :--- | :--- |
| Policy Doctrine | `Machine ID` | `Machine ID` (same until fork/merge/split) |
| Rule Schema | `rule.lineage_id` | `rule.id` |
| CG-IR | `node.lineage_id` | `node.directive_id` |

**Invariant:** `rule.lineage_id` is immutable. `rule.id` changes only on fork/merge/split.

---

## Key Concepts

| Concept | Definition |
| :--- | :--- |
| **Directive Graph** | Human-authored source-of-truth. Structured, versioned, diffable. |
| **CG-IR Snapshot** | Immutable, content-addressed DAG instance. Stored in content-addressed store. |
| **Finding Event Stream** | Append-only audit log with HLC ordering. Finding FSM enforced. |
| **Execution Artifacts** | Immutable inspection snapshots, pipeline traces, system state hashes. |
| **Hermetic Compilation** | Frozen environment ensures reproducibility. Read lock on Directive Graph. |
| **Control Node** | CG-IR node with pure evaluator, scope, severity, dependencies. |
| **Evaluator** | Pure function. Types: regex, field_check, threshold, composite. |
| **Evaluator Config** | Schema-enforced if/then binding — config MUST match evaluator_type. |
| **Finding FSM** | Strict state machine: Created → Open → Acknowledged → Evidence Submitted → Pending Verification → Verified/Closed |
| **Hybrid Logical Clock** | HLC ordering for distributed systems: physical_time + logical_counter + node_id |
| **Capability Model** | Role → Capability → Action. Segregation of duties enforced. |
| **Execution Fault Taxonomy** | Deterministic, Partial, Ambiguous, Dependency, Timeout, Resource, Schema, Corruption |
| **Conflict Resolution Mapping** | Deterministic operators. Explicit override takes precedence. Cycles detected and resolved. |
| **Deterministic Serialization** | Canonical JSON with sorted keys, ISO 8601 UTC, SHA-256, NaN/Infinity prohibited. |
| **Version Resolution** | `system_state_hash = f(directive_version, cg_ir_hash, frozen_env, engine, target_hash)` |
| **Cross-Layer Binding** | Spec is normative; schema is structural projection; policy is governance intent. |
| **Concurrency Model** | Compilation = read lock; modification = write lock (exclusive). Queue serializes requests. |
| **CG-IR Storage** | Content-addressed: snapshots → nodes → edges. Deduplication by hash. |

---

## Actors & Capabilities

### Regulatory Official (Human or AI Agent)

| Attribute | Description |
| :--- | :--- |
| **Acts On Behalf Of** | The Regulatory Authority |
| **Role** | Rule Author & Governance Owner |
| **Capabilities** | `directive.*`, `finding.view`, `finding.dismiss`, `finding.waive`, `finding.approve_remediation`, `finding.reject_remediation`, `analytics.view`, `conflict.resolve` |
| **AI Agent Constraint** | Same capabilities as humans. All actions audit-logged with actor identity. |

### Compliance Representative (Human or System)

| Attribute | Description |
| :--- | :--- |
| **Acts On Behalf Of** | The Regulated Entity |
| **Role** | Compliance Seeker & Remediation Owner |
| **Capabilities** | `inspection.submit`, `inspection.reinspect`, `finding.view`, `finding.acknowledge`, `evidence.submit`, `analytics.view` |
| **Non-Capabilities** | Cannot create/modify/retire directives. Cannot waive findings. |

**Segregation of Duties:**
- Directive creator ≠ Finding waiver
- Evidence submitter ≠ Remediation approver

---

## Epic 1: Directive Lifecycle

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-01** | Regulatory Official | I want to submit a new directive. | **Given** I express a need. **When** Selma processes it. **Then** Selma assigns lineage_id + execution_id, records in Directive Graph, compiles to CG-IR snapshot via hermetic boundary (read lock), performs structural review. **And** directive in "Draft" state with scope. | **P0** |
| **S-02** | Regulatory Official | I want to modify an existing directive. | **Given** I specify directive execution_id and change. **When** Selma processes it. **Then** Selma acquires write lock, creates new revision (same lineage_id), incrementally compiles to new CG-IR snapshot (reuses unchanged subgraph via content-addressed store), re-assesses consistency, records provenance. **And** lineage_id unchanged. **And** new Ruleset Version. | **P0** |
| **S-03** | Regulatory Official | I want to retire a directive. | **Given** I specify directive to retire. **When** Selma processes it. **Then** Selma transitions to "Retired", records reason, marks CG-IR nodes deprecated, generates new snapshot. | **P1** |
| **S-19** | Regulatory Official | I want to fork a directive into two distinct directives. | **Given** I specify a directive and describe the split. **When** Selma processes it. **Then** Selma creates two new execution_ids (inheriting lineage_id), records lineage (parent_lineage_ids, parent_execution_ids, operation=fork), compiles both to CG-IR, deprecates original nodes. | **P1** |
| **S-20** | Regulatory Official | I want to merge two directives into one. | **Given** I specify two directives and describe the merge. **When** Selma processes it. **Then** Selma creates one new execution_id (inheriting both lineage_ids), records lineage, compiles to CG-IR, deprecates both originals. | **P1** |

---

## Epic 2: Directive Governance

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-04** | Regulatory Official | I want to view all active requirements. | **Given** I request active requirements. **When** Selma processes it. **Then** Selma returns active directives and compiled nodes from current CG-IR snapshot. | **P0** |
| **S-05** | Regulatory Official | I want to inspect the regulatory set for conflicts. | **Given** I request consistency review. **When** Selma processes it. **Then** Selma assesses CG-IR, applies Conflict Resolution Mapping (explicit override first, then priority → specificity → recency), issues report with Conflict Artifacts. | **P1** |
| **S-06** | Regulatory Official | I want a comprehensive audit. | **Given** I request full audit. **When** Selma processes it. **Then** Selma generates audit report with gaps, redundancies, remedial measures. | **P2** |
| **S-07** | Regulatory Official | I want to view revision and lineage history of any directive. | **Given** I request history by lineage_id. **When** Selma processes it. **Then** Selma provides full revision log with timestamps, originator, changes, and lineage (fork/merge/split operations). Lineage_id constant across all revisions. | **P1** |
| **S-08** | Regulatory Official | I want to restore a directive to a previous revision. | **Given** I specify directive lineage_id and target revision. **When** Selma processes it. **Then** Selma creates new revision copying target, recompiles to new CG-IR snapshot, records provenance. | **P1** |
| **S-09** | Regulatory Official | I want to preview impact before finalizing. | **Given** I request change. **When** Selma generates proposal. **Then** Selma shows current vs proposed CG-IR snapshots, requires confirmation. | **P2** |

---

## Epic 3: Inspection

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-10** | Compliance Representative | I want to submit a target for inspection. | **Given** I provide a target (conforming to target schema). **When** Selma processes it. **Then** Selma validates target schema, populates context (conforming to context schema), validates evaluator_config matches evaluator_type, executes DAG pipeline, produces findings. **And** records inspection snapshot with: target_hash, ruleset_version, frozen_env_hash, engine_version, pipeline_trace (with fault taxonomy), skipped_nodes, system_state_hash. **And** failed nodes produce findings per fault taxonomy. **And** report is consistent point-in-time snapshot. | **P0** |
| **S-15** | Compliance Representative | I want to reinspect against latest directives. | **Given** I specify previously inspected target. **When** Selma processes it. **Then** Selma reads target (new hash), creates new inspection snapshot against current CG-IR, produces new Report. **And** original immutable. | **P1** |
| **S-16** | Compliance Representative | I want Selma to explain why a finding was raised. | **Given** I request explanation. **When** Selma processes it. **Then** Selma traverses causal chain (Finding → Control Node → Directive → Revision → Scope), highlights target portions, explains reasoning. | **P1** |

---

## Epic 4: Finding Management

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-11** | Compliance Representative | I want to view all findings. | **Given** I request findings. **When** Selma processes it. **Then** Selma returns findings with FSM state, computed disposition, severity, inspection reference, control node. | **P0** |
| **S-12** | Compliance Representative | I want to acknowledge a finding. | **Given** I specify finding. **When** I acknowledge (valid FSM transition: Open → Acknowledged). **Then** Selma creates Remediation record, status "In Progress", records timestamp and actor. **And** event log unchanged. | **P1** |
| **S-13** | Compliance Representative | I want to submit remediation evidence. | **Given** I specify finding and evidence. **When** Selma processes it (valid FSM transition: Acknowledged → Evidence Submitted → Pending Verification). **Then** Selma attaches evidence, records submission. **And** event log unchanged. | **P1** |
| **S-14** | Regulatory Official | I want to review remediation evidence. | **Given** I request pending reviews. **When** Selma presents evidence. **Then** I approve (Pending Verification → Verified → Closed) or reject (Pending Verification → Rejected → Open). **And** event log append-only with event_hash and HLC. | **P1** |

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
| Dual Identity (lineage + execution) | S-01, S-02, S-03, S-19, S-20 |
| Incremental Compilation (content-addressed) | S-02, S-03, S-19, S-20 |
| Hermetic Reproducibility | S-10 |
| Inspection Consistency (point-in-time) | S-10 |
| Evaluator Type Safety | S-10 |
| Finding FSM | S-11, S-12, S-13, S-14 |
| HLC Event Ordering | S-14 |
| Capability-Based Permissions | S-14 |
| Conflict Resolution Mapping (explicit override first) | S-05 |
| Mediated Feedback | S-17, S-18 |
| DAG Execution with Fault Taxonomy | S-10 |
| Concurrency Safety (read/write locks) | S-01, S-02 |
| Cross-Layer Binding | All |

---

## System Invariants

| Invariant | Description |
| :--- | :--- |
| **Normative Source** | SPECIFICATION.md v8.1.0 is the single normative source |
| **Dual Identity** | Lineage ID (immutable root) + Execution ID (active node) |
| **Lineage ID Immutability** | Once assigned, lineage_id never reused |
| **Execution ID Stability** | Changes only on fork/merge/split |
| **Hermetic Compilation** | CG-IR reproducibility requires pinned frozen_env |
| **CG-IR Snapshot Immutability** | Once published, immutable; compilation creates new snapshots |
| **CG-IR Content Addressing** | Identical content produces identical hash |
| **Finding Event Immutability** | Append-only; event_hash + HLC ensure integrity |
| **Finding FSM** | Strict state transitions enforced |
| **Inspection Immutability** | Completed snapshots never modified |
| **Evaluator Purity** | Pure functions: no IO, no randomness |
| **Evaluator Type Safety** | evaluator_config MUST match evaluator_type (schema-enforced if/then) |
| **DAG Acyclicity** | Enforced at compile time |
| **Segregation of Duties** | Directive creator ≠ Finding waiver; Evidence submitter ≠ Approver |
| **Capability Enforcement** | All actions checked against capability matrix |
| **Mediated Feedback** | No direct finding → CG-IR path |
| **Declarative Governance** | Policy describes intent; engine implements via Conflict Resolution Mapping |
| **Deterministic Serialization** | Canonical JSON with sorted keys; NaN/Infinity prohibited |
| **HLC Event Ordering** | physical_time + logical_counter + node_id |
| **Version Compatibility** | MAJOR versions match across spec/schema/policy |
| **Cross-Layer Binding** | Schema MUST conform to spec; policy MUST NOT contradict spec |
| **Concurrency Safety** | Compilation = read lock; modification = write lock |

---

## Internal View

| Engine | What It Does |
| :--- | :--- |
| **Directive Drafting Engine** | Natural language → Directive Graph entries |
| **Structural Compliance Reviewer** | Validates against schema, spec invariants, and contamination rules |
| **Control Compilation Engine** | Directive Graph → CG-IR snapshot. Hermetic. Incremental. Content-addressed. |
| **DAG Evaluation Engine** | Topological sort, parallel execution, strict context, fault taxonomy handling |
| **Conflict Resolution Engine** | Applies Conflict Resolution Mapping (explicit override first), creates Conflict Artifacts |
| **Finding FSM Engine** | Enforces state transitions, validates capability permissions |
| **Provenance Manager** | Tracks lineage IDs, execution IDs, revisions, frozen_env hashes, causal traceability |
| **Analytics Engine** | Read-only aggregates from Finding Event Stream. Feeds context. Never modifies CG-IR. |
