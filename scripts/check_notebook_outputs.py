#!/usr/bin/env python3
"""Find lesson notebooks committed with cell outputs or execution counts.

Students should open a clean notebook and see only what their own run
produces; saved outputs also make diffs noisy (Bokeh/Panel outputs embed
hundreds of kilobytes of JavaScript). Strip them with
`uvx nbstripout <notebook>` or let the pre-commit hook do it.

Usage
-----
    python3 scripts/check_notebook_outputs.py            # all qos-*/qos_*/*.ipynb
    python3 scripts/check_notebook_outputs.py FILE ...   # given files

Exits with status 1 when a notebook has outputs.
"""

import json
import sys
from pathlib import Path


def check(path: Path) -> list[str]:
    cells = json.loads(path.read_text())["cells"]
    return [
        f"{path}: cell {i} has saved outputs or an execution count"
        for i, cell in enumerate(cells)
        if cell.get("outputs") or cell.get("execution_count") is not None
    ]


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    files = [Path(a) for a in argv] or sorted(root.glob("qos-*/qos_*/*.ipynb"))
    problems = [p for f in files for p in check(f)]
    print("\n".join(problems) or f"OK: {len(files)} notebook(s), no saved outputs.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
