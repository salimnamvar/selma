# Selma — Unified User Stories

**Project:** Selma — Rule Regularity Platform  
**Version:** 12.0  
**Date:** 2026-07-05  
**Status:** Final  

> **Note:** Selma is domain-agnostic. It can serve financial compliance, environmental standards, organizational governance, software engineering, or any other regulatory domain.

---

## Core Architecture

Selma is a unified regulatory platform built on two authorities:

```
Selma

├── Regulatory Authority
│
│   Creates regulations
│   Updates regulations
│   Retires regulations
│   Reviews consistency
│   Publishes active directives
│
└── Inspection Authority
    Receives targets
    Applies controls
    Detects findings
    Produces inspection reports
    Tracks remediation
```

---

## Key Concepts

| Concept | Definition |
| :--- | :--- |
| **Directive** | A formal regulatory requirement issued by the Regulatory Authority. Each directive has an immutable identifier (e.g., `REG-024`) and a lifecycle state (Draft → Review → Approved → Active → Deprecated → Retired). |
| **Directive Revision** | A versioned change to a directive. The directive identifier never changes; only the revision increments. |
| **Directive Scope** | The applicability context of a directive: domain, jurisdiction, context filters, and applicability rules that determine which targets the directive applies to. |
| **Control** | A testable condition derived from a directive. A single directive may produce multiple controls. Controls are the units evaluated during inspection. Controls are versioned independently of directives—allowing control logic to evolve without directive edits. |
| **Control Derivation** | The process of transforming a directive into testable controls. Derivation can be deterministic (fixed rules), AI-assisted (LLM interpretation), or hybrid. Each derivation produces a Control Version independent of the Directive Revision. |
| **Control Version** | The version of a control's evaluation logic. A directive revision may or may not produce a new control version, and a control version may change without a directive revision. |
| **Executable Representation** | A normalized constraint graph derived from controls, evaluated by the Inspection Authority. Its implementation is internal to Selma and independent of any particular execution technology. |
| **Evaluation Semantics** | The rule by which a control resolves against a target. Each control produces one of: Pass, Fail, Partial, Needs Review, or Ambiguous. Evaluation semantics may be deterministic (rule engine) or probabilistic (AI judgment) depending on the control type. |
| **Ruleset** | The set of all active directives (and their derived controls) for a domain, identified by a version number. A ruleset version pins both directive versions and control versions. |
| **Ruleset Version** | An immutable snapshot of all active directives and their derived controls at a point in time. Once created, never modified. |
| **Inspection** | An execution event: the evaluation of a target against a specific ruleset version. Each inspection is immutable once completed and references the exact ruleset version used. |
| **Inspection Pipeline** | The sequence: Target → Normalize → Classify → Select Controls → Evaluate → Aggregate Findings → Generate Report. |
| **Inspection Report** | A rendered artifact produced from inspection findings. Reports can be regenerated, reformatted, or viewed in multiple formats (legal, technical, executive) without rerunning the inspection. |
| **Target** | Any external artifact submitted for inspection (document, code, file, context, or any information format). |
| **Finding** | An immutable record of a deviation detected during inspection. **Finding Invariant:** Findings are permanent records—once created, they are never modified. A finding has three independent dimensions: lifecycle status (Open / Closed), disposition (Valid / Invalid / Waived), and severity (Critical / High / Medium / Low / Informational). Disposition changes are recorded as events on the finding's event log; remediation is tracked separately. |
| **Finding Causal Chain** | The traceability graph linking a finding back through its origin: Finding → Control → Directive → Revision → Scope. This chain enables impact analysis ("which findings are affected by a rule change?") and explainability ("why was this finding raised?"). |
| **Remediation** | A mutable record of corrective action taken in response to a finding. **Remediation Invariant:** Remediation is always attached to an immutable finding and never modifies the finding itself. Remediation has its own lifecycle: In Progress → Evidence Submitted → Pending Verification → Verified → Closed. |
| **Evidence** | Data submitted by the Compliance Representative to demonstrate that a finding has been corrected. |
| **Authorization Model** | The permission framework governing who can perform which actions on which resources. Roles (Regulatory Official, Compliance Representative) map to permissions (create directive, view findings, approve remediation, waive finding) via a Role → Permission → Action → Resource model. |
| **Conflict Resolution** | The runtime mechanism for resolving contradictory directives or controls. Applies Priority Hierarchy, specificity rules, and temporal precedence. Unresolved conflicts escalate to Regulatory Official. |

