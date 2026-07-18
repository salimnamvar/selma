# ADR 0002: Agent adapter plugin model

## Status

Accepted

## Context

The product coordinates OpenCode, Mimo, Poolside, and future agents. If the core
references those names in domain or service logic, every new vendor becomes a
core change and agents will hardcode vendor assumptions.

## Decision

1. Define `AgentProtocol` with `execute(task, context) -> result`
2. Define `AgentFactoryProtocol` for registry-based construction
3. Bind agents in YAML via `adapter: <registry_key>`
4. Place concrete adapters under `infrastructure/agents/` (future modules)
5. Core services depend only on the protocol

Vendor-specific CLIs, APIs, prompts formats, and env vars live **only** in adapters.

## Consequences

**Positive**

- New agents without core edits (factory registration only)
- Independent testing with `NoOpAgentAdapter`
- Clear review rule: vendor import in domain/service = BLOCKER

**Negative**

- Some duplication of “run subprocess” helpers (mitigate with shared util later)
- Registry must stay documented

## Alternatives considered

- **Direct subprocess in service:** couples core to CLI shape
- **RPC microservice per agent:** too heavy for v1
- **Single multi-vendor class with if/else:** violates OCP and SRP
