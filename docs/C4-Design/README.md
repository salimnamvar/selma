# Selma -- C4 Architecture Diagrams

**Version:** 8.2.4  
**Date:** 2026-07-10  
**Contract Alignment:** 8.2.4  
**Status:** Unified C4 — three diagrams (Context, Container, Component) aligned with SPECIFICATION.md and User_Stories.md  
**Structural source of truth:** PlantUML sources (ADR-AIP-001)  
**AIP:** `AIP.md` v1.3.0 · **Change log:** `CHANGE_LOG.md`  
**Deployability audit:** `CONTAINER_DEPLOYABILITY_AUDIT.md`

## Diagram Inventory

| Diagram   | File                      | Level     | Elements                         | Purpose                                                                                              |
| :-------- | :------------------------ | :-------- | :------------------------------- | :--------------------------------------------------------------------------------------------------- |
| Context   | `c4_selma_context.puml`   | Context   | 3 actors + Selma + 6 externals   | System boundary, governance actors, compile-time contracts, CI/CD certification trigger              |
| Container | `c4_selma_container.puml` | Container | **12** containers (+ actors/ext) | Runtime units: hermetic compile, CG-IR, inspection, conflict, FSM, analytics, audit store, AA engine |
| Component | `c4_selma_component.puml` | Component | **58** components (+ actors/ext) | White-box decomposition of all 12 containers                                                         |

**Constraint:** Exactly three C4 diagram files. No additional C4 diagrams.

## Actors

| Name (PlantUML ID)                           | Type       | Description                                                                   |
| :------------------------------------------- | :--------- | :---------------------------------------------------------------------------- |
| Regulatory Official (`regulatory_official`)  | Person     | Full directive lifecycle, conflict.resolve, finding disposition; SoD on waive |
| Compliance Representative (`compliance_rep`) | Person     | Targets, acknowledge, evidence; SoD on remediation approve                    |
| Automated Service Account (`system_actor`)   | Person_Ext | inspection.submit, finding.view, analytics.view only                          |

## External Systems

| Name (PlantUML ID)                                      | Description                                                                                       |
| :------------------------------------------------------ | :------------------------------------------------------------------------------------------------ |
| Governance Contracts (`governance_contracts`)           | policy_doctrine.yaml (runtime-prohibited), rule_schema.json, directive tables — compile-time only |
| Identity & Access Management (`iam`)                    | OAuth 2.0 / OIDC identity and capability assertions                                               |
| CI/CD Pipeline (`cicd`)                                 | Triggers Architectural Audit Engine (S-30); AA-02 static analysis hooks                           |
| Target & Regulated Entity Systems (`regulated_systems`) | Domain-agnostic inspection targets                                                                |
| Audit & Observability Platform (`audit_platform`)       | Long-term retention of finding stream, denial audit, artifacts, certifications                    |
| Remediation & Case Management (`remediation_systems`)   | Mediated finding notifications only (AA-01)                                                       |

## Containers (12)

All twelve containers are **valid, independently deployable runtime units** (C4 container semantics). They support independent packaging (Docker/OCI, Kubernetes Deployments/StatefulSets/Jobs, managed services), scaling, failure isolation, and versioning while enforcing Selma’s isolation and auditability invariants.