---

## Actors

### Actor 1: Regulatory Official (Human or AI Agent)

| Attribute | Description |
| :--- | :--- |
| **Actor** | The Regulatory Official (Human or AI Agent) |
| **Acts On Behalf Of** | The Regulatory Authority |
| **Role** | The Rule Author & Governance Owner |
| **Core Mission** | Creates, modifies, retires, and governs regulatory directives. |
| **Responsibilities** | Submits, modifies, retires, and reviews regulatory directives via natural language or structured requests. Defines controls derived from directives. Reviews consistency, audits the ruleset, manages versions, restores revisions, reviews remediation evidence, and authorizes finding dispositions. |
| **Non-Responsibilities** | Does NOT submit artifacts for inspection. Selma handles all structural compliance reviews, consistency assessments, and corrective feedback automatically. |

### Actor 2: Compliance Representative (Human or System)

| Attribute | Description |
| :--- | :--- |
| **Actor** | The Compliance Representative (Human or System) |
| **Acts On Behalf Of** | The Regulated Entity |
| **Role** | The Compliance Seeker & Remediation Owner |
| **Core Mission** | Submits targets for inspection, addresses findings, and demonstrates compliance. |
| **Responsibilities** | Submits artifacts (documents, code, files, contexts) for inspection. Views findings, acknowledges them, submits remediation evidence, and requests reinspection. |
| **Non-Responsibilities** | Does NOT create, modify, or retire regulatory directives. Does NOT waive findings (requires Regulatory Official authorization). |

---

## Epic 1: Directive Lifecycle

*The Regulatory Official submits, modifies, or retires regulatory directives.*

| Story ID | Actor | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-01** | Regulatory Official | I want to submit a new regulatory directive using natural language, so that Selma creates a formal standardized entry for both the official directive and the executable representation. | **Given** I express a regulatory need in natural language. <br> **When** Selma processes it. <br> **Then** Selma drafts the formal directive, assigns an immutable unique identifier, records it in the official policy register and the executable representation, and automatically performs a structural compliance review before finalizing. <br> **And** the directive is created in "Draft" state. <br> **And** the directive includes a scope defining its applicability context. | **P0** |
| **S-02** | Regulatory Official | I want to modify an existing regulatory directive, so that Selma updates both the official directive and the executable representation simultaneously. | **Given** I specify a directive identifier and describe the modification. <br> **When** Selma processes it. <br> **Then** Selma creates a new revision of the directive, updates the official directive, re-inspects for structural compliance, re-assesses for regulatory consistency, and records the revision with full change provenance. <br> **And** the directive identifier remains unchanged. <br> **And** affected controls are re-evaluated and versioned as needed. | **P0** |
| **S-03** | Regulatory Official | I want to retire a regulatory directive from active enforcement, so that it is no longer applicable while preserving the historical audit trail. | **Given** I specify a directive to retire. <br> **When** Selma processes it. <br> **Then** Selma transitions the directive to "Retired" state, records the retirement reason, preserves the historical record, and removes it from the active requirements set. | **P1** |

---

## Epic 2: Directive Governance

*The Regulatory Official manages the lifecycle, history, and restoration of regulatory directives.*

