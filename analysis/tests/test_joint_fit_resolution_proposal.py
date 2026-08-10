from __future__ import annotations

import numpy as np
import pytest

from radio_pipeline.fitting.joint_burst import BandObservation, DispersionState
from radio_pipeline.fitting.products import sha256_file
from radio_pipeline.fitting.resolution import (
    arrays_sha256,
    residual_smearing_calculation,
    sample_time_axis_ns,
)
from scripts.propose_joint_fit_resolution import validate_source_contract


def observation(product_dm: float = 100.0) -> BandObservation:
    frequency = np.asarray([800.0, 799.0, 798.0, 797.0])
    return BandObservation(
        instrument="chime",
        waterfall=np.ones((4, 8)),
        valid=np.ones((4, 8), dtype=bool),
        frequency_mhz=frequency,
        channel_width_mhz=np.ones(4),
        sample_interval_s=1.0e-3,
        time0_unix_ns=0,
        noise_std=np.ones((4, 8)),
        reference_frequency_mhz=400.0,
        dispersion=DispersionState(
            input_dm_pc_cm3=product_dm,
            coherent_correction_pc_cm3=0.0,
            incoherent_correction_pc_cm3=0.0,
            product_dm_pc_cm3=product_dm,
            mode="coherent_anchor_plus_fractional_residual",
        ),
        input_sha256={"raw": "a" * 64},
    )


def test_residual_smearing_uses_absolute_and_product_dm_endpoint_hull() -> None:
    result = residual_smearing_calculation(
        observation(),
        absolute_dm_bounds_pc_cm3=(99.8, 100.3),
        frequency_bin_factor=2,
    )

    assert result["maximum_absolute_residual_dm_pc_cm3"] == pytest.approx(0.3)
    expected = 4148.808 * 0.3 * (796.5**-2 - 798.5**-2)
    assert result["maximum_smearing_s"] == pytest.approx(expected)
    assert result["output_frequency_count"] == 2


def test_residual_smearing_records_exact_product_dm() -> None:
    source = observation()
    source.dispersion = DispersionState(
        input_dm_pc_cm3=100.0,
        coherent_correction_pc_cm3=0.0,
        incoherent_correction_pc_cm3=0.0,
        product_dm_pc_cm3=100.0,
        mode="inferred_raw_input",
    )
    result = residual_smearing_calculation(
        source,
        absolute_dm_bounds_pc_cm3=(99.8, 100.3),
        frequency_bin_factor=2,
    )

    assert result["maximum_absolute_residual_dm_pc_cm3"] == pytest.approx(0.3)
    assert result["product_dm_bounds_pc_cm3"] == [100.0, 100.0]


def test_residual_smearing_rejects_grouping_across_frequency_gap() -> None:
    source = observation()
    gapped = BandObservation(
        instrument=source.instrument,
        waterfall=source.waterfall,
        valid=source.valid,
        frequency_mhz=np.asarray([800.0, 798.0, 797.0, 796.0]),
        channel_width_mhz=source.channel_width_mhz,
        sample_interval_s=source.sample_interval_s,
        time0_unix_ns=source.time0_unix_ns,
        noise_std=source.noise_std,
        reference_frequency_mhz=source.reference_frequency_mhz,
        dispersion=source.dispersion,
        input_sha256=source.input_sha256,
    )
    with pytest.raises(ValueError, match="divisible|gap"):
        residual_smearing_calculation(
            gapped,
            absolute_dm_bounds_pc_cm3=(99.8, 100.3),
            frequency_bin_factor=2,
        )


def test_source_contract_rejects_cross_event_observation_hash(tmp_path) -> None:
    path = tmp_path / "observation.npz"
    waterfall = np.ones((4, 8))
    valid = np.ones((4, 8), dtype=bool)
    frequency = np.asarray([800.0, 799.0, 798.0, 797.0])
    width = np.ones(4)
    noise = np.ones((4, 8))
    off_pulse = np.asarray([True, True, False, False, False, False, True, True])
    np.savez(
        path,
        waterfall=waterfall,
        pixel_valid=valid,
        frequency_mhz=frequency,
        channel_width_mhz=width,
        noise_std=noise,
        noise_estimation_mask=off_pulse,
        sample_interval_s=np.asarray(1.0e-3),
        time0_unix_ns=np.asarray(10, dtype=np.int64),
        frequency_bin_factor=np.asarray(1),
        time_bin_factor=np.asarray(1),
    )
    time_axis = sample_time_axis_ns(
        time0_unix_ns=10,
        sample_interval_s=1.0e-3,
        sample_count=8,
    )
    template = {
        "chime_shape": [4, 8],
        "chime_sample_interval_s": 1.0e-3,
        "chime_frequency_bin_factor": 1,
        "chime_time_bin_factor": 1,
        "chime_frequency_grid_sha256": arrays_sha256(frequency, width),
        "chime_valid_mask_sha256": arrays_sha256(valid),
        "chime_off_pulse_mask_sha256": arrays_sha256(off_pulse),
        "chime_waterfall_sha256": arrays_sha256(waterfall),
        "chime_noise_std_sha256": arrays_sha256(noise),
        "chime_time_axis_sha256": arrays_sha256(time_axis),
        "chime_time0_unix_ns": 10,
    }
    contract = {
        "shape": [4, 8],
        "sample_interval_s": 1.0e-3,
        "frequency_grid_sha256": arrays_sha256(frequency, width),
        "valid_mask_sha256": arrays_sha256(valid),
    }
    diagnostic = {
        "inputs": {"chime_observation": sha256_file(path)},
        "observation_contracts": {"chime": contract},
    }
    validate_source_contract("chime", path, template, diagnostic)

    diagnostic["inputs"]["chime_observation"] = "0" * 64
    with pytest.raises(ValueError, match="differs"):
        validate_source_contract("chime", path, template, diagnostic)
