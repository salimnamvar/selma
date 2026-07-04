#!/usr/bin/env python3
"""CT/API fixer."""
import argparse, difflib, sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).parent))
from ct_api.parser import parse_oas_file
from ct_api.fixer import apply_oas_fixes
from ct_api.rewriter import rewrite_oas
from ct_api.validator import validate_oas


def find_yamls(paths):
    out = []
    for p in paths:
        pp=Path(p)
        if pp.is_file() and pp.suffix in ('.yaml','.yml'): out.append(pp)
        elif pp.is_dir(): out += list(pp.rglob('*.yaml')) + list(pp.rglob('*.yml'))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--in-place", "-i", action="store_true")
    ap.add_argument("--stdout", action="store_true")
    ap.add_argument("--diff", action="store_true")
    a = ap.parse_args()
    for f in find_yamls(a.paths):
        try:
            o = f.read_text()
            d = parse_oas_file(f)
            vs = validate_oas(d)
            if not vs:
                if a.stdout: print(o, end=""); return 0
                print("[clean]", f); continue
            fr = apply_oas_fixes(d, vs)
            c = rewrite_oas(fr.doc)
            if a.stdout: print(c, end=""); return 0
            if a.diff and c != o:
                sys.stdout.writelines(difflib.unified_diff(o.splitlines(keepends=True), c.splitlines(keepends=True)))
            if a.in_place and c != o:
                f.write_text(c); print("[fixed]", f)
            else:
                print("[would]", f)
        except Exception as e: print("ERR", f, e, file=sys.stderr)
    return 0

if __name__ == "__main__": sys.exit(main())
