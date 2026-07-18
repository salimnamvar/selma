"""Agent adapter package.

Only protocols exist at foundation. Concrete adapters are added per ADR
without changing core domain or service contracts.
"""

from agent_orchestrator.infrastructure.agents.protocol import AgentFactoryProtocol
from agent_orchestrator.infrastructure.agents.protocol import AgentProtocol

__all__ = [
    "AgentFactoryProtocol",
    "AgentProtocol",
]
