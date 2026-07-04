# C4 Design — Selma Universal Rule Governance Engine

## Architecture Overview

Selma's C4 model captures the **dual-contract architecture**: the Policy Doctrine (human lens) and Rule Schema (machine lens) connected by a strict **Traceability Bond** (Machine ID ↔ anchor_ref).

The Core Engine is structured as a **four-pillar pipeline** where each pillar handles a distinct concern:

```
┌─────────────────────────────────────────────────────────────────┐
│                      SELMA CORE ENGINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ Pillar 1    │───▶│ Pillar 2    │───▶│ Pillar 3    │         │
│  │ Definition  │    │ Maintenance │    │ Mechanical  │         │
│  │ (Creator)   │    │ (Curator)   │    │ Linting     │         │
│  └─────────────┘    └─────────────┘    │ (Inspector) │         │
│                                         └──────┬──────┘         │
│                                                │                │
│                                                ▼                │
│                                         ┌─────────────┐         │
│                                         │ Pillar 4    │         │
│                                         │ Reasoning   │         │
│                                         │ (Arbiter)   │         │
│                                         └─────────────┘         │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Steward Agent (Orchestrator)                             │ │
│  │  Runs the four-pillar pipeline sequentially               │ │
│  │  Self-corrects on lint failures                           │ │
│  │  Delegates deep reasoning to LLM                          │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  RULE SETS (per domain)                                        │
│  domains/traffic/policy.md   (Human prose)                     │
│  domains/traffic/rules.yaml  (Machine data)                    │
│                                                                 │
│  Connected by Traceability Bond:                               │
│  Machine ID (policy) ↔ anchor_ref (rules)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Four Pillars

### Pillar 1: Definition Engine (The Creator)

**Goal:** Turn human intent (or prompts) into structured, stubbed-out rules.

| Aspect | Detail |
| :--- | :--- |
| **Input** | Natural language OR structured rule template (Type, Description, Params) |
| **Process** | Generates stable Machine ID, drafts prose for `policy.md` (WP-001 to WP-005), drafts YAML stub for `rules.yaml`, assigns default `priority` (`operational`) and `status` (`draft`) |
| **Output** | Raw, unverified "Candidate Rule" inserted into file system |
| **Code Module** | `src/selma/core/definition.py` |

### Pillar 2: Maintenance Engine (The Curator)

**Goal:** Manage the lifecycle of rules and policies (CRUD + Versioning).

| Aspect | Detail |
| :--- | :--- |
| **Input** | Request to Create, Read, Update, Deprecate, or Delete a rule |
| **Process** | Mutates prose and YAML simultaneously, auto-bumps SemVer (MAJOR/MINOR/PATCH), handles deprecation (flips status, appends `[DEPRECATED]`), refactors between domains |
| **Output** | Committed, version-bumped rule set |
| **Code Module** | `src/selma/core/maintenance.py` |

### Pillar 3: Mechanical Linting Engine (The Inspector)

**Goal:** Syntax, Structure, and Contamination checks. **Fast, deterministic, runs automatically.**

| Aspect | Detail |
| :--- | :--- |
| **Input** | Raw or updated rule set files |
| **Checks** | YAML/JSON syntax, Contamination Guard (policy ↔ rules separation), Traceability (Machine ID ↔ rule id), Schema compliance (`rule_schema.json`), Complexity limits (`max_depth`, `max_parameters`) |
| **Output** | Strict **Pass/Fail** report with line numbers and fix suggestions |
| **Failure Type** | **Hard Fail** — blocks pipeline, returns to Steward for fix |
| **Code Module** | `src/selma/core/linter.py` |

### Pillar 4: Reasoning Engine (The Arbiter)

**Goal:** Semantics, Logic, and Conflict Resolution. **Deep, contextual, may require LLM.**

| Aspect | Detail |
| :--- | :--- |
| **Input** | Validated rule set (post-linting) |
| **Checks** | Conflict Detection (overlapping conditions), Priority Enforcement (hierarchy validation), Dependency Resolution (circular dependency check), Redundancy Detection (duplicate rules) |
| **Output** | **Reasoning Report** — Risks, Contradictions, suggested resolutions |
| **Failure Type** | **Soft Warning** — highlights risk, suggests fixes, requires human/Steward judgment |
| **Code Module** | `src/selma/core/reasoner.py` |

---

## Linting vs. Reasoning: The Crucial Boundary

| Aspect | Mechanical Linting (Pillar 3) | Reasoning (Pillar 4) |
| :--- | :--- | :--- |
| **What it checks** | Syntax, Contamination, Schema compliance | Logic, Conflicts, Priority override |
| **Speed** | Fast (milliseconds) | Potentially slower (LLM or graph traversal) |
| **Failure Type** | **Hard Fail** (Blocks deployment) | **Soft Warning** (Highlights risk, suggests fixes) |
| **Trigger** | Runs on every `validate` or `write` command | Runs on-demand or as a scheduled audit |
| **Action** | Auto-fixable (Steward can rewrite immediately) | Requires human/Steward judgment to resolve |

---

## Orchestration Pipeline

When the **Steward** (AI agent) or a **User** (via API) requests a rule change, Selma runs the data through a strict pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER REQUEST                               │
│        (Natural Language or Structured Edit)                    │
└───────────────────────────┬─────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. DEFINITION ENGINE                                          │
│     - Generates ID                                             │
│     - Writes raw prose & YAML                                  │
└───────────────────────────┬─────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. MAINTENANCE ENGINE                                         │
│     - Applies version bump (SemVer)                            │
│     - Writes files to disk                                     │
└───────────────────────────┬─────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. MECHANICAL LINTING ENGINE                                  │
│     - Runs strict syntax/structural checks                     │
│     - IF FAIL: Returns Error Report to User/Steward for fixes  │
│     - IF PASS: Proceeds                                        │
└───────────────────────────┬─────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. REASONING ENGINE                                           │
│     - Runs semantic conflict detection                         │
│     - GENERATES REPORT (Warnings, not blockers)                │
│     - IF CONFLICT: Suggests fixes via Steward                  │
└───────────────────────────┬─────────────────────────────────────┘
                              ▼
                   ┌─────────────────────┐
                   │  FINAL OUTPUT       │
                   │  (Passed + Reasoned)│
                   └─────────────────────┘
```