| Name (PlantUML ID)                                        | Technology                | Description                                                     |
| :-------------------------------------------------------- | :------------------------ | :-------------------------------------------------------------- |
| API Gateway (`api_gateway`)                               | FastAPI / REST            | Ingress; S-34 gate 1; routes; denial forward                    |
| Directive Store (`directive_store`)                       | PostgreSQL                | Mutable directives; S-34 gate 2; locks; lineage                 |
| Compilation Engine (`compilation_engine`)                 | Python                    | Hermetic compile (AA-02); dual-hash; frozen_env; boot assertion; **on-demand Job preferred** |
| CG-IR Store (`cgir_store`)                                | Content-Addressed Storage | Immutable snapshots by snapshot_hash                            |
| Inspection Pipeline (`inspection_pipeline`)               | Python                    | Pure DAG evaluate (AA-03); S-34 gate 3                          |
| Conflict Resolution Engine (`conflict_engine`)            | Python                    | resolve_conflict (AA-05); S-34 gate 5                           |
| Finding FSM Engine (`finding_fsm`)                        | Python                    | 10-state FSM; S-34 gate 4; SoD (AA-04)                          |
| Finding Event Store (`finding_event_store`)               | Append-Only Log           | HLC finding lifecycle events only                               |
| Audit Event Store (`audit_event_store`)                   | Append-Only Log           | Capability/SoD denials (S-32..S-34)                             |
| Analytics Engine (`analytics_engine`)                     | Python                    | Read-only aggregates + traceability queries (AA-01)             |
| Execution Artifact Store (`artifact_store`)               | Object Store              | Snapshots, traces, hashes, Conflict Artifacts, cert artifacts   |
| Architectural Audit Engine (`architectural_audit_engine`) | Python                    | AA-01..AA-07 orchestration (S-30); **CI-invoked Job**; validation only |

## Components by Container (58)

### API Gateway (4)

| Component           | Role                                                                 |
| :------------------ | :------------------------------------------------------------------- |
| Auth Middleware     | JWT/OIDC validation                                                  |
| Capability Enforcer | S-34 gate 1 — ingress hard-deny                                      |
| Denial Handler      | Gate-1 denial serialization → Audit Event Store (record-shape owner) |
| Request Router      | Capability-domain routing                                            |

**Denial topology (container-aligned):** Gate 1 uses Denial Handler. Gates 2–5 (Directive Store, Inspection Pipeline, Finding FSM, Conflict Engine) append denials **directly** to Audit Event Store with the same record shape — no reverse call into API Gateway.

### Directive Store (6)

| Component                 | Role                                          |
| :------------------------ | :-------------------------------------------- |
| Directive Capability Gate | S-34 gate 2                                   |
| Directive Command Handler | create/modify/retire/fork/merge/split/restore |
| Compilation Orchestrator  | Triggers compile / dry-run (S-09)             |
| Directive Repository      | Persistence                                   |
| Lineage Manager           | Dual identity fork/merge/split                |
| Lock Manager              | Read/write locks (Sec.3.4)                    |

### Hermetic Compilation Boundary (10)

| Component                   | Role                                                              |
| :-------------------------- | :---------------------------------------------------------------- |
| Policy Boot Assertion       | AA-02 **startup-once** policy absence (not per-compile pipeline)  |
| Schema Validator            | JSON Schema Draft-07 first pass (per-compile pipeline head)       |
| Cross-Layer Version Checker | MAJOR / policy_contract_version          |
| AST Discriminator Validator | AA-06                                    |
| Portability Validator       | AA-07 / RE2 canaries                     |
| Lineage DAG Validator       | Sec.2.2.3                                |
| Dual-Hash Computer          | semantic + presentation hashes           |
| Conflict Resolution Mapper  | Compile-time resolve_conflict precompute |
| Frozen Env Manager          | frozen_env_hash (Sec.2.7)                |
| CG-IR Snapshot Generator    | Publish immutable snapshot               |

### CG-IR Store (2)

| Component                | Role                        |
| :----------------------- | :-------------------------- |
| Snapshot Store           | Content-addressed snapshots |
| Node / Edge Deduplicator | node_hash / edge_hash dedup |

### Inspection Pipeline (7)

| Component                  | Role                          |
| :------------------------- | :---------------------------- |
| Inspection Capability Gate | S-34 gate 3                   |
| Target Normalizer          | Stages 1–2                    |
| Control Selector           | Stage 3                       |
| DAG Executor               | Topological execute + timeout |
| Pure Evaluator Runtime     | AA-03 purity                  |
| Finding Aggregator         | Stage 5 + conflict invoke     |
| Snapshot Finalizer         | Stage 6 + emit findings       |

### Conflict Resolution Engine (5)

