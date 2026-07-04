#!/usr/bin/env python3
"""CT/API (OpenAPI) Linter CLI.

Canonical ~/.grok/tools/software-design/ct_api/oas_lint.py
"""
import argparse, json, sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).parent))
from ct_api.parser import parse_oas_file
from ct_api.validator import validate_oas
from ct_api.report import build_oas_report


def find_yamls(paths: Iterable[str]):
    fs = []
    for p in paths:
        pp = Path(p)
        if pp.is_file() and pp.suffix in (".yaml", ".yml"):
            fs.append(pp)
        elif pp.is_dir():
            fs += list(pp.rglob("*.yaml")) + list(pp.rglob("*.yml"))
    return sorted(fs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--format", default="text", choices=["text", "json"])
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    files = find_yamls(a.paths)
    if not files:
        print("no files", file=sys.stderr); return 2
    rs = []
    t = c = 0
    for f in files:
        try:
            d = parse_oas_file(f)
            vs = validate_oas(d)
            r = build_oas_report(d, vs)
            rs.append(r)
            t += r.total_violations; c += r.critical
        except Exception as e: print("ERR", f, e, file=sys.stderr)
    if a.format == "json":
        print(json.dumps({"layer":"ct-api","files":len(rs),"total":t,"critical":c,"reports":[json.loads(x.to_json()) for x in rs]}, indent=2))
    else:
        [print(x.to_text(), "\n---") for x in rs]
        print("SUMMARY ct-api:", len(rs), t, "v", c, "crit")
    return 1 if a.strict and t else 0


if __name__ == "__main__":
    sys.exit(main())
