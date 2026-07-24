from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = (
    ROOT
    / "docs/rse/verify/joint-scattering-controlled-rerun-06-owner-review-20260723"
)
PACKET = PACKET_DIR / "decision-packet.json"
TICKET = (
    ROOT
    / "docs/rse/wayfinder/tickets"
    / "joint-scattering-controlled-rerun-06-admit-new-panels.md"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_owner_packet_is_exact_and_fail_closed() -> None:
    packet = json.loads(PACKET.read_text(encoding="utf-8"))

    assert packet["status"] == "owner_scientific_visual_decision_pending"
    assert packet["scientific_trust"] == "pending"
    assert packet["manuscript_promotion_enabled"] is False
    assert [panel["burst"] for panel in packet["panels"]] == [
        "oran",
        "johndoeII",
        "zach",
    ]
    for panel in packet["panels"]:
        assert sha256(PACKET_DIR / panel["panel_path"]) == panel["panel_sha256"]
        receipt = (PACKET_DIR / panel["verification_receipt_path"]).resolve()
        assert sha256(receipt) == panel["verification_receipt_sha256"]
        assert panel["recommendation"] == "revise"
        assert panel["owner_decision"] is None
        assert panel["panel_review_eligible"] is False
        assert panel["panel_approved"] is False
        assert panel["readiness_flags"]


def test_ticket_stops_at_owner_gate() -> None:
    ticket = TICKET.read_text(encoding="utf-8")
    normalized = " ".join(ticket.split())

    assert "owner scientific and visual decision pending" in ticket
    assert "No panel was promoted" in normalized
    assert "fitted values remain untrusted" in normalized
