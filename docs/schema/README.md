# Selma — Design Schemas

> **Authority:** This directory is the **design-time SSoT** for executable rule and policy doctrine **document shapes**. Design freeze: [`docs/standards/VERSION`](../standards/VERSION).  
> **Normative behavior:** [`../spec/contracts/`](../spec/README.md)  
> **Durable tables:** [`../erd/`](../erd/README.md) · store contracts `physical_model`  
> **Structural IDs:** [`../standards/c4_registry.yaml`](../standards/c4_registry.yaml)

## Files

| File | Role | Body version (`schema_version`) |
| :--- | :--- | :--- |
| [`rule_schema.json`](rule_schema.json) | Executable dual-document rule (JSON Schema Draft 2020-12) | 1.0.0 |
| [`policy_doctrine.yaml`](policy_doctrine.yaml) | Guidance / governance doctrine (not evaluation logic) | 1.0.0 |

## Relation to root `schema/`

| Path | Role |
| :--- | :--- |
| **`docs/schema/`** (this dir) | **Single source of truth** for the latest rule + policy schema versions. Edit here first. |
| **Repository root `schema/`** | **Mirror** for runtime / product paths (`pyproject.toml`, `directive/policy/*`). MUST stay byte-aligned with this directory after any design schema change. |

Workflow: change `docs/schema/` → copy to root `schema/` (or a future sync script) in the same commit. Never edit root `schema/` alone.

## Identical alignment with store contracts and ERD

| Schema document | Store column (contract `physical_model`) | ERD entity |
| :--- | :--- | :--- |
| `rule_schema.json` | `directives_store.DirectiveRevisions.executable_document` | ERD-001 `DirectiveRevisions.executable_document` |
| `policy_doctrine.yaml` | `directives_store.DirectiveRevisions.policy_doctrine_document` | ERD-001 `DirectiveRevisions.policy_doctrine_document` |
| `paired_policy_ref` (both docs) | `DirectiveRevisions.paired_policy_ref` · finding pin | ERD-001 + ERD-003 `FindingProjections.paired_policy_ref` |
| Executable projection → CG-IR | `compiled_rules_store.Nodes.node_body` (executable only) | ERD-002 `Nodes` |

**Dual-document rule (INV-DS-005):** every `DirectiveRevisions` row stores **both** documents linked by `paired_policy_ref`. There is no separate policy-doctrine store.

**Compile path:** reads `executable_document` only (`CompilerReadPort`).  
**Guidance path:** reads `policy_doctrine_document` by finding-pinned `paired_policy_ref` only (`GuidanceReadPort`).  
**Inspection / finding FSM:** never load doctrine for evaluation or transitions.

Store contract anchors:

| C4 store | Contract | ERD |
| :--- | :--- | :--- |
| `directives_store` | [`../spec/contracts/data_stores/directives_store.yaml`](../spec/contracts/data_stores/directives_store.yaml) | [`../erd/erd_001_directives_store.puml`](../erd/erd_001_directives_store.puml) |
| `compiled_rules_store` | [`../spec/contracts/data_stores/compiled_rules_store.yaml`](../spec/contracts/data_stores/compiled_rules_store.yaml) | [`../erd/erd_002_compiled_rules_store.puml`](../erd/erd_002_compiled_rules_store.puml) |
| `finding_events_store` | [`../spec/contracts/data_stores/finding_events_store.yaml`](../spec/contracts/data_stores/finding_events_store.yaml) | [`../erd/erd_003_finding_events_store.puml`](../erd/erd_003_finding_events_store.puml) |
| `artifacts_store` | [`../spec/contracts/data_stores/artifacts_store.yaml`](../spec/contracts/data_stores/artifacts_store.yaml) | [`../erd/erd_004_artifacts_store.puml`](../erd/erd_004_artifacts_store.puml) |

Finding FSM storage enums (`FindingState` / dispositions) are **not** JSON Schema constraints on rules; they are durable columns defined in `finding_events_store.physical_model` and `finding_lifecycle/states.yaml` (`storage_id`). `rule_schema.json` `x-finding-fsm` is informative only and MUST use the same `storage_id` set.

## Cross-layer binding

1. **Spec contracts** define behavior (hash inclusion, `paired_policy_ref` lifecycle, conflict determinism) and **`physical_model`** tables.
2. **This schema** structurally projects dual-document invariants (`required` fields, discriminators, hash field lists in `x-cg-ir-hashing`).
3. **ERD** visualizes `physical_model` only — no second schema of tables.
4. **Policy doctrine** describes human guidance only; never evaluation/FSM input.

## Audit hardening (design)

- `paired_policy_ref` required; included in `node_body` / `node_hash` (see `x-cg-ir-hashing`)
- Post-merge `parameters` land in detection before hash
- Doctrine revisions co-versioned for guidance pinning