---

## Component Inventory

### System Context (L1)

| Component | Type | Description | Traceability |
|-----------|------|-------------|--------------|
| Selma | System | Universal Rule Governance Engine | SPECIFICATION.md §1 |
| Rule Administrator | Actor | Human authoring and maintaining rule sets via CLI or REST API | SPECIFICATION.md §1.3 |
| AI Steward | Actor | Autonomous agent that orchestrates the four-pillar pipeline | SPECIFICATION.md §1.3 |
| Domain Developer | Actor | Builds downstream services that consume rules via API or export | SPECIFICATION.md §1.3 |
| LLM Service | External | OpenAI/Anthropic API for natural language understanding and deep reasoning | SPECIFICATION.md §5 |
| File System | External | Stores policy.md and rules.yaml per domain (YAML + Markdown) | SPECIFICATION.md §2 |
| Git Repository | External | Optional version control for tracking rule history and audit trail | SPECIFICATION.md §7 |

### Containers (L2)

| Container | Technology | Description | Traceability |
|-----------|-----------|-------------|--------------|
| Web API | Python / FastAPI | REST endpoints for CRUD, validation, and queries | SPECIFICATION.md §6 |
| Core Engine | Python | Four-pillar pipeline: Definition, Maintenance, Mechanical Linting, Reasoning | C4_Design/README.md §The Four Pillars |
| Policy Doctrine | YAML | policy_doctrine.yaml — The Societal Lens | contracts/policy_doctrine.yaml |
| Rule Schema | JSON | rule_schema.json — The Mechanical Lens | contracts/rule_schema.json |
| Rule Storage | File System | Per-domain policy.md and rules.yaml | SPECIFICATION.md §2 |
| LLM Adapter | Python | Handles communication with external LLM API (retry, fallback, prompt management) | SPECIFICATION.md §5 |

### Components (L3 — Core Engine)

