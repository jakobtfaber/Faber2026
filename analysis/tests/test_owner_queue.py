from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_known_unassigned_owner_tickets_are_in_frontier():
    from scripts.owner_queue import collect_wayfinder_frontier

    titles = {
        ticket.title for ticket in collect_wayfinder_frontier(owner_facing_only=True)
    }
    assert "Freeze protected WISE--PS1--STRM and UNIONS/CFIS evidence" in titles
    assert "Obtain the authoritative host-redshift ledger" in titles


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
    assert "Freeze protected WISE--PS1--STRM and UNIONS/CFIS evidence" in rendered
    assert "Obtain the authoritative host-redshift ledger" in rendered
    assert "Not queried (`--offline`)" in rendered
