from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


def _write_ticket(path: Path, *, title: str, status: str, assignee: str) -> None:
    path.write_text(
        "\n".join(
            [
                f"# {title}",
                "",
                "- Type: `wayfinder:task` (HITL)",
                f"- Status: {status}",
                f"- Assignee: {assignee}",
                "- Blocked by: none",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_owner_frontier_keeps_open_hitl_tickets_even_when_assigned(tmp_path):
    from scripts.owner_queue import collect_wayfinder_frontier

    tickets = tmp_path / "tickets"
    tickets.mkdir()
    _write_ticket(
        tickets / "open.md",
        title="Open owner decision",
        status="open",
        assignee="unassigned",
    )
    _write_ticket(
        tickets / "claimed.md",
        title="Claimed owner decision",
        status="open",
        assignee="Codex",
    )
    _write_ticket(
        tickets / "resolved.md",
        title="Resolved owner decision",
        status="resolved",
        assignee="unassigned",
    )
    titles = {
        ticket.title
        for ticket in collect_wayfinder_frontier(tickets, owner_facing_only=True)
    }
    assert titles == {"Open owner decision", "Claimed owner decision"}


def test_owner_queue_cli_regenerates_from_authoritative_frontier(tmp_path):
    output = tmp_path / "OWNER_QUEUE.md"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/owner_queue.py"),
            "--offline",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    rendered = output.read_text(encoding="utf-8")
    assert "Decisions (wayfinder frontier, owner-facing)" in rendered
    assert "Obtain the authoritative host-redshift ledger" not in rendered
    assert "Not queried (`--offline`)" in rendered


def test_owner_queue_queries_analysis_repository(monkeypatch):
    from scripts import owner_queue

    seen: list[str] = []

    def fake_run(command, **_kwargs):
        seen.extend(command)
        return SimpleNamespace(returncode=0, stdout=json.dumps([]))

    monkeypatch.setattr(owner_queue.shutil, "which", lambda _name: "/usr/bin/gh")
    monkeypatch.setattr(owner_queue.subprocess, "run", fake_run)

    assert owner_queue.collect_open_prs() == []
    assert seen[seen.index("--repo") + 1] == "jakobtfaber/Faber2026-analysis"
