# Selma — User Story Map

**Project:** Selma — Rule Governance & Validation Platform
**Version:** 1.0
**Date:** 2026-07-05
**Status:** Draft

---

## Actors

| Actor | Description | Primary Stories |
|-------|-------------|-----------------|
| **Rule Administrator** | Human steward. Creates, edits, deprecates, audits rules. Ultimate source of truth. | S-01, S-03, S-04, S-05, S-07, S-12, S-13, S-14, S-15 |
| **AI Agent** | Autonomous scribe. Submits rule requests via API for human approval. Scales rule creation. | S-02, S-06 |
| **Domain Developer** | Enforcer. Integrates Selma into CI/CD pipelines, fetches rules for downstream linters. | S-09, S-10, S-11 |

---

## Epic 1: Rule Lifecycle Management (The Core)

*Creating, storing, and maintaining rules in a standardized Human/Machine format.*

| ID | User Story | Acceptance Criteria | Priority |
|----|------------|---------------------|----------|
| **S-01** | As a **Rule Administrator**, I want to write a new rule using natural language, so that Selma generates a standardized `policy.md` entry and a `rules.yaml` entry with a unique Machine ID. | A complete, traceable rule is created. Passes all Mechanical validators. | P0 |
| **S-02** | As an **AI Agent**, I want to submit a rule request via the API, so that Selma drafts the rule, validates it, and returns it to me for human approval. | The agent receives a draft rule with a validation report. | P0 |
| **S-03** | As a **Rule Administrator**, I want to edit an existing rule (description, conditions, parameters), so that the policy and rule files stay synchronized. | Both `policy.md` and `rules.yaml` update simultaneously. | P0 |
| **S-04** | As a **Rule Administrator**, I want to deprecate or delete a rule, so that it is marked `deprecated` in the machine file and the policy is updated. | The rule is soft-deleted (status: deprecated). Traceability remains intact. | P1 |

---

## Epic 2: Rule Validation — Mechanical Linting (Fast, Hard-Fail)

*"Is the rule file formatted correctly and free of contamination?"*

| ID | User Story | Acceptance Criteria | Priority |
|----|------------|---------------------|----------|
| **S-05** | As a **Rule Administrator**, I want to run a **Mechanical Linter** against my rule set, so that syntax errors, missing fields, or contamination guard violations are flagged immediately. | The linter fails fast with exact line numbers if `policy.md` contains `parameters` or `rules.yaml` contains `preamble`. | P0 |
| **S-06** | As an **AI Agent**, I want the Mechanical Linter to auto-correct common formatting errors (e.g., missing headers), so that I can fix issues without manual rewriting. | The Steward can automatically fix simple errors and re-run the linter. | P1 |

---

## Epic 3: Rule Validation — Reasoning Linting (Deep, Soft-Fail)

*"Do the rules make logical sense together?"*

| ID | User Story | Acceptance Criteria | Priority |
|----|------------|---------------------|----------|
| **S-07** | As a **Rule Administrator**, I want to run a **Reasoning Linter** to detect conflicts between rules, so that I can resolve contradictions before they cause enforcement issues. | The Reasoner identifies conflicting `conditions` and suggests the correct outcome based on the `priority_hierarchy` (e.g., Constitutional overrides Operational). | P1 |
| **S-08** | As a **Rule Administrator**, I want to see a "Reasoning Report" for my domain, so that I understand the logical implications of my rule set (redundancies, missing dependencies, circular logic). | A structured report highlights warnings (e.g., "Rule A and Rule B overlap but have different enforcement weights"). | P2 |

---

## Epic 4: Rule Consumption & Enforcement

*Making rules available for downstream tools (Linters for C4, OAS, etc.).*

| ID | User Story | Acceptance Criteria | Priority |
|----|------------|---------------------|----------|
| **S-09** | As a **Domain Developer**, I want to fetch all active rules for a specific domain via a REST API, so that my downstream linter can enforce them against artifacts (e.g., C4 diagrams). | `GET /domains/{domain}/rules` returns a structured JSON/YAML payload. | P0 |
| **S-10** | As a **Domain Developer**, I want to export a domain's rule set as a single package, so that I can share it between projects or back it up. | Export includes both `policy.md` and `rules.yaml` in a zip/tarball. | P1 |
| **S-11** | As a **Domain Developer**, I want to query rules by specific criteria (status: active, priority: constitutional), so that I can filter rules based on my linter's context. | API supports query parameters for `status`, `priority`, `type`. | P1 |

---

## Epic 5: Governance & Compliance (The Meta-Layer)

*Who changed what, and when?*

| ID | User Story | Acceptance Criteria | Priority |
|----|------------|---------------------|----------|
| **S-12** | As a **Rule Administrator**, I want Selma to automatically bump the semantic version (SemVer) when I edit a rule, so that I know if the change is a major, minor, or patch. | The `version` field in `rules.yaml` increments correctly. | P1 |
| **S-13** | As a **Rule Administrator**, I want Selma to commit every change to a Git repository, so that I have a complete audit trail of who changed what and when. | Git commit messages include the Rule ID and the nature of the change (e.g., "feat: added TRAF-011"). | P1 |

---

## Epic 6: Critical Supporting Stories

*Essential for trust, transparency, and regulatory compliance.*

| ID | User Story | Acceptance Criteria | Priority |
|----|------------|---------------------|----------|
| **S-14** | As a **Rule Administrator**, I want to easily distinguish between rules written by a Human vs. rules generated by the AI Agent, so that I can prioritize human review for AI-generated content. | A `provenance` field exists in `rules.yaml` with values `human` or `ai_agent`. | P1 |
| **S-15** | As a **Rule Administrator**, I want to see a visual diff (side-by-side) of the changes I am about to commit to a rule, so that I can review the exact prose and data changes before saving. | The Steward outputs a "dry-run" diff before applying changes. | P2 |

---

## Story Mapping by Actor

### Rule Administrator (Human)

| Capability | Stories |
|------------|---------|
| Author & maintain rules | S-01, S-03, S-04 |
| Validate rule quality | S-05, S-07, S-08 |
| Governance & audit | S-12, S-13, S-14, S-15 |

### AI Agent (Autonomous)

| Capability | Stories |
|------------|---------|
| Submit rules via API | S-02 |
| Auto-fix formatting | S-06 |

### Domain Developer (Human/System)

| Capability | Stories |
|------------|---------|
| Fetch & consume rules | S-09, S-10, S-11 |

---

## Priority Summary

| Priority | Count | Stories |
|----------|-------|---------|
| **P0** | 4 | S-01, S-02, S-05, S-09 |
| **P1** | 7 | S-04, S-06, S-07, S-10, S-11, S-12, S-13, S-14 |
| **P2** | 2 | S-08, S-15 |

---

## Open Questions

1. **S-02** — What is the maximum payload size for AI Agent rule submissions?
2. **S-07** — Should the Reasoning Linter support custom conflict-resolution policies beyond the priority hierarchy?
3. **S-13** — Should Git commits be signed (GPG) for compliance requirements?
4. **S-15** — Should the diff view be terminal-based (CLI) or web-based (UI)?
