# Selma — User Story: Rule Administrator

**Project:** Selma — Selma — Rule Regularity Platform
**Actor:** Rule Administrator (The Legislator)
**Version:** 2.0
**Date:** 2026-07-05
**Status:** Review Ready

---

## Actor Profile

| Attribute | Description |
| :--- | :--- |
| **Persona** | The Legislator (Human) |
| **Core Mission** | Ensures the **Semantic Integrity** (correctness) of the rule set |
| **Responsibilities** | Writes, edits, audits, and validates rules. Holds ultimate accountability. |

---

## Epic 1: Rule Lifecycle Management

*Creating, storing, and maintaining rules in a standardized Human/Machine format.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-01** | As a Rule Administrator, I want to submit a new rule request using natural language, so that Selma generates a standardized rule entry in both `policy.md` (prose) and `rules.yaml` (data). | **Given** I provide a natural language description (e.g., "Ban combustion engines in city centers"). <br> **When** the Steward Agent processes it. <br> **Then** a unique `Machine ID` (e.g., `POL-001`) is generated, and <br> **And** both files are updated without breaking the Traceability Bond. | **P0** |
| **S-02** | As a Rule Administrator, I want to edit an existing rule's parameters or description, so that the prose and the structured data stay synchronized automatically. | **Given** I specify a rule ID (e.g., `TRAF-001`). <br> **When** I update the `speed_limit` parameter. <br> **Then** the `rules.yaml` is updated, and <br> **And** the corresponding `Context / Conditions` cell in the `policy.md` table is updated to reflect the change. | **P0** |
| **S-03** | As a Rule Administrator, I want to deprecate or delete a rule, so that it is removed from active enforcement while preserving the audit trail. | **Given** I specify a rule ID to deprecate. <br> **When** I execute the delete command. <br> **Then** the rule `status` changes to `deprecated` in `rules.yaml` (soft delete). <br> **And** the `policy.md` entry remains but is marked with a `[DEPRECATED]` label. | **P1** |

---

## Epic 2: Rule Validation (Mechanical & Reasoning)

*Ensuring rules are syntactically correct and logically consistent.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-04** | As a Rule Administrator, I want to run a Mechanical Linter against my rule set, so that syntax errors, contamination (e.g., `parameters` in the Policy), and schema violations are flagged immediately. | **Given** I have a rule set. <br> **When** I run the mechanical linting command. <br> **Then** it checks the `forbidden_fields` list from the `contamination_guard`. <br> **And** if a violation exists (e.g., `preamble` in `rules.yaml`), it returns a Hard Fail with exact line numbers and exits. | **P0** |
| **S-05** | As a Rule Administrator, I want to run a Reasoning Linter on my rule set, so that I can detect logical contradictions (e.g., two active rules with conflicting conditions). | **Given** I have a rule set with overlapping conditions. <br> **When** I run the reasoning linter. <br> **Then** it identifies conflicts and applies the `priority_hierarchy`. <br> **And** it outputs a Reasoning Report with warnings (e.g., "TRAF-001 (Operational) is overridden by CONST-002 (Constitutional)"). | **P1** |
| **S-06** | As a Rule Administrator, I want to see a holistic Reasoning Audit for my domain, so that I understand redundancy, circular dependencies, and unused rules. | **Given** I request a full domain audit. <br> **When** the Reasoner runs the full suite. <br> **Then** it highlights circular `depends_on` loops and duplicate rules. <br> **And** suggests specific actions (e.g., "Rule X is identical to Rule Y, consider merging"). | **P2** |

---

## Epic 3: Governance & Meta-Rules

*Version control, audit trails, and provenance tracking.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-07** | As a Rule Administrator, I want Selma to auto-bump the domain version (SemVer) on every rule change, so that I know the impact scope (Major/Minor/Patch) without manual calculation. | **Given** I edit a rule. <br> **When** the edit is a breaking change (e.g., removing a required field). <br> **Then** the `version` in `rules.yaml` increments the `MAJOR` segment. <br> **And** the `policy_contract_version` is synchronized. | **P1** |
| **S-08** | As a Rule Administrator, I want every rule change to be committed to Git with a descriptive message, so that I have a complete audit trail for compliance. | **Given** I save a change. <br> **When** the Steward completes the update. <br> **Then** it auto-commits with the message `feat: Updated TRAF-001 (Changed speed limit to 25mph)`. <br> **And** the commit references the Story ID (S-01). | **P1** |
| **S-09** | As a Rule Administrator, I want to clearly distinguish between rules drafted by a Human and rules drafted by the AI Agent, so that I prioritize human review for AI-generated content. | **Given** A rule is created. <br> **When** the source is the AI Agent (via API). <br> **Then** a `provenance: ai_agent` field is added to the `rules.yaml` entry. <br> **And** the UI/CLI highlights these entries for mandatory review. | **P1** |
| **S-10** | As a Rule Administrator, I want to see a visual diff (preview) of the rule changes before they are finalized, so that I can catch unexpected errors or hallucinations introduced by the AI Agent. | **Given** I request a change (or the Agent drafts one). <br> **When** the Steward generates the updated files. <br> **Then** it outputs a side-by-side diff of the `policy.md` table rows and `rules.yaml` nodes before saving. <br> **And** I must confirm ("yes") to commit. | **P2** |

---

## Story Summary

| Epic | P0 | P1 | P2 | Total |
| :--- | :--- | :--- | :--- | :--- |
| Rule Lifecycle Management | 2 | 1 | 0 | **3** |
| Rule Validation | 1 | 1 | 1 | **3** |
| Governance & Meta-Rules | 0 | 3 | 1 | **4** |
| **Total** | **3** | **5** | **2** | **10** |
