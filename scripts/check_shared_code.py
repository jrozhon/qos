#!/usr/bin/env python3
"""Check that code copied between lessons has not drifted apart.

Each lesson is its own `uv` project, so shared helpers are copied rather than
imported. The copies are compared here:

- `lib/params.py` must be byte-identical in every lesson that has one.
- `card_html` must be identical in qos-01 (`lib/core.py`), qos-02 and
  qos-03 (`lib/plots.py`).
- Every top-level function and constant of `qos-03/qos_03/lib/plots.py` must
  be identical to the one of the same name in `qos-02/qos_02/lib/plots.py`
  (qos-02 may have more, e.g. `sample_card`).

Usage
-----
    python3 scripts/check_shared_code.py

Exits with status 1 when a copy differs.
"""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def definitions(path: Path) -> dict[str, str]:
    """Return the source of each top-level function, class and constant."""
    source = path.read_text()
    found = {}
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names = [node.name]
        elif isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names = [node.target.id]
        else:
            continue
        for name in names:
            found[name] = ast.get_source_segment(source, node)
    return found


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def check_params() -> list[str]:
    files = sorted(ROOT.glob("qos-*/qos_*/lib/params.py"))
    reference = files[0].read_bytes()
    return [
        f"{rel(f)} differs from {rel(files[0])}"
        for f in files[1:]
        if f.read_bytes() != reference
    ]


def check_card_html() -> list[str]:
    files = [
        ROOT / "qos-01/qos_01/lib/core.py",
        ROOT / "qos-02/qos_02/lib/plots.py",
        ROOT / "qos-03/qos_03/lib/plots.py",
    ]
    copies = {f: definitions(f).get("card_html") for f in files}
    problems = [f"{rel(f)}: card_html missing" for f, c in copies.items() if c is None]
    reference = copies[files[1]]
    problems += [
        f"{rel(f)}: card_html differs from {rel(files[1])}"
        for f, c in copies.items()
        if c is not None and c != reference
    ]
    return problems


def check_plots() -> list[str]:
    source = ROOT / "qos-02/qos_02/lib/plots.py"
    copy = ROOT / "qos-03/qos_03/lib/plots.py"
    original, copied = definitions(source), definitions(copy)
    return [
        f"{rel(copy)}: {name} {'missing in' if name not in original else 'differs from'} {rel(source)}"
        for name, code in copied.items()
        if original.get(name) != code
    ]


def main() -> int:
    problems = check_params() + check_card_html() + check_plots()
    print("\n".join(problems) or "OK: params.py, card_html and qos-03 plots.py match their copies.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
