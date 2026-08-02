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
' Contract:  <VERSION>                        # stamp of docs/standards/VERSION only
' ============================================================
```

| Field | Rule |
| :--- | :--- |
| **Title** | Human title; state uses `State Machine NNN — Name` (full words); may match `@startuml` name |
| **Source** | One or more paths under `docs/spec/contracts/` or `docs/schema/`; never invent authority |
| **C4** | Only IDs from [`c4_registry.yaml`](c4_registry.yaml) peers; non-peers labeled `(domain)` / `(offline)` |
| **Package** | Optional; package module map for behavior views (`findings_application`, `conflicts_domain`, …) |
| **Contract** | Exactly the SemVer in [`VERSION`](VERSION). Not a per-diagram version. Bump `VERSION` + `python scripts/check_design_alignment.py --fix` |

**State diagram files:** `docs/state/state_machine_NNN_*.puml` (aligned with `pkg_NNN`, `dep_NNN`, `seq_NNN`, `act_NNN`, `uc_NNN`, `cd_NNN`).  
**Use case diagram files:** `docs/usecase/uc_NNN_*.puml` / diagram ID `UC-NNN`. Shared includes: `usecase/common/uc_styles.puml` + `uc_identities.puml` + `uc_section_*`. ROD oval names identical to package application leaves and class `<<Use Case>>` types.  
**Notes forbidden** on state, package, class, C4, deployment, and use-case diagrams — encode invariants as state body / guards / actions / associations / include edges, or leave them in Source contracts.

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
- Independent per-file design versions (e.g. `Version: 1.0.3` on one diagram only)
- `Contract:` values that do not equal `docs/standards/VERSION`
- Source paths to removed files (e.g. `event_store.yaml`)

## Style includes

Shared `common/*_styles.puml` files SHOULD note:

```text
' Contract: design_contract_version <VERSION> (docs/standards/VERSION)
```

Use the real SemVer from `VERSION` (stamped by the alignment checker), not the placeholder word.