| Story ID | Actor | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-04** | Regulatory Official | I want to view all active regulatory requirements for my domain, so that I know what is currently expected and enforced. | **Given** I request the active requirements for my domain. <br> **When** Selma processes it. <br> **Then** Selma returns all active directives and their derived controls in both a formal reference format and an executable representation suitable for enforcement. | **P0** |
| **S-05** | Regulatory Official | I want to inspect the regulatory set itself for internal conflicts, so that I can resolve contradictions before they affect external compliance. | **Given** I request a regulatory consistency review. <br> **When** Selma processes it. <br> **Then** Selma conducts a full assessment of the ruleset and issues a formal report detailing identified conflicts, contradictions, and required corrective actions. | **P1** |
| **S-06** | Regulatory Official | I want to receive a comprehensive audit of my entire regulatory set, so that I understand redundancies, gaps, and circular dependencies. | **Given** I request a full compliance audit. <br> **When** Selma processes it. <br> **Then** Selma generates a formal audit report highlighting deficiencies, redundancies, logical gaps, and required remedial measures. | **P2** |
| **S-07** | Regulatory Official | I want to view the complete revision history of any directive, so that I can trace its evolution and understand past decisions. | **Given** I request the history of a directive. <br> **When** Selma processes it. <br> **Then** Selma provides a full revision log with timestamps, originator, nature of each change, and summary of modifications. <br> **And** the directive identifier remains constant across all revisions. | **P1** |
| **S-08** | Regulatory Official | I want to restore a directive to a previous revision, so that I can undo unintended changes or revert to a previously validated state. | **Given** I specify a directive identifier and a target revision. <br> **When** Selma processes it. <br> **Then** Selma creates a new revision that is a copy of the target revision, records the restoration in the change provenance, and documents the reason for the restoration. | **P1** |
| **S-09** | Regulatory Official | I want to preview the impact of changes before they are finalized, so that I can review and approve them before they become effective. | **Given** I request a change. <br> **When** Selma generates the proposed update. <br> **Then** Selma presents a side-by-side comparison of the current and proposed revisions and requires formal confirmation before the changes are recorded. | **P2** |

---

## Epic 3: Inspection

*The Compliance Representative submits targets for inspection against active controls.*

| Story ID | Actor | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-10** | Compliance Representative | I want to submit a target (document, code, file, or any information format) for inspection against my active controls, so that I can identify deviations and receive corrective recommendations. | **Given** I provide a target and optionally specify which controls to apply. <br> **When** Selma processes it. <br> **Then** Selma executes the inspection pipeline: Normalize → Classify → Select Controls → Evaluate → Aggregate Findings → Generate Report. <br> **And** Selma creates an Inspection record (Inspection ID, Target, Ruleset Version, Inspector, Date, Status). <br> **And** the inspection references the exact ruleset version used. | **P0** |
| **S-15** | Compliance Representative | I want to reinspect a previously inspected target against the latest active directives, so that I can determine whether regulatory changes introduce new findings. | **Given** I specify a previously inspected target. <br> **When** Selma processes it. <br> **Then** Selma reads the target again (in its current state) and creates a new Inspection record against the current active directives, producing a new Inspection Report. <br> **And** the original inspection remains immutable as historical record. | **P1** |
| **S-16** | Compliance Representative | I want Selma to explain why a finding was raised, so that I understand the applicable control, the evidence considered, and the reasoning behind the decision. | **Given** I request an explanation for a finding. <br> **When** Selma processes it. <br> **Then** Selma traverses the finding's causal chain (Finding → Control → Directive → Revision → Scope), highlights the relevant portions of the submitted target, explains the reasoning that led to the finding, and suggests corrective actions where appropriate. | **P1** |

---

## Epic 4: Finding Management

*The Compliance Representative tracks findings from inspection through remediation and closure. Findings are immutable; remediation is the mutable process attached to findings.*

| Story ID | Actor | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-11** | Compliance Representative | I want to view all inspection findings so that I can understand my current compliance posture. | **Given** I request my findings for a domain. <br> **When** Selma processes it. <br> **Then** Selma returns all findings with their lifecycle status (Open / Closed), disposition (Valid / Invalid / Waived), severity (Critical / High / Medium / Low / Informational), the inspection that produced them, and the associated control. | **P0** |
| **S-12** | Compliance Representative | I want to acknowledge a finding so that Selma records that remediation has begun. | **Given** I specify a finding identifier. <br> **When** I acknowledge it. <br> **Then** Selma creates a Remediation record linked to the finding, sets the remediation status to "In Progress," and records the acknowledgment timestamp and actor. <br> **And** the original finding remains unchanged. | **P1** |
| **S-13** | Compliance Representative | I want to submit evidence that a finding has been corrected so that Selma can verify the remediation. | **Given** I specify a finding identifier and provide remediation evidence. <br> **When** Selma processes it. <br> **Then** Selma attaches the evidence to the remediation record, updates the remediation status to "Pending Verification," and records the submission. <br> **And** the original finding remains unchanged. | **P1** |
| **S-14** | Regulatory Official | I want to review submitted remediation evidence so that I can close or reopen findings. | **Given** I request pending remediation reviews. <br> **When** Selma presents the evidence. <br> **Then** I can approve (set finding status to Closed, disposition to Valid) or reject (reopen with comments). <br> **And** Selma records the decision, the reviewer, and the timestamp. <br> **And** the original finding remains unchanged. | **P1** |

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

