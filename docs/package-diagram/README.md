# Selma Package Diagrams

PlantUML package diagrams documenting the architectural layer boundaries and dependency flow of the Selma compliance platform.

## Prerequisites

- [PlantUML](https://plantuml.com/) (v1.2022.1+)
- Java Runtime (for PlantUML rendering)

## Usage

```bash
# Render all diagrams
plantuml docs/package-diagram/*.puml

# Render a single diagram
plantuml docs/package-diagram/pkg_001_clean_architecture.puml

# Render to SVG (recommended for docs)
plantuml -tsvg docs/package-diagram/*.puml
```

## Diagram Index

| ID | File | Description |
|----|------|-------------|
| PKG-001 | [pkg_001_clean_architecture.puml](pkg_001_clean_architecture.puml) | Clean Architecture concentric layers with DDD bounded contexts and C4 component annotations |

## Architecture Layers

| Layer | Colour | Dependency Rule |
|-------|--------|----------------|
| **Interfaces** | Blue | Outermost — depends on Application |
| **Infrastructure** | Orange | Implements ports — depends on Domain + Application |
| **Application** | Green | Use cases — depends on Domain only |
| **Domain** | White | Innermost — no external dependencies |
| **Composition** | Purple | Wiring — depends on all layers |

All dependency arrows point **inward** — the Dependency Rule is enforced structurally.

## Bounded Contexts (Domain Layer)

| Context | Packages | C4 Component Mapping |
|---------|----------|---------------------|
| domain.shared | LineageId, Hlc, hashes, errors | Shared value objects |
| domain.governance | Directive aggregate, LineageService | directives_adapter |
| domain.compilation | CgIrSnapshot, ControlNode, DependencyEdge | hermetic_compiler |
| domain.inspection | Target, InspectionSnapshot, DetectionOutcome | rule_inspector |
| domain.finding | Finding aggregate, FindingFsm, Disposition | lifecycle_finder |
| domain.conflict | ConflictArtifact, ResolveConflict | conflict_resolver |
| domain.authorization | Capability value objects | CapabilitySource |
| domain.certification | Gate IDs, CertificationRun | architectural_auditor |

## Shared Styles

Styling is inherited from [`../class-diagram/common/cd_styles.puml`](../class-diagram/common/cd_styles.puml).

## Design Reference

- Package architecture: [`../design/04-package-architecture.md`](../design/04-package-architecture.md)
- Ports and adapters: [`../design/03-ports-and-adapters.md`](../design/03-ports-and-adapters.md)
- DDD model: [`../design/02-ddd-model.md`](../design/02-ddd-model.md)
