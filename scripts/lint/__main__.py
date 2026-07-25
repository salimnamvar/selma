"""CLI entry point: python -m scripts.lint [paths...]

Orchestrates ALL lint checks:
  1. External tools: ruff check, ruff format, pylint, pyright
  2. Custom AST rules: SC-001..SC-104, a-prefix, contracts, imports

All configuration is read from pyproject.toml [tool.selma.lint].
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts.lint.config import load_config
from scripts.lint.core.engine import LintEngine
from scripts.lint.core.violation import Violation
from scripts.lint.rules import all_rules
from scripts.lint.runners.ruff import RuffCheckRunner, RuffFormatRunner
from scripts.lint.runners.pylint import PylintRunner
from scripts.lint.runners.pyright import PyrightRunner
from scripts.lint.runners.base import ToolResult

INVALID_RESULT = None


def _print_result(v: Violation, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps({
            "file": v.filepath, "line": v.line, "col": v.col,
            "code": v.code, "message": v.message, "severity": v.severity,
        }))
    elif fmt == "gcc":
        print(f"{v.filepath}:{v.line}:{v.col}: {v.severity} [{v.code}] {v.message}")
    else:
        print(v)


def _print_tool_result(result: ToolResult) -> None:
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)


def main() -> None:
    """Parse CLI arguments and run lint checks."""
    parser = argparse.ArgumentParser(
        prog="selma-lint",
        description="Python AST-based linter enforcing selma coding standards",
    )
    parser.add_argument("paths", nargs="*", help="Files or directories to lint (default: from pyproject.toml)")
    parser.add_argument("--codes", nargs="*", help="Only run AST rules with these codes")
    parser.add_argument("--exclude-codes", nargs="*", help="Exclude AST rules with these codes")
    parser.add_argument("--format", choices=["default", "json", "gcc"], default="default")
    parser.add_argument("--skip-tools", action="store_true", help="Skip external tools (ruff/pylint/pyright)")
    parser.add_argument("--skip-ast", action="store_true", help="Skip custom AST rules")
    parser.add_argument("--only", choices=["ruff-check", "ruff-format", "pylint", "pyright", "ast"], help="Run only one check")
    parser.add_argument("--config", help="Path to pyproject.toml (default: auto-detect)")
    args = parser.parse_args()

    service_root = Path(args.config).parent if args.config else Path(__file__).resolve().parent.parent.parent
    config = load_config(service_root)

    paths = args.paths or list(config.paths)
    paths = [str(service_root / p) if not Path(p).is_absolute() else p for p in paths]

    exclude_codes = set(config.exclude.codes)
    if args.exclude_codes:
        exclude_codes.update(args.exclude_codes)

    failed = False

    # --- External tool checks ---
    if not args.skip_tools and args.only in (None, "ruff-check"):
        result = RuffCheckRunner().run(paths)
        _print_tool_result(result)
        if not result.ok:
            failed = True

    if not args.skip_tools and args.only in (None, "ruff-format"):
        result = RuffFormatRunner().run(paths)
        _print_tool_result(result)
        if not result.ok:
            failed = True

    if not args.skip_tools and args.only in (None, "pylint"):
        result = PylintRunner().run(paths, project_root=str(service_root))
        _print_tool_result(result)
        if not result.ok:
            failed = True

    if not args.skip_tools and args.only in (None, "pyright"):
        result = PyrightRunner().run(paths, project_root=str(service_root))
        _print_tool_result(result)
        if not result.ok:
            failed = True

    # --- Custom AST rules ---
    if not args.skip_ast and args.only in (None, "ast"):
        rules = all_rules(config)
        if args.codes:
            rules = [r for r in rules if r.code in args.codes]
        if exclude_codes:
            rules = [r for r in rules if r.code not in exclude_codes]

        engine = LintEngine(rules, config)
        violations = engine.lint_paths(paths)
        for v in violations:
            _print_result(v, args.format)
        if violations:
            failed = True

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
