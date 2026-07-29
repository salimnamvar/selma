# Selma — Entity-Relationship Diagrams

PlantUML ERDs for each data store.

| File | Store | Storage Model | Mutability |
|------|-------|---------------|------------|
| `erd_001_directive_store.puml` | Directive Store | PostgreSQL | Mutable, versioned |
| `erd_002_cgir_store.puml` | CGIR Store | Content-Addressed | Immutable |
| `erd_003_event_store.puml` | Event Store | Append-Only Log | Immutable |
| `erd_004_artifact_store.puml` | Artifact Store | Object Store | Write-once |

## Rendering

```bash
# Single file
plantuml docs/erd/erd_001_directive_store.puml

# All ERDs
plantuml docs/erd/erd_00*.puml
```

## Shared Styles

`common/erd_styles.puml` contains skinparam configuration included by all diagrams.
