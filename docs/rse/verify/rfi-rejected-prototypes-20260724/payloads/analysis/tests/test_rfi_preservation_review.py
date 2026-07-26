from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import build_rfi_preservation_review as review


def test_rejected_cleaner_uses_only_off_pulse_samples() -> None:
    rng = np.random.default_rng(7)
    data = rng.normal(size=(review.N_FREQ, review.N_TIME))
    _, original_mask = review.rejected_row_cleaner(data)
    data[:, review.ON_PULSE] += 1_000.0
    _, burst_changed_mask = review.rejected_row_cleaner(data)
    assert np.array_equal(original_mask, burst_changed_mask)


def test_review_is_deterministic_and_fail_closed(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    metrics = review.build(first)
    review.build(second)

    assert metrics["verdict"] == "not cleaner validation; not science admissible"
    assert metrics["masked_frequency_rows"]
    assert (first / "rfi_preservation_review.svg").read_bytes() == (
        second / "rfi_preservation_review.svg"
    ).read_bytes()
    first_metrics = json.loads((first / "rfi_preservation_metrics.json").read_text())
    second_metrics = json.loads((second / "rfi_preservation_metrics.json").read_text())
    assert first_metrics == second_metrics
    assert first_metrics["hashes"]["truth"] == metrics["hashes"]["truth"]
    assert set(first_metrics["proposed_limit_checks"]) == {
        "median_shift_le_0.25_sigma",
        "p95_shift_le_0.5_sigma",
        "all_shifts_le_1_sigma",
        "at_least_95_percent_within_1_sigma",
        "median_systematic_le_0.25_sigma",
        "detection_unchanged",
        "component_count_unchanged",
    }
