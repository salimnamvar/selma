import argparse
from pathlib import Path
import sys


class DocumentMerger:
    def __init__(self, input_dir: Path, output_file: Path, exclude: list[str] | None = None):
        self.input_dir = input_dir
        self.output_file = output_file
        self.exclude = set(exclude) if exclude else set()

    def merge(self):
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, "w", encoding="utf-8") as out:
            self._walk(self.input_dir, out)

    def _walk(self, directory: Path, out):
        entries = sorted(directory.iterdir(), key=lambda p: (p.is_dir(), p.name))

        readme = [e for e in entries if e.is_file() and e.name.lower().startswith("readme")]
        common = [e for e in entries if e.is_dir() and e.name == "common" and e.name not in self.exclude]
        rest_files = [e for e in entries if e.is_file() and not e.name.lower().startswith("readme")]
        rest_dirs = [e for e in entries if e.is_dir() and e.name != "common" and e.name not in self.exclude]

        for f in readme:
            self._emit(f, out)
        for d in common:
            self._walk(d, out)
        for f in rest_files:
            self._emit(f, out)
        for d in rest_dirs:
            self._walk(d, out)

    def _emit(self, path: Path, out):
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            out.write(f"\n\n--- SOURCE: {path} ---\n\n")
            out.write(content)
            out.write("\n")
        except Exception as e:
            print(f"Warning: could not read {path}: {e}", file=sys.stderr)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Merge doc directories into separate .md files.")
    p.add_argument(
        "-i",
        "--input",
        nargs="+",
        default=["docs/C4", "docs/SQ", "docs/UC", "docs/SM"],
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
        default=["archived"],
        help="Subdirectory names to exclude (default: archived)",
    )
    args = p.parse_args(argv)
    if args.output is None:
        root = Path(__file__).resolve().parents[2]
        args.output = [root / f"{Path(d).name}.md" for d in args.input]
    if len(args.input) != len(args.output):
        p.error("Number of --input and --output must match")
    return args


def main(
    input=["docs/C4-Design", "docs/Regulation", "docs/User-Story"],
    output=None,
    exclude=["archived"],
    argv=None,
):
    if output is None:
        root = Path(__file__).resolve().parents[2]
        output = [root / f"{Path(d).name}.md" for d in input]
    if argv is not None:
        args = parse_args(argv)
        input = args.input
        output = args.output
        exclude = args.exclude
    for in_dir, out_file in zip(input, output):
        in_path, out_path = Path(in_dir), Path(out_file)
        if not in_path.is_dir():
            print(f"Warning: {in_dir} is not a directory. Skipping.", file=sys.stderr)
            continue
        merger = DocumentMerger(in_path, out_path, exclude=exclude)
        merger.merge()
        print(f"Merged {in_dir} -> {out_file}")


if __name__ == "__main__":
    main()
