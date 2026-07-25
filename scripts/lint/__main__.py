"""CLI entry point: python -m scripts.lint [paths...].

Orchestrates ALL lint checks:
  1. External tools: ruff check, ruff format, pylint, pyright
  2. Custom AST rules: SC-001..SC-104, a-prefix, contracts, imports

All configuration is read from pyproject.toml [tool.selma.lint].
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from scripts.lint.config import load_config
from scripts.lint.core.engine import LintEngine
from scripts.lint.core.result import Result
from scripts.lint.core.violation import Violation
from scripts.lint.rules import all_rules
from scripts.lint.runners.base import ToolResult
from scripts.lint.runners.base import ToolRunner
from scripts.lint.runners.pylint import PylintRunner
from scripts.lint.runners.pyright import PyrightRunner
from scripts.lint.runners.ruff import RuffCheckRunner
from scripts.lint.runners.ruff import RuffFormatRunner


def _print_result(v: Violation, fmt: str) -> Result[None]:
    """Print a violation in the specified output format.

    Precondition: v is a valid Violation, fmt is 'json', 'gcc', or 'default'.
    Postcondition: violation printed to stdout.
    Side effect: writes to stdout.
    Resource: stdout file descriptor.
    Failure: never fails, always returns Ok.
    """
    b_continue = True
    ret: Result[None] = Result.success(None)
    if fmt not in ("json", "gcc", "default"):
        b_continue = False
    if b_continue:
        if fmt == "json":
            sys.stdout.write(
                json.dumps(
                    {
                        "file": v.filepath,
                        "line": v.line,
                        "col": v.col,
                        "code": v.code,
                        "message": v.message,
                        "severity": v.severity,
                    }
                )
                + "\n"
            )
        elif fmt == "gcc":
            sys.stdout.write(
                f"{v.filepath}:{v.line}:{v.col}: {v.severity} [{v.code}] {v.message}\n"
            )
        else:
            sys.stdout.write(str(v) + "\n")
    return ret


def _print_tool_result(result: ToolResult) -> Result[None]:
    """Print tool stdout and stderr to appropriate streams.

    Precondition: result is a valid ToolResult.
    Postcondition: tool output printed to stdout and stderr.
    Side effect: writes to stdout and stderr.
    Resource: stdout and stderr file descriptors.
    Failure: never fails, always returns Ok.
    """
    b_continue = True
    ret: Result[None] = Result.success(None)
    if not isinstance(result, ToolResult):
        b_continue = False
    if b_continue:
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
    return ret


def _run_tool_check(
    a_runner: ToolRunner, a_paths: list[str], **kwargs: object
) -> Result[bool]:
    """Run a tool check and print results.

    Precondition: a_runner is a valid ToolRunner instance.
    Postcondition: returns Ok(True) on failure, Ok(False) on success.
    Side effect: prints tool output to stdout/stderr.
    Resource: subprocess handles, file descriptors.
    Failure: returns Failure if tool execution errors.
    """
    b_continue = True
    failed: Result[bool] = Result.success(a_value=False)
    run_result = a_runner.run(a_paths, **kwargs)
    if run_result.is_failure().value:
        b_continue = False
        sys.stderr.write(run_result.message + "\n")
        failed = Result.success(a_value=True)
    if b_continue:
        _print_tool_result(run_result.value)
        if not run_result.value.success:
            failed = Result.success(a_value=True)
    return failed


def _build_parser() -> Result[argparse.ArgumentParser]:
    """Build the CLI argument parser.

    Precondition: None.
    Postcondition: Returns Ok with a configured ArgumentParser.
    Side effect: None.
    Resource: None.
    Failure: Never fails.
    """
    b_continue = True
    ret: Result[argparse.ArgumentParser] = Result.success(
        argparse.ArgumentParser(
            prog="selma-lint",
            description="Python AST-based linter enforcing selma coding standards",
        )
    )
    if b_continue:
        ret.value.add_argument(
            "paths",
            nargs="*",
            help="Files or directories to lint (default: from pyproject.toml)",
        )
        ret.value.add_argument(
            "--codes", nargs="*", help="Only run AST rules with these codes"
        )
        ret.value.add_argument(
            "--exclude-codes", nargs="*", help="Exclude AST rules with these codes"
        )
        ret.value.add_argument(
            "--format", choices=["default", "json", "gcc"], default="default"
        )
        ret.value.add_argument(
            "--skip-tools",
            action="store_true",
            help="Skip external tools (ruff/pylint/pyright)",
        )
        ret.value.add_argument(
            "--skip-ast", action="store_true", help="Skip custom AST rules"
        )
        ret.value.add_argument(
            "--only",
            choices=["ruff-check", "ruff-format", "pylint", "pyright", "ast"],
            help="Run only one check",
        )
        ret.value.add_argument(
            "--config", help="Path to pyproject.toml (default: auto-detect)"
        )
    return ret


def _resolve_paths(
    a_args_paths: list[str],
    a_config_paths: tuple[str, ...],
    a_service_root: Path,
) -> Result[list[str]]:
    """Resolve lint target paths relative to service root.

    Precondition: a_args_paths or a_config_paths is non-empty.
    Postcondition: Returns Ok with list of absolute path strings.
    Side effect: None.
    Resource: None.
    Failure: Never fails.
    """
    b_continue = True
    ret: Result[list[str]] = Result.success([])
    if b_continue:
        raw = a_args_paths or list(a_config_paths)
        ret = Result.success(
            [str(a_service_root / p) if not Path(p).is_absolute() else p for p in raw]
        )
    return ret


def _run_external_tools(
    a_only: str | None,
    a_paths: list[str],
    a_service_root: Path,
    *,
    a_skip_tools: bool,
) -> Result[bool]:
    """Run external tool checks (ruff, pylint, pyright).

    Precondition: a_paths is non-empty.
    Postcondition: Returns Ok(True) if any tool reported failure, Ok(False) otherwise.
    Side effect: prints tool output to stdout/stderr.
    Resource: subprocess handles, file descriptors.
    Failure: Never fails; errors reported via return value.
    """
    b_continue = True
    ret: Result[bool] = Result.success(a_value=False)
    if b_continue and not a_skip_tools:
        runners: list[tuple[str, ToolRunner, dict[str, object]]] = [
            ("ruff-check", RuffCheckRunner(), {}),
            ("ruff-format", RuffFormatRunner(), {}),
            ("pylint", PylintRunner(), {"project_root": str(a_service_root)}),
            ("pyright", PyrightRunner(), {"project_root": str(a_service_root)}),
        ]
        for name, runner, kwargs in runners:
            if a_only is not None and a_only != name:
                continue
            tr = _run_tool_check(runner, a_paths, **kwargs)
            if tr.is_success().value and tr.value:
                ret = Result.success(a_value=True)
    return ret


def _run_ast_rules(
    a_only: str | None,
    a_codes: list[str] | None,
    a_exclude_codes: set[str],
    a_paths: list[str],
    a_config: object,
    a_format: str,
    *,
    a_skip_ast: bool,
) -> Result[bool]:
    """Run custom AST lint rules.

    Precondition: a_paths is non-empty.
    Postcondition: Returns Ok(True) if any violations found, Ok(False) otherwise.
    Side effect: prints violations to stdout.
    Resource: None.
    Failure: Never fails; errors encoded in return value.
    """
    b_continue = True
    ret: Result[bool] = Result.success(a_value=False)
    if b_continue and not a_skip_ast and a_only in (None, "ast"):
        rules_result = all_rules(a_config)
        rules = rules_result.value if rules_result.is_success().value else []
        if a_codes:
            rules = [r for r in rules if r.code in a_codes]
        if a_exclude_codes:
            rules = [r for r in rules if r.code not in a_exclude_codes]
        engine = LintEngine(rules, a_config)
        violations_result = engine.lint_paths(a_paths)
        violations = (
            violations_result.value if violations_result.is_success().value else []
        )
        for v in violations:
            _print_result(v, a_format)
        if violations:
            ret = Result.success(a_value=True)
    return ret


def _run_checks(
    a_args: argparse.Namespace,
    a_config: object,
    a_paths: list[str],
    a_service_root: Path,
    a_exclude_codes: set[str],
) -> Result[int]:
    """Run all lint checks and return the exit code.

    Precondition: config loaded successfully.
    Postcondition: Returns Ok with exit code (0=pass, 1=fail).
    Side effect: prints results to stdout/stderr.
    Resource: subprocess handles, file descriptors.
    Failure: Never fails.
    """
    b_continue = True
    failed = False
    if b_continue:
        tools_result = _run_external_tools(
            a_args.only,
            a_paths,
            a_service_root,
            a_skip_tools=a_args.skip_tools,
        )
        if tools_result.is_success().value and tools_result.value:
            failed = True
    if b_continue:
        ast_result = _run_ast_rules(
            a_args.only,
            a_args.codes,
            a_exclude_codes,
            a_paths,
            a_config,
            a_args.format,
            a_skip_ast=a_args.skip_ast,
        )
        if ast_result.is_success().value and ast_result.value:
            failed = True
    return Result.success(1 if failed else 0)


def main() -> Result[int]:
    """Parse CLI arguments and run lint checks.

    Precondition: sys.argv contains valid CLI arguments.
    Postcondition: lint results printed, returns exit code.
    Side effect: writes to stdout/stderr, reads pyproject.toml.
    Resource: subprocess handles, file descriptors.
    Failure: always returns Ok with appropriate exit code.
    """
    b_continue = True
    result: Result[int] = Result.success(0)

    parser_result = _build_parser()
    if parser_result.is_failure().value:
        b_continue = False
        result = Result.failure(parser_result.message)

    if b_continue:
        args = parser_result.value.parse_args()

        service_root = (
            Path(args.config).parent
            if args.config
            else Path(__file__).resolve().parent.parent.parent
        )
        config_result = load_config(service_root)

        if config_result.is_failure().value:
            b_continue = False
            result = Result.failure(config_result.message)

    if b_continue:
        config = config_result.value
        paths_result = _resolve_paths(args.paths, config.paths, service_root)
        if paths_result.is_failure().value:
            b_continue = False
            result = Result.failure(paths_result.message)

    if b_continue:
        exclude_codes = set(config.exclude.codes)
        if args.exclude_codes:
            exclude_codes.update(args.exclude_codes)

        result = _run_checks(
            args,
            config,
            paths_result.value,
            service_root,
            exclude_codes,
        )

    return result


if __name__ == "__main__":
    exit_result = main()
    if exit_result.is_success().value:
        sys.exit(exit_result.value)
    else:
        sys.exit(1)
