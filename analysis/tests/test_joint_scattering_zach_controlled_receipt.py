from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = (
    ROOT
    / "docs/rse/verify/joint-scattering-controlled-rerun-05-zach-c2d4-20260723"
    / "verification-receipt.json"
)
TICKET = (
    ROOT
    / "docs/rse/wayfinder/tickets"
    / "joint-scattering-controlled-rerun-05-regenerate-zach-c2d4.md"
)


def test_zach_receipt_is_reproduced_but_fail_closed() -> None:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    assert receipt["morphology"] == "C2D4"
    assert receipt["source_revision"] == (
        "fba755ad7edbd69dece059c8c5f0868da41e3f2b"
    )
    assert all(receipt["checks"].values())
    assert set(receipt["outputs"]) == {
        "diagnostics",
        "fit_summary",
        "model_grid",
        "panel",
        "weighted_samples",
    }
    assert len(receipt["superseded_job_180_artifacts"]) == 5
    assert receipt["scientific_trust"] == "pending"
    assert receipt["component_count_evidence_trust"] == "pending"
    assert receipt["panel_review_eligible"] is False
    assert receipt["panel_approved"] is False


def test_zach_ticket_stops_at_scientific_and_visual_gate() -> None:
    normalized = " ".join(TICKET.read_text(encoding="utf-8").split())

    assert "Status: resolved" in normalized
    assert "science and visual review pending" in normalized
    assert "does not interpret its fit-derived values or component-count evidence" in normalized
    assert "panel remains unapproved and ineligible for review" in normalized
