# Selma -- C4 Architecture Diagrams

**Version:** 8.2.4
**Date:** 2026-07-06
**Contract Alignment:** 8.2.4
**Status:** Enhanced Design — audit v2.1.0 remediated with runtime and assurance concerns separated

## Diagram Inventory

| Diagram | File | Level | Elements | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| Context | `c4_selma_context.puml` | Context | 4 | System boundary and primary actors |
| Container | `c4_selma_container.puml` | Container | 16 | Operational runtime units organized by 6 layers |
| CompilationEngine Overview | `c4_selma_component_compilation.puml` | Component | 10 | High-level view of compilation subsystems — delegates to 4 focused diagrams |
| CompilationEngine — Validation | `c4_selma_component_compilation_validation.puml` | Component | 10 | Three-pass validation pipeline with normative compile-time validators |
| CompilationEngine — Core | `c4_selma_component_compilation_core.puml` | Component | 9 | Hermetic compilation: identity, transformation, hashing, incremental |
| CompilationEngine — Conflict | `c4_selma_component_compilation_conflict.puml` | Component | 5 | Candidate conflict preparation, snapshot assembly, provenance |
| InspectionPipeline | `c4_selma_component_inspection.puml` | Component | 17 | DAG execution, fault taxonomy, finding aggregation, runtime conflict resolution (AA-03 gate) |
| FindingFsmEngine | `c4_selma_component_finding.puml` | Component | 8 | State machine with SoD enforcement (AA-04 gate), audit trail, and separate audit store |
| TraceabilityQueryService | `c4_selma_component_traceability_query.puml` | Component | 12 | Read-only explanation, lineage history, consistency review, and governance audit queries |
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
| TraceabilityQueryService | Python | Container | Read-only explanation, lineage history, consistency review, and governance audit queries |
| AnalyticsEngine | Python | Container | Read-only aggregate analytics |

### Stores

| Name | Technology | C4 Level | Description |
| :--- | :--- | :--- | :--- |
| DirectiveStore | PostgreSQL | Container | Directive graph persistence |
| CgIrStore | Content-Addressed Storage | Container | Immutable CG-IR snapshot storage |
| FindingEventStore | Append-Only Log | Container | HLC-ordered finding lifecycle events |
| AuditEventStore | Append-Only Log | Container | Security audit entries: denials, transition attempts (S-32, S-33, S-34) |
| ExecutionArtifactStore | Object Store | Container | Immutable inspection snapshots |

### External Configuration Artifact

| Name | Technology | C4 Level | Description |
| :--- | :--- | :--- | :--- |
| FrozenEnvConfig | Configuration File | External Artifact | Pinned environment configuration (Content-addressed). Not a deployable unit — external configuration consumed by CompilationEngine. |

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
        -> DirectiveManager (CRUD + identity lifecycle)
            -> DirectiveStore (PostgreSQL)
        -> CompilationEngine (hermetic compilation, frozen conflict metadata, deterministic snapshot assembly)
            <- FrozenEnvConfig (pinned environment, content-addressed)
            -> CgIrStore (content-addressed, AA-06 Discriminator Completeness, AA-07 Portable Serialization)
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
        -> AnalyticsEngine (read-only aggregates)
            -> FindingEventStore (read)
