# Selma Package Diagrams

PlantUML package diagrams for Clean Architecture with **`{resource}_{layer}`** modules.

## Usage

```bash
plantuml docs/package/pkg_001_clean_architecture.puml
plantuml -tsvg docs/package/*.puml
```

## Diagram Index

| ID | File | Description |
|----|------|-------------|
| PKG-001 | [pkg_001_clean_architecture.puml](pkg_001_clean_architecture.puml) | Resource_layer packages + dependency rule |

## Module naming

| Layer suffix | Responsibility |
|--------------|----------------|
| `*_domain` | Aggregates, pure domain services |
| `*_application` | Use cases (ROD operations) + port interfaces |
| `*_infrastructure` | Repositories, gateways, engines |
| `*_interface` | REST / CLI / TUI driving adapters |

## Alignment with C4

Package structure aligns with C4 components:
- `directives_*` → `directives_repository`
- `compiled_rules_*` → `compiled_rules_repository`
- `inspections_*` → `inspection` component
- `findings_*` → `findings` component
- `conflicts_domain` → Domain service (not C4 component)

**Not in core packages:**
- `certifications` — Offline/CI tool suite (separate directory)
- `authorization` — Enforced at API gate (cross-cutting concern)
- `detections` — Part of inspection pipeline

## Design reference

- [04-package-architecture.md](../design/04-package-architecture.md)
- [03-ports-and-adapters.md](../design/03-ports-and-adapters.md)
- [05-application-use-cases.md](../design/05-application-use-cases.md)
