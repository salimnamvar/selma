# Selma — Unified User Stories

**Project:** Selma — Rule Regularity Platform  
**Version:** 15.0  
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
│   - Human-authored rules    │
│   - Structured metadata     │
│   - Versioned as artifact   │
└──────────────┬──────────────┘
               │ compile (hermetic boundary)
               ▼
┌─────────────────────────────┐
│   2. Compiled Control DAG   │
│   (= CG-IR)                 │
│   - Content-addressed       │
│   - Incremental snapshots   │
│   - Frozen at publish time  │
└──────────────┬──────────────┘
               │ evaluate (pure functions)
               ▼
┌─────────────────────────────┐
│   3. Finding Event Stream   │
│   - Append-only events      │
│   - Computed state          │
│   - Read-only analytics     │
│   - Mediated feedback       │
└─────────────────────────────┘
```

---

## Key Concepts

| Concept | Definition |
| :--- | :--- |
| **Directive Graph** | The human-authored source-of-truth specification. Structured, versioned, diffable. Contains directives, scope, priority, prose sections, and metadata. |
| **Compiled Control DAG (CG-IR)** | The immutable executable intermediate representation. All directives compile into it. Content-addressed (Ruleset Version = SHA-256 hash). Supports incremental snapshots—only changed nodes get new versions. |
| **Finding Event Stream** | The append-only audit log of all findings. Provides read-only analytics. Informs human-driven policy evolution through mediated feedback (never direct CG-IR modification). |
| **Hermetic Compilation Boundary** | The boundary between Directive Graph and CG-IR. The entire compilation environment is frozen (engine version, model weights, system prompts, toolchain). Ensures reproducibility. |
| **Frozen Environment** | The pinned compilation environment recorded in CG-IR provenance. Required for reproducibility of both CG-IR and inspections. |
| **Control Node** | A node in the CG-IR DAG. Represents a testable condition with a pure evaluator function, scope, severity, and dependencies. |
| **Evaluator Function** | `evaluate(node, target, context) → {outcome, confidence, evidence, reasoning}`. A pure function: no IO, no randomness, no side effects. |
| **Context Object** | Read-only input to evaluators containing target metadata, domain constants, and pre-computed finding aggregates. Enables state-dependent rules without breaking purity. |
| **Finding Aggregates** | Pre-computed statistics from the Finding Event Stream (open finding counts, recurrence counts, severity distributions). Fed into the context object at inspection time. |
| **Incremental Compilation** | Delta CG-IR snapshots that reuse unchanged subgraphs. Only modified nodes and their dependents get new versions. |
| **Mediated Feedback** | The auditable process where analytics inform humans, humans modify directives, and new CG-IR is compiled. No direct finding → CG-IR path. |
| **Directive Revision** | A versioned change to a directive. The directive identifier never changes; only the revision increments. |
| **Control Version** | The version of a control node's evaluation logic. Increments on directive change, logic change, or scope change. |
| **Ruleset Version** | Content-addressed hash of CG-IR. Immutable once published. |
| **Inspection** | An execution event: DAG evaluation of a target against a CG-IR snapshot. Records target hash, CG-IR hash, frozen_env hash, engine version, and full pipeline trace. |
| **Finding** | An immutable event in the Finding Event Stream. Current state is computed by replaying events. Three dimensions: lifecycle (Open/Closed), disposition (Valid/Invalid/Waived), severity (Critical/High/Medium/Low/Informational). |
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
| **Responsibilities** | Submits, modifies, retires, and reviews directives. Reviews consistency, audits the ruleset, manages versions, restores revisions, reviews remediation evidence, authorizes finding dispositions. Reviews analytics and drives mediated feedback. |
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
| **S-01** | Regulatory Official | I want to submit a new directive using natural language, so that Selma creates a Directive Graph entry and compiles it into CG-IR. | **Given** I express a regulatory need. <br> **When** Selma processes it. <br> **Then** Selma drafts the directive, assigns an immutable identifier, records it in the Directive Graph, compiles it into CG-IR using a hermetic frozen environment, and performs a structural review. <br> **And** the directive is in "Draft" state with a defined scope. | **P0** |
| **S-02** | Regulatory Official | I want to modify an existing directive, so that Selma updates the Directive Graph and incrementally recompiles affected CG-IR nodes. | **Given** I specify a directive and describe the change. <br> **When** Selma processes it. <br> **Then** Selma creates a new revision, recompiles only affected nodes and their dependents (reusing unchanged subgraph), re-assesses consistency, and records provenance. <br> **And** the directive identifier remains unchanged. <br> **And** a new Ruleset Version is generated. | **P0** |
| **S-03** | Regulatory Official | I want to retire a directive, so that it is removed from active enforcement while preserving the audit trail. | **Given** I specify a directive to retire. <br> **When** Selma processes it. <br> **Then** Selma transitions to "Retired" state, records the reason, preserves history, marks affected CG-IR nodes as deprecated, and generates a new snapshot. | **P1** |

---

## Epic 2: Directive Governance

*The Regulatory Official manages the lifecycle, history, and consistency of the Directive Graph.*

| Story ID | Actor | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-04** | Regulatory Official | I want to view all active requirements, so that I know what is currently enforced. | **Given** I request active requirements. <br> **When** Selma processes it. <br> **Then** Selma returns all active directives and their compiled control nodes from the current CG-IR snapshot. | **P0** |
| **S-05** | Regulatory Official | I want to inspect the regulatory set for internal conflicts. | **Given** I request a consistency review. <br> **When** Selma processes it. <br> **Then** Selma assesses the CG-IR and issues a report with Conflict Artifacts. | **P1** |
| **S-06** | Regulatory Official | I want a comprehensive audit of my regulatory set. | **Given** I request a full audit. <br> **When** Selma processes it. <br> **Then** Selma generates an audit report highlighting gaps, redundancies, and remedial measures. | **P2** |
| **S-07** | Regulatory Official | I want to view the revision history of any directive. | **Given** I request directive history. <br> **When** Selma processes it. <br> **Then** Selma provides a full revision log with timestamps, originator, changes. Identifier remains constant. | **P1** |
| **S-08** | Regulatory Official | I want to restore a directive to a previous revision. | **Given** I specify a directive and target revision. <br> **When** Selma processes it. <br> **Then** Selma creates a new revision copying the target, recompiles affected nodes, records provenance. | **P1** |
| **S-09** | Regulatory Official | I want to preview the impact of changes before they are finalized. | **Given** I request a change. <br> **When** Selma generates the proposal. <br> **Then** Selma shows current vs proposed CG-IR and requires confirmation. | **P2** |

---

## Epic 3: Inspection

*The Compliance Representative submits targets for inspection against CG-IR snapshots.*

| Story ID | Actor | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-10** | Compliance Representative | I want to submit a target for inspection against active controls. | **Given** I provide a target. <br> **When** Selma processes it. <br> **Then** Selma populates the context object (target metadata, domain constants, finding aggregates), executes the DAG evaluation pipeline, and produces findings. <br> **And** Selma records: target_hash, ruleset_version, frozen_env_hash, engine_version, pipeline_trace, skipped_nodes. <br> **And** failed nodes produce NeedsReview findings; others continue. | **P0** |
| **S-15** | Compliance Representative | I want to reinspect a target against the latest directives. | **Given** I specify a previously inspected target. <br> **When** Selma processes it. <br> **Then** Selma reads the target (new target_hash), creates a new Inspection against current CG-IR, produces a new Report. <br> **And** original inspection remains immutable. | **P1** |
| **S-16** | Compliance Representative | I want Selma to explain why a finding was raised. | **Given** I request an explanation. <br> **When** Selma processes it. <br> **Then** Selma traverses the causal chain (Finding → Control Node → Directive → Revision → Scope), highlights relevant target portions, explains reasoning. | **P1** |

---

## Epic 4: Finding Management

*The Compliance Representative tracks findings through remediation. Findings are immutable events; remediation is mutable.*

| Story ID | Actor | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-11** | Compliance Representative | I want to view all findings, so that I understand my compliance posture. | **Given** I request findings. <br> **When** Selma processes it. <br> **Then** Selma returns findings with computed lifecycle_status, computed disposition, severity, inspection reference, and associated control node. | **P0** |
| **S-12** | Compliance Representative | I want to acknowledge a finding so remediation begins. | **Given** I specify a finding. <br> **When** I acknowledge it. <br> **Then** Selma creates a Remediation record, sets status to "In Progress," records timestamp and actor. <br> **And** finding event log is unchanged. | **P1** |
| **S-13** | Compliance Representative | I want to submit evidence that a finding has been corrected. | **Given** I specify a finding and provide evidence. <br> **When** Selma processes it. <br> **Then** Selma attaches evidence, updates status to "Pending Verification," records submission. <br> **And** finding event log is unchanged. | **P1** |
| **S-14** | Regulatory Official | I want to review remediation evidence so I can close or reopen findings. | **Given** I request pending reviews. <br> **When** Selma presents evidence. <br> **Then** I can approve (append FindingClosed event) or reject (append DispositionChanged event). <br> **And** finding event log is append-only. | **P1** |

---

## Epic 5: Analytics & Mediated Feedback

*The Regulatory Official reviews analytics from the Finding Event Stream and drives policy evolution through the standard Directive Graph path.*

| Story ID | Actor | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-17** | Regulatory Official | I want to view analytics on finding patterns, so that I can identify systemic issues. | **Given** I request analytics for a domain. <br> **When** Selma processes it. <br> **Then** Selma returns read-only aggregate views: finding rates over time, severity distributions, recurrence patterns, compliance trends. <br> **And** analytics are derived from the Finding Event Stream without modifying CG-IR. | **P1** |
| **S-18** | Regulatory Official | I want to propose a directive change based on analytics findings, so that I can close systemic gaps. | **Given** I review analytics and decide to modify a directive. <br> **When** I submit the change via the standard Directive Lifecycle (S-02). <br> **Then** Selma records the analytics provenance on the directive revision (linking the change to its triggering analysis). <br> **And** the change follows the normal Directive Graph → CG-IR compilation path. | **P2** |

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
| Rule Creation & Maintenance | S-01, S-02, S-03 |
| Directive Governance & Versioning | S-04, S-07, S-08, S-09 |
| Consistency & Conflict Detection | S-05, S-06 |
| Inspection with State-Dependent Context | S-10 |
| Reinspection | S-15 |
| Finding Explainability | S-16 |
| Finding Lifecycle Management | S-11, S-12, S-13, S-14 |
| Incremental Compilation | S-02, S-03 |
| Hermetic Reproducibility | S-10 |
| Event-Sourced Findings | S-11, S-12, S-13, S-14 |
| Analytics & Mediated Feedback | S-17, S-18 |
| DAG Execution with Failure Handling | S-10 |

---

## System Invariants

| Invariant | Description |
| :--- | :--- |
| **Hermetic Compilation** | CG-IR reproducibility requires pinned frozen_env. Environment drift breaks reproducibility. |
| **CG-IR Immutability** | Once published, CG-IR is immutable. Changes produce new snapshots. |
| **Finding Event Immutability** | Finding event logs are append-only. No events modified or deleted. |
| **Inspection Immutability** | Completed inspections are never modified. |
| **Directive ID Immutability** | Directive identifiers never change across revisions. |
| **Ruleset Version Anchoring** | Every inspection references the exact CG-IR hash used. |
| **Causal Traceability** | Every finding traces: Finding → Control Node → Directive → Revision → Scope. |
| **Segregation of Duties** | Directive creator ≠ Finding waiver. |
| **DAG Acyclicity** | CG-IR dependency graph is acyclic. Enforced at compile time. |
| **Evaluator Purity** | Evaluators are pure functions: no IO, no randomness, no side effects. |
| **Mediated Feedback** | Analytics inform humans; humans modify directives; no direct finding → CG-IR path. |
| **Time Consistency** | All timestamps are event time. |

---

## The Internal View (For Implementation)

The user interacts with Selma as a single unified authority. Internally, Selma has seven engines—this is an implementation detail never exposed to the user:

| Engine | What It Does |
| :--- | :--- |
| **Directive Drafting Engine** | Translates natural language into structured Directive Graph entries. |
| **Structural Compliance Reviewer** | Validates Directive Graph against schema and contamination rules. |
| **Control Compilation Engine** | Compiles Directive Graph into CG-IR using hermetic frozen environment. Supports incremental compilation. Caches AI outputs. |
| **DAG Evaluation Engine** | Executes CG-IR as a DAG: topological sort, parallel evaluation, context population from Finding Event Stream, failure handling, finding generation. |
| **Conflict Resolution Engine** | Detects conflicts, creates Conflict Artifacts, applies resolution rules, escalates when needed. |
| **Provenance Manager** | Tracks all versions, revisions, restoration, and frozen environment hashes. Maintains causal traceability graph. |
| **Analytics Engine** | Computes read-only aggregates from Finding Event Stream. Feeds context object. Provides dashboards. Never modifies CG-IR. |
