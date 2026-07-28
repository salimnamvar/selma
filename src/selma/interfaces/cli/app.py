"""CLI interface — non-interactive entry for inspect and query.

Interactive governance sessions use the Textual TUI (selma.interfaces.tui).
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys

from selma.application.dto.inspect_request import InspectRequest
from selma.application.dto.query_request import QueryKind
from selma.application.dto.query_request import QueryRequest
from selma.composition import Container
from selma.domain.value_objects.file_path import FilePath
from selma.domain.value_objects.result import Result
from selma.infrastructure.bootstrap import lifespan
from selma.infrastructure.config import ConfigLoader
from selma.infrastructure.config.models import SelmaConfig


def _collect_file_paths(a_path_strings: list[str]) -> list[FilePath]:
    """Collect Python file paths from argument strings."""
    file_paths: list[FilePath] = []
    for path_str in a_path_strings:
        path = Path(path_str)
        if path.is_file() and path.suffix == ".py":
            file_paths.append(FilePath(str(path)))
        elif path.is_dir():
            file_paths.extend(
                FilePath(str(py_file)) for py_file in sorted(path.rglob("*.py"))
            )
    return file_paths


def _build_shared_parent() -> argparse.ArgumentParser:
    """Shared flags inherited by all subcommands."""
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )
    parent.add_argument("--skip-tools", action="store_true", help="Skip external tools")
    parent.add_argument("--skip-ast", action="store_true", help="Skip AST rules")
    parent.add_argument("--file-timeout", type=int, help="Per-file timeout in seconds")
    parent.add_argument("--disable", nargs="*", help="Disable rules with these codes")
    parent.add_argument("--directive-root", help="Root directive directory")
    parent.add_argument("--directive-policy-dir", help="Policy definitions directory")
    parent.add_argument("--directive-rule-dir", help="Rule definitions directory")
    parent.add_argument("--schema-root", help="Root schema directory")
    parent.add_argument("--schema-rule-schema", help="Rule schema JSON file")
    parent.add_argument("--schema-policy-doctrine", help="Policy doctrine YAML file")
    parent.add_argument(
        "--config",
        help="Path to pyproject.toml (auto-detected if not specified)",
    )
    parent.add_argument("-v", "--verbose", action="store_true")
    parent.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive Textual TUI",
    )
    return parent


def _build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    shared = _build_shared_parent()
    parser = argparse.ArgumentParser(
        prog="selma",
        description=(
            "Selma — governance platform: inspect source, query directives, "
            "and run an interactive reasoning session"
        ),
        parents=[shared],
    )
    parser.add_argument("--version", action="version", version="Selma v0.1.0")

    sub = parser.add_subparsers(dest="command")

    inspect_p = sub.add_parser(
        "inspect",
        help="Inspect source against directives",
        parents=[shared],
    )
    inspect_p.add_argument("paths", nargs="*", help="Files or directories to inspect")
    inspect_p.add_argument(
        "-f",
        "--format",
        choices=["default", "json", "gcc", "guidance"],
        help="Output format",
    )
    inspect_p.add_argument(
        "--guide", action="store_true", help="Include guidance in output"
    )
    inspect_p.add_argument("--output", help="Output file path")
    inspect_p.add_argument("--codes", nargs="*", help="Only these directive codes")
    inspect_p.add_argument(
        "--exclude-codes", nargs="*", help="Exclude these directive codes"
    )
    inspect_p.add_argument("--only", help="Run only one evaluator type")
    inspect_p.add_argument("--max-workers", type=int, help="Max concurrent workers")

    query_p = sub.add_parser(
        "query",
        help="Query directive catalog for reasoning",
        parents=[shared],
    )
    query_p.add_argument(
        "kind",
        choices=["list", "policy", "rule", "directive", "guidance", "search"],
        help="Query kind",
    )
    query_p.add_argument("--id", dest="lineage_id", default="", help="Machine ID")
    query_p.add_argument("--text", default="", help="Search text")
    query_p.add_argument("--limit", type=int, default=50)

    sub.add_parser("tui", help="Interactive Textual session", parents=[shared])

    return parser


def _find_pyproject() -> Path | None:
    """Find pyproject.toml by walking up from cwd."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / "pyproject.toml"
        if candidate.is_file():
            return candidate
    return None


