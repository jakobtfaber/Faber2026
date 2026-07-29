"""Why the installed Figure 1 cannot be reaffirmed by the dispersion-measure refutation.

The twelve-burst gallery installed in the manuscript
(``figures/codetection_data_grid.pdf``) is the version the manuscript owner
approved on 2026-07-15. Two later candidates exist, and the correction-bearing
one was refuted, which invites the shortcut "the corrections were wrong, so keep
what is installed".

That shortcut does not hold. The refutation only removes the *dmcorr* candidate.
The installed bytes fail on a separate and independent ground: their time axes
were anchored on fitted joint-model arrival times, not on the observed burst
profile, so the installed Figure 1 is not the data-only product the manuscript
claims it is. These checks pin that reasoning so a later session does not have
to rediscover it.

See ``docs/rse/specs/validation-fig1-observed-peak-audit.md``, addendum
"Reaffirmation test".
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT_ROOT = ROOT.parent

INSTALLED_TARGET = "figures/codetection_data_grid.pdf"

# The manuscript-owner approval and promotion receipt for the installed bytes.
APPROVAL_RECEIPT = ROOT / "figure_review/decisions/approval_receipts/fig1-gallery.json"

# The two later candidates. Neither has been promoted.
OBSERVED_PEAK_BATCH = "2026-07-17-fig1-observed-peak-audit"
DMCORR_BATCH = "2026-07-17-fig1-observed-peak-dmcorr"
BATCHES = ROOT / "figure_review/artifacts/batches"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidate(batch_id: str, candidate_id: str = "fig1-gallery") -> dict:
    manifest = json.loads((BATCHES / batch_id / "manifest.json").read_text())
    return next(item for item in manifest["candidates"] if item["id"] == candidate_id)


def show_at_source_revision(relative_path: str) -> str:
    """Read a file as it stood at the source revision named in the approval receipt.

    The installed bytes are only interpretable against the code and roster that
    produced them, not against today's files, which have since moved and changed.
    """
    revision = json.loads(APPROVAL_RECEIPT.read_text())["source_revision"]
    blob = f"{revision}:{relative_path}"
    probe = subprocess.run(
        ["git", "cat-file", "-e", blob],
        cwd=MANUSCRIPT_ROOT,
        capture_output=True,
    )
    if probe.returncode != 0:
        pytest.skip(f"manuscript history for {blob} is not available in this checkout")
    return subprocess.run(
        ["git", "show", blob],
        cwd=MANUSCRIPT_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout


def test_installed_figure_is_exactly_the_approved_and_promoted_bytes() -> None:
    """The installed target still matches its receipt, so the receipt is usable evidence."""
    receipt = json.loads(APPROVAL_RECEIPT.read_text())
    assert receipt["decision"]["status"] == "approved"
    assert receipt["decision"]["reviewer_role"] == "manuscript_owner"
    assert receipt["promoted_target"] == INSTALLED_TARGET
    assert receipt["candidate_sha256"] == receipt["promoted_sha256"]
    assert sha256(MANUSCRIPT_ROOT / INSTALLED_TARGET) == receipt["promoted_sha256"]


def test_installed_bytes_are_neither_surviving_candidate() -> None:
    """Keeping the installed figure is a third outcome, not "the uncorrected candidate"."""
    installed = sha256(MANUSCRIPT_ROOT / INSTALLED_TARGET)
    assert installed != candidate(OBSERVED_PEAK_BATCH)["artifact_sha256"]
    assert installed != candidate(DMCORR_BATCH)["artifact_sha256"]


def test_installed_figure_was_rendered_with_fitted_arrival_time_anchors() -> None:
    """The disqualifying fact: the installed panels depend on the joint-fit family.

    At the source revision recorded in the approval receipt the producer passed
    ``extra_shift_ms=fit_toa_shift_ms(...)``, moving each panel's display anchor
    from the observed profile peak to a fitted arrival time. Pull Request #121
    removed that call. Figure 1 is required to be data-only and independent of
    joint-model acceptance, so those bytes cannot be reaffirmed.
    """
    producer = show_at_source_revision("scripts/plot_codetection_data_grid.py")
    assert "extra_shift_ms=fit_toa_shift_ms(" in producer

    # The current producer no longer does this; see
    # tests/test_codetection_data_grid.py for the positive observed-peak check.
    current = (ROOT / "scripts/plot_codetection_data_grid.py").read_text()
    assert "fit_toa_shift_ms" not in current


def test_fitted_anchor_would_have_touched_eleven_of_twelve_panels() -> None:
    """Scope of the defect: only the burst without an accepted joint fit escaped it.

    ``fit_toa_shift_ms`` returned an empty shift for rows carrying no fit
    artifact, so the roster in force at the time fixes how many panels were
    re-anchored. Several of the artifacts it used are themselves flagged
    rejected or morphology-audit only, which is why the dependence matters
    rather than being cosmetic. The roster has since been narrowed, so this
    reads it at the receipt's source revision rather than from the working tree.
    """
    roster = yaml.safe_load(show_at_source_revision("scripts/jointmodel_triptych_manifest.yaml"))
    bursts = roster["bursts"]
    assert len(bursts) == 12
    with_fit = [burst["nick"] for burst in bursts if burst.get("npz")]
    assert len(with_fit) == 11
    assert [burst["nick"] for burst in bursts if not burst.get("npz")] == ["chromatica"]
    not_physical = [
        burst["nick"]
        for burst in bursts
        if burst.get("npz") and (burst.get("flag") or "").startswith(("rejected", "morphology"))
    ]
    assert sorted(not_physical) == ["casey", "hamilton", "wilhelm", "zach"]


def test_both_later_fig1_candidates_remain_owner_gated() -> None:
    """The replacement decision is still the owner's; no agent may pre-empt it.

    The surviving candidate must stay undispositioned, so it keeps surfacing
    fail-closed in the owner queue. The refuted companion may carry a
    disposition, but only a suppressing one — never an approval.
    """
    for batch_id in (OBSERVED_PEAK_BATCH, DMCORR_BATCH):
        assert candidate(batch_id)["decision"]["status"] == "pending"
    dispositions = json.loads(
        (ROOT / "figure_review/decisions/batch_dispositions.json").read_text()
    )["batches"]
    assert OBSERVED_PEAK_BATCH not in dispositions
    dmcorr = dispositions.get(DMCORR_BATCH)
    if dmcorr is not None:
        assert dmcorr["owner_queue"] is False
        assert dmcorr["status"] != "approved"
