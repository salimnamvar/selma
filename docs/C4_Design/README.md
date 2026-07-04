# C4 Design — Selma Universal Rule Governance Engine

## Component Inventory

| Component | Container | Description | Traceability |
|-----------|-----------|-------------|--------------|
| Selma | System | Universal Rule Governance Engine | SPECIFICATION.md §1 |
| Rule Administrator | Actor | Human authoring and maintaining rule sets | SPECIFICATION.md §1.3 |
| AI Steward | Actor | Autonomous agent that writes rules from natural language | SPECIFICATION.md §1.3 |
| Domain Developer | Actor | Builds downstream services that consume rules | SPECIFICATION.md §1.3 |
| LLM Service | External | OpenAI/Anthropic API for natural language understanding | SPECIFICATION.md §5 |
| File System | External | Stores policy.md and rules.yaml per domain | SPECIFICATION.md §2 |
| Version Control | External | Git repository for tracking rule history | SPECIFICATION.md §7 |
| Web API | Container | Python / FastAPI REST endpoints | SPECIFICATION.md §6 |
| Core Engine | Container | Python — validators, CRUD, and Steward orchestrator | SPECIFICATION.md §4-5 |
| Rule Storage | Container | File System — per-domain policy.md and rules.yaml | SPECIFICATION.md §2 |
| LLM Adapter | Container | Python — handles communication with external LLM API | SPECIFICATION.md §5 |
| Domain Registry | Component | Manages registration of new domains and folder scaffolding | SPECIFICATION.md §4.1 |
| CRUD Operations | Component | Creates, reads, updates, and deletes rules while maintaining traceability | SPECIFICATION.md §4.2 |
| Validator | Component | Validates policy structure, rule schema, traceability, and contamination | SPECIFICATION.md §4.3 |
| Steward Agent | Component | Orchestrates AI-driven rule writing | SPECIFICATION.md §4.4 |
| Reasoner | Component | Detects rule conflicts and suggests resolution | SPECIFICATION.md §4.5 |
| Version Manager | Component | Auto-bumps versions (SemVer) for domains | SPECIFICATION.md §4.6 |

## Diagram Files

| File | Level | Purpose |
|------|-------|---------|
| `c4_selma_context.puml` | L1 | System context — actors and external dependencies |
| `c4_selma_container.puml` | L2 | Internal containers and their interactions |
| `c4_selma_component.puml` | L3 | Core Engine internal components |

## Architecture Pattern

```
Actor → Web API → Core Engine → Rule Storage
                    ↓
              LLM Adapter → LLM Service
```

## Design Decisions

1. **Single Service**: Selma is a self-contained service, not a microservices architecture.
2. **File System Storage**: Policy and rule files stored as YAML/Markdown for human readability.
3. **Optional Git**: Version control is optional — Selma works standalone.
4. **LLM Integration**: External LLM for AI-agentic rule writing, not embedded.