def _load_config(a_args: argparse.Namespace) -> Result[SelmaConfig]:
    """Load SelmaConfig from CLI args and pyproject."""
    b_continue = True
    result: Result[SelmaConfig] = Result.failure("unreachable")

    cli_args: dict[str, object] = {}
    if getattr(a_args, "format", None):
        cli_args["format"] = a_args.format
    if getattr(a_args, "guide", False):
        cli_args["guide"] = True
    if getattr(a_args, "output", None):
        cli_args["output"] = a_args.output
    if getattr(a_args, "no_color", False):
        cli_args["no_color"] = True
    if getattr(a_args, "skip_tools", False):
        cli_args["skip_tools"] = True
    if getattr(a_args, "skip_ast", False):
        cli_args["skip_ast"] = True
    if getattr(a_args, "only", None):
        cli_args["only"] = a_args.only
    if getattr(a_args, "max_workers", None):
        cli_args["max_workers"] = a_args.max_workers
    if getattr(a_args, "file_timeout", None):
        cli_args["file_timeout"] = a_args.file_timeout
    if getattr(a_args, "codes", None):
        cli_args["codes"] = a_args.codes
    if getattr(a_args, "exclude_codes", None):
        cli_args["exclude_codes"] = a_args.exclude_codes
    if getattr(a_args, "disable", None):
        cli_args["disable"] = a_args.disable
    if getattr(a_args, "directive_root", None):
        cli_args["directive_root"] = a_args.directive_root
    if getattr(a_args, "directive_policy_dir", None):
        cli_args["directive_policy_dir"] = a_args.directive_policy_dir
    if getattr(a_args, "directive_rule_dir", None):
        cli_args["directive_rule_dir"] = a_args.directive_rule_dir
    if getattr(a_args, "schema_root", None):
        cli_args["schema_root"] = a_args.schema_root
    if getattr(a_args, "schema_rule_schema", None):
        cli_args["schema_rule_schema"] = a_args.schema_rule_schema
    if getattr(a_args, "schema_policy_doctrine", None):
        cli_args["schema_policy_doctrine"] = a_args.schema_policy_doctrine

    config_path: Path | None = None
    if getattr(a_args, "config", None):
        config_path = Path(a_args.config)
    else:
        config_path = _find_pyproject()

    loader = ConfigLoader()
    config_result = loader.load(
        a_config_path=config_path,
        a_cli_args=cli_args or None,
    )
    if config_result.is_failure():
        b_continue = False
        result = Result.failure(config_result.message)
    if b_continue:
        result = Result.success(config_result.unwrap())
    return result


async def _run_inspect(
    a_args: argparse.Namespace, a_config: SelmaConfig
) -> Result[int]:
    """Run source inspection."""
    b_continue = True
    exit_code = 0
    paths = list(getattr(a_args, "paths", None) or [])
    if b_continue and not paths:
        sys.stderr.write("No paths provided to inspect.\n")
        b_continue = False
        exit_code = 0

    if b_continue:
        container = Container()
        reporter = container.get_reporter(a_config.output.format)
        repository = container.get_directive_repository(
            a_rules_dir=a_config.directive.rule_dir,
            a_schema_path=a_config.schema_paths.rule_schema,
            a_policy_dir=a_config.directive.policy_dir,
        )
        use_case = container.get_inspect_use_case(
            a_directive_repository=repository,
            a_reporter=reporter,
        )

        exclude_codes: frozenset[str] = (
            frozenset(a_args.exclude_codes)
            if getattr(a_args, "exclude_codes", None)
            else frozenset(a_config.rules_filter.exclude_codes)
        )
        codes: frozenset[str] = (
            frozenset(a_args.codes)
            if getattr(a_args, "codes", None)
            else frozenset(a_config.rules_filter.codes)
        )
        file_paths = _collect_file_paths(paths)
        request = InspectRequest(
            paths=tuple(file_paths),
            exclude_codes=exclude_codes,
            codes=codes,
            format=a_config.output.format,
            guide=a_config.output.guide or bool(getattr(a_args, "guide", False)),
            skip_tools=a_config.execution.skip_tools,
            skip_ast=a_config.execution.skip_ast,
            only=str(getattr(a_args, "only", None) or a_config.execution.only or ""),
            max_workers=int(
                getattr(a_args, "max_workers", None) or a_config.execution.max_workers
            ),
        )
        lint_result = await use_case.execute(request)
        if lint_result.is_success():
            response = lint_result.unwrap()
            if response.report_text:
                sys.stdout.write(response.report_text + "\n")
            # Gate on violations (critical/high) — low/informational findings
            # remain visible but do not fail the process (CI / pre-commit).
            if response.has_errors:
                exit_code = 1
        else:
            sys.stderr.write(f"Error: {lint_result.message}\n")
            exit_code = 1

    return Result.success(exit_code)


