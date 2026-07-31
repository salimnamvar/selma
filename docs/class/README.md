# Selma Class Diagrams

PlantUML class diagrams documenting the domain model, application services, and infrastructure adapters of the Selma compliance platform.

## Prerequisites

- [PlantUML](https://plantuml.com/) (v1.2022.1+)
- Java Runtime (for PlantUML rendering)

## Usage

```bash
# Render all diagrams
plantuml docs/class/*.puml

# Render a single diagram
plantuml docs/class/cd_001_domain_model.puml

# Render to SVG (recommended for docs)
plantuml -tsvg docs/class/*.puml
```

## Diagram Index

| ID | File | Description |
|----|------|-------------|
| CLS-001 | [cd_001_domain_model.puml](cd_001_domain_model.puml) | Domain model aligned with C4 resources: directives, compiled rules, inspections, findings; domain `ResolveConflict`; offline cert artifacts; findings read models |
| CLS-002 | [cd_002_application_services.puml](cd_002_application_services.puml) | Application use cases for the four `*_application` clusters + artifact-backed conflict review (no freestanding guidance/cert engines) |
| CLS-003 | [cd_003_infrastructure_adapters.puml](cd_003_infrastructure_adapters.puml) | Infrastructure: `*_repository` / `target_sources_gateway` adapters matching C4 driven ports |

## Layer Summary

| Diagram | Clean Architecture Layer | Key Elements |
|---------|------------------------|--------------|
| CLS-001 | Domain | Aggregates (Directive, CgIrSnapshot, Finding, etc.), Value Objects, Domain Services, Events, Repository Ports |
| CLS-002 | Application | ROD use cases (`CreateDirective`, `GetFindingGuidance`, …) + ports with Verb+Resource methods |
| CLS-003 | Infrastructure | `{resource}_infrastructure` adapters implementing ROD-named ports |

## Shared Styles

Common styling definitions are in [`common/cd_styles.puml`](common/cd_styles.puml). All diagrams include this file via `!includeurl common/cd_styles.puml`.

### Colour Palette

| Archetype | Background | Border |
|-----------|-----------|--------|
| Aggregate Root | `#E0F2F1` (teal) | `#00897B` |
| Value Object | `#E8EAF6` (slate-blue) | `#3F51B5` |
| Domain Event | `#FFF8E1` (amber) | `#FF8F00` |
| Domain Service | `#E8F5E9` (green) | `#2E7D32` |
| Port | `#FCE4EC` (crimson) | `#C62828` |
| Entity | `#ECEFF1` (grey) | `#546E7A` |

## Related Documents

- [C4 Architecture](../c4-model/README.md) — structural architecture
- [Package Diagrams](../package/README.md) — Clean Architecture package layout
