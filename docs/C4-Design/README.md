# Selma -- C4 Architecture Diagrams

**Version:** 8.2.4
**Date:** 2026-07-06
**Contract Alignment:** 8.2.4
**Status:** Enhanced Design — audit v2.1.0 remediated with AA gate enforcement

## Diagram Inventory

| Diagram | File | Level | Elements | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| Context | `c4_selma_context.puml` | Context | 6 | System boundary, actors, external dependencies, policy prohibition (AA-02) |
| Container | `c4_selma_container.puml` | Container | 18 | Deployable units organized by 5 layers with AA gate enforcement |
| CompilationEngine | `c4_selma_component_compilation.puml` | Component | 27 | Three-pass validation, hermetic boundary, compilation core, AA-02, AA-05, AA-06, AA-07 gates |
| InspectionPipeline | `c4_selma_component_inspection.puml` | Component | 15 | DAG execution, fault taxonomy, finding aggregation (AA-03 gate) |
| FindingFsmEngine | `c4_selma_component_finding.puml` | Component | 8 | State machine with SoD enforcement (AA-04 gate), audit trail, and separate audit store |
| CgIrStore | `c4_selma_component_cgir_store.puml` | Component | 9 | Content-addressed storage with deduplication and lineage tracing (AA-06, AA-07) |

## Component Inventory

### Actors

| Name | Type | C4 Level | Description |
| :--- | :--- | :--- | :--- |
| RegulatoryOfficial | Person | Context, Container | Rule Author and Governance Owner |
| ComplianceRepresentative | Person | Context, Container | Compliance Seeker and Remediation Owner |
| System | Person_Ext | Context, Container | Automated Actor. Submits inspections, views findings |

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
| FindingEventStore | Append-Only Log | Container | HLC-ordered finding lifecycle events |
| AuditEventStore | Append-Only Log | Container | Security audit entries: denials, transition attempts (S-32, S-33, S-34) |
| ExecutionArtifactStore | Object Store | Container | Immutable inspection snapshots |
| FrozenEnvConfig | Configuration | Container | Pinned environment configuration (Content-addressed) |

### External Systems

| Name | Type | C4 Level | Description |
| :--- | :--- | :--- | :--- |
| CICDPipeline | System_Ext | Context | Scans runtime source for policy references |
| PolicyDocument | System_Ext | Context | Governance intent. Authoring-time ONLY |

### Compilation Engine Components (27)

| Name | Container | Pass | Description |
| :--- | :--- | :--- | :--- |
| JsonSchemaValidator | CompilationEngine | Pass 1 | First-pass structural filter (Draft-07) |
| AstDiscriminatorWalker | CompilationEngine | Pass 2 | evaluator_type + config verification |
| EvaluatorComplexityWalker | CompilationEngine | Pass 2 | Complexity limits enforcement |
| LineageDagValidator | CompilationEngine | Pass 2 | Cycle detection, depth bound, temporal ordering |
| ReferenceValidator | CompilationEngine | Pass 2 | RE2, UTC timestamps, finite numerics, regex flags |
| PolicyVersionChecker | CompilationEngine | Pass 2 | Cross-file version consistency |
| CrossFieldValidator | CompilationEngine | Pass 3 | scope/priority consistency, acyclicity |
| FrozenEnvManager | CompilationEngine | Hermetic | Pins environment, computes frozen_env_hash |
| ConcurrencyManager | CompilationEngine | Core | Read lock for compilation (DirectiveManager has own control) |
| IdentityResolver | CompilationEngine | Core | lineage_id/execution_id assignment |
| RuleToNodeMapper | CompilationEngine | Core | Directive-to-CG-IR node transformation |
| ParameterMerger | CompilationEngine | Core | Shallow merge of evaluator configs |
| DependencyGraphBuilder | CompilationEngine | Core | DAG construction, acyclicity validation |
| ConflictPairGenerator | CompilationEngine | Core | Candidate pair generation from conflicts_with |
| ScopeSpecificityScorer | CompilationEngine | Core | Specificity scoring for conflict resolution |
| ConflictResolver | CompilationEngine | Core | Precedence chain (sole implementation per §2.15) |
| HashComputer | CompilationEngine | Core | Dual hash model: semantic + presentation |
| EdgeHashComputer | CompilationEngine | Core | Directional edge hash computation |
| IncrementalCompilationManager | CompilationEngine | Core | Semantic hash subgraph reuse |
| SnapshotAssembler | CompilationEngine | Core | Snapshot assembly, hash computation, dry-run support |
| ProvenanceRecorder | CompilationEngine | Core | Frozen env and lineage provenance |
| ErrorHandler | CompilationEngine | Error | Aggregates validation failures, returns SchemaError |
| PolicyAccessBlocker | CompilationEngine | AA-02 | Validates NO runtime access to policy_doctrine.yaml. Static analysis hooks for CI/CD (S-30). |
| AAGateValidator | CompilationEngine | AA-01-07 | Validates all AA-01 through AA-07 gates: Mediated Feedback, Policy Runtime Prohibition, Evaluator Purity, SoD, Conflict Resolution Determinism, Discriminator Completeness, Portable Serialization. |

### Inspection Pipeline Components (12)

