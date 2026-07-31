# Selma — Entity-Relationship Diagrams

PlantUML ERDs for each **C4 resource store** (`*_store`). Store IDs and display
names match [`../c4-model/README.md`](../c4-model/README.md).

| File | C4 store ID | Display name | Storage model | Mutability |
|------|-------------|--------------|---------------|------------|
| `erd_001_directives_store.puml` | `directives_store` | Directives Store | PostgreSQL | Mutable, versioned dual documents |
| `erd_002_compiled_rules_store.puml` | `compiled_rules_store` | Compiled Rules Store | Content-addressed | Immutable CG-IR snapshots |
| `erd_003_finding_events_store.puml` | `finding_events_store` | Finding Events Store | Append-only log | Immutable |
| `erd_004_artifacts_store.puml` | `artifacts_store` | Artifacts Store | Object store | Write-once |

Contract filenames under `spec/contracts/data_stores/` match C4 store IDs
(`directives_store.yaml`, `compiled_rules_store.yaml`, `finding_events_store.yaml`,
`artifacts_store.yaml`).

## Rendering

```bash
# Single file
plantuml docs/erd/erd_001_directives_store.puml

# All ERDs
plantuml docs/erd/erd_00*.puml
```

## Shared Styles

`common/erd_styles.puml` contains skinparam configuration included by all diagrams.