| Component                 | Role                              |
| :------------------------ | :-------------------------------- |
| Conflict Capability Gate  | S-34 gate 5                       |
| Override Resolver         | Single resolve_conflict authority |
| defer_to Cycle Detector   | DFS cycle handling                |
| Precedence Chain Scorer   | priority → specificity → recency  |
| Conflict Artifact Emitter | Escalation / advisory artifacts   |

### Finding FSM Engine (3)

| Component           | Role                            |
| :------------------ | :------------------------------ |
| FSM Capability Gate | S-34 gate 4 + SoD + fail-closed |
| FSM State Machine   | 10 states / auto-transitions    |
| HLC Event Writer    | HLC + event_hash                |

### Finding Event Store (2)

| Component           | Role                       |
| :------------------ | :------------------------- |
| Event Appender      | Append-only finding stream |
| Hash Chain Verifier | event_hash integrity       |

### Audit Event Store (2)

| Component            | Role             |
| :------------------- | :--------------- |
| Audit Event Appender | Denial records   |
| Audit Hash Verifier  | Denial integrity |

### Analytics Engine (3)

| Component          | Role                                     |
| :----------------- | :--------------------------------------- |
| Aggregate Computer | finding_aggregates + S-17 (AA-01)        |
| Causal Explainer   | S-16 explanations (AA-01 zero-write)     |
| Query Processor    | S-04, S-06, S-07, S-11, S-21..S-24, S-27 (AA-01 zero-write) |

AA-01 Mediated Feedback Validator inspects **all three** Analytics components for zero-write certification.

### Execution Artifact Store (5)

| Component                    | Role                             |
| :--------------------------- | :------------------------------- |
| Inspection Snapshot Store    | Point-in-time inspection results |
| Pipeline Trace Store         | Traces + fault taxonomy          |
| Conflict Artifact Store      | Nested Conflict Artifacts (S-05) |
| System State Hash Store      | Reproducibility anchors          |
| Certification Artifact Store | AA gate PASS/FAIL evidence       |

### Architectural Audit Engine (9)

| Component               | Role                       |
| :---------------------- | :------------------------- |
| AA Gate Orchestrator    | Suite coordinator (S-30)   |
| AA-01..AA-07 Validators | One component per gate     |
| Certification Reporter  | Gate-ID report + artifacts |

## Capability Gates (S-34)

|    # | Gate                | Component                  |
| ---: | :------------------ | :------------------------- |
|    1 | Request ingress     | Capability Enforcer        |
|    2 | Directive mutation  | Directive Capability Gate  |
|    3 | Pipeline entry      | Inspection Capability Gate |
|    4 | FSM transition      | FSM Capability Gate        |
|    5 | Conflict resolution | Conflict Capability Gate   |

## Architectural Audit Gates (S-30 / §9.9)

| Gate  | Name                       | Enforcement (runtime)                     | Certification   |
| :---- | :------------------------- | :---------------------------------------- | :-------------- |
| AA-01 | Mediated Feedback          | Analytics zero-write edges                | AA-01 Validator |
| AA-02 | Policy Runtime Prohibition | compile_only + Policy Boot Assertion + CI | AA-02 Validator |
| AA-03 | Evaluator Purity           | Pure Evaluator Runtime                    | AA-03 Validator |
| AA-04 | Segregation of Duties      | FSM Capability Gate                       | AA-04 Validator |
| AA-05 | Conflict Determinism       | Override Resolver chain                   | AA-05 Validator |
| AA-06 | Discriminator Completeness | AST Discriminator Validator               | AA-06 Validator |
| AA-07 | Portable Serialization     | Portability Validator                     | AA-07 Validator |

CI/CD triggers **Architectural Audit Engine** (not Schema Validator alone). The AA engine is a **CI-invoked Job/sidecar**, not part of the always-running user-facing request path. It writes only certification artifacts to the Execution Artifact Store and has **no mutation authority** over Directive Store, CG-IR, Finding FSM, or Event Stores.

## Architecture Pattern