| Component | Module | Description | Traceability |
|-----------|--------|-------------|--------------|
| **Definition Engine** | Module | Turns human intent into structured rules: ID generation, prose drafting, YAML scaffolding | C4_Design/README.md §Pillar 1 |
| **Maintenance Engine** | Module | Manages rule lifecycle: CRUD, SemVer bumping, deprecation, refactoring | C4_Design/README.md §Pillar 2 |
| **Mechanical Linting Engine** | Module | Fast syntax/structure checks: YAML syntax, contamination guard, traceability, schema compliance, complexity limits | C4_Design/README.md §Pillar 3 |
| **Reasoning Engine** | Module | Deep semantic checks: conflict detection, priority enforcement, dependency resolution, redundancy detection | C4_Design/README.md §Pillar 4 |
| **Steward Agent** | Module | Orchestrates the four-pillar pipeline sequentially, self-corrects on lint failures, delegates deep reasoning to LLM | C4_Design/README.md §Orchestration Pipeline |
| Domain Registry | Module | Manages registration of new domains. Scaffolds folder structure with policy.md and rules.yaml templates | SPECIFICATION.md §4.1 |
| Version Manager | Module | Auto-bumps versions (SemVer MAJOR.MINOR.PATCH). Synchronizes contract versions | SPECIFICATION.md §4.5 |
| Domain Exporter | Module | Packages entire domains for export. Import/export rule sets for backup or cross-domain transfer | SPECIFICATION.md §7 |
| Query Engine | Module | Retrieves rules by ID, domain, status, priority, or type. Returns filtered, sorted results | SPECIFICATION.md §6 |

## Five Validation Pillars (Legacy — Now Mapped to Four Pillars)

The original five validation pillars are now mapped to the four-pillar architecture:

| Original Pillar | New Pillar | Mapping |
|----------------|------------|---------|
| Pillar 1: Policy Structure | Mechanical Linting (Pillar 3) | Contamination Guard + Structure Check |
| Pillar 2: Rule Schema | Mechanical Linting (Pillar 3) | Schema Compliance |
| Pillar 3: Traceability Bond | Mechanical Linting (Pillar 3) | Traceability Validation |
| Pillar 4: Contamination Guard | Mechanical Linting (Pillar 3) | Cross-contract Pollution Detection |
| Pillar 5: Conflict Detection | Reasoning Engine (Pillar 4) | Semantic Conflict Resolution |

## Steward Orchestration Loop

The Steward Agent runs the four-pillar pipeline as a self-correcting loop:

```
┌─────────────────────────────────────────────────────┐
│              STEWARD ORCHESTRATION LOOP              │
├─────────────────────────────────────────────────────┤
│  1. READ STATE      — Load domain policy + rules    │
│  2. DEFINITION      — Generate rules via LLM        │
│  3. MAINTENANCE     — Apply version bump, write     │
│  4. LINT            — Run mechanical checks         │
│     IF FAIL: Self-correct and retry from step 2     │
│  5. REASON          — Run semantic checks           │
│     IF CONFLICT: Suggest resolution via Steward     │
│  6. OUTPUT DIFF     — Summary of changes            │
└─────────────────────────────────────────────────────┘
```

**Key behaviors:**
- Self-corrects lint failures iteratively (never persists invalid rules)
- Auto-generates Machine IDs (e.g., TRAF-011)
- Bumps version based on change severity (MAJOR/MINOR/PATCH)
- Delegates deep reasoning to LLM when graph traversal is insufficient

## Design Decisions

1. **Dual-Contract Architecture**: Policy Doctrine (human) and Rule Schema (machine) are strictly separated with only the Traceability Bond connecting them.
2. **Four-Pillar Pipeline**: Definition → Maintenance → Mechanical Linting → Reasoning. Each pillar is a distinct engine with clear input/output.
3. **Hard Fail vs. Soft Warning**: Mechanical linting blocks on violations (Hard Fail); reasoning highlights risks and suggests fixes (Soft Warning).
4. **Self-Correcting Steward**: The AI agent orchestrates the pipeline and self-corrects on lint failures.
5. **File System Storage**: Policy and rule files stored as YAML/Markdown for human readability.
6. **Optional Git**: Version control is optional — Selma works standalone.
7. **LLM Integration**: External LLM for AI-agentic rule writing and deep reasoning, not embedded.
8. **Priority Hierarchy**: Five authority levels with automatic conflict resolution.
9. **Separation of Concerns**: Each pillar has a single responsibility. Definition creates, Maintenance curates, Linting inspects, Reasoning arbitrates.

## Diagram Files

| File | Level | Purpose |
|------|-------|---------|
| `c4_selma_context.puml` | L1 | System context — actors, external dependencies, and the four-pillar core |
| `c4_selma_container.puml` | L2 | Internal containers — API, Core Engine (four pillars), Contracts, Storage, LLM Adapter |
| `c4_selma_component.puml` | L3 | Core Engine components — four-pillar engines, Steward orchestrator, supporting modules |
