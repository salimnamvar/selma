# Selma — Unified User Stories

**Project:** Selma — Rule Regularity Platform
**Version:** 4.0
**Date:** 2026-07-05
**Status:** Final

---

## Actor: The User

| Attribute | Description |
| :--- | :--- |
| **Actor** | The User (Human or AI Agent) |
| **Role** | The Rule Regulator |
| **Core Mission** | Regulates rules in their domain |
| **What They Do** | Generates, modifies, removes, and inspects rules via natural language or structured requests |
| **What They DON'T Do** | They do NOT worry about validation, linting, versioning, or formatting. Selma handles all of that automatically. |

---

## The User's View of Selma

| The User's Need | What the User Does | What Selma Does Automatically |
| :--- | :--- | :--- |
| "I need a rule for X." | Expresses intent in natural language. | Generates the rule, validates it mechanically, checks for conflicts, stores it in dual format, and versions it. |
| "Change rule TRAF-001." | Requests a change. | Updates both formats, re-validates, re-checks conflicts, versions the change, and commits to Git. |
| "Remove rule TRAF-001." | Requests removal. | Deprecates the rule, preserves the audit trail, and removes it from active enforcement. |
| "Show me the rules." | Queries for rules. | Returns the active rules in a structured format. |
| "Are there any conflicts?" | Asks for inspection. | Runs logical reasoning and returns a conflict report with suggested resolutions. |

---

## Epic 1: Rule Generation

*The user requests new rules or changes to existing ones.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-01** | As a User, I want to generate a new rule using natural language, so that Selma creates a standardized rule entry for both humans and machines. | **Given** I express a need in natural language. <br> **When** Selma processes it. <br> **Then** Selma generates a unique Rule ID, writes the human prose, writes the machine data, and automatically validates the rule before saving. | **P0** |
| **S-02** | As a User, I want to modify an existing rule, so that Selma updates both the human and machine versions simultaneously. | **Given** I specify a rule ID and describe the change. <br> **When** Selma processes it. <br> **Then** Selma updates the rule, re-validates it, re-checks for conflicts, and versions the change. | **P0** |
| **S-03** | As a User, I want to remove a rule from active enforcement, so that it is no longer applied while preserving the audit trail. | **Given** I specify a rule to deprecate. <br> **When** Selma processes it. <br> **Then** Selma marks the rule as deprecated, preserves the history, and removes it from active rule sets. | **P1** |

---

## Epic 2: Rule Inspection & Validation

*The user inspects the rules and their quality.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-04** | As a User, I want to see all active rules for my domain, so that I know what is currently enforced. | **Given** I request the rules for my domain. <br> **When** Selma processes it. <br> **Then** Selma returns all active rules in a human-readable and machine-readable format. | **P0** |
| **S-05** | As a User, I want to see if any rules conflict with each other, so that I can resolve contradictions. | **Given** I request a conflict check. <br> **When** Selma processes it. <br> **Then** Selma runs logical reasoning and returns a conflict report with suggested resolutions. | **P1** |
| **S-06** | As a User, I want to receive a full audit of my rule set, so that I understand redundancies, gaps, and circular dependencies. | **Given** I request a full audit. <br> **When** Selma processes it. <br> **Then** Selma generates an audit report highlighting issues and suggesting improvements. | **P2** |

---

## Epic 3: Rule Evolution & History

*The user manages the lifecycle and history of rules.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-07** | As a User, I want to see the history of any rule, so that I can trace its evolution. | **Given** I request the history of a rule. <br> **When** Selma processes it. <br> **Then** Selma provides a full version history with timestamps, authors, and change summaries. | **P1** |
| **S-08** | As a User, I want to roll back a rule to a previous version, so that I can undo unintended changes. | **Given** I specify a rule ID and target version. <br> **When** Selma processes it. <br> **Then** Selma restores the rule to the specified version and documents the rollback. | **P1** |
| **S-09** | As a User, I want to preview changes before they are saved, so that I can approve them. | **Given** I request a change. <br> **When** Selma generates the update. <br> **Then** Selma shows a side-by-side diff of proposed changes and requires confirmation. | **P2** |

---

## Story Summary

| Epic | P0 | P1 | P2 | Total |
| :--- | :--- | :--- | :--- | :--- |
| Rule Generation | 2 | 1 | 0 | **3** |
| Rule Inspection & Validation | 1 | 1 | 1 | **3** |
| Rule Evolution & History | 0 | 2 | 1 | **3** |
| **Total** | **3** | **4** | **2** | **9** |

---

## How This Matches the Vision

| Vision Statement | How It Maps to the Unified Stories |
| :--- | :--- |
| "Selma generates and maintains the rules" | ✅ S-01, S-02, S-03 |
| "Selma validates them automatically" | ✅ Validation is built into S-01, S-02, and S-05 |
| "Users can be human or AI agent" | ✅ The User is a single actor that can be either |
| "Users don't think about validation" | ✅ Validation is automatic and invisible (S-01, S-02) |
| "Selma inspects if rules are implemented well" | ✅ S-04, S-05, S-06 |

---

## The Internal View (For Developers)

While the user only sees one actor (the User), the platform internally has four pillars that work together. This is purely an implementation detail and should NOT be exposed to the user:

| Internal Pillar | What It Does | Exposed to User? |
| :--- | :--- | :--- |
| **Definition Engine** | Generates rules from natural language | ❌ No. The user just "generates a rule." |
| **Mechanical Linter** | Validates syntax and structure | ❌ No. The user just "generates a rule" and it works. |
| **Reasoning Linter** | Detects logical conflicts | ❌ No. The user just "inspects" and sees conflicts. |
| **Version Manager** | Versions and stores rules | ❌ No. The user just "sees history" and "rolls back." |

The user does not need to know these exist. They just interact with Selma as a single, unified regulator.
