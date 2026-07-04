# C4 Design — Selma Universal Rule Governance Engine

## Architecture Overview

Selma's C4 model captures the **dual-contract architecture**: the Policy Doctrine (human lens) and Rule Schema (machine lens) connected by a strict **Traceability Bond** (Machine ID ↔ anchor_ref).

```
┌─────────────────────────────────────────────────────────────┐
│                    SELMA SYSTEM BOUNDARY                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌─────────────────┐    ┌──────────────┐   │
│  │ Web API  │───▶│   Core Engine   │◀──▶│ Rule Storage │   │
│  │ FastAPI  │    │                 │    │ File System  │   │
│  └──────────┘    │  ┌───────────┐  │    └──────────────┘   │
│       ▲          │  │ Validator │──┤                        │
│       │          │  │ (5 Pillars│  │    ┌──────────────┐   │
│  ┌────┴────┐     │  └───────────┘  │◀──▶│ LLM Adapter  │   │
│  │ Actors  │     │  ┌───────────┐  │    └──────┬───────┘   │
│  │ Admin   │     │  │ Steward   │──┤           │           │
│  │ Steward │     │  │ Agent     │  │    ┌──────▼───────┐   │
│  │ Dev     │     │  └───────────┘  │    │ LLM Service  │   │
│  └─────────┘     │  ┌───────────┐  │    │ OpenAI/Anthro │   │
│                  │  │ Reasoner  │  │    └──────────────┘   │
│                  │  └───────────┘  │                        │
│                  │  ┌───────────┐  │                        │
│                  │  │ Versioner │  │                        │
│                  │  └───────────┘  │                        │
│                  └─────────────────┘                        │
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │ Policy Doctrine     │  │ Rule Schema         │          │
│  │ policy_doctrine.yaml│◀▶│ rule_schema.json    │          │
│  │ (Societal Lens)     │  │ (Mechanical Lens)   │          │
│  └─────────────────────┘  └─────────────────────┘          │
│         ▲ Machine ID              anchor_ref ▲              │
│         └────────────────────────────────────┘              │
│              THE TRACEABILITY BOND                          │
└─────────────────────────────────────────────────────────────┘
```

## Component Inventory

### System Context (L1)

| Component | Type | Description | Traceability |
|-----------|------|-------------|--------------|
| Selma | System | Universal Rule Governance Engine | SPECIFICATION.md §1 |
| Rule Administrator | Actor | Human authoring and maintaining rule sets via CLI or REST API | SPECIFICATION.md §1.3 |
| AI Steward | Actor | Autonomous agent that writes rules from natural language. Self-validates and self-corrects iteratively | SPECIFICATION.md §1.3 |
| Domain Developer | Actor | Builds downstream services that consume rules via API or export | SPECIFICATION.md §1.3 |
| LLM Service | External | OpenAI/Anthropic API for natural language understanding | SPECIFICATION.md §5 |
| File System | External | Stores policy.md and rules.yaml per domain (YAML + Markdown) | SPECIFICATION.md §2 |
| Git Repository | External | Optional version control for tracking rule history and audit trail | SPECIFICATION.md §7 |

### Containers (L2)

| Container | Technology | Description | Traceability |
|-----------|-----------|-------------|--------------|
| Web API | Python / FastAPI | REST endpoints for CRUD, validation, and queries | SPECIFICATION.md §6 |
| Core Engine | Python | Validators, CRUD operations, Steward orchestrator, Reasoner, Version Manager, Domain Registry | SPECIFICATION.md §4-5 |
| Policy Doctrine | YAML | policy_doctrine.yaml — The Societal Lens | contracts/policy_doctrine.yaml |
| Rule Schema | JSON | rule_schema.json — The Mechanical Lens | contracts/rule_schema.json |
| Rule Storage | File System | Per-domain policy.md and rules.yaml | SPECIFICATION.md §2 |
| LLM Adapter | Python | Handles communication with external LLM API (retry, fallback, prompt management) | SPECIFICATION.md §5 |

### Components (L3 — Core Engine)

| Component | Module | Description | Traceability |
|-----------|--------|-------------|--------------|
| Domain Registry | Module | Manages registration of new domains. Scaffolds folder structure with policy.md and rules.yaml templates | SPECIFICATION.md §4.1 |
| CRUD Operations | Module | Creates, reads, updates, and deletes rules while maintaining traceability. Auto-bumps versions on changes | SPECIFICATION.md §4.2 |
| Version Manager | Module | Auto-bumps versions (SemVer MAJOR.MINOR.PATCH). Synchronizes contract versions. Increments based on change severity | SPECIFICATION.md §4.5 |
| **Validator Orchestrator** | Module | Coordinates the five validation pillars | SPECIFICATION.md §6 |
| Policy Validator | Module | Validates policy.md structure: required sections, correct content types, no forbidden fields | SPECIFICATION.md §6.1 |
| Rule Validator | Module | Validates rules.yaml against rule_schema.json: JSON Schema compliance, required fields, no forbidden root fields | SPECIFICATION.md §6.2 |
| Traceability Validator | Module | Validates bidirectional bond: Machine ID ↔ rule id, anchor_ref → valid section, contract version synchronization | SPECIFICATION.md §6.3 |
| Contamination Guard | Module | Enforces separation principle: policy has no machine fields, rules have no human prose fields | SPECIFICATION.md §6.4 |
| **Conflict Reasoner** | Module | Detects rule conflicts and suggests resolution based on priority hierarchy: constitutional > statutory > regulatory > operational > advisory | SPECIFICATION.md §4.4 |
| **Steward Agent** | Module | Autonomous AI rule writer with orchestration loop: read state → generate via LLM → persist → validate (all 5 pillars) → self-correct → bump version → output diff | SPECIFICATION.md §4.4 |
| Domain Exporter | Module | Packages entire domains for export. Import/export rule sets for backup or cross-domain transfer | SPECIFICATION.md §7 |
| Query Engine | Module | Retrieves rules by ID, domain, status, priority, or type. Returns filtered, sorted results | SPECIFICATION.md §6 |

