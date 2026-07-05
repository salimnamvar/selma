# Selma — User Story: Selma Platform

**Project:** Selma — Rule Regularity Platform
**Actor:** Selma (The Autonomous Regulator)
**Version:** 3.0
**Date:** 2026-07-05
**Status:** Generalized

---

## Actor Profile

| Attribute | Description |
| :--- | :--- |
| **Persona** | The Autonomous Regulator |
| **Core Mission** | Generates, validates, maintains, stores, reasons, and evolves rules |
| **Responsibilities** | Handles all rule lifecycle operations automatically |
| **What It Does** | Generates rules from natural language, validates rules (mechanical + reasoning), maintains rules (updates, deprecations, versioning), stores rules in dual format (Human + Machine), reasons about conflicts and resolves them, learns from feedback and evolves |
| **What It Doesn't Do** | Does NOT require human intervention for validation or linting |

---

## Epic 1: Rule Generation & Maintenance

*Creating and maintaining rules from natural language requests.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-01** | As Selma, I want to generate a standardized rule entry from a natural language request, so that the rule is stored in both human-readable and machine-readable formats. | **Given** a natural language request. <br> **When** I process it. <br> **Then** I generate a unique Rule ID, write the prose to the human policy document, and write the structured data to the machine rule set. <br> **And** I automatically validate the rule before saving. | **P0** |
| **S-02** | As Selma, I want to update an existing rule based on a natural language request, so that both the human and machine representations are synchronized automatically. | **Given** a rule ID and a change request. <br> **When** I process it. <br> **Then** I update both documents simultaneously. <br> **And** I automatically validate the change before saving. | **P0** |
| **S-03** | As Selma, I want to deprecate a rule based on a request, so that it is removed from active enforcement while preserving the audit trail. | **Given** a deprecation request. <br> **When** I process it. <br> **Then** I mark the rule as deprecated in both documents. <br> **And** I preserve the history for audit purposes. | **P1** |

---

## Epic 2: Automatic Rule Validation

*Validating all rules automatically without human intervention.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-04** | As Selma, I want to automatically validate every rule I process, so that users never have to worry about formatting, contamination, or structural errors. | **Given** a rule request. <br> **When** I process it. <br> **Then** I automatically run mechanical validation. <br> **And** if errors are found, I fix them or ask for clarification. | **P0** |
| **S-05** | As Selma, I want to automatically check if new rules conflict with existing ones, so that I never allow contradictory rules to be saved. | **Given** a new rule. <br> **When** I process it. <br> **Then** I automatically run logical validation against all existing rules. <br> **And** if conflicts are found, I warn the user and suggest resolutions. | **P1** |
| **S-06** | As Selma, I want to regularly audit the entire rule set for redundancies, circular dependencies, and logical gaps, so that the rule set remains coherent. | **Given** a full domain audit is requested. <br> **When** I run the audit. <br> **Then** I generate a report highlighting issues and suggesting improvements. | **P2** |

---

## Epic 3: Rule Evolution & Governance

*Managing rule history, provenance, and changes over time.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-10** | As Selma, I want to automatically version every rule change, so that users can trace the history of any rule. | **Given** a rule change is made. <br> **When** I save it. <br> **Then** I assign a version number (SemVer) and maintain a full audit trail. | **P1** |
| **S-11** | As Selma, I want to tag every rule with its provenance (human or ai_agent), so that users know the source of each rule. | **Given** a rule is created. <br> **When** I save it. <br> **Then** I tag it with a provenance field. | **P1** |
| **S-12** | As Selma, I want to support rollback to any previous version of a rule, so that users can undo unintended changes. | **Given** a rollback request. <br> **When** I process it. <br> **Then** I restore the rule to the specified version. <br> **And** I create a new commit documenting the rollback. | **P1** |
| **S-13** | As Selma, I want to show a preview of changes before saving, so that users can approve them. | **Given** a change request. <br> **When** I generate the update. <br> **Then** I show a side-by-side diff of the proposed changes. <br> **And** I wait for confirmation before saving. | **P2** |

---

## Epic 4: Rule Consumption & Retrieval

*Providing rules to consumers for enforcement and compliance.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-07** | As Selma, I want to provide the current rule set for a specific domain, so that consumers can enforce them. | **Given** a domain query. <br> **When** I process it. <br> **Then** I return all active rules in a structured format with all parameters and conditions. | **P0** |
| **S-08** | As Selma, I want to support filtering rules by type, priority, and status, so that consumers can apply them appropriately. | **Given** a filtered query. <br> **When** I process it. <br> **Then** I return only the rules that match the criteria. | **P1** |
| **S-09** | As Selma, I want to notify consumers when rules change, so that they can update their enforcement logic. | **Given** a subscription to rule changes. <br> **When** a rule is created, updated, or deprecated. <br> **Then** I send a notification with the rule ID, change type, and new data. | **P1** |

---

## Story Summary

| Epic | P0 | P1 | P2 | Total |
| :--- | :--- | :--- | :--- | :--- |
| Rule Generation & Maintenance | 2 | 1 | 0 | **3** |
| Automatic Rule Validation | 1 | 1 | 1 | **3** |
| Rule Evolution & Governance | 0 | 3 | 1 | **4** |
| Rule Consumption & Retrieval | 1 | 2 | 0 | **3** |
| **Total** | **4** | **7** | **1** | **13** |
