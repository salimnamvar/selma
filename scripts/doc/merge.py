"""Document merger.

Merges subdirectories of source files into a single Markdown document.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Set


class DocumentMerger:
    """Merges files from a directory tree into a single Markdown output.

    Attributes:
        _input_dir (Path): Root directory to scan.
        _output_file (Path): Target Markdown file.
        _exclude (Set[str]): Directory names to skip.
        _extensions (Set[str]): File extensions to include.
    """

    def __init__(
        self,
        a_input_dir: Path,
        a_output_file: Path,
        a_exclude: Optional[List[str]] = None,
        a_extensions: Optional[Set[str]] = None,
    ) -> None:
        """Initialise the merger.

        Args:
            a_input_dir (Path): Root directory to scan.
            a_output_file (Path): Target Markdown file.
            a_exclude (Optional[List[str]]): Directory names to skip.
            a_extensions (Optional[Set[str]]): File extensions to include.
        """
        self._input_dir: Path = a_input_dir
        self._output_file: Path = a_output_file
        self._exclude: Set[str] = set(a_exclude) if a_exclude else set()
        self._extensions: Set[str] = a_extensions or {".py", ".md", ".txt", ".rst"}

    def merge(self) -> None:
        """Write merged content to the output file."""
        self._output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._output_file, "w", encoding="utf-8") as out:
            self._walk(self._input_dir, out)

    def _walk(self, a_directory: Path, a_out: "Path | None") -> None:
        """Recursively walk a directory and emit matching files.

        Args:
            a_directory (Path): Directory to scan.
            a_out (Path | None): Open output file handle.
        """
        entries: List[Path] = sorted(a_directory.iterdir(), key=lambda p: (p.is_dir(), p.name))

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

    def _emit(self, a_path: Path, a_out: "Path | None") -> None:
        """Write a single file's content to the output.

        Args:
            a_path (Path): File to read.
            a_out (Path | None): Open output file handle.
        """
        try:
            content: str = a_path.read_text(encoding="utf-8", errors="ignore")
            a_out.write(f"\n\n--- SOURCE: {a_path} ---\n\n")
            a_out.write(content)
            a_out.write("\n")
        except Exception as e:
            print(f"Warning: could not read {a_path}: {e}", file=sys.stderr)


def parse_args(a_argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        a_argv (Optional[List[str]]): Argument list to parse. Uses sys.argv when None.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    p: argparse.ArgumentParser = argparse.ArgumentParser(description="Merge doc directories into separate .md files.")
    p.add_argument(
        "-i",
        "--input",
        nargs="+",
        default=["src/domain"],
        help="Input directories (one per merge)",
    )
    p.add_argument(
        "-o",
        "--output",
        nargs="+",
        default=None,
        help="Output .md files (one per input, same order)",
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
        help="Subdirectory names to exclude",
    )
    p.add_argument(
        "--extensions",
        nargs="*",
        default=[".py", ".md", ".txt", ".rst"],
        help="File extensions to include",
    )
    args: argparse.Namespace = p.parse_args(a_argv)
    if args.output is None:
        root: Path = Path(__file__).resolve().parents[2]
        args.output = [str(root / f"{Path(d).name}.md") for d in args.input]
    if len(args.input) != len(args.output):
        p.error("Number of --input and --output must match")
    return args


def main(
    a_input: Optional[List[str]] = None,
    a_output: Optional[List[str]] = None,
    a_exclude: Optional[List[str]] = None,
    a_extensions: Optional[Set[str]] = None,
    a_argv: Optional[List[str]] = None,
) -> None:
    """Merge doc directories into separate Markdown files.

    Args:
        a_input (Optional[List[str]]): Input directories. Overrides parse_args default.
        a_output (Optional[List[str]]): Output .md files. Overrides parse_args default.
        a_exclude (Optional[List[str]]): Directory names to skip. Overrides parse_args default.
        a_extensions (Optional[Set[str]]): File extensions to include. Overrides parse_args default.
        a_argv (Optional[List[str]]): CLI arguments to parse. Uses sys.argv when None.
    """
    args: argparse.Namespace = parse_args(a_argv)

    input_dirs: List[str] = a_input if a_input is not None else args.input
    output_files: List[str] = a_output if a_output is not None else args.output
    exclude: List[str] = a_exclude if a_exclude is not None else args.exclude
    extensions: Set[str] = a_extensions if a_extensions is not None else set(args.extensions)

    for in_dir, out_file in zip(input_dirs, output_files, strict=True):
        in_path: Path = Path(in_dir)
        out_path: Path = Path(out_file)
        if not in_path.is_dir():
            print(f"Warning: {in_dir} is not a directory. Skipping.", file=sys.stderr)
            continue
        merger: DocumentMerger = DocumentMerger(
            a_input_dir=in_path,
            a_output_file=out_path,
            a_exclude=exclude,
            a_extensions=extensions,
        )
        merger.merge()
        print(f"Merged {in_dir} -> {out_file}")


if __name__ == "__main__":
    main()
