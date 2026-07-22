from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


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
    assert "Not queried (`--offline`)" in rendered
