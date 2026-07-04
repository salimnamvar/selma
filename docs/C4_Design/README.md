# C4 Design — Selma Universal Rule Governance Engine

## Architecture Overview

Selma's C4 model captures the **dual-contract architecture**: the Policy Doctrine (human lens) and Rule Schema (machine lens) connected by a strict **Traceability Bond** (Machine ID ↔ anchor_ref).

The Core Engine is structured as a **four-pillar pipeline**:

| Pillar | Engine | Responsibility |
|--------|--------|----------------|
| 1 | Definition Engine (Creator) | Generates Machine IDs, drafts prose and YAML stubs |
| 2 | Maintenance Engine (Curator) | CRUD, SemVer bumping, deprecation, refactoring |
| 3 | Mechanical Linting Engine (Inspector) | Syntax, schema, contamination guard — hard fail |
| 4 | Reasoning Engine (Arbiter) | Conflict detection, priority enforcement, soft warnings |

## Diagram Set

| File | C4 Level | Version | Description |
| ---- | -------- | ------- | ----------- |
| [c4_selma_context.puml](c4_selma_context.puml) | Context | v1.0.0 | Selma as a system with 3 actors and 3 external systems |
| [c4_selma_container.puml](c4_selma_container.puml) | Container | v1.0.0 | Internal containers: API, Core Engine, Contracts, Storage, LLM Adapter |
| [c4_selma_component.puml](c4_selma_component.puml) | Component | v1.0.0 | Four-pillar engines, Steward orchestrator, supporting modules |
| [common/c4_styles.puml](common/c4_styles.puml) | — | v1.0.0 | Shared palette, skinparam stereotypes, element + relationship tags |

## How to Read

1. **Context** — what Selma is and what it talks to.
2. **Container** — the system boundary, internal containers, and dependencies.
3. **Component** — the four-pillar pipeline, Steward orchestration, and dual-contract bond.

## Architecture

Selma runs as a single Python process. Three actors (Rule Administrator, AI Steward, Domain Developer) connect via HTTPS or CLI. Internally the application follows a four-pillar pipeline orchestrated by the Steward Agent:

```
Actor / CLI / REST API
    → Web API (FastAPI)
        → Steward Agent (orchestrator)
            → Definition Engine → Maintenance Engine → Mechanical Linting → Reasoning Engine
                → Policy Doctrine (human lens) ↔ Rule Schema (machine lens)
                → Rule Storage (file system)
                → LLM Adapter → LLM Service (external)
```

**Dual-Contract Bond**: Policy Doctrine and Rule Schema are strictly separated. They connect only through the Traceability Bond (Machine ID ↔ anchor_ref).

**Error Recovery**: Mechanical Linting produces hard failures that block the pipeline. The Steward self-corrects and retries. Reasoning produces soft warnings that suggest fixes but do not block.

## Consistency Rules

All diagrams enforce:
- **Global IDs**: identical element IDs across all diagrams
- **External tag**: every `System_Ext` carries `$tags="external"` (dashed border, muted grey)
- **Internal tags**: `system`, `backend_container`, `contract`, `controller`, `service`, `repository` for Selma-owned elements
- **Direction arrows**: every `Rel` label starts with `→` (one-way) or `⟷` (bidirectional)
- **Sprite consistency**: `Person` elements use `$sprite="person"` across all levels
- **Protocol consistency**: CLI→HTTPS/CLI, REST→HTTPS, LLM→HTTPS, Storage→I/O, Git→Git
- **Mandatory legend**: each diagram calls its `$selma_legend_*()` procedure
- **Version pins**: all `!include` directives pin to C4-PlantUML v2.13.0
- **No notes**: diagrams speak for themselves — no `note` blocks

## Rendering

Requires [C4-PlantUML](https://github.com/plantuml-stdlib/C4-PlantUML)
v2.13.0:

```bash
plantuml c4_selma_context.puml
plantuml c4_selma_container.puml
plantuml c4_selma_component.puml
```

## Design Chain

C4 feeds into UC → SM → SQ → ERD → CL → CT. All lifelines in SQ diagrams
trace back to components defined here.
