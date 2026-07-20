#!/usr/bin/env python3
"""Assemble the owner-decision queue from canonical sources → OWNER_QUEUE.md.

Manually triggered (never scheduled): the owner says "walk me through my
queue" in any agent session; the agent runs this, then walks the items one
at a time per the CLAUDE.md ritual. Sources:

  1. wayfinder tickets  (docs/rse/wayfinder/tickets/*.md)
     open + unblocked + owner-facing (HITL / grilling / owner markers)
  2. figure_review      (batches without an approval receipt)
  3. BOARD.md           (lines carrying the ✋ owner marker)
  4. open PRs           (via `gh`, best-effort; skipped offline)

Stdlib only (tomllib requires Python ≥3.11, same as sync_state.py).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TICKETS = ROOT / "docs/rse/wayfinder/tickets"
BOARD = ROOT / "docs/rse/control/BOARD.md"
FIGREV = ROOT / "figure_review"
OUT = ROOT / "OWNER_QUEUE.md"


def ticket_state(text: str) -> str:
    m = re.search(r"^- Status:\s*(.+)$", text, re.M)
    s = (m.group(1) if m else "").lower()
    return "closed" if "closed" in s else "open"


def blockers(text: str) -> list[str]:
    m = re.search(r"^- Blocked by:\s*(.+)$", text, re.M)
    if not m:
        return []
    return re.findall(r"\((\d{2}-[a-z0-9-]+\.md)\)", m.group(1))


def owner_facing(text: str) -> bool:
    return bool(re.search(r"HITL|grilling|owner", text[:600], re.I))


def wayfinder_items() -> list[dict]:
    tickets = {p.name: p.read_text(encoding="utf-8") for p in sorted(TICKETS.glob("*.md"))}
    states = {name: ticket_state(t) for name, t in tickets.items()}
    items = []
    for name, text in tickets.items():
        if states[name] == "closed":
            continue
        blocked = any(states.get(b, "open") == "open" for b in blockers(text))
        if blocked or not owner_facing(text):
            continue
        title = text.splitlines()[0].lstrip("# ").strip()
        items.append({
            "kind": "decision",
            "title": title,
            "where": f"docs/rse/wayfinder/tickets/{name}",
            "note": "open, unblocked, owner-facing",
        })
    return items


def figure_review_items() -> list[dict]:
    batches = FIGREV / "batches"
    receipts_dir = FIGREV / "approval_receipts"
    if not batches.is_dir():
        return []
    receipts = " ".join(p.name for p in receipts_dir.glob("*.json")) if receipts_dir.is_dir() else ""
    items = []
    for b in sorted(p for p in batches.iterdir() if p.is_dir()):
        # heuristic: a batch with no receipt mentioning its name awaits a decide
        if b.name not in receipts:
            items.append({
                "kind": "figure decide",
                "title": b.name,
                "where": f"figure_review/batches/{b.name}",
                "note": "no approval receipt found — run figure_review.py decide (verify before acting; heuristic)",
            })
    return items


def board_items() -> list[dict]:
    if not BOARD.is_file():
        return []
    items = []
    for line in BOARD.read_text(encoding="utf-8").splitlines():
        if "✋" in line and "[ ]" in line:
            items.append({
                "kind": "board",
                "title": re.sub(r"^\s*-\s*\[ \]\s*✋?\s*", "", line).strip()[:110],
                "where": "docs/rse/control/BOARD.md",
                "note": "owner-marked board task",
            })
    return items


def pr_items() -> list[dict]:
    try:
        out = subprocess.check_output(
            ["gh", "pr", "list", "--json", "number,title,isDraft"],
            cwd=ROOT, text=True, timeout=20, stderr=subprocess.DEVNULL,
        )
        prs = json.loads(out)
    except Exception:
        return [{"kind": "prs", "title": "(gh unavailable — check PRs manually)",
                 "where": "https://github.com/jakobtfaber/Faber2026/pulls", "note": ""}]
    return [{
        "kind": "pr",
        "title": f"#{p['number']} {p['title']}",
        "where": f"https://github.com/jakobtfaber/Faber2026/pull/{p['number']}",
        "note": "draft" if p.get("isDraft") else "open",
    } for p in prs]


def main() -> int:
    sections = [
        ("Decisions (wayfinder frontier, owner-facing)", wayfinder_items()),
        ("Approvals (figure review / data cards)", figure_review_items()),
        ("Owner-marked board tasks", board_items()),
        ("Open PRs (review or delegate)", pr_items()),
    ]
    from datetime import date
    lines = [
        "# OWNER QUEUE — regenerate with `python3 scripts/owner_queue.py`",
        "",
        f"_Generated {date.today().isoformat()}. Manual walkthrough ritual: see CLAUDE.md_",
        "",
    ]
    total = 0
    for header, items in sections:
        lines.append(f"## {header}")
        lines.append("")
        if not items:
            lines.append("- (none)")
        for it in items:
            total += 1
            note = f" — {it['note']}" if it["note"] else ""
            lines.append(f"- **{it['title']}**{note}\n  `{it['where']}`")
        lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"OWNER_QUEUE.md written: {total} items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
