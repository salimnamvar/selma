"""CLI interface — command-line entry point.

Minimal composition root. All logic in use cases.
Selma lints its own source code.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import selma as _selma_pkg
from selma.application.dto.lint_request import LintRequest
from selma.composition import Container
from selma.domain.value_objects.file_path import FilePath
from selma.infrastructure.rule_repository.json_rule_repository import JsonRuleRepository


def _collect_file_paths(a_path_strings: list[str]) -> list[FilePath]:
    """Collect Python file paths from argument strings."""
    file_paths: list[FilePath] = []
    for a_path_str in a_path_strings:
        a_path = Path(a_path_str)
        if a_path.is_file() and a_path.suffix == ".py":
            file_paths.append(FilePath(str(a_path)))
        elif a_path.is_dir():
            file_paths.extend(
                FilePath(str(a_py)) for a_py in sorted(a_path.rglob("*.py"))
            )
    return file_paths


def main() -> int:
    """CLI entry point.

    Parses arguments, wires dependencies via Container, runs lint,
    formats and outputs results.
    """
    b_continue = True
    result = 0
    a_parser = argparse.ArgumentParser(
        prog="selma",
        description=("Selma — Schema-driven AST linter enforcing Safe Coding Doctrine"),
    )
    a_parser.add_argument("--version", action="version", version="Selma v0.1.0")
    a_parser.add_argument("paths", nargs="*", help="Files or directories to lint")
    a_parser.add_argument(
        "-f",
        "--format",
        choices=["default", "json", "gcc", "guidance"],
        default="default",
    )
    a_parser.add_argument(
        "--guide",
        action="store_true",
        help="Include guidance in output",
    )
    a_parser.add_argument(
        "--skip-tools",
        action="store_true",
        help="Skip external tools",
    )
    a_parser.add_argument(
        "--skip-ast",
        action="store_true",
        help="Skip AST rules",
    )
    a_parser.add_argument("--only", help="Run only one check")
    a_parser.add_argument(
        "--codes",
        nargs="*",
        help="Only run rules with these codes",
    )
    a_parser.add_argument(
        "--exclude-codes",
        nargs="*",
        help="Exclude rules with these codes",
    )
    a_parser.add_argument("-v", "--verbose", action="store_true")

    args = a_parser.parse_args()

    if b_continue and not args.paths:
        b_continue = False
        a_parser.print_help()
        result = 0

    if b_continue:
        _pkg_dir = Path(_selma_pkg.__file__).parent
        rules_dir = _pkg_dir.parent.parent / "schema" / "rules"

        a_container = Container()
        a_rule_repository = JsonRuleRepository(
            a_rules_dir=rules_dir,
        )
        a_use_case = a_container.get_lint_use_case(
            a_rule_repository=a_rule_repository,
        )

        a_exclude_codes = (
            frozenset(args.exclude_codes) if args.exclude_codes else frozenset()
        )
        a_codes = frozenset(args.codes) if args.codes else frozenset()

        a_file_paths = _collect_file_paths(args.paths)

        a_request = LintRequest(
            paths=tuple(a_file_paths),
            exclude_codes=a_exclude_codes,
            codes=a_codes,
            format=args.format,
            guide=args.guide,
            skip_tools=args.skip_tools,
            skip_ast=args.skip_ast,
            only=args.only,
        )

        a_lint_result = a_use_case.execute(a_request)
        if a_lint_result.is_success():
            a_response = a_lint_result.unwrap()
            a_reporter = a_container.get_reporter(
                args.format,
            )
            a_report_result = a_reporter.report(
                a_response.findings,
            )
            if a_report_result.is_success():
                print(a_report_result.unwrap())  # noqa: T201
            if a_response.finding_count > 0:
                result = 1
        else:
            print(  # noqa: T201
                f"Error: {a_lint_result.message}",
                file=sys.stderr,
            )
            result = 1

    return result


if __name__ == "__main__":
    sys.exit(main())
