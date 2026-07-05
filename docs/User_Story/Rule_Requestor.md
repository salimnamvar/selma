# Selma — User Story: Rule Requestor

**Project:** Selma — Rule Regularity Platform
**Actor:** Rule Requestor (Human or AI Agent)
**Version:** 3.0
**Date:** 2026-07-05
**Status:** Generalized

---

## Actor Profile

| Attribute | Description |
| :--- | :--- |
| **Persona** | The Intent Provider |
| **Core Mission** | Expresses needs for rules and rule changes |
| **Responsibilities** | Requests rules via natural language, reviews changes, approves updates |
| **What They Don't Do** | They do NOT validate, lint, or format rules. Selma handles all validation automatically. |

---

## Epic 1: Rule Generation

*Requesting new rules and changes via natural language.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-01** | As a Rule Requestor, I want to request a new rule using natural language, so that Selma generates a standardized rule entry in both human-readable and machine-readable formats. | **Given** I express a need (e.g., "Ban combustion engines in city centers"). <br> **When** Selma processes it. <br> **Then** a unique Rule ID is generated, the prose is written to the human policy document, and the structured data is written to the machine rule set. <br> **And** Selma automatically validates the rule before saving. | **P0** |
| **S-02** | As a Rule Requestor, I want to request a change to an existing rule, so that Selma updates both the human and machine representations automatically. | **Given** I specify a rule ID and describe the change. <br> **When** Selma processes it. <br> **Then** both documents are updated simultaneously. <br> **And** Selma automatically validates the change before saving. | **P0** |
| **S-03** | As a Rule Requestor, I want to request that a rule be removed or deprecated, so that it is no longer active while preserving the audit trail. | **Given** I specify a rule to deprecate. <br> **When** Selma processes it. <br> **Then** the rule is marked as deprecated in both documents. <br> **And** the history is preserved for audit purposes. | **P1** |

---

## Epic 2: Rule Evolution & Governance

*Managing rule history, provenance, and changes over time.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-10** | As a Rule Requestor, I want Selma to automatically version every rule change, so that I can trace the history of any rule. | **Given** a rule change is made. <br> **When** Selma saves it. <br> **Then** it assigns a version number (SemVer) and maintains a full audit trail. | **P1** |
| **S-11** | As a Rule Requestor, I want to distinguish between rules created by a human and rules created by an AI agent, so that I know the provenance. | **Given** a rule is created. <br> **When** Selma saves it. <br> **Then** it tags the rule with a provenance field (human or ai_agent). | **P1** |
| **S-12** | As a Rule Requestor, I want to roll back a rule to a previous version, so that I can undo unintended changes. | **Given** I specify a rule ID and target version. <br> **When** Selma processes it. <br> **Then** it restores the rule to the specified version. <br> **And** a new commit is created documenting the rollback. | **P1** |
| **S-13** | As a Rule Requestor, I want to see a preview of the changes I am about to make, so that I can approve them before they are saved. | **Given** I request a change. <br> **When** Selma generates the update. <br> **Then** it shows a side-by-side diff of the proposed changes. <br> **And** I must confirm before the changes are saved. | **P2** |

---

## Epic 3: Automatic Rule Validation

*Selma validates all rules automatically—users never worry about validation.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-04** | As a Rule Requestor, I want Selma to automatically validate every rule I create or modify, so that I never have to worry about formatting, contamination, or structural errors. | **Given** I submit a rule request. <br> **When** Selma processes it. <br> **Then** it automatically runs mechanical validation. <br> **And** if errors are found, Selma fixes them or asks for clarification. | **P0** |
| **S-05** | As a Rule Requestor, I want Selma to automatically check if new rules conflict with existing ones, so that I never create contradictory rules. | **Given** I submit a new rule. <br> **When** Selma processes it. <br> **Then** it automatically runs logical validation against all existing rules. <br> **And** if conflicts are found, Selma warns me and suggests resolutions. | **P1** |
| **S-06** | As a Rule Requestor, I want Selma to regularly audit the entire rule set for redundancies, circular dependencies, and logical gaps, so that the rule set remains coherent. | **Given** I request a full domain audit. <br> **When** Selma runs the audit. <br> **Then** it generates a report highlighting issues and suggesting improvements. | **P2** |

---

## Story Summary

| Epic | P0 | P1 | P2 | Total |
| :--- | :--- | :--- | :--- | :--- |
| Rule Generation | 2 | 1 | 0 | **3** |
| Rule Evolution & Governance | 0 | 3 | 1 | **4** |
| Automatic Rule Validation | 1 | 1 | 1 | **3** |
| **Total** | **3** | **5** | **1** | **9** |
