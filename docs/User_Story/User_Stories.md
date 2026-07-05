# Selma — Unified User Stories

**Project:** Selma — Rule Regularity Platform  
**Version:** 16.0  
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
│   (= CG-IR)                 │
└──────────────┬──────────────┘
               │ evaluate (pure functions)
               ▼
┌─────────────────────────────┐
│   3. Finding Event Stream   │
│   - Append-only events      │
│   - Read-only analytics     │
│   - Mediated feedback       │
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

**Invariant:** `Machine ID` = `rule.id` = `node.directive_id`. No other identifier serves this function.

---

## Key Concepts

| Concept | Definition |
| :--- | :--- |
| **Directive Graph** | Human-authored source-of-truth. Structured, versioned, diffable. |
| **CG-IR** | Immutable executable DAG. Content-addressed. Incremental snapshots. |
| **Finding Event Stream** | Append-only audit log. Read-only analytics. Mediated feedback. |
| **Hermetic Compilation** | Frozen environment (engine, model, prompts, toolchain) ensures reproducibility. |
| **Control Node** | CG-IR node with pure evaluator, scope, severity, dependencies. |
| **Evaluator** | Pure function: no IO, no randomness. Types: regex, field_check, threshold, composite. |
| **Context Object** | Read-only input: target metadata, domain constants, finding aggregates. |
| **Incremental Compilation** | Only changed nodes recompiled; unchanged subgraph reused. |
| **Mediated Feedback** | Analytics → human → directive change → recompile. No direct finding → CG-IR. |
| **Canonical Identity** | Machine ID = rule.id = directive_id. Single ID across all layers. |
| **Version Resolution** | `system_state_hash = f(directive_version, cg_ir_hash, frozen_env, engine_version, target_hash)` |

---

## Actors

### Regulatory Official (Human or AI Agent)

| Attribute | Description |
| :--- | :--- |
| **Acts On Behalf Of** | The Regulatory Authority |
| **Role** | Rule Author & Governance Owner |
| **Responsibilities** | Create, modify, retire directives. Review consistency, audits, versions. Review remediation evidence. Authorize finding dispositions. Review analytics, drive mediated feedback. |
| **AI Agent Constraint** | AI agents acting as Regulatory Official have the same permissions as humans. All actions are audit-logged with actor identity (human or AI agent ID). Segregation of duties applies equally. |

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
| **S-01** | Regulatory Official | I want to submit a new directive using natural language. | **Given** I express a need. **When** Selma processes it. **Then** Selma assigns a canonical ID (Machine ID), records in Directive Graph, compiles to CG-IR via hermetic boundary, performs structural review. **And** directive in "Draft" state with scope. | **P0** |
| **S-02** | Regulatory Official | I want to modify an existing directive. | **Given** I specify directive ID and change. **When** Selma processes it. **Then** Selma creates new revision, incrementally recompiles affected nodes (reuses unchanged subgraph), re-assesses consistency, records provenance. **And** canonical ID unchanged. **And** new Ruleset Version generated. | **P0** |
| **S-03** | Regulatory Official | I want to retire a directive. | **Given** I specify directive to retire. **When** Selma processes it. **Then** Selma transitions to "Retired", records reason, marks CG-IR nodes deprecated, generates new snapshot. | **P1** |

---

## Epic 2: Directive Governance

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-04** | Regulatory Official | I want to view all active requirements. | **Given** I request active requirements. **When** Selma processes it. **Then** Selma returns active directives and compiled nodes from current CG-IR. | **P0** |
| **S-05** | Regulatory Official | I want to inspect the regulatory set for conflicts. | **Given** I request consistency review. **When** Selma processes it. **Then** Selma assesses CG-IR, issues report with Conflict Artifacts. | **P1** |
| **S-06** | Regulatory Official | I want a comprehensive audit. | **Given** I request full audit. **When** Selma processes it. **Then** Selma generates audit report with gaps, redundancies, remedial measures. | **P2** |
| **S-07** | Regulatory Official | I want to view revision history of any directive. | **Given** I request history. **When** Selma processes it. **Then** Selma provides full revision log. Canonical ID constant. | **P1** |
| **S-08** | Regulatory Official | I want to restore a directive to a previous revision. | **Given** I specify directive and target revision. **When** Selma processes it. **Then** Selma creates new revision copying target, recompiles affected nodes, records provenance. | **P1** |
| **S-09** | Regulatory Official | I want to preview impact before finalizing. | **Given** I request change. **When** Selma generates proposal. **Then** Selma shows current vs proposed CG-IR, requires confirmation. | **P2** |

---

