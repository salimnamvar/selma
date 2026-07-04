"""Click-based CLI for the usecase-diagram subproject."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from usecase_diagram.config.settings import get_config
from usecase_diagram.repository.contracts import ContractRepository
from usecase_diagram.repository.diagrams import DiagramRepository
from usecase_diagram.repository.project import ProjectRepository
from usecase_diagram.service.fixing import FixingService
from usecase_diagram.service.validation import ValidationService
from usecase_diagram.utils.report import (
    build_uc_report,
    format_text_report,
)


@click.group()
@click.option("--log-level", default=None, help="Override log level.")
@click.pass_context
def cli(ctx: click.Context, log_level: str | None) -> None:
    """Use case diagram linter and auto-fixer."""
    ctx.ensure_object(dict)
    if log_level:
        import logging
        logging.basicConfig(level=getattr(logging, log_level.upper(), logging.INFO))


@cli.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--strict", is_flag=True, help="Exit 1 on violations.")
@click.option("--project-root", type=click.Path(), default=None)
@click.option("--contracts-dir", type=click.Path(), default=None)
def lint(
    paths: tuple[str, ...],
    fmt: str,
    strict: bool,
    project_root: str | None,
    contracts_dir: str | None,
) -> None:
    """Validate use case diagrams against contracts."""
    get_config()
    contracts_path = Path(contracts_dir) if contracts_dir else None
    contract_repo = ContractRepository(contracts_path)
    diagram_repo = DiagramRepository()
    validation_svc = ValidationService(contract_repo)

    all_violations = []
    all_assessments = []

    for path_str in paths:
        path = Path(path_str)
        if path.is_file():
            diagrams = [diagram_repo.parse(path)]
        elif path.is_dir():
            files = diagram_repo.discover(path)
            diagrams = [diagram_repo.parse(f) for f in files]
        else:
            click.echo(f"Skipping: {path}", err=True)
            continue

        for diagram in diagrams:
            violations = validation_svc.validate_diagram(diagram)
            all_violations.extend(violations)

    if project_root:
        pr = ProjectRepository(Path(project_root))
        ctx_obj = pr.build_context()
        project_violations = validation_svc.validate_project(ctx_obj)
        all_violations.extend(project_violations)
        all_assessments.extend(validation_svc.run_assessments(ctx_obj))

    report = build_uc_report(all_violations, all_assessments)

    if fmt == "json":
        output = {
            "layer": report.layer,
            "errors": report.error_count,
            "warnings": report.warning_count,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "severity": v.severity,
                    "message": v.message,
                    "file": v.file,
                    "line": v.line,
                    "fix": v.fix,
                }
                for v in report.violations
            ],
            "assessments": [
                {"id": a.id, "name": a.name, "status": a.status, "detail": a.detail}
                for a in report.assessments
            ],
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(format_text_report(report))

    if strict and report.has_errors:
        sys.exit(1)
    if not all_violations and not all_assessments:
        click.echo("No diagrams found.", err=True)
        sys.exit(2)


@cli.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--in-place", "-i", is_flag=True, help="Write changes in place.")
@click.option("--stdout", is_flag=True, help="Print fixed content to stdout.")
@click.option("--diff", is_flag=True, help="Show diff of changes.")
@click.option("--contracts-dir", type=click.Path(), default=None)
def fix(
    paths: tuple[str, ...],
    in_place: bool,
    stdout: bool,
    diff: bool,
    contracts_dir: str | None,
) -> None:
    """Apply deterministic fixes to use case diagrams."""
    get_config()
    contracts_path = Path(contracts_dir) if contracts_dir else None
    contract_repo = ContractRepository(contracts_path)
    diagram_repo = DiagramRepository()
    validation_svc = ValidationService(contract_repo)
    fixing_svc = FixingService(diagram_repo)

    for path_str in paths:
        path = Path(path_str)
        if path.is_file():
            files = [path]
        elif path.is_dir():
            files = diagram_repo.discover(path)
        else:
            continue

        for filepath in files:
            diagram = diagram_repo.parse(filepath)
            violations = validation_svc.validate_diagram(diagram)

            if not violations:
                click.echo(f"[clean] {filepath.name}")
                continue

            result = fixing_svc.apply_fixes(diagram, violations)
            fixed_source = fixing_svc.rewrite(result.original_source)

            if diff:
                import difflib
                diff_text = "\n".join(
                    difflib.unified_diff(
                        result.original_source.splitlines(),
                        fixed_source.splitlines(),
                        fromfile=str(filepath),
                        tofile=str(filepath) + " (fixed)",
                    )
                )
                if diff_text:
                    click.echo(diff_text)
            elif stdout:
                click.echo(fixed_source)
            elif in_place:
                diagram_repo.write(filepath, fixed_source)
                click.echo(f"[fixed] {filepath.name}")
            else:
                click.echo(f"[would-fix] {filepath.name} ({len(result.fixes_applied)} fixes)")
