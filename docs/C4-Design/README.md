# Selma -- C4 Architecture Diagrams

**Version:** 8.2.4
**Date:** 2026-07-07
**Contract Alignment:** 8.2.4
**Status:** Unified C4 — three diagrams (Context, Container, Component) with aligned layer boundaries and naming

## Diagram Inventory

| Diagram | File | Level | Elements | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| Context | `c4_selma_context.puml` | Context | 8 | System boundary, primary actors, compile-time contracts, and CI/CD pipeline integration |
| Container | `c4_selma_container.puml` | Container | 21 | Operational runtime units organized by 7 layers (incl. Assurance) |
| Component | `c4_selma_component.puml` | Component | 38 components (+ actors/ext) | White-box decomposition of all 10 containers from Container Diagram v6.0.0 |

All three diagrams share the same boundary taxonomy: Request Ingress, Authoring Layer, Compilation Layer, Storage Layer, Read-side Query Layer, Runtime Layer, and Assurance Layer. The component diagram uses section comments to mark each layer and container group, keeping names and relationships aligned with the container diagram.

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
| ApiGateway | FastAPI | Container | AA-01 Mediated Feedback gate. Request ingress, capability checking, segregation of duties |
| DirectiveManager | Python | Container | CRUD and identity lifecycle (fork/merge/split/retire) |
| CompilationEngine | Python | Container | Hermetic compilation, CG-IR generation |
| PolicyAccessBlocker | Python | Container | AA-02 Policy Runtime Prohibition enforcement (compile-time, boot-time, CI/CD hooks) |
| InspectionPipeline | Python | Container | DAG execution, target evaluation |
| FindingFsmEngine | Python | Container | Finding lifecycle state machine |
| TraceabilityQueryService | Python | Container | Read-only explanation, lineage history, consistency review, and governance audit queries |
| AnalyticsEngine | Python | Container | Read-only aggregate analytics |
| ArchitecturalAuditEngine | Python | Container | AA gate validation orchestrator (AA-01 through AA-07 certification per S-30) |

### Stores

| Name | Technology | C4 Level | Description |
| :--- | :--- | :--- | :--- |
| DirectiveStore | PostgreSQL | Container | Directive graph persistence |
| CgIrStore | Content-Addressed Storage | Container | Immutable CG-IR snapshot storage |
| FindingEventStore | Append-Only Log | Container | HLC-ordered finding lifecycle events |
| AuditEventStore | Append-Only Log | Container | Security audit entries: denials, transition attempts (S-32, S-33, S-34) |
| ExecutionArtifactStore | Object Store | Container | Immutable inspection snapshots |
| ConflictArtifactStore | Append-Only Log | Container | Escalation records for unresolved conflicts (2.15) |

### External Systems

| Name | Technology | C4 Level | Description |
| :--- | :--- | :--- | :--- |
| FrozenEnvConfig | Configuration File | External Artifact | Pinned environment configuration (Content-addressed). Not a deployable unit — external configuration consumed by CompilationEngine. |
| rule_schema.json | JSON Schema | Compile-Time Contract | Structural validation contract for directives. AA-06, AA-07 subject. NEVER accessed at runtime (1.2). |
| policy_doctrine.yaml | YAML | Compile-Time Contract | Governance policy contract. AA-02 subject. MUST NOT be read during runtime (1.2). |
| CI/CD Pipeline | External System | Context | Runs AA gate certification (S-30), AA-02 Policy Runtime Prohibition static analysis, and deployment validation. |

### DirectiveManager Components (5)

| Name | Container | Description |
| :--- | :--- | :--- |
| DirectiveCapabilityGate | DirectiveManager | Verifies actor holds required capability for directive mutations (S-34) |
| DirectiveCommandHandler | DirectiveManager | Routes CRUD operations: create, update, fork, merge, split, retire, restore |
| IdentityLifecycleManager | DirectiveManager | lineage_id assignment, execution_id generation, merge: lexmin lineage |
| DirectiveVersionManager | DirectiveManager | Tracks directive versions, revision history, and lineage provenance |
| CompilationOrchestrator | DirectiveManager | Triggers compilation on directive mutation. Manages read-lock coordination |

