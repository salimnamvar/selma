"""Infrastructure layer for the Agent Collaboration Orchestrator.

Contains settings and agent adapter ports at foundation. Future: YAML
repositories, filesystem, subprocess runners, concrete agent adapters.
"""

from agent_orchestrator.infrastructure.agents import AgentFactoryProtocol
from agent_orchestrator.infrastructure.agents import AgentProtocol
from agent_orchestrator.infrastructure.config import OrchestratorSettings

__all__ = [
    "AgentFactoryProtocol",
    "AgentProtocol",
    "OrchestratorSettings",
]