```
RegulatoryOfficial / ComplianceRepresentative / System
  -> API Gateway (S-34 gate 1, Denial Handler)
      -> Directive Store (gate 2, Command Handler, Lineage, Locks)
          -> Compilation Engine [Hermetic, on-demand Job] -> CG-IR Store
      -> Inspection Pipeline (gate 3, pure DAG) -> Artifact Store, Finding FSM
      -> Conflict Engine (gate 5) -> Conflict Artifact Store (nested)
      -> Finding FSM (gate 4, SoD) -> Finding Event Store
      -> Analytics Engine (read-only, AA-01)
      -> Audit Event Store (denials) -> Audit Platform
  -> Architectural Audit Engine (S-30, CI Job) <- CI/CD
      -> validates AA-01..AA-07 against enforcement components
      -> Certification Artifact Store
```

## Deployment View

Maps each C4 container to a concrete runtime shape. PlantUML remains the structural source of truth; this section is the **deployment projection** (artifact class, workload type, scale posture). Concrete Dockerfiles and manifests land in implementation PRs; names below are the intended packaging contracts.

### Workload classification

| Class | Meaning | Typical K8s / runtime |
| :---- | :------ | :-------------------- |
| **Stateless service** | Horizontally scalable request workers | Deployment + HPA / serverless |
| **On-demand Job** | Triggered work unit; not always-on | Job / CronJob / CI step / queue worker |
| **Stateful store** | Durable data plane; HA patterns required | StatefulSet, managed DB/log/object store |
| **CI validation** | Certification only; no core mutation authority | CI pipeline Job / sidecar |

### Per-container deployment matrix

| # | Container | Class | Packaging contract | Scale / HA notes | Stateful? | Writes core state? |
| :- | :-------- | :---- | :----------------- | :--------------- | :-------- | :----------------- |
| 1 | **API Gateway** | Stateless service | `Dockerfile.api-gateway` · Deployment | HPA on RPS/latency; multi-replica | No | No (routes + denial append) |
| 2 | **Directive Store** | Stateful store | Managed PostgreSQL or `StatefulSet` + PVC | Primary + replica; backups; Sec.3.4 locks | Yes | Yes (directive mutations) |
| 3 | **Compilation Engine** | **On-demand Job** (preferred) | `Dockerfile.compilation-engine` · Job / worker | Scale-to-zero; one compile per mutation/CI; hermetic image | Ephemeral | Yes (CG-IR publish only) |
| 4 | **CG-IR Store** | Stateful store | CAS (S3/MinIO/content-addressed FS) | Immutable objects; multi-AZ replication | Yes | Append-only publish |
| 5 | **Inspection Pipeline** | Stateless service | `Dockerfile.inspection-pipeline` · Deployment / Job pool | HPA; pure DAG (AA-03) — ideal for parallel workers | No | Artifacts + findings emit |
| 6 | **Conflict Resolution Engine** | Stateless service | `Dockerfile.conflict-engine` · Deployment | Single-authority logic; pin shared lib versions | No | Conflict Artifacts only |
| 7 | **Finding FSM Engine** | Stateful coordinator | `Dockerfile.finding-fsm` · Deployment (leader election) | Affinity / leader election recommended; fail-closed SoD | Soft (session) | Finding Event append |
| 8 | **Finding Event Store** | Stateful store | Append-only log (Kafka / Pulsar / event DB) | HLC order; `event_hash` chain; retention policy | Yes | Append-only |
| 9 | **Audit Event Store** | Stateful store | Separate append-only log stream | Isolation from finding stream (SoC) | Yes | Append-only denials |
| 10 | **Analytics Engine** | Stateless / query layer | `Dockerfile.analytics-engine` · Deployment or serverless | Read replicas of event/CAS; **zero write path** (AA-01) | No | **None** (AA-01) |
| 11 | **Execution Artifact Store** | Stateful store | Object store (S3-compatible) | Immutable snapshots/traces/certs; lifecycle rules | Yes | Append-only objects |
| 12 | **Architectural Audit Engine** | **CI validation Job** | `Dockerfile.architectural-audit` · CI Job | Triggered by `cicd` only; not user-path replicas | Ephemeral | Cert artifacts only |

### Deployment notes (high-impact clarifications)

#### 1. Compilation Engine — on-demand, not always-on

