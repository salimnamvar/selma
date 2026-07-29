# Selma — C4 Architecture Diagrams

Three-level C4 architecture model for the Selma rule regularity platform.

## Diagrams

| Level | File | Scope |
| :--- | :--- | :--- |
| **Context** | `c4_selma_context.puml` | Actors, external systems, Selma as a black box |
| **Container** | `c4_selma_container.puml` | Interface, Application, four data stores |
| **Component** | `c4_selma_component.puml` | 12 internal components with adapters |

## Component Inventory

| Component | Package | Responsibility |
| :--- | :--- | :--- |
| **Application Service** | Ingress | Entry point: authenticates, validates, dispatches, orchestrates compilation |
| **Hermetic Compiler** | Core | Compile-time only: validates directives, publishes immutable CG-IR snapshots |
| **Rule Inspector** | Core | Runtime evaluation: executes compiled rules against submitted targets |
| **Conflict Resolver** | Core | Deterministic conflict resolution: priority, specificity, recency precedence |
| **Lifecycle Finder** | Core | Finding FSM: 10-state lifecycle with SoD enforcement |
| **Finding Analyzer** | Read | Read-only aggregates, trends, causal explanations, and guidance resolution from policy doctrines |
| **Architectural Auditor** | Read | Seven-gate certification on CI/CD trigger |
| **Directives Adapter** | Persistence | Directive CRUD and lineage identity resolution |
| **Compiled Rules Adapter** | Persistence | Content-addressed storage of CG-IR snapshots |
| **Findings Audit Adapter** | Persistence | Append-only event streams and audit replication |
| **Inspection Snapshots Adapter** | Persistence | Immutable snapshots and certification artifacts |
| **Target Adapter** | Persistence | Outbound mediation to external regulated systems |

## Canonical Identity Registry

All entity IDs, names, tech stacks, and descriptions are defined in `common/c4_identities.puml`. This file is the single source of truth — no diagram hardcodes entity metadata.

## Visual Styling

`common/c4_styles.puml` defines the shared palette: element colors, relationship line styles, boundary styles, and legend entries. Include after the C4-PlantUML macro, before `c4_identities.puml`.

## Rendering

Requires [PlantUML](https://plantuml.com/) and [C4-PlantUML](https://github.com/plantuml-stdlib/C4-PlantUML) v2.13.0:

```bash
plantuml docs/c4-model/c4_selma_context.puml
plantuml docs/c4-model/c4_selma_container.puml
plantuml docs/c4-model/c4_selma_component.puml
```

## Behavioral state machines

C4 describes *structure* (containers, components, adapters).  
Lifecycle and pipeline *behavior* lives in [`../state-machine/`](../state-machine/README.md) (PlantUML catalog + README).

Ownership of each machine maps to the component inventory above (e.g. Hermetic Compiler ↔ Compilation pipeline, Lifecycle Finder ↔ Finding FSM).

## Design Principles

- **Compile-time/runtime separation**: Executable rules compiled to CG-IR at compile time; policy doctrines read at runtime for guidance only, never for evaluation
- **Dual-document directives**: Every directive has a paired executable rule (JSON) for evaluation and a policy doctrine (YAML) for reasoning/guidance
- **Immutable storage**: CG-IR, events, snapshots are append-only
- **Capability-based access control**: Permissions enforced at component boundaries
- **Segregation of duties**: Directive creator ≠ Finding waiver

## Design Freeze

Application architecture (DDD, ports & adapters, packages, use cases) is frozen in
[`../design/`](../design/README.md). C4 remains the structural view; design docs own
package and port surfaces for Implementation.
