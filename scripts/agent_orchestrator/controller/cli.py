"""CLI controller surface for the Agent Collaboration Orchestrator.

Foundation: command names, options, and help text only. No business logic.
Implementations must wire Typer handlers to service ports (see architecture.md).
"""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(
    name="agent-orchestrator",
    help="Coordinate AI coding agents through configuration-driven workflows.",
    no_args_is_help=True,
)


@app.command("run")
def run_workflow(
    workflow: Path = typer.Option(
        ...,
        "--workflow",
        "-w",
        help="Path to workflow.yaml (or directory containing it).",
        exists=False,
    ),
    config_dir: Path | None = typer.Option(
        None,
        "--config-dir",
        "-c",
        help="Directory with agents.yaml / roles.yaml / prompts.yaml.",
    ),
    workspace: Path = typer.Option(
        Path(),
        "--workspace",
        help="Workspace root for agent execution and artifacts.",
    ),
) -> None:
    """Start a workflow run from configuration.

    Not implemented at foundation stage.
    """
    _ = (workflow, config_dir, workspace)
    msg = "Workflow execution is not implemented yet. See docs/roadmap.md Phase 1-2 and service protocols."
    raise NotImplementedError(msg)


@app.command("status")
def show_status(
    run_id: str = typer.Argument(..., help="Workflow run identifier."),
) -> None:
    """Show status of a workflow run.

    Not implemented at foundation stage.
    """
    _ = run_id
    msg = "Run status is not implemented yet. See WorkflowExecutionServiceProtocol."
    raise NotImplementedError(msg)


@app.command("list-agents")
def list_agents(
    config_dir: Path = typer.Option(
        Path("config"),
        "--config-dir",
        "-c",
        help="Directory containing agents.yaml.",
    ),
) -> None:
    """List configured agents.

    Not implemented at foundation stage.
    """
    _ = config_dir
    msg = "Agent listing is not implemented yet. See AgentRepositoryProtocol."
    raise NotImplementedError(msg)


@app.command("validate-config")
def validate_config(
    config_dir: Path = typer.Option(
        Path("config"),
        "--config-dir",
        "-c",
        help="Directory containing configuration YAML files.",
    ),
) -> None:
    """Validate agents/workflows/roles/prompts configuration.

    Not implemented at foundation stage.
    """
    _ = config_dir
    msg = "Config validation is not implemented yet. Planned: load YAML via repositories and report schema errors."
    raise NotImplementedError(msg)
