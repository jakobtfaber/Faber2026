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
    training, burst = MODULE.load_allowed_slices(observed)

    assert observed.keys == [
        (slice(None), slice(55, 137)),
        (slice(None), slice(232, 248)),
    ]
    assert training.shape == (65536, 82)
    assert burst.shape == (65536, 16)


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
