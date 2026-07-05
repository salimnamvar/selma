# Selma — Unified User Stories
**Project:** Selma — Rule Regularity Platform
**Version:** 6.0
**Date:** 2026-07-05
**Status:** Final

> **Note:** Selma is domain-agnostic. It can serve financial compliance, environmental standards, organizational governance, software engineering, or any other regulatory domain.

---

## Foundational Interaction Assumptions

Selma operates as a unified regulatory platform with two integrated bodies:

1. **Regulatory Body**: The user defines, modifies, and retires directives (rules). Selma standardizes them for human and machine consumption.
2. **Inspection Body**: The user submits a target (document, code, book, file, context, or any information format). Selma applies the applicable rules to the target, identifies deviations, and produces a formal inspection report with findings and corrective recommendations.

The user interacts with Selma as a single unified authority—not a collection of tools. Selma handles all standardization, validation, and inspection automatically.

---

## Actor: The Regulated Entity (Human or AI Agent)

| Attribute | Description |
| :--- | :--- |
| **Actor** | The Regulated Entity (Human or AI Agent) |
| **Role** | The Rule Submitter & Compliance Seeker |
| **Core Mission** | Establishes and maintains regulatory directives for their domain |
| **What They Do** | Submits, modifies, retires, and reviews regulatory directives via natural language or structured requests (Selma handles both seamlessly) |
| **What They DON'T Do** | They do NOT perform compliance inspections, consistency assessments, or formatting reviews. Selma automatically handles all regulatory oversight, inspections, and corrective feedback. |

---

## The User's View of Selma

| The User's Need | What the User Does | What Selma Does Automatically |
| :--- | :--- | :--- |
| "I need a directive for X." | Expresses intent in natural language. | Drafts the formal rule, performs a structural compliance review, checks for regulatory conflicts, issues a compliance report, and records the revision. |
| "Change directive TRAF-001." | Requests a modification. | Updates the formal record, re-inspects for compliance, re-assesses for consistency, records the revision, and updates the change provenance. |
| "Retire directive TRAF-001." | Requests retirement. | Formally retires the directive, preserves the historical record, and removes it from active requirements. |
| "Show me the active directives." | Queries for requirements. | Returns the current active regulatory requirements in a standardized format. |
| "Are there any conflicts?" | Requests an inspection. | Conducts a regulatory consistency assessment and issues an advisory report with recommended corrective actions. |
| "Give me a full compliance audit." | Requests a comprehensive review. | Generates a detailed compliance audit report highlighting redundancies, gaps, circular dependencies, and required corrective actions. |

---

## Epic 1: Regulatory Directive Submission

*The user submits, modifies, or retires regulatory directives.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-01** | As a Regulated Entity, I want to submit a new regulatory directive using natural language, so that Selma creates a formal standardized entry for both official records and technical enforcement. | **Given** I express a regulatory need in natural language. <br> **When** Selma processes it. <br> **Then** Selma drafts the formal directive, assigns a unique identifier, records it in the official policy register and the technical requirements set, and automatically performs a structural compliance review before finalizing. | **P0** |
| **S-02** | As a Regulated Entity, I want to modify an existing regulatory directive, so that Selma updates both the official record and the technical requirements simultaneously. | **Given** I specify a directive identifier and describe the modification. <br> **When** Selma processes it. <br> **Then** Selma updates the official record, re-inspects for structural compliance, re-assesses for regulatory consistency, and records the revision with full change provenance. | **P0** |
| **S-03** | As a Regulated Entity, I want to retire a regulatory directive from active enforcement, so that it is no longer applicable while preserving the historical audit trail. | **Given** I specify a directive to retire. <br> **When** Selma processes it. <br> **Then** Selma formally retires the directive, records the retirement reason, preserves the historical record, and removes it from the active requirements set. | **P1** |

---

## Epic 2: Regulatory Inspection & Compliance Review

