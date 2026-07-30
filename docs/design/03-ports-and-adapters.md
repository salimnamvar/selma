# 03 — Ports & Adapters (Hexagonal / Clean Architecture)

## Dependency rule

```
*_interface  (rest / cli / tui)
        │
        ▼
*_application  (use cases + port interfaces)
        │
        ▼
*_domain  (aggregates, pure domain services)
        ▲
        │ implements ports
*_infrastructure  (repositories, gateways, engines)
```

Modules follow **`{resource}_{layer}`** (see [04-package-architecture.md](04-package-architecture.md)).

## Port interfaces (ROD method names)

Ports live in the **application** module of the owning resource (or `shared` application ports package if split). Method names are **Verb + Resource** (explicit; no ambiguous `find` / `save` / `execute`).

### `DirectiveRepository` — `directives_application` port

| Method | Intent |
| :--- | :--- |
| `GetDirective(lineage_id) → Directive` | Instance read |
| `ListDirectives(filter) → List[Directive]` | Collection read |
| `SaveDirective(directive) → void` | Persist current dual-document revision |
| `AllocateExecutionId() → ExecutionId` | Identity allocation |
| `GetDirectiveExecutableDocument(id) → ExecutableRuleDoc` | Compile path only |
| `GetDirectivePolicyDoctrine(ref) → GuidancePayload` | Guidance path only (`guidance_only`) |
| `ListDirectivePolicyRefs(filter) → List[PairedPolicyRef]` | Guidance catalog |

**Consumers of `GetDirectivePolicyDoctrine`:** `findings_application` only after a finding exists.  
**Forbidden:** `inspections_application` evaluation path; finding FSM transitions.

### `CompiledRulesRepository` — `compiled_rules_application` port

| Method | Intent |
| :--- | :--- |
| `GetCompiledRules(snapshot_hash) → CgIrSnapshot` | Load frozen snapshot |
| `GetLatestCompiledRules() → CgIrSnapshot` | Active ruleset |
| `PublishCompiledRules(snapshot) → void` | Immutable CAS publish |

### `FindingEventRepository` — `findings_application` port  
(formerly generic `EventStore`)

| Method | Intent |
| :--- | :--- |
| `AppendFindingEvent(event) → void` | Append lifecycle or denial event |
| `ListFindingEvents(finding_id) → List[DomainEvent]` | Stream by finding |
| `ListFindingEventsSince(hlc) → List[DomainEvent]` | Catch-up / projections |

### `ArtifactRepository` — shared artifacts port (`artifacts_infrastructure`)

| Method | Intent |
| :--- | :--- |
| `SaveInspectionArtifact(snapshot) → void` | Write-once inspection evidence |
| `GetInspectionArtifact(id) → InspectionSnapshot` | Read inspection |
| `SaveConflictArtifact(artifact) → void` | Conflict pack |
| `GetConflictArtifact(id) → ConflictArtifact` | Read conflict |
| `SaveCertificationArtifact(run) → void` | Cert report |

### `TargetSourcesGateway` — optional (`inspections_infrastructure`)

| Method | Intent |
| :--- | :--- |
| `GetTarget(target_ref) → Target` | Remote fetch by reference |
| `HashTarget(target) → TargetHash` | Content hash |

### Supporting ports

| Port | Methods (ROD-style) | Module |
| :--- | :--- | :--- |
| `DetectionEngine` | `ValidateDetectionSpec`, `EvaluateControls` | `detections_infrastructure` |
| `CapabilitySource` | `ListActorCapabilities`, `HasCapability` | `authorization_infrastructure` |
| `HashService` | `ComputeSha256`, `ComposeHashes` | `platform_infrastructure` |
| `HlcClock` | `Now`, `Advance` | `platform_infrastructure` |

## Driving adapters

| Adapter module | C4 | Calls |
| :--- | :--- | :--- |
| `rest_interface` | `clients` → `api` | `*_application` use cases |
| `cli_interface` / `tui_interface` | `clients` | subset of same use cases |

## Driven adapters

| Port | Implementation class | Module | C4 store |
| :--- | :--- | :--- | :--- |
| `DirectiveRepository` | `SqlDirectiveRepository` | `directives_infrastructure` | `directives` |
| `CompiledRulesRepository` | `ContentAddressedCompiledRulesRepository` | `compiled_rules_infrastructure` | `compiled_rules` |
| `FindingEventRepository` | `AppendOnlyFindingEventRepository` | `findings_infrastructure` | `finding_events` |
| `ArtifactRepository` | `ObjectArtifactRepository` | `artifacts_infrastructure` | `artifacts` |
| `TargetSourcesGateway` | `HttpTargetSourcesGateway` | `inspections_infrastructure` | `target_sources` |

## Explicit non-ports

- `PolicyDoctrineReader` (use `GetDirectivePolicyDoctrine`)
- Peer components for conflict analyzer / architectural auditor
- External Governance Contracts corpus
- Generic `execute()` as the only public method name on use cases

## Testing

| Level | Doubles |
| :--- | :--- |
| Domain | pure aggregates; no ports |
| Application | in-memory fakes implementing ROD port methods |
| Infrastructure | testcontainers / CAS fixtures |
| Certification | offline tool against fixtures |
