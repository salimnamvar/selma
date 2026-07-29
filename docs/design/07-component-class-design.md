# 07 — Component Class Design

Design-level classes and methods. Not a code generator; names should match
ubiquitous language. Implementation languages map these to modules/types.

## Application Service (`application_service`)

| Type | Responsibility |
| :--- | :--- |
| `ApplicationService` / router layer | Authn, capability gate, DTO validation, dispatch |
| `CapabilityGate` | Check cap; on fail emit `CapabilityDenied` via EventStore |
| `UseCaseBus` (optional) | Map action → use case handler |

**Collaborators:** all use cases; never owns store technology.

## Hermetic Compiler (`hermetic_compiler`)

| Type | Responsibility |
| :--- | :--- |
| `CompilationPipeline` | Ordered stages: ingest → identity → validate → compile → reuse → publish |
| `DetectionDiscriminator` | `detection.strategy` vs active `*_spec` + adapters |
| `ComplexityValidator` | depth/nodes/width/regex/metadata limits |
| `PortabilityValidator` | RE2, UTC, finite numbers, flags |
| `CgIrMaterializer` | nodes/edges, dual hash, depends_on sort |
| `IncrementalReusePlanner` | dirty set from lineage changes |
| `HermeticBoundary` | freeze env; no network; no policy evaluation load |

## Rule Inspector (`rule_inspector`)

| Type | Responsibility |
| :--- | :--- |
| `InspectionPipeline` | normalize → classify → select → evaluate → aggregate → report |
| `ScopeFilter` | applicability of CG-IR nodes to target |
| `DetectionRunner` | pure `evaluate(node, target, context)` |
| `FindingFactory` | map detection outcomes + deontic → finding draft + `paired_policy_ref` |
| `InspectionSnapshotBuilder` | hashes, pipeline_trace, skipped_nodes |

**Must not:** call `PolicyDoctrineReader` on evaluate path.

## Conflict Resolver (`conflict_resolver`)

| Type | Responsibility |
| :--- | :--- |
| `ConflictDetector` | within-lineage pairs; cross-lineage advisory |
| `ResolveConflict` | override → compatible_overrides → priority → specificity → recency |
| `DeferToGraph` | DFS cycle detection |
| `ConflictArtifactFactory` | binding_status, human action flags |

## Lifecycle Finder (`lifecycle_finder` / `finding_fsm_engine`)

| Type | Responsibility |
| :--- | :--- |
| `FindingFsm` | transition table from `transitions.yaml` |
| `SodPolicy` | creator_cannot_waive; submitter_cannot_approve |
| `FindingStream` | load state from events; append new events |
| `AutoTransitionRunner` | system edges after human/system triggers |

## Finding Analyzer (`finding_analyzer`)

| Type | Responsibility |
| :--- | :--- |
| `GuidanceResolver` | `paired_policy_ref` → doctrine sections |
| `AggregateQueryService` | rates, severity, trends (read-only) |
| `CausalExplainer` | finding → node → directive → revision |

**Must not:** write CG-IR, directives, or FSM state.

## Architectural Auditor (`architectural_auditor`)

| Type | Responsibility |
| :--- | :--- |
| `CertificationSuite` | run AA-01…AA-07 |
| `GateResult` | pass/fail + evidence refs |
| `CertificationArtifactWriter` | artifact_store only |

Gate definitions: `certification/gates.yaml` (including AA-02 guidance_only interpretation).

## Adapters (persistence)

| Adapter class | Port | Notes |
| :--- | :--- | :--- |
| `SqlDirectiveRepository` (example) | `DirectiveRepository` | locking semantics per contract |
| `ContentAddressedCgIrStore` | `CgIrRepository` | publish idempotent by hash |
| `AppendOnlyEventLog` | `EventStore` | hash chain + HLC |
| `ObjectArtifactStore` | `ArtifactRepository` | write-once |
| `HttpTargetGateway` | `TargetGateway` | schema validation on ingress |
| `FilesystemPolicyDoctrineReader` | `PolicyDoctrineReader` | guidance_only |

## Detection infrastructure

| Type | Responsibility |
| :--- | :--- |
| `AdapterRegistry` | `adapter_id` → implementation |
| `PatternEvaluator` / `StructuralEvaluator` / … | pure functions |
| `CompositeEvaluator` | recursive composition with complexity limits |

Language-specific code (e.g. Python AST) lives **only** behind adapters referenced from `detection.adapters[]`, not in domain.

## Shared value objects (design)

```
LineageId, ExecutionId, SnapshotHash, NodeHash, EdgeHash,
FrozenEnvHash, EventId, FindingId, HlcTimestamp,
CapabilityId, PairedPolicyRef, DetectionStrategy,
DeonticModality, Disposition, FsmState
```

## Sequence sketch — SubmitInspection

```
Interface → SubmitInspection
  → CapabilityGate(inspection.submit)
  → CgIrRepository.get(latest)
  → InspectionPipeline.run(target, snapshot)
  → ArtifactRepository.put_inspection
  → for each finding: EventStore.append(FindingCreated)  # FSM auto-open
  → return snapshot + findings (guidance optional lazy)
```

## Sequence sketch — WaiveFinding

```
Interface → WaiveFinding
  → CapabilityGate(finding.waive)
  → FindingStream.load
  → SodPolicy.creator_cannot_waive(actor, creator_provenance)
  → FindingFsm.transition(Open → Waived)
  → EventStore.append(DispositionChanged)
  → FindingFsm.auto(Waived → Closed)
  → EventStore.append(FindingClosed)
```

## Sequence sketch — ResolveGuidance

```
Interface → ResolveGuidance(finding_id)
  → load finding projection (paired_policy_ref)
  → PolicyDoctrineReader.get(ref)
  → map vocabulary + remediation + domain_examples
  → return GuidanceView
```
