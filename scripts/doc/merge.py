"""Document merger.

Merges source files and directory trees into Markdown document(s).
Inputs may be files, directories, or nested paths under either.
Supports separate outputs (one file per input) or a single aggregated output.
"""

import argparse
from pathlib import Path
import sys
from typing import List, Optional, Set, TextIO


class DocumentMerger:
    """Merges files and/or directory trees into a Markdown output.

    Attributes:
        _inputs (List[Path]): File or directory paths to merge (in order).
        _output_file (Path): Target Markdown file.
        _exclude (Set[str]): Directory names to skip when walking trees.
        _extensions (Set[str]): File extensions to include when walking directories.
            Explicitly listed file inputs are always included.
    """

    def __init__(
        self,
        a_inputs: List[Path],
        a_output_file: Path,
        a_exclude: Optional[List[str]] = None,
        a_extensions: Optional[Set[str]] = None,
    ) -> None:
        """Initialise the merger.

        Args:
            a_inputs (List[Path]): File or directory paths to merge (in order).
            a_output_file (Path): Target Markdown file.
            a_exclude (Optional[List[str]]): Directory names to skip when walking.
            a_extensions (Optional[Set[str]]): File extensions to include when
                walking directories. Explicit file inputs are always emitted.
        """
        self._inputs: List[Path] = list(a_inputs)
        self._output_file: Path = a_output_file
        self._exclude: Set[str] = set(a_exclude) if a_exclude else set()
        self._extensions: Set[str] = a_extensions or {".py", ".md", ".txt", ".rst", ".puml"}
        self._emitted: Set[Path] = set()

    def merge(self) -> None:
        """Write merged content from all inputs to the output file."""
        self._output_file.parent.mkdir(parents=True, exist_ok=True)
        self._emitted.clear()
        with self._output_file.open("w", encoding="utf-8") as out:
            first_written = True
            for input_path in self._inputs:
                if first_written:
                    wrote = self._process_input(input_path, out, a_separator=False)
                else:
                    wrote = self._process_input(input_path, out, a_separator=True)
                if wrote:
                    first_written = False

    def _process_input(self, a_path: Path, a_out: TextIO, a_separator: bool) -> bool:
        """Process a single input path (file or directory).

        Args:
            a_path (Path): File or directory to merge.
            a_out (TextIO): Open output file handle.
            a_separator (bool): If True, write an INPUT marker before content.

        Returns:
            bool: True if any content was written for this input.
        """
        before = len(self._emitted)
        if a_separator:
            a_out.write(f"\n\n--- INPUT: {a_path} ---\n\n")

        if a_path.is_file():
            # Explicit file inputs are always included (extension filter applies to walks only).
            self._emit(a_path, a_out, a_force=True)
        elif a_path.is_dir():
            self._walk(a_path, a_out)
        else:
            print(f"Warning: {a_path} is neither a file nor a directory. Skipping.", file=sys.stderr)

        return len(self._emitted) > before

    def _walk(self, a_directory: Path, a_out: TextIO) -> None:
        """Recursively walk a directory and emit matching files.

        Args:
            a_directory (Path): Directory to scan.
            a_out (TextIO): Open output file handle.
        """
        try:
            entries: List[Path] = sorted(a_directory.iterdir(), key=lambda p: (p.is_dir(), p.name))
        except OSError as e:
            print(f"Warning: could not list {a_directory}: {e}", file=sys.stderr)
            return

        readme: List[Path] = [e for e in entries if e.is_file() and e.name.lower().startswith("readme")]
        common: List[Path] = [e for e in entries if e.is_dir() and e.name == "common" and e.name not in self._exclude]
        rest_files: List[Path] = [
            e
            for e in entries
            if e.is_file() and not e.name.lower().startswith("readme") and e.suffix in self._extensions
        ]
        rest_dirs: List[Path] = [
            e for e in entries if e.is_dir() and e.name != "common" and e.name not in self._exclude
        ]

        for f in readme:
            self._emit(f, a_out)
        for d in common:
            self._walk(d, a_out)
        for f in rest_files:
            self._emit(f, a_out)
        for d in rest_dirs:
            self._walk(d, a_out)

    def _emit(self, a_path: Path, a_out: TextIO, a_force: bool = False) -> None:
        """Write a single file's content to the output.

        Skips files already emitted (handles overlapping/nested inputs).
        When not forced, only includes paths whose suffix is in ``_extensions``.

        Args:
            a_path (Path): File to read.
            a_out (TextIO): Open output file handle.
            a_force (bool): If True, emit even when extension is not in the filter
                (used for explicitly listed file inputs).
        """
        resolved: Path = a_path.resolve()
        if resolved in self._emitted:
            return
        if not a_force and a_path.suffix not in self._extensions:
            return

        try:
            content: str = a_path.read_text(encoding="utf-8", errors="ignore")
            a_out.write(f"\n\n--- SOURCE: {a_path} ---\n\n")
            a_out.write(content)
            a_out.write("\n")
            self._emitted.add(resolved)
        except Exception as e:
            print(f"Warning: could not read {a_path}: {e}", file=sys.stderr)


