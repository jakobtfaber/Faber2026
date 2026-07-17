"""CLI selection tests for the fail-closed figure-review workflow."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import figure_review  # noqa: E402


def test_new_batch_accepts_a_single_candidate_selection():
    args = figure_review.parser().parse_args(
        [
            "new-batch",
            "test-batch",
            "--title",
            "test",
            "--pipeline-revision",
            "deadbeef",
            "--candidate",
            "fig1-gallery",
        ]
    )
    assert args.candidate == ["fig1-gallery"]