The **Hermetic Compilation Boundary** is primarily a **security/isolation boundary** (AA-02 + policy runtime prohibition), not a requirement for a persistent replica set.

| Trigger | Workload |
| :------ | :------- |
| Directive mutation (create/modify/retire/fork/merge/split/restore) | Job/worker invoked by Compilation Orchestrator |
| Dry-run impact preview (S-09) | Short-lived Job |
| CI static analysis hooks (AA-02) | CI step against compile image |

**Rationale:** Avoids over-provisioning idle compile capacity while preserving hermetic emphasis (clean image, boot-time policy absence assertion, no runtime `policy_doctrine.yaml`).

#### 2. Architectural Audit Engine — CI-invoked only

| Aspect | Contract |
| :----- | :------- |
| Trigger | External `cicd` system only (S-30) |
| Authority | Validation/read only — **no** mutation of Directive Store, CG-IR, FSM, or Event Stores |
| Writes | Certification artifacts (gate-ID PASS/FAIL evidence) → Execution Artifact Store |
| Topology | Prefer CI Job / ephemeral runner over long-lived Deployment in the user-facing platform |

This removes any implication that AA is part of the always-running request path.

#### 3. Optional co-deploy topology (Conflict + FSM)

Default topology keeps **Conflict Resolution Engine** and **Finding FSM Engine** as separate containers (independent versioning, S-34 gates 4 vs 5, single-authority `resolve_conflict`).

**Valid alternative:** co-deploy both in one image/process group for lower latency on transactional “emit finding + apply conflict disposition” paths.

| Option | When to use |
| :----- | :---------- |
| **Separate containers** (default) | Strong isolation, independent scale, strict gate ownership |
| **Co-deployed image** | Small deployments; reduce hop latency; still expose separate capability gates internally |

Co-deploy does **not** merge capability authorities: gate 4 (FSM/SoD) and gate 5 (conflict.resolve) remain distinct checks.

#### 4. Shared-library versioning risk

Python engines share hashing, AST discrimination, HLC, specificity scoring, and RE2 portability logic. Mitigate with monorepo + pinned base images or strict promotion pipelines so container independence does not produce algorithm drift (AA-05, AA-06, AA-07).

## Inter-Engine Contracts

Cross-container edges that are not mediated solely by stores (CAS / append-only logs) MUST use **narrow, versioned contracts** so independent deployments do not drift.

### Contract catalog

| ID | Consumer → Provider | Transport (normative intent) | Schema anchor | Notes |
| :- | :------------------ | :--------------------------- | :------------ | :---- |
| **IEC-01** | Inspection Pipeline → Conflict Resolution Engine | Internal RPC (gRPC/OpenAPI) or in-process when co-deployed | `resolve_conflict` Sec.2.15; frozen CG-IR node fields only | Multi-fire resolution; deterministic; no Directive Store IO |
| **IEC-02** | Inspection Pipeline → Finding FSM Engine | Internal RPC / event emit | FindingCreated payload Sec.3.3; outcome mapping Sec.2.9.1 | Emits Created→Open path after DAG complete (S-10) |
| **IEC-03** | Compilation Engine → Conflict Resolution Engine | Internal RPC / library call at compile-time | Same `resolve_conflict` single authority (AA-05) | Precompute conflict mapping into CG-IR metadata |
| **IEC-04** | API Gateway → Finding FSM Engine | Capability-checked route | finding.* / evidence.* Sec.3.1, S-34 gate 4 | Human-triggered transitions only through gates |
| **IEC-05** | API Gateway → Conflict Resolution Engine | Capability-checked route | conflict.resolve S-05, S-34 gate 5 | Human disposition of Conflict Artifacts |
| **IEC-06** | Inspection Pipeline → Analytics Engine | Read-only query | `finding_aggregates` Sec.2.11 | Pre-inspection context; **no write-back** (AA-01) |
| **IEC-07** | Finding FSM → Finding Event Store | Append-only write | HLC + `event_hash` chain Sec.3.3 | Store-mediated; source of truth for lifecycle |
| **IEC-08** | Any gate denial → Audit Event Store | Append-only write | Denial record Sec.3.2, S-32..S-34 | Gate 1 via Denial Handler; gates 2–5 direct append from each container |