*The user requests inspections of external targets, conflict assessments, and full compliance audits.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-04** | As a Regulated Entity, I want to view all active regulatory requirements for my domain, so that I know what is currently expected and enforced. | **Given** I request the active requirements for my domain. <br> **When** Selma processes it. <br> **Then** Selma returns all active directives in both a formal reference format and a technical format suitable for implementation. | **P0** |
| **S-05** | As a Regulated Entity, I want to know if any directives conflict with one another, so that I can resolve contradictions before they cause compliance issues. | **Given** I request a regulatory consistency review. <br> **When** Selma processes it. <br> **Then** Selma conducts a full assessment and issues a formal inspection report with findings, identified conflicts, contradictions, and required corrective actions. | **P1** |
| **S-06** | As a Regulated Entity, I want to receive a comprehensive compliance audit of my entire regulatory set, so that I understand redundancies, gaps, and circular dependencies. | **Given** I request a full compliance audit. <br> **When** Selma processes it. <br> **Then** Selma generates a formal compliance inspection report with findings, deficiencies, redundancies, logical gaps, and required corrective actions. | **P2** |
| **S-10** | As a Regulated Entity, I want to submit a target (document, code, file, or any information format) for inspection against my active directives, so that I can identify deviations and receive corrective recommendations. | **Given** I provide a target and optionally specify which rules to apply. <br> **When** Selma processes it. <br> **Then** Selma reads the target, applies the applicable rules, identifies deviations, and produces a formal inspection report with findings and corrective recommendations. | **P0** |

---

## Epic 3: Regulatory Revision History & Provenance

*The user manages the lifecycle, history, and restoration of regulatory directives.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-07** | As a Regulated Entity, I want to view the complete revision history of any directive, so that I can trace its evolution and understand past decisions. | **Given** I request the history of a directive. <br> **When** Selma processes it. <br> **Then** Selma provides a full revision log with timestamps, originator, nature of each change, and summary of modifications. | **P1** |
| **S-08** | As a Regulated Entity, I want to restore a directive to a previous revision, so that I can undo unintended changes or revert to a previously validated state. | **Given** I specify a directive identifier and a target revision. <br> **When** Selma processes it. <br> **Then** Selma restores the directive to the specified revision, records the restoration in the change provenance, and documents the reason for the restoration. | **P1** |
| **S-09** | As a Regulated Entity, I want to preview the impact of changes before they are finalized, so that I can review and approve them before they become effective. | **Given** I request a change. <br> **When** Selma generates the proposed update. <br> **Then** Selma presents a side-by-side comparison of the current and proposed revisions and requires formal confirmation before the changes are recorded. | **P2** |

---

## Story Summary

| Epic | P0 | P1 | P2 | Total |
| :--- | :--- | :--- | :--- | :--- |
| Regulatory Directive Submission | 2 | 1 | 0 | **3** |
| Regulatory Inspection & Compliance Review | 2 | 1 | 1 | **4** |
| Regulatory Revision History & Provenance | 0 | 2 | 1 | **3** |
| **Total** | **4** | **4** | **2** | **10** |

---

## How This Matches the Regulatory Vision

| Regulatory Principle | How It Maps to the Unified Stories |
| :--- | :--- |
| **Rule Creation & Maintenance** | ✅ S-01, S-02, S-03 (Submit, Modify, Retire) |
| **Automatic Compliance Verification** | ✅ Selma performs structural reviews and consistency checks automatically during S-01 and S-02. |
| **Inspection of External Targets** | ✅ S-10 allows the user to submit any target (document, code, file) for inspection against active directives. |
| **Meta-Inspection (Rule Consistency)** | ✅ S-05 and S-06 inspect the ruleset itself for conflicts, gaps, and redundancies. |
| **Provenance & Audit Trail** | ✅ S-07 ensures full traceability of every directive's evolution. |
| **Corrective Action & Restoration** | ✅ S-08 allows restoration to a prior compliant state (mirroring corrective action implementation). |

---

## The Internal View (For Implementation)

While the user only sees a unified regulatory platform, Selma internally has five engines that work together. This is purely an implementation detail and is **never exposed** to the user:

| Internal Engine | What It Does | Exposed to User? |
| :--- | :--- | :--- |
| **Directive Drafting Engine** | Translates natural language into formal directives and technical specifications. | ❌ No. The user just "submits a directive." |
| **Structural Compliance Reviewer** | Checks that directives are correctly formatted, structured, and free of technical contamination. | ❌ No. The user just "submits" and it passes automatically. |
| **Regulatory Consistency Assessor** | Detects conflicts, contradictions, and circular dependencies between directives. | ❌ No. The user simply "requests an inspection" and receives the report. |
| **External Inspection Engine** | Reads any target (document, code, file, context) and applies active rules to identify deviations. | ❌ No. The user just "submits a target" and receives the inspection report. |
| **Revision & Provenance Manager** | Tracks all changes, versions, and restorations. | ❌ No. The user just "views history" or "restores" a directive. |

The user interacts with Selma as a single, unified regulatory authority—not as a collection of tools. Selma performs the inspection, provides the findings, and issues the corrective feedback automatically, exactly as a regulator would.