| Name | Container | Phase | Description |
| :--- | :--- | :--- | :--- |
| TargetValidator | InspectionPipeline | Input | Target schema validation |
| ContextPopulator | InspectionPipeline | Input | Read-only context construction |
| DagScheduler | InspectionPipeline | DAG | Topological sort with parallel execution |
| EvaluatorDispatcher | InspectionPipeline | DAG | Routes by evaluator type, enforces timeout |
| EvaluatorPool | InspectionPipeline | DAG | Pure evaluator functions (extensible via plugin registration) |
| FaultTaxonomyClassifier | InspectionPipeline | DAG | 8-class fault classification |
| SkippedNodeTracker | InspectionPipeline | DAG | Dependency-failed node tracking |
| FindingAggregator | InspectionPipeline | Output | Finding collection and severity application |
| PipelineTraceRecorder | InspectionPipeline | Output | Ordered trace entry recording |
| InspectionSnapshotSerializer | InspectionPipeline | Output | Snapshot serialization |
| SystemStateHasher | InspectionPipeline | Output | System state hash computation |

### Finding FSM Components (8)

| Name | Container | Description |
| :--- | :--- | :--- |
| CapabilityChecker | FindingFsmEngine | Capability matrix enforcement |
| SegregationOfDutiesEnforcer | FindingFsmEngine | SoD constraint enforcement |
| FsmStateMachine | FindingFsmEngine | 10 states, 11 transitions |
| HlcClockManager | FindingFsmEngine | Hybrid Logical Clock management |
| EventHasher | FindingFsmEngine | Event integrity hashing |
| EventAppender | FindingFsmEngine | Atomic event append to FindingEventStore |
| AuditLogger | FindingFsmEngine | Transition audit logging to AuditEventStore |
| DenialHandler | FindingFsmEngine | 403 CapabilityDenied handling |

### CG-IR Store Components (9)

| Name | Container | Description |
| :--- | :--- | :--- |
| NodeDeduplicator | CgIrStore | Node deduplication by hash |
| EdgeDeduplicator | CgIrStore | Edge deduplication by hash |
| NodeStore | CgIrStore | Content-addressed node storage |
| EdgeStore | CgIrStore | Content-addressed edge storage |
| SnapshotManifestStore | CgIrStore | Snapshot manifest persistence |
| NodeLookup | CgIrStore | Multi-index node query |
| EdgeLookup | CgIrStore | Multi-index edge query |
| SnapshotLookup | CgIrStore | Snapshot query and retrieval |
| LineageTracer | CgIrStore | Lineage traversal and parent queries |

## Architecture Pattern

```
RegulatoryOfficial / ComplianceRepresentative / System
    -> ApiGateway (AA-01 Mediated Feedback, capability checking, segregation of duties)
        -> DirectiveManager (CRUD + identity lifecycle)
            -> DirectiveStore (PostgreSQL)
        -> CompilationEngine (hermetic compilation, AA-02 Policy Runtime Prohibition enforcement)
            -> FrozenEnvConfig (pinned environment, content-addressed)
            -> CgIrStore (content-addressed, AA-06 Discriminator Completeness, AA-07 Portable Serialization)
        -> InspectionPipeline (AA-03 Evaluator Purity, DAG execution, no runtime conflict resolution)
            -> CgIrStore (read)
            -> ExecutionArtifactStore (write)
            -> FindingEventStore (write findings)
        -> FindingFsmEngine (AA-04 Segregation of Duties, lifecycle state machine)
            -> FindingEventStore (lifecycle events)
            -> AuditEventStore (security audit entries)
        -> AnalyticsEngine (read-only aggregates)
            -> FindingEventStore (read)
    <- CICDPolicyPipeline (static analysis, AA-02 prohibition enforcement)
    x  PolicyDocument (PROHIBITED at runtime - AA-02 gate enforced)
```

## Architectural Audit (AA) Gates

The C4 design now explicitly implements all 7 Architectural Audit gates from User_Stories.md S-30:

| AA Gate | Name | Implementation | Spec Reference |
|---------|------|----------------|----------------|
| AA-01 | Mediated Feedback | ApiGateway request/response mediation | §1.2 Rule 6 |
| AA-02 | Policy Runtime Prohibition | PolicyAccessBlocker component + CI/CD Pipeline enforcement | §1.2 Rule 7 |
| AA-03 | Evaluator Purity | EvaluatorPool pure functions, no IO, no randomness | §2.9 |
| AA-04 | Segregation of Duties | SegregationOfDutiesEnforcer component | §3.1-3.4, S-29, S-32, S-33 |
| AA-05 | Conflict Resolution Determinism | ConflictResolver component + compiled_at exclusion | §2.15 |
| AA-06 | Discriminator Completeness | AstDiscriminatorWalker component | §2.9, S-27, S-31 |
| AA-07 | Portable Serialization | Snapshot serialization with excluded compiled_at | §2.6, §2.13 |

## Version Synchronization Matrix

C4-Design.md is now part of the version synchronization matrix per SPECIFICATION.md §1.2:

| Document | Version | Synchronization Status |
|----------|---------|---------------------|
| SPECIFICATION.md | 8.2.4 | Canonical |
| rule_schema.json | 8.2.4 | Synchronized |
| policy_doctrine.yaml | 8.2.4 | Synchronized |
| User_Stories.md | 8.2.4 | Synchronized |
| C4-Design/README.md | 8.2.4 | Synchronized ✅ |

## Validation

Run C4 linter before merging:

```bash
python ~/.agent-global/shared/tools/software-design/c4/c4_lint.py docs/C4-Design/ --strict
```
