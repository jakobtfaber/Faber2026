from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "review_real_zach_rfi_cleaner.py"
SPEC = importlib.util.spec_from_file_location("real_zach_review", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class SliceRecorder:
    shape = (65536, 437)

    def __init__(self):
        self.keys = []

    def __getitem__(self, key):
        self.keys.append(key)
        rows, columns = key
        assert rows == slice(None)
        return np.zeros((65536, columns.stop - columns.start), dtype=np.float32)


def test_observed_loader_reads_only_approved_training_and_burst_slices():
    observed = SliceRecorder()
    training, context = MODULE.load_allowed_slices(observed)

    assert observed.keys == [
        (slice(None), slice(55, 137)),
        (slice(None), slice(149, 305)),
    ]
    assert training.shape == (65536, 82)
    assert context.shape == (65536, 156)


def test_observed_loader_rejects_unexpected_shape():
    observed = SliceRecorder()
    observed.shape = (65536, 438)

    with pytest.raises(ValueError, match="unexpected observed-array shape"):
        MODULE.load_allowed_slices(observed)


def test_coarsening_uses_nan_for_missing_support_not_zero():
    values = np.arange(32, dtype=float).reshape(8, 4)
    frequency = np.arange(8, dtype=float)
    valid = np.array([False, False, False, False, True, True, True, True])
    coarse, coarse_frequency, counts = MODULE.coarsen(values, frequency, valid, factor=4)

    assert np.isnan(coarse[0]).all()
    assert np.isnan(coarse_frequency[0])
    assert counts.tolist() == [0, 4]
    np.testing.assert_allclose(coarse[1], np.mean(values[4:], axis=0))


def test_status_forbids_cleaner_validation_claim():
    assert MODULE.STATUS == "diagnostic_only_real_event_method_comparison"


def test_display_contains_documented_on_pulse_envelope_with_padding():
    display_width_ms = (MODULE.DISPLAY[1] - MODULE.DISPLAY[0]) * MODULE.DT_MS
    on_pulse_width_ms = (MODULE.ON_PULSE[1] - MODULE.ON_PULSE[0]) * MODULE.DT_MS
    left_padding_ms = (MODULE.ON_PULSE[0] - MODULE.DISPLAY[0]) * MODULE.DT_MS
    right_padding_ms = (MODULE.DISPLAY[1] - MODULE.ON_PULSE[1]) * MODULE.DT_MS

    assert on_pulse_width_ms >= 14.21
    assert display_width_ms > on_pulse_width_ms
    assert left_padding_ms >= 10.0
    assert right_padding_ms >= 10.0


def test_analytic_time0_alignment_recovers_known_extra_offset():
    target_dm = 20.0
    frequency_mhz = np.array([800.0, 400.0])
    coarse_ids = np.array([0, 1])
    native_dt_s = 2.56e-6
    output_dt_s = 0.32768e-3
    dispersive_samples = (
        MODULE.K_DM_S_MHZ2
        * target_dm
        * (1.0 / frequency_mhz[1] ** 2 - 1.0 / frequency_mhz[0] ** 2)
        / native_dt_s
    )
    extra_bins = 3
    fpga = {
        0: 1_000_000,
        1: 1_000_000
        + int(round(dispersive_samples + extra_bins * output_dt_s / native_dt_s)),
    }

    shifts, offsets = MODULE.alignment_shifts(
        frequency_mhz,
        coarse_ids,
        fpga,
        target_dm=target_dm,
        native_dt_s=native_dt_s,
        output_dt_s=output_dt_s,
    )

    assert shifts.tolist() == [0, extra_bins]
    assert offsets[1] == pytest.approx(extra_bins * output_dt_s, abs=native_dt_s)


def test_nonwrapping_alignment_keeps_shifted_edges_missing():
    values = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    aligned = MODULE.align_nonwrapping(values, np.array([0, 2]))

    np.testing.assert_array_equal(aligned[0, :3], values[0])
    assert np.isnan(aligned[0, 3:]).all()
    assert np.isnan(aligned[1, :2]).all()
    np.testing.assert_array_equal(aligned[1, 2:], values[1])


def test_integrated_spectrum_uses_only_fixed_on_pulse_window_and_valid_rows():
    values = np.array(
        [
            [100.0, 1.0, 2.0, 100.0],
            [100.0, 3.0, 4.0, 100.0],
        ]
    )
    spectrum = MODULE.integrated_spectrum(
        values,
        np.array([True, False]),
        (1, 3),
    )

    assert spectrum[0] == 3.0
    assert np.isnan(spectrum[1])
