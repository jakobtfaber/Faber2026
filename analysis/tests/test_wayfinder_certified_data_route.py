from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from scripts.owner_queue import collect_wayfinder_frontier

ROOT = Path(__file__).resolve().parents[1]
TICKETS = ROOT / "docs/rse/wayfinder/tickets"

ROUTE = [
    "16-build-verified-zach-chime-preprocessing-baseline.md",
    "rfi-validation-01a-review-preservation-dynamic-spectrum.md",
    "rfi-validation-01-define-acceptance-contract.md",
    "rfi-validation-01b-stabilize-bandpass-model.md",
    "rfi-validation-02-build-frozen-benchmark.md",
    "rfi-validation-03-compare-and-choose-cleaner.md",
    "rfi-validation-04-blind-validate-cleaner.md",
    "rfi-validation-05-ratify-cleaning-boundary.md",
    "17-remediate-scintillation-inputs-and-rerun.md",
    "02-ratify-chime-scintillation-method.md",
]


def ticket(name: str) -> str:
    return (TICKETS / name).read_text(encoding="utf-8")


def test_certified_data_route_files_and_blockers_exist():
    for name in ROUTE:
        assert (TICKETS / name).is_file(), name

    for path in TICKETS.glob("*.md"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("- Blocked by:"):
                for target in re.findall(r"\]\(([^)]+\.md)\)", line):
                    assert (path.parent / target).resolve().is_file(), (
                        path.name,
                        target,
                    )

    for prerequisite, downstream in zip(ROUTE[:-1], ROUTE[1:], strict=True):
        if downstream == "rfi-validation-01-define-acceptance-contract.md":
            # Preservation review informed the contract but is not a live
            # dependency after its limits were accepted.
            continue
        if "Status: closed" in ticket(prerequisite) or "Status: resolved" in ticket(
            prerequisite
        ):
            continue
        blocker_line = next(
            line
            for line in ticket(downstream).splitlines()
            if line.startswith("- Blocked by:")
        )
        assert f"]({prerequisite})" in blocker_line, (
            downstream,
            prerequisite,
            blocker_line,
        )


def test_completed_baseline_is_resolved_without_science_promotion():
    zach = ticket("16-build-verified-zach-chime-preprocessing-baseline.md")
    assert "Status: resolved" in zach
    assert "pre-bad-channel mask" in zach
    assert "no science fit or claim is admitted" in zach


def test_rfi_contract_remains_owner_pending_and_fail_closed():
    contract = ticket("rfi-validation-01-define-acceptance-contract.md")
    normalized = " ".join(contract.split())
    assert "Status: open — owner ratification" in normalized
    assert "at least 90 percent of injected excess power" in normalized
    assert "no more than 1 percent overall" in normalized
    assert "95 percent for the relatively quiet test file" in normalized
    assert "Each contiguous half" in normalized
    assert "cluster bootstrap" in normalized
    assert "Treating correlated pixels as independent" in normalized
    assert "candidate-inflated uncertainty" in normalized
    assert "Unlabelled native raw samples cannot establish" in normalized
    assert "Pooled success cannot rescue" in normalized
    assert "minimum sample and injection counts" in normalized
    assert "will not validate a cleaner" in normalized


def test_chime_ratification_waits_for_remediated_campaign_review():
    ratification = ticket("02-ratify-chime-scintillation-method.md")
    remediation = ticket("17-remediate-scintillation-inputs-and-rerun.md")
    assert "17-remediate-scintillation-inputs-and-rerun.md" in ratification
    assert "rfi-validation-05-ratify-cleaning-boundary.md" in remediation
    assert "owner review" in remediation.lower()


GUARDED_LINKS = [
    (
        "rfi-validation-01b-stabilize-bandpass-model.md",
        "rfi-validation-02-build-frozen-benchmark.md",
    ),
    (
        "rfi-validation-03-compare-and-choose-cleaner.md",
        "rfi-validation-04-blind-validate-cleaner.md",
    ),
    (
        "rfi-validation-05-ratify-cleaning-boundary.md",
        "17-remediate-scintillation-inputs-and-rerun.md",
    ),
]


@pytest.mark.parametrize("upstream,downstream", GUARDED_LINKS)
@pytest.mark.parametrize(
    "status,outcome,clears",
    [
        ("open", "pending", False),
        ("open", "no-go", False),
        ("resolved", "no-go", False),
        ("resolved", "pass", True),
    ],
)
def test_authoritative_frontier_enforces_exact_route_transitions(
    tmp_path, upstream, downstream, status, outcome, clears
):
    tickets = tmp_path / "tickets"
    tickets.mkdir()
    for name in {upstream, downstream}:
        shutil.copy2(TICKETS / name, tickets / name)

    upstream_path = tickets / upstream
    upstream_text = upstream_path.read_text(encoding="utf-8")
    upstream_text = re.sub(
        r"^- Status:.*$", f"- Status: {status}", upstream_text, flags=re.M
    )
    upstream_text = re.sub(
        r"^- Gate outcome:.*$", f"- Gate outcome: {outcome}", upstream_text, flags=re.M
    )
    upstream_path.write_text(upstream_text, encoding="utf-8")

    frontier = {item.path.name for item in collect_wayfinder_frontier(tickets)}
    assert (downstream in frontier) is clears


def test_recovered_cluster_redshifts_have_deterministic_classification():
    contract = ticket(
        "expanded-foreground-catalog-repair-13-set-nine-sightline-search-contract.md"
    )
    assert "search_geometry_redshift_source" in contract
    assert re.search(r"catalog or\s+separately sourced", contract)
    assert "same frozen redshift evidence" in contract
    assert "conflicting recovered redshifts" in contract