### Compilation Engine Components (22)

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
| ConflictMetadataAssembler | CompilationEngine | Core | Candidate pair and specificity metadata assembly for frozen snapshots |
| HashComputer | CompilationEngine | Core | Dual hash model: semantic + presentation |
| EdgeHashComputer | CompilationEngine | Core | Directional edge hash computation |
| IncrementalCompilationManager | CompilationEngine | Core | Semantic hash subgraph reuse |
| SnapshotAssembler | CompilationEngine | Core | Snapshot assembly, hash computation, dry-run support |
| ProvenanceRecorder | CompilationEngine | Core | Frozen env and lineage provenance |
| ErrorHandler | CompilationEngine | Error | Aggregates validation failures, returns SchemaError |

### Inspection Pipeline Components (13)

| Name | Container | Phase | Description |
| :--- | :--- | :--- | :--- |
| InspectionCapabilityGate | InspectionPipeline | Ingress | Stage-local gate for inspection.submit and inspection.reinspect |
| TargetValidator | InspectionPipeline | Input | Target schema validation |
| ContextPopulator | InspectionPipeline | Input | Read-only context construction |
| DagScheduler | InspectionPipeline | DAG | Topological sort with parallel execution |
| EvaluatorDispatcher | InspectionPipeline | DAG | Routes by evaluator type, enforces timeout |
| EvaluatorPool | InspectionPipeline | DAG | Pure evaluator functions (extensible via plugin registration) |
| FaultTaxonomyClassifier | InspectionPipeline | DAG | 8-class fault classification |
| SkippedNodeTracker | InspectionPipeline | DAG | Dependency-failed node tracking |
| FindingAggregator | InspectionPipeline | Output | Finding collection and severity application |
| ConflictResolverRuntime | InspectionPipeline | Output | Runtime conflict resolution among concurrent findings |
| PipelineTraceRecorder | InspectionPipeline | Output | Ordered trace entry recording |
| InspectionSnapshotSerializer | InspectionPipeline | Output | Snapshot serialization |
| SystemStateHasher | InspectionPipeline | Output | System state hash computation |

### Traceability Query Components (6)

| Name | Container | Phase | Description |
| :--- | :--- | :--- | :--- |
| QueryCapabilityGate | TraceabilityQueryService | Ingress | Stage-local gate for explanation, history, audit, and consistency-review queries |
| QueryRouter | TraceabilityQueryService | Routing | Dispatches explanation, history, consistency, and audit queries |
| ExplanationQueryHandler | TraceabilityQueryService | Read | Causal chain traversal for finding.explain |
| LineageHistoryQueryHandler | TraceabilityQueryService | Read | Active directive and lineage/revision history queries |
| ConsistencyReviewQueryHandler | TraceabilityQueryService | Read | Read-only consistency review over frozen CG-IR metadata |
| GovernanceAuditQueryHandler | TraceabilityQueryService | Read | Full audit plus provenance/determinism/edge-hash verification |

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
        -> DirectiveManager (CRUD + identity lifecycle, capability gate)
            -> DirectiveStore (PostgreSQL)
        -> CompilationEngine (hermetic compilation, frozen conflict metadata, deterministic snapshot assembly)
            <- FrozenEnvConfig (pinned environment, content-addressed)
            <- rule_schema.json (structural validation, compile-time only, AA-06, AA-07)
            <- policy_doctrine.yaml (governance validation, compile-time only, AA-02)
            -> PolicyAccessBlocker (AA-02 Policy Runtime Prohibition enforcement)
            -> CgIrStore (content-addressed, AA-06 Discriminator Completeness, AA-07 Portable Serialization)
            -> ConflictArtifactStore (escalation records, compile-time only)
        -> InspectionPipeline (AA-03 Evaluator Purity, DAG execution, runtime conflict resolution over frozen inputs)
            -> CgIrStore (read)
            -> ExecutionArtifactStore (write)
            -> FindingEventStore (write findings)
        -> FindingFsmEngine (AA-04 Segregation of Duties, lifecycle state machine)
            -> FindingEventStore (lifecycle events)
            -> AuditEventStore (security audit entries)
        -> TraceabilityQueryService (explanation, lineage history, consistency review, governance audit)
            -> DirectiveStore (read)
            -> CgIrStore (read)
            -> FindingEventStore (read)
            -> AuditEventStore (read)
            -> ExecutionArtifactStore (read)
            -> ConflictArtifactStore (read)
        -> AnalyticsEngine (read-only aggregates)
            -> FindingEventStore (read)
    -> ArchitecturalAuditEngine (AA-01 through AA-07 certification per S-30)
        -> ApiGateway (validates AA-01 gate mediation)
        -> CompilationEngine (validates AA-02, AA-05, AA-06, AA-07)
        -> InspectionPipeline (validates AA-03)
        -> FindingFsmEngine (validates AA-04)
        -> AnalyticsEngine (validates AA-01)

