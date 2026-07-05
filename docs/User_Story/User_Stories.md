# Selma — Unified User Stories

**Project:** Selma — Rule Regularity Platform  
**Version:** 8.0  
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
    Applies regulations
    Detects findings
    Produces inspection reports
    Tracks remediation
```

The user interacts with Selma as a single unified authority—not a collection of tools. Selma handles all standardization, validation, and inspection automatically.

---

## Actors

### Actor 1: Regulatory Authority (Human or AI Agent)

| Attribute | Description |
| :--- | :--- |
| **Actor** | The Regulatory Authority (Human or AI Agent) |
| **Role** | The Rule Author & Governance Owner |
| **Core Mission** | Creates, modifies, retires, and governs regulatory directives. |
| **Responsibilities** | Submits, modifies, retires, and reviews regulatory directives via natural language or structured requests. Reviews consistency, audits the ruleset, manages versions, and restores revisions. |
| **Non-Responsibilities** | Does NOT submit artifacts for inspection. Selma handles all structural compliance reviews, consistency assessments, and corrective feedback automatically. |

### Actor 2: Regulated Entity (Human or System)

| Attribute | Description |
| :--- | :--- |
| **Actor** | The Regulated Entity (Human or System) |
| **Role** | The Compliance Seeker & Remediation Owner |
| **Core Mission** | Submits targets for inspection, addresses findings, and demonstrates compliance. |
| **Responsibilities** | Submits artifacts (documents, code, files, contexts) for inspection. Views findings, acknowledges them, submits remediation evidence, and requests reinspection. |
| **Non-Responsibilities** | Does NOT create, modify, or retire regulatory directives. |

---

## Epic 1: Regulatory Directive Submission

*The Regulatory Authority submits, modifies, or retires regulatory directives.*

| Story ID | Actor | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-01** | Regulatory Authority | I want to submit a new regulatory directive using natural language, so that Selma creates a formal standardized entry for both the official directive and the executable representation. | **Given** I express a regulatory need in natural language. <br> **When** Selma processes it. <br> **Then** Selma drafts the formal directive, assigns a unique identifier, records it in the official policy register and the executable representation, and automatically performs a structural compliance review before finalizing. | **P0** |
| **S-02** | Regulatory Authority | I want to modify an existing regulatory directive, so that Selma updates both the official directive and the executable representation simultaneously. | **Given** I specify a directive identifier and describe the modification. <br> **When** Selma processes it. <br> **Then** Selma updates the official directive, re-inspects for structural compliance, re-assesses for regulatory consistency, and records the revision with full change provenance. | **P0** |
| **S-03** | Regulatory Authority | I want to retire a regulatory directive from active enforcement, so that it is no longer applicable while preserving the historical audit trail. | **Given** I specify a directive to retire. <br> **When** Selma processes it. <br> **Then** Selma formally retires the directive, records the retirement reason, preserves the historical record, and removes it from the active requirements set. | **P1** |

---

## Epic 2: Regulatory Inspection & Compliance Review

*The Regulatory Authority reviews the ruleset for consistency. The Regulated Entity submits targets for inspection.*

| Story ID | Actor | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-04** | Regulatory Authority | I want to view all active regulatory requirements for my domain, so that I know what is currently expected and enforced. | **Given** I request the active requirements for my domain. <br> **When** Selma processes it. <br> **Then** Selma returns all active directives in both a formal reference format and an executable representation suitable for enforcement. | **P0** |
| **S-05** | Regulatory Authority | I want to inspect the regulatory set itself for internal conflicts, so that I can resolve contradictions before they affect external compliance. | **Given** I request a regulatory consistency review. <br> **When** Selma processes it. <br> **Then** Selma conducts a full assessment of the ruleset and issues a formal report detailing identified conflicts, contradictions, and required corrective actions. | **P1** |
| **S-06** | Regulatory Authority | I want to receive a comprehensive audit of my entire regulatory set, so that I understand redundancies, gaps, and circular dependencies. | **Given** I request a full compliance audit. <br> **When** Selma processes it. <br> **Then** Selma generates a formal audit report highlighting deficiencies, redundancies, logical gaps, and required remedial measures. | **P2** |
| **S-10** | Regulated Entity | I want to submit a target (document, code, file, or any information format) for inspection against my active directives, so that I can identify deviations and receive corrective recommendations. | **Given** I provide a target and optionally specify which rules to apply. <br> **When** Selma processes it. <br> **Then** Selma reads the target, applies the applicable rules, identifies deviations, and produces a formal inspection report with findings and corrective recommendations. | **P0** |
| **S-15** | Regulated Entity | I want to reinspect a previously inspected target against the latest active directives, so that I can determine whether regulatory changes introduce new findings. | **Given** I specify a previously inspected target. <br> **When** Selma processes it. <br> **Then** Selma re-inspects the target against the current active directives and produces a new inspection report, preserving the original inspection as immutable history. | **P1** |

---

## Epic 3: Regulatory Revision History & Provenance

*The Regulatory Authority manages the lifecycle, history, and restoration of regulatory directives.*

| Story ID | Actor | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-07** | Regulatory Authority | I want to view the complete revision history of any directive, so that I can trace its evolution and understand past decisions. | **Given** I request the history of a directive. <br> **When** Selma processes it. <br> **Then** Selma provides a full revision log with timestamps, originator, nature of each change, and summary of modifications. | **P1** |
| **S-08** | Regulatory Authority | I want to restore a directive to a previous revision, so that I can undo unintended changes or revert to a previously validated state. | **Given** I specify a directive identifier and a target revision. <br> **When** Selma processes it. <br> **Then** Selma restores the directive to the specified revision, records the restoration in the change provenance, and documents the reason for the restoration. | **P1** |
| **S-09** | Regulatory Authority | I want to preview the impact of changes before they are finalized, so that I can review and approve them before they become effective. | **Given** I request a change. <br> **When** Selma generates the proposed update. <br> **Then** Selma presents a side-by-side comparison of the current and proposed revisions and requires formal confirmation before the changes are recorded. | **P2** |

---

## Epic 4: Finding Management

*The Regulated Entity tracks findings from inspection through remediation and closure.*

| Story ID | Actor | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **S-11** | Regulated Entity | I want to view all inspection findings so that I can understand my current compliance posture. | **Given** I request my findings for a domain. <br> **When** Selma processes it. <br> **Then** Selma returns all findings with their current status (Open, Accepted, In Progress, Resolved, Rejected, Waived, Expired), the inspection that produced them, and the associated directive. | **P0** |
| **S-12** | Regulated Entity | I want to acknowledge a finding so that Selma records that remediation has begun. | **Given** I specify a finding identifier. <br> **When** I acknowledge it. <br> **Then** Selma updates the finding status to "Accepted" or "In Progress" and records the acknowledgment timestamp and actor. | **P1** |
| **S-13** | Regulated Entity | I want to submit evidence that a finding has been corrected so that Selma can verify the remediation. | **Given** I specify a finding identifier and provide remediation evidence. <br> **When** Selma processes it. <br> **Then** Selma attaches the evidence to the finding, updates the status to "Resolved" (pending verification), and records the submission. | **P1** |
| **S-14** | Regulatory Authority | I want to review submitted remediation evidence so that I can close or reopen findings. | **Given** I request pending remediation reviews. <br> **When** Selma presents the evidence. <br> **Then** I can approve (close the finding) or reject (reopen with comments). <br> **And** Selma records the decision, the reviewer, and the timestamp. | **P1** |

---

## Story Summary

| Epic | P0 | P1 | P2 | Total |
| :--- | :--- | :--- | :--- | :--- |
| Regulatory Directive Submission | 2 | 1 | 0 | **3** |
| Regulatory Inspection & Compliance Review | 2 | 2 | 1 | **5** |
| Regulatory Revision History & Provenance | 0 | 2 | 1 | **3** |
| Finding Management | 1 | 3 | 0 | **4** |
| **Total** | **5** | **8** | **2** | **15** |

---

## Traceability to Regulatory Principles

| Regulatory Principle | Supporting Stories |
| :--- | :--- |
| **Rule Creation & Maintenance** | S-01, S-02, S-03 |
| **Automatic Compliance Verification** | S-01, S-02 |
| **Inspection of External Targets** | S-10, S-15 |
| **Meta-Inspection (Ruleset Consistency)** | S-05, S-06 |
| **Provenance & Audit Trail** | S-07 |
| **Corrective Action & Restoration** | S-08 |
| **Finding Lifecycle Management** | S-11, S-12, S-13, S-14 |
| **Reinspection After Regulatory Change** | S-15 |

---

## The Internal View (For Implementation)

The user interacts with Selma as a single, unified regulatory authority. Internally, Selma is composed of five engines—this is purely an implementation detail and is **never exposed** to the user:

| Internal Engine | What It Does | Exposed to User? |
| :--- | :--- | :--- |
| **Directive Drafting Engine** | Translates natural language into formal directives and executable representations. | ❌ No. The user just "submits a directive." |
| **Structural Compliance Reviewer** | Checks that directives are correctly formatted, structured, and free of contamination. | ❌ No. The user just "submits" and it passes automatically. |
| **Regulatory Consistency Assessor** | Detects conflicts, contradictions, and circular dependencies *within the ruleset*. | ❌ No. The user simply "requests an inspection" of the ruleset and receives the report. |
| **External Inspection Engine** | Reads any target (document, code, file, context) and applies active rules to identify deviations. | ❌ No. The user just "submits a target" and receives the inspection report. |
| **Revision & Provenance Manager** | Tracks all changes, versions, and restorations. | ❌ No. The user just "views history" or "restores" a directive. |
