"""Document merger.

Merges source files and directory trees into Markdown document(s).
Inputs may be files, directories, or nested paths under either.
Supports separate outputs (one file per input) or a single aggregated output.
When max-context is set, aggregated output exceeding the limit is split into
numbered files: <doc-name>.<seq-number>.md
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


class DocumentMerger:
    """Merges files and/or directory trees into Markdown output.

    Attributes:
        _inputs: File or directory paths to merge (in order).
        _output_file: Target Markdown file.
        _exclude: Directory names to skip when walking trees.
        _extensions: File extensions to include when walking directories.
        _max_context: Maximum character count per output file.
    """

    def __init__(
        self,
        a_inputs: list[Path],
        a_output_file: Path,
        a_exclude: list[str] | None = None,
        a_extensions: set[str] = frozenset({".py", ".md", ".txt", ".rst", ".puml"}),
        a_max_context: int | None = None,
    ) -> None:
        """Initialise the merger.

        Args:
            a_inputs: File or directory paths to merge (in order).
            a_output_file: Target Markdown file.
            a_exclude: Directory names to skip when walking.
            a_extensions: File extensions to include when walking directories.
                Defaults to {".py", ".md", ".txt", ".rst", ".puml"}.
            a_max_context: Maximum character count per output file. If the merged
                content exceeds this limit, the output is split into numbered files.
        """
        self._inputs: list[Path] = list(a_inputs)
        self._output_file: Path = a_output_file
        self._exclude: set[str] = set(a_exclude) if a_exclude is not None else set()
        self._extensions: set[str] = a_extensions
        self._max_context: int | None = a_max_context
        self._emitted: set[Path] = set()

    def merge(self) -> str:
        """Merge all inputs and return the combined content.

        Returns:
            The merged Markdown content as a string.
        """
        self._emitted.clear()
        parts: list[str] = []
        first_written = True
        for input_path in self._inputs:
            if first_written:
                wrote = self._collect_input(input_path, parts, a_separator=False)
            else:
                wrote = self._collect_input(input_path, parts, a_separator=True)
            if wrote:
                first_written = False
        return "".join(parts)

    def merge_to_file(self) -> list[Path]:
        """Merge all inputs and write to output file(s).

        If max_context is set and content exceeds the limit, splits into
        numbered files: <name>.<seq>.md.

        Returns:
            List of output file paths that were written.
        """
        content = self.merge()
        written: list[Path] = []

        if self._max_context and len(content) > self._max_context:
            chunks = self.split_content(content)
            written = self._write_numbered_files(chunks)
        else:
            self._output_file.parent.mkdir(parents=True, exist_ok=True)
            self._output_file.write_text(content, encoding="utf-8")
            written = [self._output_file]

        return written

    def split_content(self, a_content: str) -> list[str]:
        """Split content into chunks that respect the max context limit.

        First splits at file boundary markers (--- SOURCE:) to keep source
        documents intact. If any single section still exceeds the limit,
        it is further split at line boundaries.

        Args:
            a_content: The full merged content to split.

        Returns:
            List of content chunks, each within the max context limit.
        """
        if not self._max_context:
            return [a_content]

        marker = "\n\n--- SOURCE:"
        sections = a_content.split(marker)
        raw_chunks: list[str] = []

        for i, section in enumerate(sections):
            if i == 0 and not section.strip():
                continue
            prefixed = f"{marker}{section}" if i > 0 else section
            raw_chunks.append(prefixed)

        chunks: list[str] = []
        for raw in raw_chunks:
            if len(raw) <= self._max_context:
                if chunks and len(chunks[-1]) + len(raw) <= self._max_context:
                    chunks[-1] += raw
                else:
                    chunks.append(raw)
            else:
                chunks.extend(self._split_large_section(raw))

        return chunks

    def _split_large_section(self, a_section: str) -> list[str]:
        """Split a single large section at line boundaries.

        Args:
            a_section: Content that exceeds the max context limit.

        Returns:
            List of chunks, each within the max context limit.
        """
        lines = a_section.split("\n")
        chunks: list[str] = []
        current_chunk = ""

        for line in lines:
            candidate = f"{current_chunk}\n{line}" if current_chunk else line
            if current_chunk and len(candidate) > self._max_context:
                chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk = candidate

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _write_numbered_files(self, a_chunks: list[str]) -> list[Path]:
        """Write content chunks to numbered output files.

        Args:
            a_chunks: Content chunks to write.

        Returns:
            List of written file paths.
        """
        self._output_file.parent.mkdir(parents=True, exist_ok=True)
        stem = self._output_file.stem
        suffix = self._output_file.suffix or ".md"
        parent = self._output_file.parent
        written: list[Path] = []

        for i, chunk in enumerate(a_chunks, start=1):
            out_path = parent / f"{stem}.{i}{suffix}"
            out_path.write_text(chunk, encoding="utf-8")
            written.append(out_path)

        return written

    def _collect_input(self, a_path: Path, a_parts: list[str], a_separator: bool) -> bool:
        """Collect content from a single input path.

        Args:
            a_path: File or directory to merge.
            a_parts: List to append content parts to.
            a_separator: If True, prepend an INPUT marker.

        Returns:
            True if any content was collected.
        """
        before = len(a_parts)
        if a_separator:
            a_parts.append(f"\n\n--- INPUT: {a_path} ---\n\n")

        if a_path.is_file():
            self._collect_file(a_path, a_parts, a_force=True)
        elif a_path.is_dir():
            self._walk(a_path, a_parts)
        else:
            print(f"Warning: {a_path} is neither a file nor a directory. Skipping.", file=sys.stderr)

        return len(a_parts) > before

    def _walk(self, a_directory: Path, a_parts: list[str]) -> None:
        """Recursively walk a directory and collect matching files.

        Args:
            a_directory: Directory to scan.
            a_parts: List to append content parts to.
        """
        try:
            entries: list[Path] = sorted(a_directory.iterdir(), key=lambda p: (p.is_dir(), p.name))
        except OSError as e:
            print(f"Warning: could not list {a_directory}: {e}", file=sys.stderr)
            return

        readme: list[Path] = [e for e in entries if e.is_file() and e.name.lower().startswith("readme")]
        common: list[Path] = [e for e in entries if e.is_dir() and e.name == "common" and e.name not in self._exclude]
        rest_files: list[Path] = [
            e
            for e in entries
            if e.is_file() and not e.name.lower().startswith("readme") and e.suffix in self._extensions
        ]
        rest_dirs: list[Path] = [
            e for e in entries if e.is_dir() and e.name != "common" and e.name not in self._exclude
        ]

        for f in readme:
            self._collect_file(f, a_parts)
        for d in common:
            self._walk(d, a_parts)
        for f in rest_files:
            self._collect_file(f, a_parts)
        for d in rest_dirs:
            self._walk(d, a_parts)

    def _collect_file(self, a_path: Path, a_parts: list[str], a_force: bool = False) -> None:
        """Collect a single file's content.

        Skips files already collected. When not forced, only includes paths
        whose suffix is in _extensions.

        Args:
            a_path: File to read.
            a_parts: List to append content parts to.
            a_force: If True, emit even when extension is not in the filter.
        """
        resolved: Path = a_path.resolve()
        if resolved in self._emitted:
            return
        if not a_force and a_path.suffix not in self._extensions:
            return

        try:
            content: str = a_path.read_text(encoding="utf-8", errors="ignore")
            a_parts.append(f"\n\n--- SOURCE: {a_path} ---\n\n")
            a_parts.append(content)
            a_parts.append("\n")
            self._emitted.add(resolved)
        except Exception as e:
            print(f"Warning: could not read {a_path}: {e}", file=sys.stderr)


class DocumentMergerInterface:
    """CLI interface that handles argument parsing and wiring.

    Attributes:
        _args: Parsed command-line arguments.
    """

    def __init__(self, a_argv: list[str] | None = None) -> None:
        """Initialise the interface with parsed arguments.

        Args:
            a_argv: CLI arguments to parse. Uses sys.argv when None.
        """
        self._args: argparse.Namespace = self._parse_args(a_argv)

    def run(self) -> None:
        """Execute the merge operation based on parsed arguments."""
        inputs = self._collect_inputs()
        if not inputs:
            print("Error: no valid input files or directories.", file=sys.stderr)
            sys.exit(1)

        out_resolved = self._resolve_output_root()

        if self._args.mode == "aggregate":
            self._run_aggregate(inputs, out_resolved)
        else:
            self._run_separate(inputs, out_resolved)

    def _run_aggregate(self, a_inputs: list[Path], a_out: Path) -> None:
        """Run aggregate mode: merge all inputs into a single output.

        Args:
            a_inputs: Valid input paths.
            a_out: Resolved output path.
        """
        out_path = self._aggregate_output_path(a_out)
        merger = DocumentMerger(
            a_inputs=a_inputs,
            a_output_file=out_path,
            a_exclude=self._args.exclude,
            a_extensions=set(self._args.extensions),
            a_max_context=self._args.max_context,
        )
        written = merger.merge_to_file()
        joined = ", ".join(str(p) for p in a_inputs)
        for w in written:
            print(f"Aggregated [{joined}] -> {w}")

    def _run_separate(self, a_inputs: list[Path], a_out: Path) -> None:
        """Run separate mode: one .md per input path.

        Args:
            a_inputs: Valid input paths.
            a_out: Resolved output directory.
        """
        out_root = a_out
        out_root.mkdir(parents=True, exist_ok=True)

        for in_path in a_inputs:
            out_path = out_root / self._separate_output_name(in_path)
            merger = DocumentMerger(
                a_inputs=[in_path],
                a_output_file=out_path,
                a_exclude=self._args.exclude,
                a_extensions=set(self._args.extensions),
                a_max_context=self._args.max_context,
            )
            written = merger.merge_to_file()
            for w in written:
                print(f"Merged {in_path} -> {w}")

    def _parse_args(self, a_argv: list[str] | None) -> argparse.Namespace:
        """Parse command-line arguments.

        Args:
            a_argv: Argument list to parse. Uses sys.argv when None.

        Returns:
            Parsed arguments.
        """
        p = argparse.ArgumentParser(
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
                "/home/salim/prj/salim/selma/docs/c4-model",
                "/home/salim/prj/salim/selma/docs/mindmap",
                "/home/salim/prj/salim/selma/docs/spec",
                "/home/salim/prj/salim/selma/docs/state-machine",
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
            default="separate",
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
        p.add_argument(
            "--max-context",
            type=int,
            default=None,
            help=(
                "Maximum character count per output file. If the aggregated content "
                "exceeds this limit, the output is split into numbered files: "
                "<doc-name>.<seq>.md. Approximate: ~4 characters per token."
            ),
        )
        return p.parse_args(a_argv)

    def _collect_inputs(self) -> list[Path]:
        """Validate and collect existing input files and directories.

        Returns:
            Existing files and directories.
        """
        paths: list[Path] = []
        for item in self._args.input:
            path = Path(item)
            if path.is_file() or path.is_dir():
                paths.append(path)
            else:
                print(f"Warning: {item} is not a file or directory. Skipping.", file=sys.stderr)
        return paths

    def _resolve_output_root(self) -> Path:
        """Resolve output path relative to project root when not absolute.

        Returns:
            Absolute or project-rooted path.
        """
        out = Path(self._args.output)
        if not out.is_absolute():
            out = Path(__file__).resolve().parents[2] / out
        return out

    def _aggregate_output_path(self, a_out: Path) -> Path:
        """Decide the single output file path for aggregate mode.

        Args:
            a_out: Resolved --output value.

        Returns:
            Path to the aggregated Markdown file.
        """
        if a_out.suffix.lower() == ".md" or (a_out.suffix and not a_out.is_dir()):
            result = a_out
        else:
            result = a_out / "merged.md"
        return result

    def _separate_output_name(self, a_path: Path) -> str:
        """Derive a stable .md basename for separate-mode output.

        Args:
            a_path: Input file or directory.

        Returns:
            Output filename (always ends with .md).
        """
        if a_path.is_file():
            result = f"{a_path.stem}.md"
        else:
            result = f"{a_path.name}.md"
        return result


def main(a_argv: list[str] | None = None) -> None:
    """Merge source files and/or directories into Markdown file(s).

    Args:
        a_argv: CLI arguments to parse. Uses sys.argv when None.
    """
    interface = DocumentMergerInterface(a_argv)
    interface.run()


if __name__ == "__main__":
    main()
