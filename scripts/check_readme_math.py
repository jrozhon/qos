#!/usr/bin/env python3
"""Find inline math that GitHub will break by reading `_` or `*` as emphasis.

GitHub parses Markdown before it renders math, so an underscore after a
closing brace (`}_`) can open emphasis and a later underscore after a letter
(`S_`) in the same paragraph can close it. Everything in between turns
italic, the braces vanish, and the `$...$` span is shown as plain text.
The same applies to `*` (e.g. `x^*`).

The check applies the CommonMark flanking rules to every `_` and `*` in a
paragraph (fenced code, `$$` blocks and code spans skipped, `\\_` ignored)
and reports paragraphs in which a potential opener inside inline math is
followed by a matching potential closer.

Usage
-----
    python3 scripts/check_readme_math.py            # all qos-*/README.md
    python3 scripts/check_readme_math.py FILE ...   # given files

Exits with status 1 when a problem is found.
"""

import re
import sys
import unicodedata
from pathlib import Path


def is_punct(ch: str) -> bool:
    """Return True for ASCII or Unicode punctuation (CommonMark definition)."""
    return unicodedata.category(ch).startswith(("P", "S"))


def flanking(prev: str, nxt: str) -> tuple[bool, bool]:
    """Return (left_flanking, right_flanking) for a delimiter between prev and nxt."""
    left = not nxt.isspace() and (not is_punct(nxt) or prev.isspace() or is_punct(prev))
    right = not prev.isspace() and (not is_punct(prev) or nxt.isspace() or is_punct(nxt))
    return left, right


def paragraphs(text: str):
    """Yield (first_line_number, paragraph_text), skipping code fences and $$ blocks."""
    block, start, fence, display = [], 0, False, False
    for no, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            fence = not fence
            continue
        if not fence and stripped == "$$":
            display = not display
            continue
        if fence or display or not stripped:
            if block:
                yield start, "\n".join(block)
                block = []
            continue
        if not block:
            start = no
        block.append(line)
    if block:
        yield start, "\n".join(block)


def math_mask(par: str) -> tuple[list[bool], str]:
    """Mark characters inside inline `$...$` math; return the mask and the text with code spans blanked."""
    mask = [False] * len(par)
    code = re.compile(r"`+[^`]*`+")
    blanked = code.sub(lambda m: " " * len(m.group()), par)
    for m in re.finditer(r"(?<![\\$])\$(?!\$)(.+?)(?<![\\$])\$(?!\$)", blanked, re.S):
        for i in range(m.start(), m.end()):
            mask[i] = True
    return mask, blanked


def check(path: Path) -> list[str]:
    problems = []
    for line_no, par in paragraphs(path.read_text(encoding="utf-8")):
        mask, text = math_mask(par)
        for delim in "_*":
            openers = []
            for i, ch in enumerate(text):
                if ch != delim or (i and text[i - 1] == "\\"):
                    continue
                # Runs of the same delimiter act as one; only single ones matter here.
                prev = text[i - 1] if i else " "
                nxt = text[i + 1] if i + 1 < len(text) else " "
                if prev == delim or nxt == delim:
                    continue
                left, right = flanking(prev, nxt)
                if delim == "_":
                    can_open = left and (not right or is_punct(prev))
                    can_close = right and (not left or is_punct(nxt))
                else:
                    can_open, can_close = left, right
                if can_close and openers and (mask[i] or mask[openers[-1]]):
                    o = openers.pop()
                    row = line_no + par.count("\n", 0, o)
                    snippet = par[max(o - 25, 0):i + 15].replace("\n", " ")
                    problems.append(f"{path}:{row}: `{delim}` pairs as emphasis: …{snippet}…")
                    continue
                if can_open:
                    openers.append(i)
    return problems


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    files = [Path(a) for a in argv] or sorted(root.glob("qos-*/README.md"))
    problems = [p for f in files for p in check(f)]
    print("\n".join(problems) or f"OK: {len(files)} file(s), no emphasis clashes in inline math.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
