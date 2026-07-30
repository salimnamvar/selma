# Selma Class Diagrams

PlantUML class diagrams documenting the domain model, application services, and infrastructure adapters of the Selma compliance platform.

## Prerequisites

- [PlantUML](https://plantuml.com/) (v1.2022.1+)
- Java Runtime (for PlantUML rendering)

## Usage

```bash
# Render all diagrams
plantuml docs/class-diagram/*.puml

# Render a single diagram
plantuml docs/class-diagram/cd_001_domain_model.puml

# Render to SVG (recommended for docs)
plantuml -tsvg docs/class-diagram/*.puml
```

## Diagram Index

| ID | File | Description |
|----|------|-------------|
| CLS-001 | [cd_001_domain_model.puml](cd_001_domain_model.puml) | Domain model: aggregates, value objects, domain services, events, and repository ports |
| CLS-002 | [cd_002_application_services.puml](cd_002_application_services.puml) | Application services: all use case classes, port interfaces, DTOs, and pipeline chains |
| CLS-003 | [cd_003_infrastructure_adapters.puml](cd_003_infrastructure_adapters.puml) | Infrastructure adapters: dual-document directives, CG-IR, events, artifacts, detection, targets, auth |

## Layer Summary

| Diagram | Clean Architecture Layer | Key Elements |
|---------|------------------------|--------------|
| CLS-001 | Domain | Aggregates (Directive, CgIrSnapshot, Finding, etc.), Value Objects, Domain Services, Events, Repository Ports |
| CLS-002 | Application | Use cases across bounded contexts, ports (incl. dual-document DirectiveRepository), DTOs, pipeline chains |
| CLS-003 | Infrastructure | Adapters: SqlDirectiveRepository (executable + doctrine), CG-IR, events, artifacts, detection, target gateway, bootstrap |

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

## Design Reference

- Domain model: [`../design/02-ddd-model.md`](../design/02-ddd-model.md)
- Ports and adapters: [`../design/03-ports-and-adapters.md`](../design/03-ports-and-adapters.md)
- Application use cases: [`../design/05-application-use-cases.md`](../design/05-application-use-cases.md)
- Component class design: [`../design/07-component-class-design.md`](../design/07-component-class-design.md)
