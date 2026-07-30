from __future__ import annotations

import numpy as np
import pytest

from radio_pipeline.fitting import (
    DispersionState,
    load_band_observation_product,
    write_band_observation_product,
)
from radio_pipeline.fitting.products import (
    mjd_crop_time0_unix_ns,
    unix_seconds_parts_to_ns,
)


def test_observation_product_round_trip_and_exact_dispersion(tmp_path) -> None:
    rng = np.random.default_rng(4)
    values = rng.normal(size=(4, 64))
    valid = np.ones(values.shape, dtype=bool)
    valid[1, 9] = False
    path = tmp_path / "chime-fit-observation.npz"
    receipt = write_band_observation_product(
        path,
        instrument="chime",
        waterfall=values,
        valid=valid,
        frequency_mhz=np.array([401.0, 402.0, 403.0, 404.0]),
        channel_width_mhz=0.0244140625,
        sample_interval_s=2.56e-6,
        time0_unix_ns=1_700_000_000_000_000_000,
        dispersion=DispersionState(0.0, 491.28, -0.02, 491.26, "coherent+residual"),
        input_sha256={"raw_h5": "a" * 64},
    )
    loaded = load_band_observation_product(path, expected_sha256=str(receipt["sha256"]))
    assert loaded.instrument == "chime"
    assert loaded.time0_unix_ns == 1_700_000_000_000_000_000
    assert loaded.dispersion.product_dm_pc_cm3 == pytest.approx(491.26)
    assert loaded.valid[1, 9] == np.bool_(False)
    assert np.nanmedian(loaded.waterfall[0, :16]) == pytest.approx(0.0, abs=0.5)
    with np.load(path, allow_pickle=False) as product:
        off_pulse = product["noise_estimation_mask"]
        assert off_pulse.shape == values.shape
        assert np.all(off_pulse[:, 16:48] == 0)
        assert int(product["time0_unix_ns"]) == 1_700_000_000_000_000_000


def test_observation_product_rejects_missing_contract_field(tmp_path) -> None:
    path = tmp_path / "incomplete.npz"
    np.savez_compressed(path, waterfall=np.zeros((2, 2)))
    with pytest.raises(ValueError, match="incomplete"):
        load_band_observation_product(path)


def test_observation_product_rejects_hash_drift(tmp_path) -> None:
    path = tmp_path / "product.npz"
    np.savez_compressed(path, waterfall=np.zeros((2, 2)))
    with pytest.raises(ValueError, match="SHA-256"):
        load_band_observation_product(path, expected_sha256="0" * 64)


def test_filterbank_crop_time_origin_avoids_epoch_float_loss() -> None:
    assert mjd_crop_time0_unix_ns("40587", 0.0, 0.001) == 0
    assert mjd_crop_time0_unix_ns("40587.000000001", 2.0, 0.001) == 2_086_400


def test_h5_split_epoch_preserves_nanoseconds() -> None:
    value = unix_seconds_parts_to_ns(
        np.asarray([1_700_000_000]),
        np.asarray([0.000000123]),
    )
    assert int(value[0]) == 1_700_000_000_000_000_123
