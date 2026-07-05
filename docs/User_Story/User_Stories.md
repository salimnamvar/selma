# Selma — Unified User Stories

**Project:** Selma — Rule Regularity Platform  
**Version:** 14.0  
**Date:** 2026-07-05  
**Status:** Final  

> **Note:** Selma is domain-agnostic. It can serve financial compliance, environmental standards, organizational governance, software engineering, or any other regulatory domain.

---

## Core Architecture

Selma is built on **three runtime primitives**:

```
┌─────────────────────────────┐
│   1. Directive Graph        │
│   (source-of-truth spec)    │
│                             │
│   - Human-authored rules    │
│   - Structured metadata     │
│   - Versioned as artifact   │
└──────────────┬──────────────┘
               │ compile (purity boundary)
               ▼
┌─────────────────────────────┐
│   2. Compiled Control DAG   │
│   (= CG-IR)                 │
│   (immutable executable)    │
│                             │
│   - Content-addressed       │
│   - DAG of control nodes    │
│   - Frozen at publish time  │
└──────────────┬──────────────┘
               │ evaluate (deterministic)
               ▼
┌─────────────────────────────┐
│   3. Finding Event Stream   │
│   (append-only audit log)   │
│                             │
│   - Immutable events        │
│   - Computed state          │
│   - No feedback to CG-IR    │
└─────────────────────────────┘
```

---

## Key Concepts

| Concept | Definition |
| :--- | :--- |
| **Directive Graph** | The human-authored source-of-truth specification. Structured, versioned, diffable. Contains directives, scope, priority, prose sections, and metadata. |
| **Compiled Control DAG (CG-IR)** | The immutable executable intermediate representation. All directives compile into it. Content-addressed (Ruleset Version = SHA-256 hash). Frozen at publish time. |
| **Finding Event Stream** | The append-only audit log of all findings. Current state is computed by replaying events. Never influences future CG-IR compilation. |
| **Compile-Time Purity Boundary** | The boundary between Directive Graph and CG-IR. All non-determinism (AI outputs, randomness) is resolved and cached here. CG-IR is fully deterministic. |
| **Control Node** | A node in the CG-IR DAG. Represents a testable condition with an evaluator function, scope, severity, and dependencies. |
| **Evaluator Function** | `evaluate(node, target, context) → {outcome, confidence, evidence, reasoning}`. Fully deterministic post-compilation. |
| **Directive Revision** | A versioned change to a directive. The directive identifier never changes; only the revision increments. |
| **Directive Scope** | The applicability context: domain, jurisdiction, filters. Determines which targets a directive applies to. |
| **Control Version** | The version of a control node's evaluation logic. Increments on directive change, logic change, or scope change. |
| **Ruleset Version** | Content-addressed hash of CG-IR. Immutable once published. |
| **Inspection** | An execution event: DAG evaluation of a target against a CG-IR snapshot. Records target hash, CG-IR hash, engine version, and full pipeline trace. |
| **Finding** | An immutable event in the Finding Event Stream. Current state (lifecycle_status, disposition) is computed by replaying events. Three dimensions: lifecycle (Open/Closed), disposition (Valid/Invalid/Waived), severity (Critical/High/Medium/Low/Informational). |
| **Remediation** | A mutable record attached to a finding. Tracks corrective action through evidence submission and verification. |
| **Conflict Artifact** | A first-class entity recording a detected conflict. Persistent, auditable, never transient. |
| **Authorization Model** | Role → Permission → Action → Resource. Enforces segregation of duties. |

---

## Actors

### Actor 1: Regulatory Official (Human or AI Agent)

| Attribute | Description |
| :--- | :--- |
| **Actor** | The Regulatory Official (Human or AI Agent) |
| **Acts On Behalf Of** | The Regulatory Authority |
| **Role** | The Rule Author & Governance Owner |
| **Core Mission** | Creates, modifies, retires, and governs regulatory directives. |
| **Responsibilities** | Submits, modifies, retires, and reviews directives. Reviews consistency, audits the ruleset, manages versions, restores revisions, reviews remediation evidence, authorizes finding dispositions. |
| **Non-Responsibilities** | Does NOT submit artifacts for inspection. |

### Actor 2: Compliance Representative (Human or System)

| Attribute | Description |
| :--- | :--- |
| **Actor** | The Compliance Representative (Human or System) |
| **Acts On Behalf Of** | The Regulated Entity |
| **Role** | The Compliance Seeker & Remediation Owner |
| **Core Mission** | Submits targets for inspection, addresses findings, demonstrates compliance. |
| **Responsibilities** | Submits artifacts for inspection. Views findings, acknowledges them, submits remediation evidence, requests reinspection. |
| **Non-Responsibilities** | Does NOT create, modify, or retire directives. Does NOT waive findings. |

