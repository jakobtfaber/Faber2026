from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).parents[1] / "scripts" / "manual_bad_channel_atlas.py"
SPEC = importlib.util.spec_from_file_location("manual_bad_channel_atlas", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_atlas_coarsening_uses_only_measured_rows_without_zero_fill():
    values = np.arange(24, dtype=float).reshape(6, 4)
    frequency = np.arange(700.0, 706.0)
    valid = np.array([True, False, True, True, False, False])

    coarse, coarse_frequency = MODULE.coarsen_selected(
        values,
        frequency,
        valid,
        np.ones(6, dtype=bool),
        factor=2,
    )

    np.testing.assert_allclose(coarse[0], values[0])
    np.testing.assert_allclose(coarse[1], np.mean(values[2:4], axis=0))
    assert np.isnan(coarse[2]).all()
    np.testing.assert_allclose(coarse_frequency, [700.5, 702.5, 704.5])


def test_atlas_coarsening_truncates_only_incomplete_final_group():
    values = np.arange(20, dtype=float).reshape(5, 4)
    frequency = np.arange(700.0, 705.0)

    coarse, coarse_frequency = MODULE.coarsen_selected(
        values,
        frequency,
        np.ones(5, dtype=bool),
        np.ones(5, dtype=bool),
        factor=2,
    )

    assert coarse.shape == (2, 4)
    np.testing.assert_allclose(coarse_frequency, [700.5, 702.5])


def test_review_bundle_records_full_resolution_arrays_and_bindings(tmp_path: Path):
    output = tmp_path / "review.npz"
    dynamic = np.arange(24, dtype=np.float32).reshape(6, 4)
    frequency = np.arange(700.0, 706.0)
    valid = np.array([True, False, True, True, False, True])

    MODULE.write_review_bundle(
        output,
        dynamic_spectrum=dynamic,
        frequency_mhz=frequency,
        row_valid=valid,
        time_ms=np.arange(4, dtype=float),
        off_mean=np.arange(6, dtype=float),
        off_standard_deviation=np.arange(6, dtype=float) + 1,
        on_spectrum=np.arange(6, dtype=float) + 2,
        metadata={
            "schema_version": 1,
            "event": "zach",
            "instrument": "chime-frb",
            "frequency_axis_sha256": "frequency",
            "source_product_sha256": "source",
        },
    )

    with np.load(output, allow_pickle=False) as values:
        np.testing.assert_array_equal(values["dynamic_spectrum"], dynamic)
        np.testing.assert_array_equal(values["frequency_mhz"], frequency)
        np.testing.assert_array_equal(values["row_valid"], valid)
        assert "\"source_product_sha256\": \"source\"" in str(
            values["metadata_json"].item()
        )
