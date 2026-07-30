# Selma — Entity-Relationship Diagrams

PlantUML ERDs for each **C4 resource store**. Store IDs match
[`../c4-model/README.md`](../c4-model/README.md).

| File | C4 store ID | Display name | Storage model | Mutability |
|------|-------------|--------------|---------------|------------|
| `erd_001_directive_store.puml` | `directives` | Directives | PostgreSQL | Mutable, versioned dual documents |
| `erd_002_cgir_store.puml` | `compiled_rules` | Compiled Rules | Content-addressed | Immutable CG-IR snapshots |
| `erd_003_event_store.puml` | `finding_events` | Finding Events | Append-only log | Immutable |
| `erd_004_artifact_store.puml` | `artifacts` | Artifacts | Object store | Write-once |

Contract filenames under `spec/contracts/data_stores/` keep historical names
(`directive_store.yaml`, etc.) but map 1:1 to the C4 store IDs above.

## Rendering

```bash
# Single file
plantuml docs/erd/erd_001_directive_store.puml

# All ERDs
plantuml docs/erd/erd_00*.puml
```

## Shared Styles

`common/erd_styles.puml` contains skinparam configuration included by all diagrams.
