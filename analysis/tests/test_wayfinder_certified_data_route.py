from __future__ import annotations

import re
from pathlib import Path


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


def test_chime_ratification_waits_for_remediated_campaign_review():
    ratification = ticket("02-ratify-chime-scintillation-method.md")
    remediation = ticket("17-remediate-scintillation-inputs-and-rerun.md")
    assert "17-remediate-scintillation-inputs-and-rerun.md" in ratification
    assert "rfi-validation-05-ratify-cleaning-boundary.md" in remediation
    assert "owner review" in remediation.lower()