async def _run_query(a_args: argparse.Namespace, a_config: SelmaConfig) -> Result[int]:
    """Run catalog query."""
    container = Container()
    use_case = container.get_query_use_case_with_defaults(
        a_rules_dir=a_config.directive.rule_dir,
        a_schema_path=a_config.schema_paths.rule_schema,
        a_policy_dir=a_config.directive.policy_dir,
    )
    kind = QueryKind(a_args.kind)
    request = QueryRequest(
        kind=kind,
        lineage_id=getattr(a_args, "lineage_id", "") or "",
        text=getattr(a_args, "text", "") or "",
        limit=getattr(a_args, "limit", 50) or 50,
    )
    query_result = await use_case.execute(request)
    if query_result.is_failure():
        sys.stderr.write(f"Error: {query_result.message}\n")
        return Result.success(1)
    response = query_result.unwrap()
    sys.stdout.write(response.summary + "\n")
    if response.items:
        for item in response.items:
            lineage = item.get("lineage_id", "")
            title = item.get("title", item.get("message", ""))
            sys.stdout.write(f"  {lineage}: {title}\n")
    if response.payload and request.kind != QueryKind.LIST:
        sys.stdout.write(json.dumps(response.payload, indent=2) + "\n")
    return Result.success(0)


def _normalize_argv(a_argv: list[str] | None) -> list[str]:
    """Default bare path arguments to the inspect subcommand.

    Pre-commit and scripts call ``selma src/…`` without ``inspect``.
    """
    argv = list(a_argv) if a_argv is not None else sys.argv[1:]
    if not argv:
        return argv
    first = argv[0]
    if first in {"inspect", "query", "tui", "-h", "--help", "--version"}:
        return argv
    if first.startswith("-"):
        if any(not arg.startswith("-") for arg in argv):
            return ["inspect", *argv]
        return argv
    return ["inspect", *argv]


async def async_main(a_argv: list[str] | None = None) -> Result[int]:
    """Async CLI entry."""
    parser = _build_parser()
    args = parser.parse_args(_normalize_argv(a_argv))

    command = args.command
    if getattr(args, "interactive", False) or command == "tui":
        config_result = _load_config(args)
        if config_result.is_failure():
            sys.stderr.write(f"Configuration error: {config_result.message}\n")
            return Result.success(1)
        # Lazy import keeps non-TUI CLI light if Textual is optional in some envs.
        tui_module = __import__("selma.interfaces.tui.app", fromlist=["run_tui"])
        await tui_module.run_tui(config_result.unwrap())
        return Result.success(0)

    config_result = _load_config(args)
    if config_result.is_failure():
        sys.stderr.write(f"Configuration error: {config_result.message}\n")
        return Result.success(1)
    config = config_result.unwrap()

    with lifespan(config.logging):
        if command == "query":
            return await _run_query(args, config)
        if command == "inspect" or (command is None and getattr(args, "paths", None)):
            return await _run_inspect(args, config)

        tui_module = __import__("selma.interfaces.tui.app", fromlist=["run_tui"])
        await tui_module.run_tui(config)
        return Result.success(0)


def main() -> Result[int]:
    """Sync wrapper for CLI entry."""
    return asyncio.run(async_main())


def cli_entry() -> None:
    """Console script entry point — unwraps Result for sys.exit."""
    result = main()
    sys.exit(result.unwrap() if result.is_success() else 1)


if __name__ == "__main__":
    result = main()
    sys.exit(result.unwrap() if result.is_success() else 1)
