from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = (
    ROOT
    / "docs/rse/verify/joint-scattering-controlled-rerun-03-oran-c1d1-20260723"
    / "verification-receipt.json"
)
TICKET = (
    ROOT
    / "docs/rse/wayfinder/tickets"
    / "joint-scattering-controlled-rerun-03-regenerate-oran-c1d1.md"
)


def test_oran_receipt_is_reproduced_but_fail_closed() -> None:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))

    assert receipt["morphology"] == "C1D1"
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
    assert receipt["scientific_trust"] == "pending"
    assert receipt["panel_review_eligible"] is False
    assert receipt["panel_approved"] is False


def test_oran_ticket_stops_at_scientific_and_visual_gate() -> None:
    ticket = TICKET.read_text(encoding="utf-8")
    normalized = " ".join(ticket.split())

    assert "Status: resolved" in ticket
    assert "science and visual review pending" in ticket
    assert "does not approve or interpret fit-derived values" in normalized
    assert "panel remains unapproved and ineligible for review" in normalized
