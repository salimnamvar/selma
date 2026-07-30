# 05 — Application Use Cases

Each use case is an application-layer **resource operation**. Naming follows
**Resource-Oriented Design**: **Verb + Resource** (+ sub-resource when needed).
Modules live in `{resource}_application`.

## Conventions

- **Pre:** authenticate → `HasCapability` → validate request DTO  
- **Post:** map domain errors to `403` / `404` / `409` / `400`  
- **Primary method:** ROD name (not bare `execute`); e.g. `CreateDirective(req) → Directive`  
- **Idempotency:** noted where CAS / event append requires it  

## Roles (who may call what)

Selma keeps **two distinct governance roles** (plus system). They are **not** merged:

| Role ID | Acts for | Typical coding-governance mapping |
| :--- | :--- | :--- |
| `regulatory_official` | Rule authority | Platform / org rule authors (human or agent) |
| `compliance_representative` | Regulated project | Project teams / coding agents under inspection |
| `system` | Automation | Pipelines submitting inspections |

**Why not one role:** SoD requires that directive authors cannot waive findings from their own rules, and regulated parties cannot author or waive rules. Merging roles collapses that control. One *person* may hold different roles in different tenants; one *capability set* must not.

See `authorization/role_matrix.yaml`.

---

## Directives — `directives_application`

| Operation (ROD) | Capability | Ports | Contract |
| :--- | :--- | :--- | :--- |
| `CreateDirective` | `directive.create` | `SaveDirective`, then `CompileDirectives` | US-CP-001 |
| `UpdateDirective` | `directive.modify` | `GetDirective`, `SaveDirective`, write lock, compile | US-CP-003 |
| `RetireDirective` | `directive.retire` | `SaveDirective`, compile | US-DL-001 |
| `ForkDirective` | `directive.fork` | LineageService, `SaveDirective`, compile | US-ID-001 |
| `MergeDirectives` | `directive.merge` | same | US-ID-001 |
| `SplitDirective` | `directive.fork` | same | US-ID-001 |
| `RestoreDirective` | `directive.restore` | `SaveDirective`, compile | US-DL-001 |
| `GetDirective` | (read) | `GetDirective` | US-DS-001 |
| `ListDirectives` | (read) | `ListDirectives` | US-DS-001 |
| `GetDirectiveExecutableDocument` | system / compile | `GetDirectiveExecutableDocument` | compile path |
| `GetDirectivePolicyDoctrine` | `finding.view` (via guidance) | `GetDirectivePolicyDoctrine` | guidance_only |

---

## Compiled rules — `compiled_rules_application`

| Operation (ROD) | Capability | Ports | Notes |
| :--- | :--- | :--- | :--- |
| `CompileDirectives` | system / on mutation | `GetDirectiveExecutableDocument` (read lock), `PublishCompiledRules`, `ValidateDetectionSpec` | no doctrine evaluation |
| `ValidateDirectiveDocuments` | system / official | `GetDirective`, `ValidateDetectionSpec` | schema + pairing |
| `GetCompiledRules` | system / inspection | `GetCompiledRules` / `GetLatestCompiledRules` | frozen snapshot |

---

## Inspections — `inspections_application`

| Operation (ROD) | Capability | Ports | Notes |
| :--- | :--- | :--- | :--- |
| `CreateInspection` | `inspection.submit` | target body or `GetTarget`, `GetLatestCompiledRules`, `EvaluateControls`, `SaveInspectionArtifact`, opens findings | primary: inline target |
| `CreateInspectionReinspection` | `inspection.reinspect` | same | — |
| `GetInspection` | (read) | `GetInspectionArtifact` | — |

**Invariant:** inspection evaluation **must not** call `GetDirectivePolicyDoctrine`.

Pipeline steps (internal, not separate public resources): `NormalizeTarget` → `ClassifyTarget` → `SelectControls` → `EvaluateControls` → `AggregateDetectionOutcomes` → `SaveInspectionArtifact`.

---

## Findings — `findings_application`

| Operation (ROD) | Capability | SoD | Ports |
| :--- | :--- | :--- | :--- |
| `CreateFinding` | system | — | `AppendFindingEvent` |
| `AcknowledgeFinding` | `finding.acknowledge` | — | `AppendFindingEvent` |
| `SubmitFindingEvidence` | `evidence.submit` | record submitter | `SaveInspectionArtifact` / evidence ref + event |
| `ApproveFindingRemediation` | `finding.approve_remediation` | submitter ≠ actor | `AppendFindingEvent` |
| `RejectFindingRemediation` | `finding.reject_remediation` | — | `AppendFindingEvent` |
| `DismissFinding` | `finding.dismiss` | official only | `AppendFindingEvent` |
| `WaiveFinding` | `finding.waive` | actor ∉ creator_provenance | `AppendFindingEvent`, compiled rules provenance |
| `GetFinding` | `finding.view` | — | event projection |
| `ListFindings` | `finding.view` | — | event projection |
| `GetFindingGuidance` | `finding.view` | — | `GetDirectivePolicyDoctrine` (**guidance_only**) |
| `GetFindingExplanation` | `finding.view` | — | events + compiled rules |
| `ListFindingAggregates` | `analytics.view` | no CG-IR write | events |

System transitions (Created→Open, …) run inside `FindingFsm` when appending events.

---

## Conflicts — `conflicts_application`

| Operation (ROD) | Capability | Ports |
| :--- | :--- | :--- |
| `DetectDirectiveConflict` | system | directives + `ResolveConflict` domain service |
| `ListConflictArtifacts` | official set | `GetConflictArtifact` / list |
| `ReviewConflictArtifact` | official | `SaveConflictArtifact` |
| `ResolveConflictManually` | official | artifacts; may lead to `UpdateDirective` |

`ResolveConflict` algorithm remains a **domain service** in `conflicts_domain`, not a C4 peer component.

---

## Certifications — `certifications_application` (offline / CI tool)

| Operation (ROD) | Capability | Ports |
| :--- | :--- | :--- |
| `CreateCertificationRun` | CI / tool | fixtures + `SaveCertificationArtifact` |
| `GetCertificationRun` | read | artifacts |

Not an in-process C4 peer of inspection/findings.

---

## REST resource mapping (ROD URLs)

| Collection | Operations |
| :--- | :--- |
| `/directives` | Create, List, Get, Update, Retire, Fork, Merge, Split, Restore |
| `/compiled-rules` | Get (or side-effect of compile) |
| `/inspections` | Create, Get, reinspect |
| `/findings` | List, Get, lifecycle verbs as custom methods or sub-resources |
| `/findings/{id}/guidance` | `GetFindingGuidance` |
| `/artifacts` | Get inspection/conflict/cert packs |
| `/certifications` | Create/Get (tool) |

CLI/TUI call the **same** application operations (no parallel domain logic).