## Five Validation Pillars

The Validator Orchestrator coordinates five independent validation pillars:

```
                    ┌─────────────────────┐
                    │  Validator          │
                    │  Orchestrator       │
                    └─────────┬───────────┘
           ┌──────────────────┼──────────────────┐
           │                  │                  │
    ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
    │  Pillar 1   │   │  Pillar 2   │   │  Pillar 3   │
    │  Policy     │   │  Rule       │   │  Trace      │
    │  Structure  │   │  Schema     │   │  Bond       │
    └─────────────┘   └─────────────┘   └─────────────┘
           │                  │                  │
    ┌──────▼──────┐   ┌──────▼──────┐          │
    │  Pillar 4   │   │  Pillar 5   │          │
    │  Contam.    │   │  Conflict   │          │
    │  Guard      │   │  Reasoner   │          │
    └─────────────┘   └─────────────┘          │
                                               │
              ┌────────────────────────────────┘
              │
    ┌─────────▼─────────────────────────────────┐
    │  Traceability Bond Validation              │
    │  • Every Machine ID ↔ rule id              │
    │  • Every anchor_ref → valid section        │
    │  • Contract version synchronization        │
    └───────────────────────────────────────────┘
```

### Pillar 1: Policy Structure Validation
- All required sections present (Preamble, Governance, Definitions, Principles, Directives, Sanctions)
- Correct content types per section
- No forbidden fields (contamination guard)

### Pillar 2: Rule Schema Validation
- JSON Schema compliance (rule_schema.json)
- Required fields present (id, type, message)
- No forbidden root-level fields

### Pillar 3: Traceability Bond Validation
- Every Machine ID in policy → exists as rule id in rules
- Every rule id → has corresponding Machine ID in policy
- Every anchor_ref → points to valid policy section
- Contract versions synchronized

### Pillar 4: Contamination Guard
- Policy contains no machine fields (parameters, conditions, evaluator_hint, etc.)
- Rules contain no human prose fields (preamble, governance, definitions, etc.)
- Cross-contract pollution detection

### Pillar 5: Conflict Detection
- Rules with `conflicts_with` references are checked
- Priority hierarchy enforced (constitutional > statutory > regulatory > operational > advisory)
- Resolution suggestions generated

## Steward Orchestration Loop

The Steward Agent runs a self-correcting loop:

```
┌─────────────────────────────────────────────────────┐
│              STEWARD ORCHESTRATION LOOP              │
├─────────────────────────────────────────────────────┤
│  1. READ STATE      — Load domain policy + rules    │
│  2. GENERATE        — Call LLM with NL request      │
│  3. PERSIST         — Write to storage              │
│  4. VALIDATE        — Run all 5 pillars             │
│  5. SELF-CORRECT    — If errors, fix and retry      │
│  6. BUMP VERSION    — Auto-increment SemVer         │
│  7. OUTPUT DIFF     — Summary of changes            │
└─────────────────────────────────────────────────────┘
```

**Key behaviors:**
- Self-corrects validation errors iteratively
- Never persists invalid rules
- Auto-generates Machine IDs (e.g., TRAF-011)
- Bumps version based on change severity (MAJOR/MINOR/PATCH)

## Design Decisions

1. **Dual-Contract Architecture**: Policy Doctrine (human) and Rule Schema (machine) are strictly separated with only the Traceability Bond connecting them.
2. **Five Validation Pillars**: Each pillar is independent and can be run in isolation or as part of the full pipeline.
3. **Self-Correcting Steward**: The AI agent validates its own output and retries until all five pillars pass.
4. **File System Storage**: Policy and rule files stored as YAML/Markdown for human readability.
5. **Optional Git**: Version control is optional — Selma works standalone.
6. **LLM Integration**: External LLM for AI-agentic rule writing, not embedded.
7. **Priority Hierarchy**: Five authority levels with automatic conflict resolution.

## Diagram Files

| File | Level | Purpose |
|------|-------|---------|
| `c4_selma_context.puml` | L1 | System context — actors, external dependencies, and the dual-contract bond |
| `c4_selma_container.puml` | L2 | Internal containers — API, Core Engine, Contracts, Storage, LLM Adapter |
| `c4_selma_component.puml` | L3 | Core Engine components — 11 modules, validation pipeline, Steward loop |
