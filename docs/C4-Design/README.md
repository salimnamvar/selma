# Selma -- C4 Architecture Diagrams

**Version:** 1.1.0
**Date:** 2026-07-06
**Status:** Initial Design

## Diagram Inventory

| Diagram | File | Level | Elements | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| Context | `c4_selma_context.puml` | Context | 3 | System boundary and actors |
| Container | `c4_selma_container.puml` | Container | 12 | Deployable units: services, databases |
| CompilationEngine | `c4_selma_component_compilation.puml` | Component | 13 | Hermetic compilation pipeline internals |
| InspectionPipeline | `c4_selma_component_inspection.puml` | Component | 8 | DAG execution and finding creation |
| FindingFsmEngine | `c4_selma_component_finding.puml` | Component | 6 | Finding lifecycle state machine |

## Component Inventory

### Actors

| Name | Type | C4 Level | Description |
| :--- | :--- | :--- | :--- |
| RegulatoryOfficial | Person | Context, Container | Rule Author and Governance Owner |
| ComplianceRepresentative | Person | Context, Container | Compliance Seeker and Remediation Owner |

### Containers

| Name | Technology | C4 Level | Description |
| :--- | :--- | :--- | :--- |
| ApiGateway | FastAPI | Container | Request ingress, capability checking, segregation of duties |
| DirectiveManager | Python | Container | CRUD and identity lifecycle (fork/merge/split/retire) |
| CompilationEngine | Python | Container | Hermetic compilation, CG-IR generation |
| InspectionPipeline | Python | Container | DAG execution, target evaluation |
| FindingFsmEngine | Python | Container | Finding lifecycle state machine |
| AnalyticsEngine | Python | Container | Read-only aggregate analytics |

### Stores

| Name | Technology | C4 Level | Description |
| :--- | :--- | :--- | :--- |
| DirectiveStore | PostgreSQL | Container | Directive graph persistence |
| CgIrStore | Content-Addressed Storage | Container | Immutable CG-IR snapshot storage |
| FindingEventStore | Append-Only Log | Container | HLC-ordered event stream |
| ExecutionArtifactStore | Object Store | Container | Immutable inspection snapshots |

### Compilation Engine Components

| Name | Container | Description |
| :--- | :--- | :--- |
| DirectiveParser | CompilationEngine | Parses directive tables, extracts Machine ID |
| IdentityResolver | CompilationEngine | Resolves lineage_id and execution_id |
| EvaluatorValidator | CompilationEngine | AST-walking discriminator, RE2, complexity checks |
| ScopeCompiler | CompilationEngine | Compiles scope objects with specificity scoring |
| ConflictResolver | CompilationEngine | Multi-factor conflict resolution per 2.15 |
| NodeCompiler | CompilationEngine | CG-IR node generation, dual hash model |
| DagBuilder | CompilationEngine | DAG construction, acyclicity validation |
| EdgeHasher | CompilationEngine | Directional edge hash computation |
| SnapshotAssembler | CompilationEngine | Snapshot assembly and hash computation |
| IncrementalCache | CompilationEngine | semantic_hash subgraph reuse |
| ProvenanceRecorder | CompilationEngine | Frozen environment and lineage provenance |

### Inspection Pipeline Components

| Name | Container | Description |
| :--- | :--- | :--- |
| TargetValidator | InspectionPipeline | Target schema validation, target_hash computation |
| ScopeFilter | InspectionPipeline | Filters CG-IR nodes by scope applicability |
| EvalExecutor | InspectionPipeline | Topological DAG execution with pure evaluators |
| FindingCreator | InspectionPipeline | Maps evaluator outcomes to findings |
| PipelineTracer | InspectionPipeline | Records pipeline trace entries |
| SnapshotRecorder | InspectionPipeline | Generates inspection snapshot |

### Finding FSM Components

| Name | Container | Description |
| :--- | :--- | :--- |
| CapabilityGater | FindingFsmEngine | Enforces capability matrix at transition gate |
| FsmTransition | FindingFsmEngine | Finding state machine transitions |
| EventEmitter | FindingFsmEngine | Appends HLC-ordered events |
| HlcClock | FindingFsmEngine | Hybrid Logical Clock for event ordering |

## Architecture Pattern

```
RegulatoryOfficial / ComplianceRepresentative
    -> ApiGateway (capability checking, segregation of duties)
        -> DirectiveManager (CRUD + identity lifecycle)
            -> DirectiveStore (PostgreSQL)
        -> CompilationEngine (hermetic compilation)
            -> CgIrStore (content-addressed)
        -> InspectionPipeline (DAG execution)
            -> CgIrStore (read)
            -> ExecutionArtifactStore (write)
        -> FindingFsmEngine (lifecycle state machine)
            -> FindingEventStore (append-only)
        -> AnalyticsEngine (read-only aggregates)
            -> FindingEventStore (read)
```

## Validation

Run C4 linter before merging:

```bash
python ~/.agent-global/shared/tools/software-design/c4/c4_lint.py docs/C4-Design/ --strict
```
