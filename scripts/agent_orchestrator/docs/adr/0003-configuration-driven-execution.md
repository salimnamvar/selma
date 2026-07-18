# ADR 0003: Configuration-driven workflow execution

## Status

Accepted

## Context

Workflows (architecture → implement → review → …) will change often. Encoding
workflows in Python classes forces code changes and Architect involvement for
routine process tweaks.

## Decision

- Workflows, agents, roles, and prompts are declared in YAML
- Engine loads config into domain models via repositories
- Step order and `depends_on` express the graph
- Review gates and `max_iterations` are config, not hardcoded loops per vendor

Example locations: `config/examples/*.yaml`.

## Consequences

**Positive**

- Process changes without releases of core logic
- Reviewable workflow diffs in git
- Enables multi-agent org model via config alone

**Negative**

- Need solid validation and good error messages
- Risk of “YAML programming” if config becomes too expressive

## Guardrails

- Keep YAML declarative (no embedded scripts in v1)
- Reject unknown fields or document extension points explicitly
- Do not invent a custom expression language without a new ADR

## Alternatives considered

- **Python workflow DSLs:** powerful but agent-hostile and less reviewable
- **Airflow/Prefect:** operationally heavy; wrong abstraction for local agent CLI