### IEC-01 — Inspection ↔ Conflict (critical)

```
Request:
  snapshot_hash: string          # frozen CG-IR key
  target_id: string
  firing_node_ids: string[]      # multi-fire set
  lineage_id: string             # within-lineage only for auto-resolve

Response:
  winner_node_id: string | null
  disposition: "resolved" | "conflict_artifact"
  artifact_ref: string | null    # when disposition = conflict_artifact
  factors: { override, priority, specificity, recency }  # audit trail
```

**Independence rules:** provider reads **only** frozen CG-IR fields + artifact store; consumer does not reimplement precedence locally (AA-05 single authority).

### IEC-02 — Inspection ↔ Finding FSM (critical)

```
Request (emit finding):
  finding_id, inspection_id, control_id, lineage_id
  snapshot_hash, outcome, confidence, evidence, reasoning, severity
  creator_provenance: string[]   # for later SoD (S-29)

Response:
  accepted: bool
  fsm_state: "Created" | "Open"  # per Sec.3.1 auto-path
  event_hash: string             # first chain link
```

**Independence rules:** FSM owns HLC assignment and append; pipeline does not write Event Store directly. Fail-closed if FSM/SoD stores unavailable.

### Versioning and compatibility

| Rule | Requirement |
| :--- | :---------- |
| Schema ID | Each IEC message carries `contract_version` (semver MAJOR aligned with platform 8.x) |
| Breaking change | MAJOR bump; dual-run or staged rollout across engine Deployments |
| Pinning | Conflict algorithm package version MUST match across Compilation Engine and Conflict Engine images |
| Tests | Contract tests in CI for IEC-01 and IEC-02 golden vectors (AA-05 determinism, FindingCreated payload) |

## Version Synchronization Matrix

| Document                | Version | Status       |
| :---------------------- | :------ | :----------- |
| SPECIFICATION.md        | 8.2.4   | Canonical    |
| rule_schema.json        | 8.2.4   | Synchronized |
| policy_doctrine.yaml    | 8.2.4   | Synchronized |
| User_Stories.md         | 8.2.4   | Synchronized |
| c4_selma_context.puml   | 8.2.4   | Synchronized |
| c4_selma_container.puml | 8.2.4   | Synchronized |
| c4_selma_component.puml | 8.2.4   | Synchronized |
| C4-Design/README.md     | 8.2.4   | Synchronized |

## Governance Artifacts

| Artifact                      | Path                                  |
| :---------------------------- | :------------------------------------ |
| Architecture Improvement Plan | `AIP.md`                              |
| Change Log                    | `CHANGE_LOG.md`                       |
| ADRs                          | `adr/ADR-AIP-001` … `007`             |
| Weighted audit (baseline)     | `WEIGHTED_AUDIT_TASK3.md`             |
| Container deployability audit | `CONTAINER_DEPLOYABILITY_AUDIT.md`    |
| Task progress                 | `TASK_PROGRESS.md`                    |

## Explicit Non-Claims (vs older README phantoms)

The following names from prior README drafts are **not** separate top-level containers in PlantUML (responsibilities re-homed):

| Prior name                        | Actual home                                             |
| :-------------------------------- | :------------------------------------------------------ |
| DirectiveManager                  | Directive Store command path + Compilation Orchestrator |
| PolicyAccessBlocker               | Policy Boot Assertion + compile_only + CI hooks         |
| TraceabilityQueryService          | Analytics Engine (Query Processor + Causal Explainer)   |
| ConflictArtifactStore (top-level) | Nested under Execution Artifact Store                   |
| FrozenEnvConfig (external system) | Frozen Env Manager inside Compilation Engine            |

## Validation

```bash
# Optional C4 linter if available
python ~/.agent-global/shared/tools/software-design/c4/c4_lint.py docs/C4-Design/ --strict
```

PlantUML sources remain authoritative over this README (ADR-AIP-001).
