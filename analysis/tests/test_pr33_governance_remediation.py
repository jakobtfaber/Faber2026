from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TICKETS = ROOT / "docs/rse/wayfinder/tickets"


def _ticket(name: str):
    from scripts.wayfinder_state import parse_ticket

    return parse_ticket(TICKETS / name)


def _ticket_text(name: str) -> str:
    return (TICKETS / name).read_text(encoding="utf-8")


@pytest.fixture
def owner_frontier():
    from scripts.owner_queue import collect_wayfinder_frontier

    return collect_wayfinder_frontier(TICKETS, owner_facing_only=True)


def test_ticket_05_resolved_and_out_of_frontier(owner_frontier):
    t = _ticket("05-profile-component-statistic-blocker-decision.md")
    assert t.status == "resolved"
    assert t not in owner_frontier


def test_ticket_05_does_not_assign_future_work_to_itself():
    text = _ticket_text("05-profile-component-statistic-blocker-decision.md")
    assert "## Decision" in text
    decision = text.split("## Decision", 1)[1]
    assert "successor" in decision.lower()
    assert "ticket 05" not in decision.lower()
    assert "20-develop-injection-calibrated-profile-component-count-statistic" in decision


def test_successor_ticket_exists_and_is_non_blocking():
    name = "20-develop-injection-calibrated-profile-component-count-statistic.md"
    text = _ticket_text(name)
    assert "non-blocking" in text.lower()
    assert "05-profile-component-statistic-blocker-decision.md" in text
    assert "15-count-audit-remediation-standing-method.md" in text
    assert "known-truth-injection-calibrated" in text.lower().replace(" ", "-")
    t = _ticket(name)
    assert t.is_open
    assert not t.is_owner_facing
    assert t.blockers == ()


def test_ticket_15_resolved_and_points_to_successor(owner_frontier):
    t = _ticket("15-count-audit-remediation-standing-method.md")
    assert t.status == "resolved"
    assert t not in owner_frontier
    text = _ticket_text("15-count-audit-remediation-standing-method.md")
    assert "20-develop-injection-calibrated-profile-component-count-statistic" in text
    assert "It is not a count setter by itself" in text
    assert "None of the proposed count changes" in text
    assert "are adopted" in text


def test_ticket_03_resolved_with_scoped_injection_policy(owner_frontier):
    t = _ticket("03-ratify-fit-retrust-contract.md")
    assert t.status == "resolved"
    assert t not in owner_frontier
    text = _ticket_text("03-ratify-fit-retrust-contract.md")
    assert "Verified gen-2+ input-data lineage" in text
    assert "Prior-rail used only for model-family rejection" in text
    assert "Posterior-predictive check pass" in text
    assert "Independent cross-check produced under this contract" in text
    assert "not required as a standalone" in text
    assert "Known-truth injection calibration is required" in text
    assert "component-count-setting statistic" in text


def test_ticket_10_unchanged_because_not_covered_by_receipt(owner_frontier):
    t = _ticket("10-disposition-technical-review-robustness-items.md")
    assert t.status == "open"
    assert t in owner_frontier
    text = _ticket_text("10-disposition-technical-review-robustness-items.md")
    assert "## Decision" not in text


def test_owner_queue_matches_canonical_ticket_state():
    from scripts.owner_queue import render_owner_queue

    rendered = render_owner_queue(ROOT, include_github=False)
    expected = (ROOT / "OWNER_QUEUE.md").read_text(encoding="utf-8")
    assert rendered == expected


def test_owner_queue_excludes_resolved_and_successor_tickets(owner_frontier):
    names = {t.path.name for t in owner_frontier}
    assert "05-profile-component-statistic-blocker-decision.md" not in names
    assert "15-count-audit-remediation-standing-method.md" not in names
    assert "03-ratify-fit-retrust-contract.md" not in names
    assert "20-develop-injection-calibrated-profile-component-count-statistic.md" not in names
    assert "10-disposition-technical-review-robustness-items.md" in names


def test_map_and_board_reference_successor():
    map_text = (ROOT / "docs/rse/wayfinder/map-apj-submission.md").read_text(
        encoding="utf-8"
    )
    assert "20-develop-injection-calibrated-profile-component-count-statistic" in map_text
    assert "non-blocking" in map_text.lower()
    board_text = (ROOT / "docs/rse/control/BOARD.md").read_text(encoding="utf-8")
    assert "Profile-component-count statistic: deferred for this submission" in board_text
    assert "Fit re-validation contract ratification" in board_text
    assert "[x] Fit re-validation contract ratification" in board_text


RECEIPT_URL = "https://github.com/jakobtfaber/Faber2026-analysis/pull/46#issuecomment-5050854194"


def test_affected_tickets_cite_exact_owner_receipt_and_ticket_10_does_not():
    for name in (
        "03-ratify-fit-retrust-contract.md",
        "05-profile-component-statistic-blocker-decision.md",
        "15-count-audit-remediation-standing-method.md",
    ):
        text = _ticket_text(name)
        assert RECEIPT_URL in text, f"{name} must cite the owner receipt URL"
        assert "Manuscript-owner governance receipt — 2026-07-22" in text
    ten = _ticket_text("10-disposition-technical-review-robustness-items.md")
    assert RECEIPT_URL not in ten
    assert "Manuscript-owner governance receipt" not in ten
