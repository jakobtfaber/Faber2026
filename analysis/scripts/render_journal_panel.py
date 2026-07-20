#!/usr/bin/env python3
"""Rebake the owner view and journal panel into the readiness board HTML.

Reads docs/rse/control/board/owner-view.json (owner-facing Now/Next/Needs-you +
component rollup) and docs/rse/protocols/journal.jsonl (append-only) and rewrites
the sections between the OWNER:BEGIN/END and JOURNAL:BEGIN/END markers in
docs/rse/control/board/readiness.html. The board is a static artifact behind a
strict CSP (no runtime fetch), so both panels must be baked in and the
artifact redeployed after rendering.
"""
import html
import json
import pathlib
import sys

N = 20
MAX_SLOT = 3  # owner-view columns are capped: glanceability over completeness
ROOT = pathlib.Path(__file__).resolve().parents[1]
J = ROOT / "docs/rse/protocols/journal.jsonl"
OWNER = ROOT / "docs/rse/control/board/owner-view.json"
BOARD = ROOT / "docs/rse/control/board/readiness.html"
BEGIN, END = "<!-- JOURNAL:BEGIN -->", "<!-- JOURNAL:END -->"
OBEGIN, OEND = "<!-- OWNER:BEGIN -->", "<!-- OWNER:END -->"

STATE_CLASS = {"done": "s-good", "working": "s-now",
               "blocked": "s-pend", "info": "s-ready"}


def replace_between(text, begin, end, payload):
    a, b = text.index(begin), text.index(end) + len(end)
    return text[:a] + begin + "\n" + payload + "\n" + end + text[b:]


def owner_items(items, dropped_label):
    out = []
    for it in items[:MAX_SLOT]:
        if isinstance(it, str):
            it = {"h": it}
        head = html.escape(it.get("h") or it.get("text", ""))
        who = (' <span class="who">' + html.escape(it["who"]) + "</span>"
               if it.get("who") else "")
        detail = ('<small>' + html.escape(it["d"]) + "</small>"
                  if it.get("d") else "")
        out.append("<li><b>" + head + "</b>" + who + detail + "</li>")
    if len(items) > MAX_SLOT:
        print(f"owner view: {dropped_label} truncated to {MAX_SLOT} "
              f"({len(items) - MAX_SLOT} dropped from render; trim the JSON)")
    return "\n".join(out)


def render_owner():
    v = json.loads(OWNER.read_text())
    comps = []
    for c in v.get("components", []):
        nx = ('<span class="cnx">' + html.escape(c["next"]) + "</span>"
              if c.get("next") else "")
        comps.append(
            '<div class="comp"><span class="cnm"><b>{nm}</b>'
            '<span class="cid">{lane}</span>'
            '<span class="chip c-{cls}">{st}</span></span>{nx}</div>'.format(
                nm=html.escape(c["name"]), lane=html.escape(c.get("lane", "")),
                cls=html.escape(c.get("status_class", "ready")),
                st=html.escape(c["status"]), nx=nx))
    return (
        '<div class="own">\n'
        '<div class="own-head"><b>Owner view</b>'
        '<span class="meta">updated {upd} · data: docs/rse/control/board/owner-view.json'
        ' (agents keep this current)</span></div>\n'
        '<div class="own-cols">\n'
        '<div class="own-col oc-you"><h4>Needs you</h4><ul>\n{you}\n</ul></div>\n'
        '<div class="own-col oc-now"><h4>In flight</h4><ul>\n{now}\n</ul></div>\n'
        '<div class="own-col oc-next"><h4>Up next — your pick</h4><ul>\n{nxt}\n</ul></div>\n'
        '</div>\n'
        '<div class="own-comps">\n{comps}\n</div>\n'
        '</div>'.format(
            upd=html.escape(v.get("updated", "?")),
            you=owner_items(v.get("needs_you", []), "needs_you"),
            now=owner_items(v.get("now", []), "now"),
            nxt=owner_items(v.get("next", []), "next"),
            comps="\n".join(comps)))


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
    text = BOARD.read_text()
    text = replace_between(text, BEGIN, END,
                           '<ul class="journal">\n' + "\n".join(rows) + "\n</ul>")
    if OWNER.exists():
        text = replace_between(text, OBEGIN, OEND, render_owner())
        print(f"baked owner view from {OWNER}")
    BOARD.write_text(text)
    print(f"baked {min(N, len(entries))}/{len(entries)} entries into {BOARD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
