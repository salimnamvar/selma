# Selma -- C4 Architecture Diagrams

**Version:** 8.2.4  
**Date:** 2026-07-09  
**Contract Alignment:** 8.2.4  
**Status:** Unified C4 — three diagrams (Context, Container, Component) aligned with SPECIFICATION.md and User_Stories.md  
**Structural source of truth:** PlantUML sources (ADR-AIP-001)  
**AIP:** `AIP.md` v1.3.0 · **Change log:** `CHANGE_LOG.md`

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

| Name (PlantUML ID)                                        | Technology                | Description                                                     |
| :-------------------------------------------------------- | :------------------------ | :-------------------------------------------------------------- |
| API Gateway (`api_gateway`)                               | FastAPI / REST            | Ingress; S-34 gate 1; routes; denial forward                    |
| Directive Store (`directive_store`)                       | PostgreSQL                | Mutable directives; S-34 gate 2; locks; lineage                 |
| Compilation Engine (`compilation_engine`)                 | Python                    | Hermetic compile (AA-02); dual-hash; frozen_env; boot assertion |
| CG-IR Store (`cgir_store`)                                | Content-Addressed Storage | Immutable snapshots by snapshot_hash                            |
| Inspection Pipeline (`inspection_pipeline`)               | Python                    | Pure DAG evaluate (AA-03); S-34 gate 3                          |
| Conflict Resolution Engine (`conflict_engine`)            | Python                    | resolve_conflict (AA-05); S-34 gate 5                           |
| Finding FSM Engine (`finding_fsm`)                        | Python                    | 10-state FSM; S-34 gate 4; SoD (AA-04)                          |
| Finding Event Store (`finding_event_store`)               | Append-Only Log           | HLC finding lifecycle events only                               |
| Audit Event Store (`audit_event_store`)                   | Append-Only Log           | Capability/SoD denials (S-32..S-34)                             |
| Analytics Engine (`analytics_engine`)                     | Python                    | Read-only aggregates + traceability queries (AA-01)             |
| Execution Artifact Store (`artifact_store`)               | Object Store              | Snapshots, traces, hashes, Conflict Artifacts, cert artifacts   |
| Architectural Audit Engine (`architectural_audit_engine`) | Python                    | AA-01..AA-07 orchestration (S-30); validation only              |

## Components by Container (58)

### API Gateway (4)

| Component           | Role                                    |
| :------------------ | :-------------------------------------- |
| Auth Middleware     | JWT/OIDC validation                     |
| Capability Enforcer | S-34 gate 1 — ingress hard-deny         |
| Denial Handler      | Serializes denials to Audit Event Store |
| Request Router      | Capability-domain routing               |

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

| Component                   | Role                                     |
| :-------------------------- | :--------------------------------------- |
| Policy Boot Assertion       | AA-02 boot-time policy absence           |
| Schema Validator            | JSON Schema Draft-07 first pass          |
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
| Causal Explainer   | S-16 explanations                        |
| Query Processor    | S-04, S-06, S-07, S-11, S-21..S-24, S-27 |

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

CI/CD triggers **Architectural Audit Engine** (not Schema Validator alone).

## Architecture Pattern

```
RegulatoryOfficial / ComplianceRepresentative / System
  -> API Gateway (S-34 gate 1, Denial Handler)
      -> Directive Store (gate 2, Command Handler, Lineage, Locks)
          -> Compilation Engine [Hermetic] -> CG-IR Store
      -> Inspection Pipeline (gate 3, pure DAG) -> Artifact Store, Finding FSM
      -> Conflict Engine (gate 5) -> Conflict Artifact Store (nested)
      -> Finding FSM (gate 4, SoD) -> Finding Event Store
      -> Analytics Engine (read-only, AA-01)
      -> Audit Event Store (denials) -> Audit Platform
  -> Architectural Audit Engine (S-30) <- CI/CD
      -> validates AA-01..AA-07 against enforcement components
      -> Certification Artifact Store
```

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

| Artifact                      | Path                      |
| :---------------------------- | :------------------------ |
| Architecture Improvement Plan | `AIP.md`                  |
| Change Log                    | `CHANGE_LOG.md`           |
| ADRs                          | `adr/ADR-AIP-001` … `007` |
| Weighted audit (baseline)     | `WEIGHTED_AUDIT_TASK3.md` |
| Task progress                 | `TASK_PROGRESS.md`        |

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