```

AA-01 through AA-07 remain certification requirements from the contract, but the operational C4 views now model only executable runtime structure. Out-of-band assurance checks such as CI static analysis and certification gates are intentionally excluded from the runtime diagrams.

## Architectural Audit (AA) Gates

The C4 design now explicitly implements all 7 Architectural Audit gates from User_Stories.md S-30:

| AA Gate | Name | Implementation | Spec Reference |
|---------|------|----------------|----------------|
| AA-01 | Mediated Feedback | ApiGateway mediation with read-only AnalyticsEngine and TraceabilityQueryService boundaries | §1.2 Rule 6 |
| AA-02 | Policy Runtime Prohibition | Architectural runtime boundary plus out-of-band static analysis and boot-time checks | §1.2 Rule 7 |
| AA-03 | Evaluator Purity | EvaluatorPool pure functions, no IO, no randomness | §2.9 |
| AA-04 | Segregation of Duties | SegregationOfDutiesEnforcer component | §3.1-3.4, S-29, S-32, S-33 |
| AA-05 | ConflictMetadataAssembler + ConflictResolverRuntime over frozen snapshot inputs | §2.15 |
| AA-06 | Discriminator Completeness | AstDiscriminatorWalker component | §2.9, S-27, S-31 |
| AA-07 | Portable serialization validators plus snapshot hashing with excluded compiled_at | §2.6, §2.13 |

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

### CompilationEngine

| Component | Diagram | Spec Section | User Story | AA Gate |
| :--- | :--- | :--- | :--- | :--- |
| JsonSchemaValidator | validation | §2.9 | S-27 | — |
| AstDiscriminatorWalker | validation | §2.9 | S-27, S-31 | AA-06 |
| EvaluatorComplexityWalker | validation | §2.9 | S-27 | — |
| LineageDagValidator | validation | §2.2.3 | S-19, S-20, S-26 | — |
| ReferenceValidator | validation | §9.2.6, §9.2.15 | S-21, S-31 | AA-07 |
| PolicyVersionChecker | validation | §1.2 Rule 7 | — | — |
| CrossFieldValidator | validation | §2.15 | S-05, S-28 | — |
| ErrorHandler | validation | — | — | — |
| FrozenEnvManager | core | §2.7 | S-01, S-02, S-10, S-23 | — |
| ConcurrencyManager | core | §3.4 | S-01, S-02 | — |
| IdentityResolver | core | §2.2, §2.3 | S-01, S-02, S-19, S-20, S-26 | — |
| RuleToNodeMapper | core | §2.8.1 | S-01, S-02 | — |
| ParameterMerger | core | §2.8.1 | S-01, S-02 | — |
| DependencyGraphBuilder | core | §2.8.4 | S-01, S-02 | — |
| HashComputer | core | §2.6 | S-22, S-23, S-24 | — |
| EdgeHashComputer | core | §2.6 | S-24 | — |
| IncrementalCompilationManager | core | §2.6 | S-02, S-03, S-19, S-20, S-26 | — |
| ConflictPairGenerator | conflict | §2.8.4, §2.15.1 | S-05, S-28 | — |
| ScopeSpecificityScorer | conflict | §2.8.2, §2.15 | S-05, S-28 | — |
| ConflictMetadataAssembler | conflict | §2.15.1 | S-05, S-28 | — |
| SnapshotAssembler | conflict | §2.6 | S-09, S-23 | — |
| ProvenanceRecorder | conflict | §2.6, §3.2 | S-01, S-02, S-22 | — |

### InspectionPipeline

| Component | Diagram | Spec Section | User Story | AA Gate |
| :--- | :--- | :--- | :--- | :--- |
| InspectionCapabilityGate | inspection | §3.2 | S-10, S-15, S-34 | — |
| TargetValidator | inspection | §2.10 | S-10 | — |
| ContextPopulator | inspection | §2.11 | S-10 | — |
| DagScheduler | inspection | §2.12 | S-10 | — |
| EvaluatorDispatcher | inspection | §2.12 | S-10 | — |
| EvaluatorPool | inspection | §2.9 | S-10, S-21 | AA-03 |
| FaultTaxonomyClassifier | inspection | §2.12, §3.3 | S-10 | — |
| SkippedNodeTracker | inspection | §2.12 | S-10 | — |
| FindingAggregator | inspection | §2.8.3, §2.9.1 | S-10 | — |
| ConflictResolverRuntime | inspection | §2.15, §2.15.2 | S-05, S-28 | AA-05 |
| PipelineTraceRecorder | inspection | §2.16.1, §3.7 | S-10, S-16 | — |
| InspectionSnapshotSerializer | inspection | §2.13, §3.6 | S-10, S-16, S-23 | — |
| SystemStateHasher | inspection | §2.13 | S-10, S-23 | — |

### TraceabilityQueryService

| Component | Diagram | Spec Section | User Story | AA Gate |
| :--- | :--- | :--- | :--- | :--- |
| QueryCapabilityGate | traceability_query | §3.2 | S-04, S-05, S-06, S-07, S-16, S-22, S-23, S-24, S-34 | — |
| QueryRouter | traceability_query | — | S-04, S-05, S-06, S-07, S-16, S-22, S-23, S-24 | — |
| ExplanationQueryHandler | traceability_query | §2.13, §3.6 | S-16 | — |
| LineageHistoryQueryHandler | traceability_query | §2.2, §2.3 | S-04, S-07 | — |
| ConsistencyReviewQueryHandler | traceability_query | §2.15, §2.15.2 | S-05, S-28 | AA-05 |
| GovernanceAuditQueryHandler | traceability_query | §2.6, §9.9 | S-06, S-22, S-23, S-24, S-30 | — |

### FindingFsmEngine

| Component | Diagram | Spec Section | User Story | AA Gate |
| :--- | :--- | :--- | :--- | :--- |
| CapabilityChecker | finding | §3.1–§3.4 | S-12, S-13, S-14a, S-14b, S-14c, S-25, S-29, S-34 | — |
| SegregationOfDutiesEnforcer | finding | §3.1–§3.4 | S-14a, S-29, S-32, S-33 | AA-04 |
| FsmStateMachine | finding | §3.1 | S-11, S-12, S-13, S-14a, S-14b, S-14c, S-25, S-29 | — |
| HlcClockManager | finding | §3.3 | S-14a, S-14b, S-14c | — |
| EventHasher | finding | §2.14, §3.1 | S-14a, S-14b, S-14c | — |
| EventAppender | finding | §2.14, §3.1 | S-14a, S-14b, S-14c | — |
| AuditLogger | finding | §3.1, §3.2 | S-32, S-33, S-34 | — |
| DenialHandler | finding | §3.2 | S-32, S-33, S-34 | — |

### CgIrStore

| Component | Diagram | Spec Section | User Story | AA Gate |
| :--- | :--- | :--- | :--- | :--- |
| NodeDeduplicator | cgir_store | §2.6 | S-02, S-23 | — |
| EdgeDeduplicator | cgir_store | §2.6 | S-24 | — |
| NodeStore | cgir_store | §2.6 | S-02, S-23 | — |
| EdgeStore | cgir_store | §2.6 | S-24 | — |
| SnapshotManifestStore | cgir_store | §2.6 | S-23 | — |
| NodeLookup | cgir_store | §2.6 | S-04, S-16 | — |
| EdgeLookup | cgir_store | §2.6 | S-05, S-24 | — |
| SnapshotLookup | cgir_store | §2.6 | S-04, S-05, S-23 | — |
| LineageTracer | cgir_store | §2.2.2, §2.2.3 | S-07, S-19, S-20, S-26 | — |

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
| CgIrStore | — | read: <50ms, write: <100ms | Content-addressed; dedup reduces write volume |
| FindingEventStore | 1000 events/s | append: <20ms | HLC-ordered; append-only |
| AuditEventStore | 500 entries/s | append: <10ms | Separate retention policy |
| EvaluatorPool | 1000 evaluators/s/node | <5ms/evaluator | Pure functions; parallelizable by DAG |
| SnapshotAssembler | 20 snapshots/s | <500ms | Depends on node/edge count |

## Security Annotations

| Component | Security Properties |
| :--- | :--- |
| ApiGateway | TLS 1.3 inbound, JWT validation, rate limiting, capability gate enforcement |
| Stores (all) | Encryption: AES-256 at rest, TLS 1.3 in transit |
| FindingEventStore | Integrity: SHA-256 event_hash chain, append-only guarantee |
| AuditEventStore | Integrity: SHA-256 hash chain, separate retention, tamper-evident |
| CgIrStore | Immutability: content-addressed, no mutation of existing objects |
| CompilationEngine validation boundary | AA-02 and portability enforcement through compile-time validators, boot-time assertions, and out-of-band static analysis |
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
