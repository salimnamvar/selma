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

## Design reference

- [04-package-architecture.md](../design/04-package-architecture.md)
- [03-ports-and-adapters.md](../design/03-ports-and-adapters.md)
- [05-application-use-cases.md](../design/05-application-use-cases.md)
