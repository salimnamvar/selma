"""Entry point for the AI Agent Collaboration Orchestrator CLI."""

from __future__ import annotations

from agent_orchestrator.controller import app


def main() -> None:
    """Invoke the Typer application."""
    app()


if __name__ == "__main__":
    main()
