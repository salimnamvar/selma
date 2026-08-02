# PlantUML diagram header standard

Every design diagram under `docs/` (except pure style includes) MUST start with a
comment block that enables investigation without opening the figure.

## Required fields

```text
' ============================================================
' Title:     <short title>                    # State Machine NNN for state; DEP-NNN / PKG-NNN when numbered
' Source:    docs/spec/contracts/<path>.yaml  # primary contract(s)
' C4:        <canonical peer IDs and edges>
' Package:   <optional {resource}_{layer} map>  # state / class implementation views
' Contract:  1.1.0                            # design_contract_version
' ============================================================
```

| Field | Rule |
| :--- | :--- |
| **Title** | Human title; state uses `State Machine NNN — Name` (full words); may match `@startuml` name |
| **Source** | One or more paths under `docs/spec/contracts/` or `docs/schema/`; never invent authority |
| **C4** | Only IDs from [`c4_registry.yaml`](c4_registry.yaml) peers; non-peers labeled `(domain)` / `(offline)` |
| **Package** | Optional; package module map for behavior views (`findings_application`, `conflicts_domain`, …) |
| **Contract** | Exactly `1.1.0` until the design line is intentionally bumped with C4 |

**State diagram files:** `docs/state/state_machine_NNN_*.puml` (aligned with `pkg_NNN`, `dep_NNN`, `seq_NNN`, `act_NNN`).  
**Notes forbidden** on state diagrams — encode invariants as state body / guards / actions or leave them in Source contracts.

## Allowed C4 line patterns

```text
' C4:      api → directives_application → directives_repository → directives_store
' C4:      compilation_application (hermetic) → compiled_rules_repository
' C4:      ResolveConflict (domain · not peer) used by compilation_application
' C4:      certification_tool (offline · not peer) → artifacts_repository
```

## Forbidden

- Stale IDs listed under `forbidden_ids` in `c4_registry.yaml`
- Presenting `ResolveConflict`, `certification_tool`, or “analytics engine” as peer boxes
- `Contract: 1.0.0` (superseded by design line 1.1.0)
- Source paths to removed files (e.g. `event_store.yaml`)

## Style includes

Shared `common/*_styles.puml` files SHOULD note:

```text
' Contract: design_contract_version 1.1.0 (docs/standards/c4_registry.yaml)
```
