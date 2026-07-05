# Selma — User Story: Rule Consumer

**Project:** Selma — Rule Regularity Platform
**Actor:** Rule Consumer (Human or System)
**Version:** 3.0
**Date:** 2026-07-05
**Status:** Generalized

---

## Actor Profile

| Attribute | Description |
| :--- | :--- |
| **Persona** | The Rule Enforcer |
| **Core Mission** | Queries and enforces rules in their domain |
| **Responsibilities** | Retrieves rules, applies them to context, receives updates |
| **What They Don't Do** | They do NOT validate, maintain, or format rules. Selma handles all of that automatically. |

---

## Epic 1: Rule Consumption & Retrieval

*Fetching rules for enforcement and compliance checking.*

| Story ID | User Story | Acceptance Criteria (Given-When-Then) | Priority |
| :--- | :--- | :--- | :--- |
| **S-07** | As a Rule Consumer, I want to query Selma for the current rule set of a specific domain, so that I can enforce them in my context. | **Given** I have a domain identifier. <br> **When** I query Selma. <br> **Then** I receive all active rules in a structured format with all parameters and conditions. | **P0** |
| **S-08** | As a Rule Consumer, I want to filter rules by type (obligation, prohibition, permission, standard), so that I can apply them appropriately. | **Given** I have a large rule set. <br> **When** I apply filters (type, priority, status). <br> **Then** I receive only the rules that match my criteria. | **P1** |
| **S-09** | As a Rule Consumer, I want to know when a rule changes, so that I can update my enforcement logic accordingly. | **Given** I subscribe to rule changes. <br> **When** a rule is created, updated, or deprecated. <br> **Then** I receive a notification with the rule ID, change type, and new data. | **P1** |

---

## Story Summary

| Epic | P0 | P1 | P2 | Total |
| :--- | :--- | :--- | :--- | :--- |
| Rule Consumption & Retrieval | 1 | 2 | 0 | **3** |
| **Total** | **1** | **2** | **0** | **3** |
