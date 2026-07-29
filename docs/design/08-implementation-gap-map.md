# 08 — Implementation Gap Map

**Purpose:** Document how the **current repository scaffold** relates to the
Design Freeze target. This is a planning aid for Implementation — **no code
is changed in this document set.**

Observation date: 2026-07-29. Paths under `src/selma/` may drift; treat this
as a baseline checklist.

## Summary

| Layer | Design Freeze target | Current scaffold (approx.) | Gap severity |
| :--- | :--- | :--- | :--- |
| Domain | Full aggregates (Directive, CG-IR, Finding FSM, …) | Lint-oriented entities (`Finding` file:line, `Rule`, `Policy`) | High |
| Application ports | Store + detection + policy guidance ports | Rule/directive/parser/evaluator/reporter ports | High |
| Use cases | Governance, compile, inspect, FSM, certify | `inspect_source`, `query_directive` | High |
| Infrastructure | Four stores + pure detection registry | Config validators, AST evaluators, JSON rule repo | High |
| Interfaces | REST Application Service + CLI/TUI | CLI/TUI shells | Medium |
| Docs contracts | Complete | Complete (docs) | — |

## Package mapping (scaffold → target)

| Current | Target fate |
| :--- | :--- |
| `domain/entities/finding.py` | Evolve into lifecycle Finding **or** rename to `LintFinding` and introduce new aggregate |
| `domain/entities/rule.py` | Align with `rule_schema` universal fields (`deontic`, `detection`, …) |
| `domain/entities/policy.py` | Guidance-only doctrine model; no eval fields |
| `domain/value_objects/guidance.py` | Keep as guidance read model VO |
| `domain/value_objects/rule_id.py` | Split/align `LineageId` vs `ExecutionId` |
| `application/ports/evaluator_port.py` | Rename/generalize to `DetectionEngine` port |
| `application/ports/rule_repository_port.py` | Split rule dataset vs CG-IR repository concepts |
| `application/use_cases/inspect_source.py` | Become `SubmitInspection` against CG-IR, not ad-hoc source lint only |
| `infrastructure/evaluators/*` | Move behind detection adapters; enforce purity |
| `infrastructure/config/*` | Keep for schema validation bootstrap |
| `interfaces/cli`, `tui` | Thin adapters over use cases |
| `composition/` | Wire ports per Design Freeze |

## Contract coverage checklist (Implementation)

| Contract domain | Implemented when… |
| :--- | :--- |
| `directive/*` | Dual ID lineage ops + store locks |
| `compilation/*` | Full pipeline + CAS publish + discriminator |
| `inspection/*` | Six-stage pipeline + snapshots |
| `finding_lifecycle/*` | 10-state FSM + SoD + events |
| `conflict/*` | Deterministic resolve + artifacts |
| `authorization/*` | Capability gates on all human edges |
| `data_stores/*` | Four stores with immutability rules |
| `certification/*` | AA-01…AA-07 automated suite |
| `interfaces/*` | REST families + CLI/TUI subsets |
| Schemas 1.0.0 | Validators reject pre-universal evaluator_type rules |

## Architectural risks if Implementation skips Design Freeze

1. Re-introducing policy doctrine into evaluation path (breaks AA-02 / concern_split).
2. Treating findings as ephemeral lint lines without event stream (breaks audit).
3. Coupling language AST into domain packages (breaks domain-agnostic core).
4. Skipping SoD checks at “UI only” (breaks normative FSM).

## Recommended Implementation order (docs guidance only)

1. Domain VOs: LineageId, ExecutionId, FsmState, DetectionSpec models  
2. EventStore port + Finding FSM domain service  
3. CgIrRepository + compilation validate/publish (even if filesystem CAS)  
4. Inspection pipeline producing FindingCreated  
5. Capability gate middleware  
6. GuidanceResolver (analyzer)  
7. Conflict + certification suites  
8. REST surface parity with `interfaces/rest_api.yaml`

## Out of scope for Design Freeze docs

- Actual refactors under `src/`
- Database migrations
- Performance budgets beyond contract complexity limits
