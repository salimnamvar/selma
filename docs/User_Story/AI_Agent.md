# Selma — User Story: AI Agent

**Project:** Selma — Selma — Rule Regularity Platform
**Actor:** AI Agent (The Scribe)
**Version:** 2.0
**Date:** 2026-07-05
**Status:** Review Ready

---

## Actor Profile

| Attribute | Description |
| :--- | :--- |
| **Persona** | The Scribe (Autonomous) |
| **Core Mission** | Scales rule **Creation** and **Enhancement** via AI |
| **Responsibilities** | Submits natural language requests to automate rule drafting |

---

## Epic 1: Automated Rule Submission

*Submitting natural language rule requests via authenticated API.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-11** | As an AI Agent, I want to submit a natural language rule request via an authenticated API, so that Selma asynchronously drafts the rule and returns a structured draft for human approval. | **Given** I send a POST request to `/api/v1/rules` with a prompt. <br> **When** Selma processes it. <br> **Then** it returns a `draft_id` and the draft rule files (preview). <br> **And** the `provenance` is set to `ai_agent`. | **P0** |

---

## Epic 2: Self-Correction & Quality Assurance

*Automatically fixing formatting errors to reduce human intervention.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-12** | As an AI Agent, I want the Mechanical Linter to automatically fix common formatting mistakes (e.g., missing YAML brackets, missing header rows), so that I reduce API retry cycles and human handover. | **Given** The LLM draft contains a syntax error. <br> **When** the Steward runs the Mechanical Linter. <br> **Then** it detects the error, asks the LLM to rewrite the specific section, and re-runs the linter automatically. <br> **And** if successful, it returns a "Validated Draft" without human intervention. | **P1** |

---

## Story Summary

| Epic | P0 | P1 | P2 | Total |
| :--- | :--- | :--- | :--- | :--- |
| Automated Rule Submission | 1 | 0 | 0 | **1** |
| Self-Correction & Quality Assurance | 0 | 1 | 0 | **1** |
| **Total** | **1** | **1** | **0** | **2** |
