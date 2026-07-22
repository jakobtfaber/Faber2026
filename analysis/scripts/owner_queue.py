#!/usr/bin/env python3
"""Regenerate the owner queue from authoritative repository state."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import shutil
import subprocess

try:
    from scripts.wayfinder_state import Ticket, wayfinder_frontier
except ModuleNotFoundError:  # direct ``python scripts/owner_queue.py`` execution
    from wayfinder_state import Ticket, wayfinder_frontier


ROOT = Path(__file__).resolve().parents[1]
TICKETS = ROOT / "docs/rse/wayfinder/tickets"
DEFAULT_OUTPUT = ROOT / "OWNER_QUEUE.md"


def collect_wayfinder_frontier(
    tickets_root: Path = TICKETS, *, owner_facing_only: bool = False
) -> list[Ticket]:
    """Return the same pass-aware frontier consumed by owner-queue generation."""

    return wayfinder_frontier(tickets_root, owner_facing_only=owner_facing_only)


def collect_undecided_figure_batches(root: Path = ROOT) -> list[Path]:
    receipts = root / "figure_review/approval_receipts"
    undecided: list[Path] = []
    for manifest_path in sorted(
        (root / "figure_review/batches").glob("*/manifest.json")
    ):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        candidate_ids = [
            candidate["id"] for candidate in manifest.get("candidates", [])
        ]
        if any(
            not (receipts / f"{candidate_id}.json").is_file()
            for candidate_id in candidate_ids
        ):
            undecided.append(manifest_path.parent)
    return undecided


def collect_owner_board_tasks(root: Path = ROOT) -> list[str]:
    tasks: list[str] = []
    for line in (
        (root / "docs/rse/control/BOARD.md").read_text(encoding="utf-8").splitlines()
    ):
        if "✋" not in line or "[ ]" not in line:
            continue
        text = re.sub(r"^\s*-\s*(?:\[[ xX]\]\s*)?", "", line).replace("✋", "").strip()
        if text:
            tasks.append(text)
    return tasks


def collect_open_prs(repo: str = "jakobtfaber/Faber2026") -> list[dict[str, object]]:
    gh = shutil.which("gh")
    if gh is None and Path("/opt/homebrew/bin/gh").is_file():
        gh = "/opt/homebrew/bin/gh"
    if gh is None:
        return []
    result = subprocess.run(
        [
            gh,
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--json",
            "number,title,url",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    return json.loads(result.stdout) if result.returncode == 0 else []


def render_owner_queue(root: Path = ROOT, *, include_github: bool = True) -> str:
    decisions = collect_wayfinder_frontier(
        root / "docs/rse/wayfinder/tickets", owner_facing_only=True
    )
    figures = collect_undecided_figure_batches(root)
    board_tasks = collect_owner_board_tasks(root)
    prs = collect_open_prs() if include_github else []
    lines = [
        "# OWNER QUEUE — regenerate with `python3 scripts/owner_queue.py`",
        "",
        f"_Generated {date.today().isoformat()}. Manual walkthrough ritual: "
        "see `docs/rse/control/owner-queue-ritual.md`._",
        "",
        "## Decisions (wayfinder frontier, owner-facing)",
        "",
    ]
    if decisions:
        for ticket in decisions:
            relative = ticket.path.relative_to(root)
            lines.extend(
                [
                    f"- **{ticket.title}** — open, unblocked, owner-facing",
                    f"  `{relative}`",
                ]
            )
    else:
        lines.append("- None.")
    lines.extend(["", "## Approvals (figure review / data cards)", ""])
    if figures:
        for batch in figures:
            lines.extend(
                [
                    f"- **{batch.name}** — at least one candidate has no approval receipt",
                    f"  `{batch.relative_to(root)}`",
                ]
            )
    else:
        lines.append("- None.")
    lines.extend(["", "## Owner-marked board tasks", ""])
    if board_tasks:
        for task in board_tasks:
            lines.extend(
                [
                    f"- **{task}** — owner-marked board task",
                    "  `docs/rse/control/BOARD.md`",
                ]
            )
    else:
        lines.append("- None.")
    lines.extend(["", "## Open PRs (review or delegate)", ""])
    if include_github and prs:
        for pr in prs:
            lines.extend(
                [
                    f"- **#{pr['number']} {pr['title']}** — open",
                    f"  `{pr['url']}`",
                ]
            )
    elif include_github:
        lines.append("- None found (GitHub query is best-effort).")
    else:
        lines.append("- Not queried (`--offline`).")
    return "\n".join(lines) + "\n"


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--offline", action="store_true", help="skip the GitHub PR query"
    )
    result.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return result


def main() -> int:
    args = parser().parse_args()
    output = args.output.resolve()
    rendered = render_owner_queue(include_github=not args.offline)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
