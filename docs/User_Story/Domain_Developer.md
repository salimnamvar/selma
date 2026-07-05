# Selma — User Story: Domain Developer

**Project:** Selma — Selma — Rule Regularity Platform
**Actor:** Domain Developer (The Enforcer)
**Version:** 2.0
**Date:** 2026-07-05
**Status:** Review Ready

---

## Actor Profile

| Attribute | Description |
| :--- | :--- |
| **Persona** | The Enforcer (Human/System) |
| **Core Mission** | Enables **Mechanical Enforcement** on downstream artifacts (diagrams, code) |
| **Responsibilities** | Integrates Selma into CI/CD pipelines to fetch rules |

---

## Epic 1: Rule Consumption & Retrieval

*Fetching rules for downstream linters and enforcement tools.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-13** | As a Domain Developer, I want to fetch all active rules for a specific domain via a REST API endpoint, so that my downstream linter (e.g., C4, OAS) can enforce them against artifacts without manual file copies. | **Given** I have a domain identifier (e.g., `traffic`). <br> **When** I call `GET /domains/traffic/rules`. <br> **Then** I receive a structured JSON payload containing only `status: active` rules. <br> **And** the payload includes all `parameters` and `conditions` for execution. | **P0** |
| **S-14** | As a Domain Developer, I want to query rules using filters (e.g., `?priority=constitutional` or `?type=prohibition`), so that I can apply fine-grained logic in my enforcement logic. | **Given** I have a large rule set. <br> **When** I call `GET /domains/traffic/rules?priority=statutory`. <br> **Then** the API returns only rules with the specified priority, drastically reducing the processing payload for my CI/CD pipeline. | **P1** |
| **S-15** | As a Domain Developer, I want to export an entire domain's rule set (including the `policy.md` and `rules.yaml`), so that I can share governance templates across projects or backup the state. | **Given** I specify a domain. <br> **When** I call the export endpoint. <br> **Then** Selma packages the `policy.md` and `rules.yaml` into a `.zip` archive. <br> **And** the archive includes a `manifest.json` with version metadata. | **P1** |

---

## Story Summary

| Epic | P0 | P1 | P2 | Total |
| :--- | :--- | :--- | :--- | :--- |
| Rule Consumption & Retrieval | 1 | 2 | 0 | **3** |
| **Total** | **1** | **2** | **0** | **3** |
