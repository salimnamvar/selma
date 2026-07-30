# 05 — Application Use Cases

Each use case is an application-layer command or query. Capabilities and
contracts are normative; this catalog is the Design Freeze surface for
orchestration.

## Conventions

- **Pre:** authenticate → load capabilities → validate input DTO  
- **Post:** map domain errors to interface errors (`403`, `404`, `409`, `400`)  
- **Idempotency:** noted where CAS/event append requires it  

## Governance authoring

| Use case | Capability | Ports | Contract / stories |
| :--- | :--- | :--- | :--- |
| `CreateDirective` | `directive.create` | DirectiveRepository, (trigger CompileDirectives) | US-CP-001, directive/* |
| `ModifyDirective` | `directive.modify` | DirectiveRepository + write lock, CompileDirectives | US-CP-003 |
| `RetireDirective` | `directive.retire` | DirectiveRepository, CompileDirectives | US-DL-001 |
| `ForkDirective` | `directive.fork` | DirectiveRepository, LineageService, CompileDirectives | US-ID-001 |
| `MergeDirectives` | `directive.merge` | same | US-ID-001 |
| `SplitDirective` | `directive.fork` (gate) | same | US-ID-001 |
| `RestoreDirectiveRevision` | `directive.restore` | DirectiveRepository, CompileDirectives | US-DL-001 |
| `GetDirective` / `ListActiveDirectives` | (read) | DirectiveRepository | US-DS-001 |

## Compilation

| Use case | Capability | Ports | Contract / stories |
| :--- | :--- | :--- | :--- |
| `CompileDirectives` | system / on mutation | DirectiveRepository.readExecutable (read lock), CgIrRepository, DetectionEngine.validate, HashService | compilation/pipeline US-CP-* |
| `ValidateDirectiveDocuments` | system / official | DirectiveRepository, DetectionEngine.validate | US-CP-002 |

**Invariant:** must not load policy doctrine for evaluation. Compiler may validate doctrine pairing/version only via repository; evaluation uses executable documents only.

## Inspection

| Use case | Capability | Ports | Contract / stories |
| :--- | :--- | :--- | :--- |
| `SubmitInspection` | `inspection.submit` | TargetGateway or body, CgIrRepository, DetectionEngine.evaluate, ArtifactRepository, EventStore (FindingCreated) | US-IP-001 |
| `ReinspectTarget` | `inspection.reinspect` | same | US-IP-001 |
| `GetInspection` | (read) | ArtifactRepository | — |
| `ExplainFinding` | `finding.view` | EventStore, CgIrRepository, DirectiveRepository.readPolicyDoctrine (guidance) | US-IP-002 |

**Invariant:** Inspection evaluation path (`inspection` component) does **not** call `DirectiveRepository.readPolicyDoctrine`.

## Finding lifecycle

| Use case | Capability | Ports | SoD | Stories |
| :--- | :--- | :--- | :--- | :--- |
| `AcknowledgeFinding` | `finding.acknowledge` | EventStore | — | US-FL-010 |
| `SubmitEvidence` | `evidence.submit` | EventStore | record submitter | US-FL-010 |
| `ApproveRemediation` | `finding.approve_remediation` | EventStore | submitter ≠ actor | US-SD-002 |
| `RejectRemediation` | `finding.reject_remediation` | EventStore | — | US-FL-010 |
| `ReopenFinding` | `finding.reject_remediation` | EventStore | comments required | US-FL-010 |
| `DismissFinding` | `finding.dismiss` | EventStore | — | US-FL-001 |
| `WaiveFinding` | `finding.waive` | EventStore, CgIrRepository (creator_provenance) | actor ∉ creator_provenance | US-SD-001 |
| `ListFindings` / `GetFinding` | `finding.view` | EventStore / projection | — | US-FC-001 |

System automatic transitions (Created→Open, Evidence→Pending, Verified/Waived→Closed) run **inside** the FSM domain service when appending events—not as separate human use cases.

## Conflict

| Use case | Capability | Ports | Stories |
| :--- | :--- | :--- | :--- |
| `ReviewConflicts` | regulatory inspect capability set | CgIrRepository, ArtifactRepository | US-CD-001, US-PR-001 |
| `ResolveConflictManually` | official | ArtifactRepository, possibly directive change path | US-CD-001 |

## Guidance & analytics

| Use case | Capability | Ports | Notes |
| :--- | :--- | :--- | :--- |
| `ResolveGuidance` | `finding.view` | DirectiveRepository.readPolicyDoctrine, rule metadata | guidance_only |
| `FindingAggregates` | analytics-oriented | EventStore read | no CG-IR write (AA-01) |
| `ProposeDirectiveFromAnalytics` | human | returns proposal; mutation via ModifyDirective | mediated feedback |

## Certification

| Use case | Capability | Ports | Stories |
| :--- | :--- | :--- | :--- |
| `RunArchitecturalCertification` | offline / CI tool (not in-process C4 peer) | fixtures + ArtifactRepository | US-GA-001, AA-01…AA-07 |

## Interface mapping (REST families)

See `contracts/interfaces/rest_api.yaml`:

| Family | Use cases |
| :--- | :--- |
| `directives` | Create/Modify/Get/lifecycle ops |
| `inspections` | Submit/Get/Reinspect |
| `findings` | List/Get/FSM transitions |
| `guidance` | ResolveGuidance (see also policy runtime_usage endpoints) |
| `certification` | RunArchitecturalCertification |

CLI/TUI expose a **subset** with identical application use cases (no parallel domain logic).