## Epic 3: Inspection

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-10** | Compliance Representative | I want to submit a target for inspection. | **Given** I provide a target. **When** Selma processes it. **Then** Selma populates context (target metadata, domain constants, finding aggregates), executes DAG pipeline, produces findings. **And** records: target_hash, ruleset_version, frozen_env_hash, engine_version, pipeline_trace, skipped_nodes. **And** failed nodes → NeedsReview; others continue. **And** report is a consistent point-in-time snapshot including partial results. | **P0** |
| **S-15** | Compliance Representative | I want to reinspect against latest directives. | **Given** I specify previously inspected target. **When** Selma processes it. **Then** Selma reads target (new hash), creates new Inspection against current CG-IR, produces new Report. **And** original immutable. | **P1** |
| **S-16** | Compliance Representative | I want Selma to explain why a finding was raised. | **Given** I request explanation. **When** Selma processes it. **Then** Selma traverses causal chain (Finding → Control Node → Directive → Revision → Scope), highlights target portions, explains reasoning. | **P1** |

---

## Epic 4: Finding Management

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-11** | Compliance Representative | I want to view all findings. | **Given** I request findings. **When** Selma processes it. **Then** Selma returns findings with computed lifecycle_status, computed disposition, severity, inspection reference, control node. | **P0** |
| **S-12** | Compliance Representative | I want to acknowledge a finding. | **Given** I specify finding. **When** I acknowledge. **Then** Selma creates Remediation record, status "In Progress", records timestamp and actor. **And** event log unchanged. | **P1** |
| **S-13** | Compliance Representative | I want to submit remediation evidence. | **Given** I specify finding and evidence. **When** Selma processes it. **Then** Selma attaches evidence, status "Pending Verification", records submission. **And** event log unchanged. | **P1** |
| **S-14** | Regulatory Official | I want to review remediation evidence. | **Given** I request pending reviews. **When** Selma presents evidence. **Then** I approve (append FindingClosed) or reject (append DispositionChanged). **And** event log append-only. | **P1** |

---

## Epic 5: Analytics & Mediated Feedback

| Story ID | Actor | User Story | Acceptance Criteria | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-17** | Regulatory Official | I want to view analytics on finding patterns. | **Given** I request analytics. **When** Selma processes it. **Then** Selma returns read-only aggregates: rates, severity distributions, recurrence, trends. **And** analytics never modify CG-IR. | **P1** |
| **S-18** | Regulatory Official | I want to propose a directive change based on analytics. | **Given** I review analytics and decide to change. **When** I submit via S-02. **Then** Selma records analytics provenance on directive revision. **And** follows standard Directive Graph → CG-IR path. | **P2** |

---

## Story Summary

| Epic | P0 | P1 | P2 | Total |
| :--- | :--- | :--- | :--- | :--- |
| Directive Lifecycle | 2 | 1 | 0 | **3** |
| Directive Governance | 1 | 3 | 1 | **5** |
| Inspection | 1 | 2 | 0 | **3** |
| Finding Management | 1 | 3 | 0 | **4** |
| Analytics & Mediated Feedback | 0 | 1 | 1 | **2** |
| **Total** | **5** | **10** | **2** | **17** |

---

## Traceability

| Principle | Stories |
| :--- | :--- |
| Canonical Identity Resolution | S-01, S-02, S-03 |
| Incremental Compilation | S-02, S-03 |
| Hermetic Reproducibility | S-10 |
| Inspection Consistency (point-in-time snapshot) | S-10 |
| State-Dependent Evaluation (context object) | S-10 |
| Event-Sourced Findings | S-11, S-12, S-13, S-14 |
| Mediated Feedback | S-17, S-18 |
| DAG Execution with Failure Handling | S-10 |
| Declarative Governance → Executable Logic | S-01, S-02 |

---

## System Invariants

| Invariant | Description |
| :--- | :--- |
| **Canonical Identity** | Machine ID = rule.id = directive_id across all layers |
| **Hermetic Compilation** | CG-IR reproducibility requires pinned frozen_env |
| **CG-IR Immutability** | Once published, immutable |
| **Finding Event Immutability** | Append-only |
| **Inspection Immutability** | Completed inspections never modified |
| **Inspector Snapshot Consistency** | Report is a consistent point-in-time view; partial results explicitly marked |
| **Evaluator Purity** | Pure functions: no IO, no randomness |
| **DAG Acyclicity** | Enforced at compile time |
| **Segregation of Duties** | Directive creator ≠ Finding waiver |
| **Mediated Feedback** | No direct finding → CG-IR path |
| **Declarative Governance** | Policy describes intent; engine implements logic |
| **AI Actor Audit Equivalence** | AI agents have same permissions as humans; all actions audit-logged with actor identity |

---

## Internal View

| Engine | What It Does |
| :--- | :--- |
| **Directive Drafting Engine** | Natural language → Directive Graph entries |
| **Structural Compliance Reviewer** | Validates against schema and contamination rules |
| **Control Compilation Engine** | Directive Graph → CG-IR. Hermetic. Incremental. |
| **DAG Evaluation Engine** | Topological sort, parallel execution, context population, failure handling |
| **Conflict Resolution Engine** | Detects conflicts, creates Conflict Artifacts, escalates |
| **Provenance Manager** | Tracks versions, revisions, frozen_env hashes, causal traceability |
| **Analytics Engine** | Read-only aggregates from Finding Event Stream. Feeds context. Never modifies CG-IR. |
