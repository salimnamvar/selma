# ADR 0005: Multi-agent engineering team model

## Status

Accepted

## Context

Users may run several coding agents. Without role separation, agents compete on
the same files and make conflicting architectural choices.

## Decision

Standard operating model:

| Stage | Role | Agent (example) |
| :--- | :--- | :--- |
| Foundation / conflicts | Architect | Grok |
| Primary implementation | Coder | OpenCode |
| Hardening | Refactor / Test / Enhance | Poolside |
| Independent review | Reviewer | Mimo |
| Unresolved contract disputes | Architect | Grok |

Role definitions live in `docs/roles/` and `config/examples/roles.yaml`.  
Workflow example encodes this collaboration in `config/examples/workflow.yaml`.

## Consequences

**Positive**

- Clear handoffs and review gates
- Architecture remains stable under parallel implementation
- Matches real senior engineering teams

**Negative**

- Slightly slower than single-agent “just ship”
- Requires discipline in prompts and config

## Alternatives considered

- **Single agent does everything:** fastest prototype; poor long-term structure
- **All agents equal committers without review:** high conflict rate