## Traceability to Regulatory Principles

| Regulatory Principle | Supporting Stories |
| :--- | :--- |
| **Rule Creation & Maintenance** | S-01, S-02, S-03 |
| **Automatic Compliance Verification** | S-01, S-02 |
| **Directive Governance & Versioning** | S-04, S-07, S-08, S-09 |
| **Meta-Inspection (Ruleset Consistency)** | S-05, S-06 |
| **Inspection of External Targets** | S-10, S-15 |
| **Finding Transparency & Explainability** | S-16 |
| **Finding Lifecycle Management** | S-11, S-12, S-13, S-14 |
| **Reinspection After Regulatory Change** | S-15 |
| **Severity & Prioritization** | S-11 |
| **Causal Traceability** | S-16 |
| **Authorization & Segregation of Duties** | S-14 |
| **Inspection Pipeline Execution** | S-10 |

---

## System Invariants

These rules must never be violated:

| Invariant | Description |
| :--- | :--- |
| **Finding Immutability** | Once created, a finding is never modified. Disposition changes are recorded as events on the finding's event log; remediation is tracked on a separate mutable record. |
| **Inspection Immutability** | Once completed, an inspection record is never modified. Reinspection creates a new inspection. |
| **Directive ID Immutability** | A directive's identifier never changes across revisions. Only the revision number increments. |
| **Ruleset Version Anchoring** | Every inspection references the exact ruleset version used. Historical inspections are never retroactively updated. |
| **Causal Traceability** | Every finding must be traceable through its causal chain: Finding → Control → Directive → Revision → Scope. |
| **Segregation of Duties** | The actor who creates a directive cannot be the same actor who waives a finding derived from it (requires separate authorization). |
| **Control Version Independence** | Control versions are independent of directive revisions. A control version may change without a directive revision. |
| **Pipeline Atomicity** | An inspection either produces all findings or fails entirely. No partial results. |

---

## The Internal View (For Implementation)

The user interacts with Selma as a single, unified regulatory authority. Internally, Selma is composed of seven engines—this is purely an implementation detail and is **never exposed** to the user:

| Internal Engine | What It Does | Exposed to User? |
| :--- | :--- | :--- |
| **Directive Drafting Engine** | Translates natural language into formal directives and executable representations. | ❌ No. The user just "submits a directive." |
| **Structural Compliance Reviewer** | Checks that directives are correctly formatted, structured, and free of contamination. | ❌ No. The user just "submits" and it passes automatically. |
| **Control Derivation Engine** | Transforms directives into testable controls via deterministic rules, AI inference, or hybrid methods. Versions controls independently of directives. | ❌ No. Controls are derived automatically when directives are created or modified. |
| **Regulatory Consistency Assessor** | Detects conflicts, contradictions, and circular dependencies *within the ruleset*. | ❌ No. The user simply "requests an inspection" of the ruleset and receives the report. |
| **Conflict Resolution Engine** | Applies Priority Hierarchy, specificity rules, and temporal precedence to resolve contradictory directives or controls. Escalates unresolved conflicts. | ❌ No. Conflicts are resolved automatically or escalated to the Regulatory Official. |
| **External Inspection Engine** | Executes the inspection pipeline: Normalize → Classify → Select Controls → Evaluate → Aggregate Findings → Generate Report. | ❌ No. The user just "submits a target" and receives the inspection report. |
| **Revision & Provenance Manager** | Tracks all changes, versions, and restorations. Maintains the causal traceability graph. | ❌ No. The user just "views history" or "restores" a directive. |