---

## Epic 1: Directive Lifecycle

*The Regulatory Official manages the Directive Graph.*

| Story ID | Actor | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-01** | Regulatory Official | I want to submit a new regulatory directive using natural language, so that Selma creates a formal entry in the Directive Graph and compiles it into CG-IR. | **Given** I express a regulatory need in natural language. <br> **When** Selma processes it. <br> **Then** Selma drafts the directive, assigns an immutable identifier, records it in the Directive Graph, compiles it into CG-IR (with all AI outputs cached at the purity boundary), and performs a structural compliance review. <br> **And** the directive is created in "Draft" state with a defined scope. | **P0** |
| **S-02** | Regulatory Official | I want to modify an existing directive, so that Selma updates the Directive Graph and recompiles affected CG-IR nodes. | **Given** I specify a directive identifier and describe the modification. <br> **When** Selma processes it. <br> **Then** Selma creates a new revision in the Directive Graph, recompiles affected control nodes into CG-IR, re-assesses for consistency, and records the revision with full provenance. <br> **And** the directive identifier remains unchanged. <br> **And** a new Ruleset Version (CG-IR hash) is generated. | **P0** |
| **S-03** | Regulatory Official | I want to retire a directive, so that it is removed from active enforcement while preserving the audit trail. | **Given** I specify a directive to retire. <br> **When** Selma processes it. <br> **Then** Selma transitions the directive to "Retired" state, records the reason, preserves the history, removes it from the active set, and generates a new CG-IR snapshot. | **P1** |

---

## Epic 2: Directive Governance

*The Regulatory Official manages the lifecycle, history, and consistency of the Directive Graph.*

| Story ID | Actor | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-04** | Regulatory Official | I want to view all active regulatory requirements, so that I know what is currently enforced. | **Given** I request active requirements. <br> **When** Selma processes it. <br> **Then** Selma returns all active directives and their compiled control nodes from the current CG-IR snapshot. | **P0** |
| **S-05** | Regulatory Official | I want to inspect the regulatory set for internal conflicts, so that I can resolve contradictions before external compliance is affected. | **Given** I request a consistency review. <br> **When** Selma processes it. <br> **Then** Selma assesses the CG-IR and issues a report with Conflict Artifacts detailing conflicts and required corrections. | **P1** |
| **S-06** | Regulatory Official | I want a comprehensive audit of my regulatory set, so that I understand gaps and redundancies. | **Given** I request a full audit. <br> **When** Selma processes it. <br> **Then** Selma generates an audit report highlighting deficiencies, redundancies, logical gaps, and remedial measures. | **P2** |
| **S-07** | Regulatory Official | I want to view the revision history of any directive, so that I can trace its evolution. | **Given** I request directive history. <br> **When** Selma processes it. <br> **Then** Selma provides a full revision log with timestamps, originator, changes, and the directive identifier remains constant. | **P1** |
| **S-08** | Regulatory Official | I want to restore a directive to a previous revision, so that I can revert unintended changes. | **Given** I specify a directive and target revision. <br> **When** Selma processes it. <br> **Then** Selma creates a new revision copying the target, recompiles affected CG-IR nodes, records the restoration with provenance, and documents the reason. | **P1** |
| **S-09** | Regulatory Official | I want to preview the impact of changes before they are finalized. | **Given** I request a change. <br> **When** Selma generates the proposed update. <br> **Then** Selma shows a side-by-side comparison of current vs proposed CG-IR and requires formal confirmation. | **P2** |

---

## Epic 3: Inspection

*The Compliance Representative submits targets for inspection against CG-IR snapshots.*

| Story ID | Actor | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-10** | Compliance Representative | I want to submit a target for inspection against active controls, so that I can identify deviations. | **Given** I provide a target and optionally specify controls. <br> **When** Selma processes it. <br> **Then** Selma executes the DAG evaluation pipeline against the current CG-IR snapshot: Normalize → Classify → Select Nodes → Topological Evaluate → Aggregate Findings → Generate Report. <br> **And** Selma records: target_hash, ruleset_version (CG-IR hash), engine_version, pipeline_trace, skipped_nodes. <br> **And** failed nodes produce NeedsReview findings; other nodes continue. | **P0** |
| **S-15** | Compliance Representative | I want to reinspect a target against the latest directives, so that I can detect new findings from regulatory changes. | **Given** I specify a previously inspected target. <br> **When** Selma processes it. <br> **Then** Selma reads the target (computing new target_hash), creates a new Inspection against the current CG-IR, and produces a new Report. <br> **And** the original inspection remains immutable. | **P1** |
| **S-16** | Compliance Representative | I want Selma to explain why a finding was raised. | **Given** I request an explanation for a finding. <br> **When** Selma processes it. <br> **Then** Selma traverses the causal chain (Finding → Control Node → Directive → Revision → Scope), highlights relevant target portions, explains the reasoning, and suggests corrective actions. | **P1** |