CI/CD Pipeline
    -> PolicyAccessBlocker (AA-02 static analysis hooks)
    -> ArchitecturalAuditEngine (triggers AA gate certification)
```

AA-01 through AA-07 are certification requirements from the contract. The operational C4 views model executable runtime structure plus the ArchitecturalAuditEngine for certification. The CI/CD Pipeline is an external system that triggers AA gate certification and runs AA-02 static analysis.

## Architectural Audit (AA) Gates

The C4 design explicitly implements all 7 Architectural Audit gates from User_Stories.md S-30, with dedicated enforcement and certification components:

| AA Gate | Name | Enforcement Component | Certification Component | Spec Reference |
|---------|------|----------------------|------------------------|----------------|
| AA-01 | Mediated Feedback | ApiGateway | ArchitecturalAuditEngine | §1.2 Rule 6 |
| AA-02 | Policy Runtime Prohibition | PolicyAccessBlocker | ArchitecturalAuditEngine + CI/CD Pipeline | §1.2 Rule 7 |
| AA-03 | Evaluator Purity | EvaluatorPool | ArchitecturalAuditEngine | §2.9 |
| AA-04 | Segregation of Duties | SegregationOfDutiesEnforcer | ArchitecturalAuditEngine | §3.1-3.4, S-29, S-32, S-33 |
| AA-05 | Conflict Resolution Determinism | ConflictResolverRuntime | ArchitecturalAuditEngine | §2.15 |
| AA-06 | Discriminator Completeness | AstDiscriminatorWalker | ArchitecturalAuditEngine | §2.9, S-27, S-31 |
| AA-07 | Portable Serialization | ReferenceValidator + SnapshotAssembler | ArchitecturalAuditEngine | §2.6, §2.13 |

### AA-02 Policy Runtime Prohibition (CF-001 Remediation)

PolicyAccessBlocker enforces SPECIFICATION.md §1.2 Rule 7 at three levels:
1. **Compile-time**: Validates policy_doctrine.yaml is not in runtime data paths
2. **Boot-time**: Assertions verify policy file absence from runtime modules
3. **CI/CD**: Static analysis hooks for external pipeline verification (S-30)

### ArchitecturalAuditEngine (MF-003 Remediation)

The ArchitecturalAuditEngine is a dedicated assurance container that validates AA-01 through AA-07 compliance:
- Validates each gate against its enforcement component
- Reports pass/fail with gate-ID traceability per S-30
- Triggered by CI/CD Pipeline for certification
- Connected to all enforcement components for runtime validation

## Version Synchronization Matrix

C4-Design.md is now part of the version synchronization matrix per SPECIFICATION.md §1.2:

| Document | Version | Synchronization Status |
|----------|---------|---------------------|
| SPECIFICATION.md | 8.2.4 | Canonical |
| rule_schema.json | 8.2.4 | Synchronized |
| policy_doctrine.yaml | 8.2.4 | Synchronized |
| User_Stories.md | 8.2.4 | Synchronized |
| C4-Design/README.md | 8.2.4 | Synchronized ✅ |

## Traceability Matrix

Comprehensive mapping from runtime C4 components to SPECIFICATION.md sections, User_Stories.md stories, and AA gates.

### DirectiveManager

| Component | Diagram | Spec Section | User Story | AA Gate |
| :--- | :--- | :--- | :--- | :--- |
| DirectiveCapabilityGate | component | §3.2 | S-34 | — |
| DirectiveCommandHandler | component | §2.2-2.5 | S-01, S-02, S-03, S-08 | — |
| IdentityLifecycleManager | component | §2.2, §2.3 | S-01, S-02, S-19, S-20, S-26 | — |
| DirectiveVersionManager | component | §2.5, §3.4 | S-01, S-02, S-03, S-08 | — |
| CompilationOrchestrator | component | §2.4 | S-01, S-02 | — |

### CompilationEngine

| Component | Diagram | Spec Section | User Story | AA Gate |
| :--- | :--- | :--- | :--- | :--- |
| JsonSchemaValidator | component | §2.9 | S-27 | — |
| AstDiscriminatorWalker | component | §2.9 | S-27, S-31 | AA-06 |
| EvaluatorComplexityWalker | component | §2.9 | S-27 | — |
| LineageDagValidator | component | §2.2.3 | S-19, S-20, S-26 | — |
| ReferenceValidator | component | §9.2.6, §9.2.15 | S-21, S-31 | AA-07 |
| PolicyVersionChecker | component | §1.2 Rule 7 | — | AA-02 |
| CrossFieldValidator | component | §2.15 | S-05, S-28 | — |
| ErrorHandler | component | — | — | — |
| PolicyAccessBlocker | container | §1.2 Rule 7 | S-30 | AA-02 |
| FrozenEnvManager | component | §2.7 | S-01, S-02, S-10, S-23 | — |
| ConcurrencyManager | component | §3.4 | S-01, S-02 | — |
| IdentityResolver | component | §2.2, §2.3 | S-01, S-02, S-19, S-20, S-26 | — |
| RuleToNodeMapper | component | §2.8.1 | S-01, S-02 | — |
| ParameterMerger | component | §2.8.1 | S-01, S-02 | — |
| DependencyGraphBuilder | component | §2.8.4 | S-01, S-02 | — |
| HashComputer | component | §2.6 | S-22, S-23, S-24 | — |
| EdgeHashComputer | component | §2.6 | S-24 | — |
| IncrementalCompilationManager | component | §2.6 | S-02, S-03, S-19, S-20, S-26 | — |
| ConflictPairGenerator | component | §2.8.4, §2.15.1 | S-05, S-28 | — |
| ScopeSpecificityScorer | component | §2.8.2, §2.15 | S-05, S-28 | — |
| ConflictMetadataAssembler | component | §2.15.1 | S-05, S-28 | AA-05 |
| SnapshotAssembler | component | §2.6 | S-09, S-23 | AA-07 |
| ProvenanceRecorder | component | §2.6, §3.2 | S-01, S-02, S-22 | — |

### ArchitecturalAuditEngine

| Component | Diagram | Spec Section | User Story | AA Gate |
| :--- | :--- | :--- | :--- | :--- |
| ArchitecturalAuditEngine | container | §1.2, S-30 | S-30 | AA-01 through AA-07 |
| ApiGateway validation | container | §1.2 Rule 6 | S-30 | AA-01 |
| PolicyAccessBlocker validation | container | §1.2 Rule 7 | S-30 | AA-02 |
| EvaluatorPool validation | container | §2.9 | S-30 | AA-03 |
| SegregationOfDutiesEnforcer validation | container | §3.1-3.4 | S-30 | AA-04 |
| ConflictResolverRuntime validation | container | §2.15 | S-30 | AA-05 |
| AstDiscriminatorWalker validation | container | §2.9 | S-30 | AA-06 |
| ReferenceValidator + SnapshotAssembler validation | container | §2.6, §2.13 | S-30 | AA-07 |

### InspectionPipeline

| Component | Diagram | Spec Section | User Story | AA Gate |
| :--- | :--- | :--- | :--- | :--- |
| InspectionCapabilityGate | component | §3.2 | S-10, S-15, S-34 | — |
| TargetValidator | component | §2.10 | S-10 | — |
| ContextPopulator | component | §2.11 | S-10 | — |
| DagScheduler | component | §2.12 | S-10 | — |
| EvaluatorDispatcher | component | §2.12 | S-10 | — |
| EvaluatorPool | component | §2.9 | S-10, S-21 | AA-03 |
| FaultTaxonomyClassifier | component | §2.12, §3.3 | S-10 | — |
| SkippedNodeTracker | component | §2.12 | S-10 | — |
| FindingAggregator | component | §2.8.3, §2.9.1 | S-10 | — |
| ConflictResolverRuntime | component | §2.15, §2.15.2 | S-05, S-28 | AA-05 |
| PipelineTraceRecorder | component | §2.16.1, §3.7 | S-10, S-16 | — |
| InspectionSnapshotSerializer | component | §2.13, §3.6 | S-10, S-16, S-23 | — |
| SystemStateHasher | component | §2.13 | S-10, S-23 | — |

### TraceabilityQueryService

| Component | Diagram | Spec Section | User Story | AA Gate |
| :--- | :--- | :--- | :--- | :--- |
| QueryCapabilityGate | component | §3.2 | S-04, S-05, S-06, S-07, S-16, S-22, S-23, S-24, S-34 | — |
| QueryRouter | component | — | S-04, S-05, S-06, S-07, S-16, S-22, S-23, S-24 | — |
| ExplanationQueryHandler | component | §2.13, §3.6 | S-16 | — |
| LineageHistoryQueryHandler | component | §2.2, §2.3 | S-04, S-07 | — |
| ConsistencyReviewQueryHandler | component | §2.15, §2.15.2 | S-05, S-28 | AA-05 |
| GovernanceAuditQueryHandler | component | §2.6, §9.9 | S-06, S-22, S-23, S-24, S-30 | — |

### FindingFsmEngine

| Component | Diagram | Spec Section | User Story | AA Gate |
| :--- | :--- | :--- | :--- | :--- |
| CapabilityChecker | component | §3.1–§3.4 | S-12, S-13, S-14a, S-14b, S-14c, S-25, S-29, S-34 | — |
| SegregationOfDutiesEnforcer | component | §3.1–§3.4 | S-14a, S-29, S-32, S-33 | AA-04 |
| FsmStateMachine | component | §3.1 | S-11, S-12, S-13, S-14a, S-14b, S-14c, S-25, S-29 | — |
| HlcClockManager | component | §3.3 | S-14a, S-14b, S-14c | — |
| EventHasher | component | §2.14, §3.1 | S-14a, S-14b, S-14c | — |
| EventAppender | component | §2.14, §3.1 | S-14a, S-14b, S-14c | — |
| AuditLogger | component | §3.1, §3.2 | S-32, S-33, S-34 | — |
| DenialHandler | component | §3.2 | S-32, S-33, S-34 | — |

### CgIrStore

| Component | Diagram | Spec Section | User Story | AA Gate |
| :--- | :--- | :--- | :--- | :--- |
| NodeDeduplicator | component | §2.6 | S-02, S-23 | — |
| EdgeDeduplicator | component | §2.6 | S-24 | — |
| NodeStore | component | §2.6 | S-02, S-23 | — |
| EdgeStore | component | §2.6 | S-24 | — |
| SnapshotManifestStore | component | §2.6 | S-23 | — |
| NodeLookup | component | §2.6 | S-04, S-16 | — |
| EdgeLookup | component | §2.6 | S-05, S-24 | — |
| SnapshotLookup | component | §2.6 | S-04, S-05, S-23 | — |
| LineageTracer | component | §2.2.2, §2.2.3 | S-07, S-19, S-20, S-26 | — |

### Cross-Component User Story Coverage

Stories without a single owning component are supported by explicit container-level paths:

| Story | Support Path |
| :--- | :--- |
| S-03 (retire directive) | ApiGateway → DirectiveManager → CompilationEngine → CgIrStore |
| S-08 (restore revision) | ApiGateway → DirectiveManager → CompilationEngine |
| S-09 (impact preview) | ApiGateway → CompilationEngine (dry-run SnapshotAssembler path) |
| S-15 (reinspect) | ApiGateway → InspectionPipeline |
| S-17 (analytics) | ApiGateway → AnalyticsEngine |
| S-18 (propose change from analytics) | AnalyticsEngine → DirectiveManager via S-02 path |

## Performance & Capacity Annotations

Target performance characteristics for key components:

| Component | Throughput | Latency | Notes |
| :--- | :--- | :--- | :--- |
| ApiGateway | 1000 req/s | <10ms routing | Rate limiting: 100 req/min per actor |
| CompilationEngine | 50 compilations/s | <2s full, <200ms incremental | Per frozen_env_hash cache hit |
| PolicyAccessBlocker | — | <1ms per validation | Compile-time check; negligible overhead |
| CgIrStore | — | read: <50ms, write: <100ms | Content-addressed; dedup reduces write volume |
| FindingEventStore | 1000 events/s | append: <20ms | HLC-ordered; append-only |
| AuditEventStore | 500 entries/s | append: <10ms | Separate retention policy |
| EvaluatorPool | 1000 evaluators/s/node | <5ms/evaluator | Pure functions; parallelizable by DAG |
| SnapshotAssembler | 20 snapshots/s | <500ms | Depends on node/edge count |
| ArchitecturalAuditEngine | — | <10s full audit | Runs on CI/CD trigger; not latency-critical |

## Security Annotations

| Component | Security Properties |
| :--- | :--- |
| ApiGateway | TLS 1.3 inbound, JWT validation, rate limiting: 100 req/min, capability gate enforcement |
| Stores (all) | Encryption: AES-256 at rest, TLS 1.3 in transit |
| FindingEventStore | Integrity: SHA-256 event_hash chain, append-only guarantee |
| AuditEventStore | Integrity: SHA-256 hash chain, separate retention, tamper-evident |
| CgIrStore | Immutability: content-addressed, no mutation of existing objects |
| CompilationEngine validation boundary | AA-02 and portability enforcement through compile-time validators, boot-time assertions, and out-of-band static analysis |
| PolicyAccessBlocker | AA-02 enforcement: compile-time path validation, boot-time assertions, CI/CD static analysis hooks |
| ArchitecturalAuditEngine | AA gate certification: validates all 7 gates, reports with gate-ID traceability |
| SegregationOfDutiesEnforcer | SoD: creator_provenance check, evidence submitter check |

## Design Principle Recommendations

The following design principle improvements are recommended for future iterations (P2-P3 priority):

| ID | Principle | Recommendation | Impact | Priority |
| :--- | :--- | :--- | :--- | :--- |
| DF-001 | Graceful Degradation | Add CircuitBreaker to ApiGateway with retry logic (max 3 attempts, exponential backoff: 1s/2s/4s). Add FallbackCache for CG-IR snapshots to enable read-only mode during store outages. | Resilience | P2 |
| DF-002 | Reusability | Extract EvaluatorPool to separate EvaluatorService container. Both InspectionPipeline and CompilationEngine can depend on it. Evaluators are pure functions with zero dependencies. | Reusability | P2 |
| DF-003 | Dependency Inversion | Introduce store interfaces: ICgIrStore, IDirectiveStore, IFindingEventStore, IExecutionArtifactStore. Use dependency injection. Components depend on abstractions, not concretions. | Testability | P2 |

## Architecture Decision Records

Major architectural decisions are documented in `/docs/adr/`:

| ADR | Title | Spec Reference |
| :--- | :--- | :--- |
| ADR-001 | Hermetic Compilation Boundary | §2.7 |
| ADR-002 | Content-Addressed Storage | §2.6 |
| ADR-003 | Dual Identity Model | §2.2, §2.3 |
| ADR-004 | Policy Runtime Prohibition | §1.2 Rule 7 |
| ADR-005 | Conflict Resolution Determinism | §2.15 |

## Validation

Run C4 linter before merging:

```bash
python ~/.agent-global/shared/tools/software-design/c4/c4_lint.py docs/C4-Design/ --strict
```
