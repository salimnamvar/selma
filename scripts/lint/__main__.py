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
            print(  # noqa: T201
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
            )
        elif fmt == "gcc":
            print(f"{v.filepath}:{v.line}:{v.col}: {v.severity} [{v.code}] {v.message}")  # noqa: T201
        else:
            print(v)  # noqa: T201
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
            print(result.stdout, end="")  # noqa: T201
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)  # noqa: T201
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
    failed: Result[bool] = Result.success(False)  # noqa: FBT003
    run_result = a_runner.run(a_paths, **kwargs)
    if run_result.is_failure().value:
        b_continue = False
        print(run_result.message, file=sys.stderr)  # noqa: T201
        failed = Result.success(True)  # noqa: FBT003
    if b_continue:
        _print_tool_result(run_result.value)
        if not run_result.value.ok:
            failed = Result.success(True)  # noqa: FBT003
    return failed


def main() -> Result[int]:  # noqa: C901
    """Parse CLI arguments and run lint checks.

    Precondition: sys.argv contains valid CLI arguments.
    Postcondition: lint results printed, returns exit code.
    Side effect: writes to stdout/stderr, reads pyproject.toml.
    Resource: subprocess handles, file descriptors.
    Failure: always returns Ok with appropriate exit code.
    """
    b_continue = True
    result: Result[int] = Result.success(0)

    parser = argparse.ArgumentParser(
        prog="selma-lint",
        description="Python AST-based linter enforcing selma coding standards",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to lint (default: from pyproject.toml)",
    )
    parser.add_argument(
        "--codes", nargs="*", help="Only run AST rules with these codes"
    )
    parser.add_argument(
        "--exclude-codes", nargs="*", help="Exclude AST rules with these codes"
    )
    parser.add_argument(
        "--format", choices=["default", "json", "gcc"], default="default"
    )
    parser.add_argument(
        "--skip-tools",
        action="store_true",
        help="Skip external tools (ruff/pylint/pyright)",
    )
    parser.add_argument("--skip-ast", action="store_true", help="Skip custom AST rules")
    parser.add_argument(
        "--only",
        choices=["ruff-check", "ruff-format", "pylint", "pyright", "ast"],
        help="Run only one check",
    )
    parser.add_argument(
        "--config", help="Path to pyproject.toml (default: auto-detect)"
    )
    args = parser.parse_args()

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
        paths = args.paths or list(config.paths)
        paths = [
            str(service_root / p) if not Path(p).is_absolute() else p for p in paths
        ]

        exclude_codes = set(config.exclude.codes)
        if args.exclude_codes:
            exclude_codes.update(args.exclude_codes)

        failed = False

        # --- External tool checks ---
        if not args.skip_tools and args.only in (None, "ruff-check"):
            tr = _run_tool_check(RuffCheckRunner(), paths)
            if tr.is_success().value and tr.value:
                failed = True

        if not args.skip_tools and args.only in (None, "ruff-format"):
            tr = _run_tool_check(RuffFormatRunner(), paths)
            if tr.is_success().value and tr.value:
                failed = True

        if not args.skip_tools and args.only in (None, "pylint"):
            tr = _run_tool_check(PylintRunner(), paths, project_root=str(service_root))
            if tr.is_success().value and tr.value:
                failed = True

        if not args.skip_tools and args.only in (None, "pyright"):
            tr = _run_tool_check(PyrightRunner(), paths, project_root=str(service_root))
            if tr.is_success().value and tr.value:
                failed = True

        # --- Custom AST rules ---
        if not args.skip_ast and args.only in (None, "ast"):
            rules_result = all_rules(config)
            rules = rules_result.value if rules_result.is_success().value else []
            if args.codes:
                rules = [r for r in rules if r.code in args.codes]
            if exclude_codes:
                rules = [r for r in rules if r.code not in exclude_codes]

            engine = LintEngine(rules, config)
            violations_result = engine.lint_paths(paths)
            violations = (
                violations_result.value if violations_result.is_success().value else []
            )
            for v in violations:
                _print_result(v, args.format)
            if violations:
                failed = True

        result = Result.success(1 if failed else 0)

    return result


if __name__ == "__main__":
    exit_result = main()
    if exit_result.is_success().value:
        sys.exit(exit_result.value)
    else:
        sys.exit(1)
