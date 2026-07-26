from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).parents[1] / "scripts" / "prototype_rfi_preservation_review.py"
SPEC = importlib.util.spec_from_file_location("rfi_prototype", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def small_fixture():
    nfreq, ntime = 128, 96
    freq = 800.0 - (np.arange(nfreq) + 0.5) * (400.0 / nfreq)
    source_valid = np.ones(nfreq, dtype=bool)
    source_valid[32:48] = False
    mean = 20.0 + 3.0 * np.sin(np.linspace(0, 3.0, nfreq))
    scale = 1.0 + 0.2 * np.cos(np.linspace(0, 5.0, nfreq))
    return freq, source_valid, mean, scale, ntime


def test_generation_is_deterministic_and_missing_rows_stay_nan():
    freq, source_valid, mean, scale, ntime = small_fixture()
    first = MODULE.generate_case(freq, source_valid, mean, scale, ntime, 0.5, 2026072101)
    second = MODULE.generate_case(freq, source_valid, mean, scale, ntime, 0.5, 2026072101)

    for key in ("truth", "signal", "raw", "rfi", "rfi_mask"):
        np.testing.assert_array_equal(first[key], second[key])
    assert np.isnan(first["truth"][~source_valid]).all()
    assert np.isnan(first["raw"][~source_valid]).all()
    assert first["parameters"]["burst"]["components"] == 2
    assert first["parameters"]["burst"]["separation_ms"] > 0


def test_each_rfi_class_is_present_and_bandpass_round_trip_is_exact():
    freq, source_valid, mean, scale, ntime = small_fixture()
    case = MODULE.generate_case(freq, source_valid, mean, scale, ntime, 0.5, 2026072101)

    for component in case["component_masks"].values():
        assert component.any()
    oracle = MODULE.oracle_normalize(case["raw"] - case["rfi"], mean, scale, source_valid)
    np.testing.assert_allclose(
        oracle[source_valid], case["truth"][source_valid], rtol=0, atol=5e-6
    )


def test_bandpass_shape_interpolation_does_not_reclassify_source_rows():
    freq, source_valid, mean, scale, ntime = small_fixture()
    mean[5:9] = np.nan
    scale[80:83] = np.nan
    case = MODULE.generate_case(freq, source_valid, mean, scale, ntime, 0.5, 2026072101)

    np.testing.assert_array_equal(case["source_valid"], source_valid)
    assert np.isfinite(case["bandpass_mean"][source_valid]).all()
    assert np.isfinite(case["bandpass_scale"][source_valid]).all()
    assert case["parameters"]["bandpass_shape_interpolated_rows"] == 7


def test_mask_confusion_accounts_for_all_valid_pixels():
    truth = np.array([[False, True, False], [True, True, False]])
    predicted_rows = np.array([True, False])
    valid = np.ones_like(truth, dtype=bool)
    counts = MODULE.mask_confusion(truth, predicted_rows, valid)

    assert counts == {"tp": 1, "fp": 2, "fn": 2, "tn": 1}
    assert sum(counts.values()) == truth.size


def test_mask_confusion_accepts_an_explicit_pixel_mask():
    truth = np.array([[False, True, False], [True, True, False]])
    predicted = np.array([[False, True, True], [False, True, False]])
    valid = np.ones_like(truth, dtype=bool)

    counts = MODULE.mask_confusion(truth, predicted, valid)

    assert counts == {"tp": 2, "fp": 1, "fn": 1, "tn": 2}


def test_prototype_uses_the_frozen_pixel_threshold():
    assert MODULE.ABSOLUTE_PIXEL_THRESHOLD == 6.0


def test_measurements_use_common_finite_support_without_zero_fill():
    freq, source_valid, mean, scale, ntime = small_fixture()
    case = MODULE.generate_case(freq, source_valid, mean, scale, ntime, 0.5, 2026072101)
    coarse, coarse_freq, counts = MODULE.coarsen(case["truth"], freq, source_valid, factor=8)
    measurements = MODULE.measure_summary(
        coarse,
        coarse_freq,
        counts > 0,
        dt_ms=0.5,
        burst_window=tuple(case["parameters"]["windows"]["burst"]),
        signal_template=MODULE.coarsen(case["signal"], freq, source_valid, factor=8)[0],
    )

    assert measurements["component_count"] == 2
    assert np.isfinite(measurements["arrival_time_ms"])
    assert np.isfinite(measurements["width_ms"])
    assert np.isfinite(measurements["dm_offset_pc_cm3"])
    assert np.isfinite(measurements["morphology_correlation"])