---

## Epic 4: Finding Management

*The Compliance Representative tracks findings through remediation. Findings are immutable events; remediation is mutable.*

| Story ID | Actor | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-11** | Compliance Representative | I want to view all findings, so that I understand my compliance posture. | **Given** I request findings for a domain. <br> **When** Selma processes it. <br> **Then** Selma returns findings with computed lifecycle_status (Open/Closed), computed disposition (Valid/Invalid/Waived), severity, the inspection, and associated control node. | **P0** |
| **S-12** | Compliance Representative | I want to acknowledge a finding so remediation begins. | **Given** I specify a finding. <br> **When** I acknowledge it. <br> **Then** Selma creates a Remediation record, sets status to "In Progress," and records the timestamp and actor. <br> **And** the finding event log is unchanged. | **P1** |
| **S-13** | Compliance Representative | I want to submit evidence that a finding has been corrected. | **Given** I specify a finding and provide evidence. <br> **When** Selma processes it. <br> **Then** Selma attaches evidence to the remediation record, updates status to "Pending Verification," and records the submission. <br> **And** the finding event log is unchanged. | **P1** |
| **S-14** | Regulatory Official | I want to review remediation evidence so I can close or reopen findings. | **Given** I request pending reviews. <br> **When** Selma presents evidence. <br> **Then** I can approve (append FindingClosed event, disposition Valid) or reject (append DispositionChanged event). <br> **And** the finding event log is append-only. | **P1** |

---

## Story Summary

| Epic | P0 | P1 | P2 | Total |
| :--- | :--- | :--- | :--- | :--- |
| Directive Lifecycle | 2 | 1 | 0 | **3** |
| Directive Governance | 1 | 3 | 1 | **5** |
| Inspection | 1 | 2 | 0 | **3** |
| Finding Management | 1 | 3 | 0 | **4** |
| **Total** | **5** | **9** | **1** | **15** |

---

## Traceability

| Principle | Stories |
| :--- | :--- |
| Rule Creation & Maintenance | S-01, S-02, S-03 |
| Directive Governance & Versioning | S-04, S-07, S-08, S-09 |
| Consistency & Conflict Detection | S-05, S-06 |
| Inspection of External Targets | S-10, S-15 |
| Finding Explainability | S-16 |
| Finding Lifecycle Management | S-11, S-12, S-13, S-14 |
| Deterministic Reproducibility | S-10 |
| Event-Sourced Findings | S-11, S-12, S-13, S-14 |
| DAG Execution with Failure Handling | S-10 |

---

## System Invariants

| Invariant | Description |
| :--- | :--- |
| **Compile-Time Purity** | All non-determinism resolved before CG-IR publication. CG-IR is fully deterministic. |
| **CG-IR Immutability** | Once published, CG-IR is immutable. Changes produce new snapshots with new hashes. |
| **Finding Event Immutability** | Finding event logs are append-only. No events modified or deleted. |
| **Inspection Immutability** | Completed inspections are never modified. |
| **Directive ID Immutability** | Directive identifiers never change across revisions. |
| **Ruleset Version Anchoring** | Every inspection references the exact CG-IR hash used. |
| **Causal Traceability** | Every finding traces: Finding → Control Node → Directive → Revision → Scope. |
| **Segregation of Duties** | Directive creator ≠ Finding waiver. |
| **No Feedback Loops** | Findings never influence future CG-IR compilation. |
| **DAG Acyclicity** | CG-IR dependency graph is acyclic. Enforced at compile time. |
| **Time Consistency** | All timestamps are event time. |

---

## The Internal View (For Implementation)

The user interacts with Selma as a single unified authority. Internally, Selma has six engines—this is an implementation detail never exposed to the user:

| Engine | What It Does |
| :--- | :--- |
| **Directive Drafting Engine** | Translates natural language into structured Directive Graph entries. |
| **Structural Compliance Reviewer** | Validates Directive Graph against schema and contamination rules. |
| **Control Compilation Engine** | Compiles Directive Graph into CG-IR. Enforces compile-time purity boundary. Caches AI outputs. |
| **DAG Evaluation Engine** | Executes CG-IR as a DAG: topological sort, parallel evaluation, failure handling, finding generation. |
| **Conflict Resolution Engine** | Detects conflicts, creates Conflict Artifacts, applies resolution rules, escalates when needed. |
| **Provenance Manager** | Tracks all versions, revisions, and restoration. Maintains causal traceability graph. |
