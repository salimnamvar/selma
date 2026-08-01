# Selma — Design Schemas

> **Authority:** This directory is the **design-time SSoT** for executable rule and policy doctrine shapes under `design_contract_version` 1.1.0.  
> **Normative behavior:** [`../spec/contracts/`](../spec/README.md)  
> **Structural IDs:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)

## Files

| File | Role | Version |
| :--- | :--- | :--- |
| [`rule_schema.json`](rule_schema.json) | Executable dual-document rule (JSON Schema Draft 2020-12) | 1.0.0 |
| [`policy_doctrine.yaml`](policy_doctrine.yaml) | Guidance / governance doctrine (not evaluation logic) | 1.0.0 |

## Relation to root `schema/`

| Path | Role |
| :--- | :--- |
| **`docs/schema/`** (this dir) | **Single source of truth** for the latest rule + policy schema versions. Edit here first. |
| **Repository root `schema/`** | **Mirror** for runtime / product paths (`pyproject.toml`, `directive/policy/*`). MUST stay byte-aligned with this directory after any design schema change. |

Workflow: change `docs/schema/` → copy to root `schema/` (or a future sync script) in the same commit. Never edit root `schema/` alone.

## Cross-layer binding

1. **Spec contracts** define behavior (hash inclusion, `paired_policy_ref` lifecycle, conflict determinism).
2. **This schema** structurally projects those invariants (`required` fields, discriminators, hash field lists in `x-cg-ir-hashing`).
3. **Policy doctrine** describes human guidance only; never evaluation/FSM input.

## Audit hardening (design)

- `paired_policy_ref` required; included in `node_body` / `node_hash` (see `x-cg-ir-hashing`)
- Post-merge `parameters` land in detection before hash
- Doctrine revisions co-versioned for guidance pinning
