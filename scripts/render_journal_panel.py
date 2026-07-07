#!/usr/bin/env python3
"""Rebake the journal panel into the readiness board HTML.

Reads docs/rse/journal.jsonl (append-only) and rewrites the section
between the JOURNAL:BEGIN / JOURNAL:END markers in
docs/rse/board/readiness.html with the newest N entries. The board is a
static artifact behind a strict CSP (no runtime fetch), so the panel must
be baked in and the artifact redeployed after rendering.
"""
import html
import json
import pathlib
import sys

N = 20
ROOT = pathlib.Path(__file__).resolve().parents[1]
J = ROOT / "docs/rse/journal.jsonl"
BOARD = ROOT / "docs/rse/board/readiness.html"
BEGIN, END = "<!-- JOURNAL:BEGIN -->", "<!-- JOURNAL:END -->"

STATE_CLASS = {"done": "s-good", "working": "s-now",
               "blocked": "s-pend", "info": "s-ready"}


def main():
    entries = [json.loads(line) for line in J.read_text().splitlines()
               if line.strip()]
    rows = []
    for e in reversed(entries[-N:]):
        cls = STATE_CLASS.get(e.get("state", "info"), "s-ready")
        rows.append(
            '<li><span class="jts mono">{ts}</span>'
            '<span class="jagent">{agent}</span>'
            '<span class="jlane">{lane}</span>'
            '<span class="jnote {cls}">{note}</span></li>'.format(
                ts=html.escape(e["ts"][5:16].replace("T", " ")),
                agent=html.escape(e.get("agent", "?")),
                lane=html.escape(e.get("lane", "")),
                cls=cls,
                note=html.escape(e.get("note", ""))))
    panel = (BEGIN + '\n<ul class="journal">\n'
             + "\n".join(rows) + "\n</ul>\n" + END)
    text = BOARD.read_text()
    a, b = text.index(BEGIN), text.index(END) + len(END)
    BOARD.write_text(text[:a] + panel + text[b:])
    print(f"baked {min(N, len(entries))}/{len(entries)} entries into {BOARD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