def parse_args(a_argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        a_argv (Optional[List[str]]): Argument list to parse. Uses sys.argv when None.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    p: argparse.ArgumentParser = argparse.ArgumentParser(
        description=(
            "Merge source files and/or directories into Markdown. "
            "Inputs may be files, directories, or nested paths. "
            "By default writes one .md per input; "
            "use --mode aggregate to combine all inputs into a single file."
        )
    )
    p.add_argument(
        "-i",
        "--input",
        nargs="+",
        default=[
            "/home/salim/prj/salim/selma/docs/User-Story",
            "/home/salim/prj/salim/selma/docs/C4-Design",
            "/home/salim/prj/salim/selma/docs/Regulation/SPECIFICATION.md",
        ],
        help="Input paths to merge: files, directories, or nested paths (one or more)",
    )
    p.add_argument(
        "-o",
        "--output",
        default=".tmp",
        help=(
            "Output location. In separate mode: directory for per-input .md files "
            "(default: .tmp under project root). In aggregate mode: output .md file path, "
            "or a directory (writes merged.md inside it)."
        ),
    )
    p.add_argument(
        "--mode",
        choices=["separate", "aggregate"],
        default="aggregate",
        help=(
            "Output mode: 'separate' writes one .md per input; "
            "'aggregate' (default) merges all inputs into a single .md file"
        ),
    )
    p.add_argument(
        "--exclude",
        nargs="*",
        default=[
            "archived",
            "__pycache__",
            ".git",
            ".mypy_cache",
            ".pytest_cache",
            "node_modules",
        ],
        help="Subdirectory names to exclude when walking directory inputs",
    )
    p.add_argument(
        "--extensions",
        nargs="*",
        default=[".py", ".md", ".txt", ".rst", ".puml"],
        help="File extensions to include when walking directory inputs",
    )
    args: argparse.Namespace = p.parse_args(a_argv)
    return args


def _resolve_output_root(a_output: str) -> Path:
    """Resolve output path relative to project root when not absolute.

    Args:
        a_output (str): Output path from CLI or caller.

    Returns:
        Path: Absolute or project-rooted path.
    """
    out: Path = Path(a_output)
    if not out.is_absolute():
        out = Path(__file__).resolve().parents[2] / out
    return out


def _collect_inputs(a_input: List[str]) -> List[Path]:
    """Validate and collect existing input files and directories.

    Nested paths are accepted as-is (file or dir). Missing paths are skipped
    with a warning.

    Args:
        a_input (List[str]): Input path strings.

    Returns:
        List[Path]: Existing files and directories.
    """
    paths: List[Path] = []
    for item in a_input:
        path: Path = Path(item)
        if path.is_file() or path.is_dir():
            paths.append(path)
        else:
            print(f"Warning: {item} is not a file or directory. Skipping.", file=sys.stderr)
    return paths


def _aggregate_output_path(a_out: Path) -> Path:
    """Decide the single output file path for aggregate mode.

    If a_out has a .md suffix (or any file-like suffix), treat it as the file.
    Otherwise treat it as a directory and write merged.md inside.

    Args:
        a_out (Path): Resolved --output value.

    Returns:
        Path: Path to the aggregated Markdown file.
    """
    if a_out.suffix.lower() == ".md" or (a_out.suffix and not a_out.is_dir()):
        return a_out
    return a_out / "merged.md"


def _separate_output_name(a_path: Path) -> str:
    """Derive a stable .md basename for separate-mode output.

    Args:
        a_path (Path): Input file or directory.

    Returns:
        str: Output filename (always ends with .md).
    """
    if a_path.is_file():
        # Keep stem so SPECIFICATION.md -> SPECIFICATION.md
        return f"{a_path.stem}.md"
    return f"{a_path.name}.md"


def main(
    a_input: Optional[List[str]] = None,
    a_output: Optional[str] = None,
    a_mode: Optional[str] = None,
    a_exclude: Optional[List[str]] = None,
    a_extensions: Optional[Set[str]] = None,
    a_argv: Optional[List[str]] = None,
) -> None:
    """Merge source files and/or directories into Markdown file(s).

    Args:
        a_input (Optional[List[str]]): Input paths (files or dirs). Overrides parse_args.
        a_output (Optional[str]): Output path. Overrides parse_args default.
        a_mode (Optional[str]): 'separate' or 'aggregate'. Overrides parse_args default.
        a_exclude (Optional[List[str]]): Directory names to skip when walking.
        a_extensions (Optional[Set[str]]): Extensions to include when walking dirs.
        a_argv (Optional[List[str]]): CLI arguments to parse. Uses sys.argv when None.
    """
    args: argparse.Namespace = parse_args(a_argv)

    input_items: List[str] = a_input if a_input is not None else args.input
    output: str = a_output if a_output is not None else args.output
    mode: str = a_mode if a_mode is not None else args.mode
    exclude: List[str] = a_exclude if a_exclude is not None else args.exclude
    extensions: Set[str] = a_extensions if a_extensions is not None else set(args.extensions)

    inputs: List[Path] = _collect_inputs(input_items)
    if not inputs:
        print("Error: no valid input files or directories.", file=sys.stderr)
        sys.exit(1)

    out_resolved: Path = _resolve_output_root(output)

    if mode == "aggregate":
        out_path: Path = _aggregate_output_path(out_resolved)
        merger: DocumentMerger = DocumentMerger(
            a_inputs=inputs,
            a_output_file=out_path,
            a_exclude=exclude,
            a_extensions=extensions,
        )
        merger.merge()
        joined: str = ", ".join(str(p) for p in inputs)
        print(f"Aggregated [{joined}] -> {out_path}")
        return

    # separate mode: one .md per input path
    out_root: Path = out_resolved
    out_root.mkdir(parents=True, exist_ok=True)

    for in_path in inputs:
        out_path = out_root / _separate_output_name(in_path)
        merger = DocumentMerger(
            a_inputs=[in_path],
            a_output_file=out_path,
            a_exclude=exclude,
            a_extensions=extensions,
        )
        merger.merge()
        print(f"Merged {in_path} -> {out_path}")


if __name__ == "__main__":
    main()
