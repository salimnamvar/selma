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
from selma.domain.value_objects.severity import Severity


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


def main() -> int:
    """CLI entry point.

    Parses arguments, wires dependencies via Container, runs lint,
    formats and outputs results.
    """
    b_continue = True
    result = 0
    parser = argparse.ArgumentParser(
        prog="selma",
        description=("Selma — Schema-driven AST linter enforcing Safe Coding Doctrine"),
    )
    parser.add_argument("--version", action="version", version="Selma v0.1.0")
    parser.add_argument("paths", nargs="*", help="Files or directories to lint")
    parser.add_argument(
        "-f",
        "--format",
        choices=["default", "json", "gcc", "guidance"],
        default="default",
    )
    parser.add_argument(
        "--guide",
        action="store_true",
        help="Include guidance in output",
    )
    parser.add_argument(
        "--skip-tools",
        action="store_true",
        help="Skip external tools",
    )
    parser.add_argument(
        "--skip-ast",
        action="store_true",
        help="Skip AST rules",
    )
    parser.add_argument("--only", help="Run only one check")
    parser.add_argument(
        "--codes",
        nargs="*",
        help="Only run rules with these codes",
    )
    parser.add_argument(
        "--exclude-codes",
        nargs="*",
        help="Exclude rules with these codes",
    )
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if b_continue and not args.paths:
        b_continue = False
        parser.print_help()
        result = 0

    if b_continue:
        _pkg_dir = Path(_selma_pkg.__file__).parent
        rules_dir = _pkg_dir.parent.parent / "schema" / "rules"

        container = Container()
        use_case = container.get_lint_use_case_with_defaults(
            a_rules_dir=rules_dir,
        )

        exclude_codes: frozenset[str] = (
            frozenset(args.exclude_codes) if args.exclude_codes else frozenset()
        )
        codes: frozenset[str] = frozenset(args.codes) if args.codes else frozenset()

        file_paths = _collect_file_paths(args.paths)

        request = LintRequest(
            paths=tuple(file_paths),
            exclude_codes=exclude_codes,
            codes=codes,
            format=args.format,
            guide=args.guide,
            skip_tools=args.skip_tools,
            skip_ast=args.skip_ast,
            only=args.only,
        )

        lint_result = use_case.execute(request)
        if lint_result.is_success():
            response = lint_result.unwrap()
            if args.verbose:
                report_findings = response.findings
            else:
                report_findings = tuple(
                    f for f in response.findings if f.severity != Severity.INFORMATIONAL
                )
            reporter = container.get_reporter(
                args.format,
            )
            report_result = reporter.report(
                report_findings,
            )
            if report_result.is_success():
                # CLI user-facing output (SC-061 / STYLE-3: avoid print()).
                sys.stdout.write(report_result.unwrap() + "\n")
            if response.finding_count > 0:
                result = 1
        else:
            sys.stderr.write(f"Error: {lint_result.message}\n")
            result = 1

    return result


if __name__ == "__main__":
    sys.exit(main())
