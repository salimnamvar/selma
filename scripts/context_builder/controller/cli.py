"""CLI controller for LLM Context Builder."""

from __future__ import annotations

from pathlib import Path

import typer

from context_builder.domain.enums import OutputMode
from context_builder.infrastructure.config import ContextBuilderSettings
from context_builder.infrastructure.tokenizer import count_tokens
from context_builder.renderer.markdown import MarkdownRenderer
from context_builder.repository.collector import FilesystemCollector
from context_builder.repository.writer import FileWriter
from context_builder.service.context_builder import ContextBuilderService

app = typer.Typer(help="Build LLM context from source files.")


@app.command()
def build(
    inputs: list[str] = typer.Argument(
        default_factory=lambda: ContextBuilderSettings().inputs,
        help="Input paths to include.",
    ),
    output: str = typer.Option(".tmp", "-o", "--output", help="Output location"),
    mode: str = typer.Option("separate", "--mode", case_sensitive=False, help="separate or aggregate"),
    exclude: list[str] = typer.Option(
        ["archived", "__pycache__", ".git", ".mypy_cache", ".pytest_cache", "node_modules"],
        "--exclude",
        help="Directories to exclude",
    ),
    extensions: list[str] = typer.Option(
        [".py", ".md", ".txt", ".rst", ".puml"],
        "--extensions",
        help="File extensions to include",
    ),
    max_tokens: int | None = typer.Option(None, "--max-tokens", help="Max tokens per chunk"),
) -> None:
    """Build context for LLM consumption."""
    config = ContextBuilderSettings(
        inputs=inputs,
        output=output,
        mode=OutputMode.AGGREGATE if mode == "aggregate" else OutputMode.SEPARATE,
        exclude=exclude,
        extensions=extensions,
        max_tokens=max_tokens,
    )

    # Wire dependencies
    collector = FilesystemCollector(
        frozenset(config.extensions),
        frozenset(config.exclude),
        count_tokens,
    )
    writer = FileWriter(a_base_path=Path(config.output))
    renderer = MarkdownRenderer()

    # Create service with injected dependencies
    service = ContextBuilderService(
        a_config=config.to_domain(),
        a_collector=collector,
        a_writer=writer,
        a_renderer=renderer,
        a_tokenizer=count_tokens,
    )
    result = service.build()

    if result.chunks > 1:
        typer.echo(f"Split into {result.chunks} chunks: {', '.join(result.output_paths)}")
    else:
        typer.echo(f"Wrote {len(result.output_paths)} file(s): {', '.join(result.output_paths)}")
