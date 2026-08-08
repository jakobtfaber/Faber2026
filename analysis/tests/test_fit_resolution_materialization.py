from __future__ import annotations

import json

import numpy as np
import pytest
from one_event_workflow import arrays_sha256 as workflow_arrays_sha256

from radio_pipeline.fitting import (
    DispersionState,
    load_band_observation_product,
    materialize_fit_resolution,
    resolve_fit_resolution,
)
from radio_pipeline.fitting.products import write_band_observation_product
from radio_pipeline.fitting.resolution import arrays_sha256


def _source(
    tmp_path,
    *,
    name,
    instrument,
    frequency_mhz,
    sample_count=32,
    valid=None,
    offset=0.0,
):
    frequency = np.asarray(frequency_mhz, dtype=float)
    row = np.arange(frequency.size, dtype=float)[:, None]
    time = np.arange(sample_count, dtype=float)[None, :]
    values = (
        offset
        + 0.4 * row
        + np.sin(2.0 * np.pi * time / 7.0)
        + 0.2 * np.cos(2.0 * np.pi * time / 3.0)
    )
    if valid is None:
        valid = np.ones(values.shape, dtype=bool)
    path = tmp_path / f"{name}.npz"
    dispersion = DispersionState(
        input_dm_pc_cm3=100.0,
        coherent_correction_pc_cm3=391.28,
        incoherent_correction_pc_cm3=0.0,
        product_dm_pc_cm3=491.28,
        mode="injected_exactly_once",
    )
    write_band_observation_product(
        path,
        instrument=instrument,
        waterfall=values,
        valid=valid,
        frequency_mhz=frequency,
        channel_width_mhz=1.0,
        sample_interval_s=2.56e-6 if instrument == "chime" else 32.768e-6,
        time0_unix_ns=1_700_000_000_000_000_123,
        dispersion=dispersion,
        input_sha256={"raw": ("1" if instrument == "chime" else "2") * 64},
    )
    return path, dispersion


def test_unequal_band_factors_and_descending_dsa_order(tmp_path) -> None:
    chime_path, _ = _source(
        tmp_path,
        name="chime-high",
        instrument="chime",
        frequency_mhz=[400.5, 401.5, 402.5, 403.5, 404.5, 405.5],
    )
    dsa_path, _ = _source(
        tmp_path,
        name="dsa-high",
        instrument="dsa",
        frequency_mhz=[1503.5, 1502.5, 1501.5, 1500.5],
    )
    chime_out = tmp_path / "chime-fit.npz"
    dsa_out = tmp_path / "dsa-fit.npz"
    chime_receipt = materialize_fit_resolution(
        chime_path,
        chime_out,
        frequency_bin_factor=3,
        time_bin_factor=1,
        minimum_valid_fraction=1.0,
    )
    dsa_receipt = materialize_fit_resolution(
        dsa_path,
        dsa_out,
        frequency_bin_factor=2,
        time_bin_factor=1,
        minimum_valid_fraction=1.0,
    )
    chime = load_band_observation_product(chime_out)
    dsa = load_band_observation_product(dsa_out)

    assert chime.waterfall.shape == (2, 32)
    assert dsa.waterfall.shape == (2, 32)
    assert np.all(np.diff(dsa.frequency_mhz) < 0)
    assert dsa.frequency_mhz.tolist() == pytest.approx([1503.0, 1501.0])
    assert chime_receipt["settings"]["frequency_bin_factor"] == 3
    assert dsa_receipt["settings"]["frequency_bin_factor"] == 2
    assert chime_receipt["status"] == "candidate_fit_grid_pending_resolution_review"


def test_weighted_mean_complete_support_and_noise_reestimation(tmp_path) -> None:
    valid = np.ones((4, 32), dtype=bool)
    valid[1, 16] = False
    source_path, _ = _source(
        tmp_path,
        name="masked",
        instrument="chime",
        frequency_mhz=[400.5, 401.5, 402.5, 403.5],
        valid=valid,
    )
    source = load_band_observation_product(source_path)
    resolved = resolve_fit_resolution(
        source,
        frequency_bin_factor=2,
        time_bin_factor=1,
        minimum_valid_fraction=1.0,
    )
    weights = 1.0 / np.square(source.noise_std[0:2, 15])
    expected = np.sum(source.waterfall[0:2, 15] * weights) / np.sum(weights)
    assert resolved.waterfall[0, 15] == pytest.approx(expected)
    assert resolved.valid[0, 15]
    assert not resolved.valid[0, 16]
    assert resolved.valid_fraction[0, 16] == pytest.approx(0.5)

    output = tmp_path / "masked-fit.npz"
    receipt = materialize_fit_resolution(
        source_path,
        output,
        frequency_bin_factor=2,
        time_bin_factor=1,
        minimum_valid_fraction=1.0,
    )
    with np.load(output, allow_pickle=False) as archive:
        assert "propagated_noise_std" in archive
        assert int(archive["frequency_bin_factor"]) == 2
        assert float(archive["minimum_valid_fraction"]) == 1.0
        assert not archive["pixel_valid"][0, 16]
        assert receipt["proposal"]["waterfall_sha256"] == arrays_sha256(
            archive["waterfall"]
        )
        assert receipt["proposal"]["noise_sha256"] == arrays_sha256(
            archive["noise_std"]
        )
    assert np.isfinite(
        receipt["proposal"]["reestimated_to_propagated_noise_ratio_median"]
    )
    assert receipt["proposal"]["propagated_noise_sha256"]


def test_time_origin_analytic_oracle_and_time_averaging_rejected(tmp_path) -> None:
    source_path, _ = _source(
        tmp_path,
        name="timing",
        instrument="chime",
        frequency_mhz=[400.5, 401.5],
    )
    source = load_band_observation_product(source_path)
    resolved = resolve_fit_resolution(
        source,
        frequency_bin_factor=1,
        time_bin_factor=1,
        minimum_valid_fraction=1.0,
    )
    assert resolved.time0_unix_ns == source.time0_unix_ns
    assert resolved.sample_interval_s == source.sample_interval_s
    with pytest.raises(ValueError, match="likelihood integrates bin duration"):
        resolve_fit_resolution(
            source,
            frequency_bin_factor=1,
            time_bin_factor=2,
            minimum_valid_fraction=1.0,
        )
    with pytest.raises(ValueError, match="exactly one"):
        resolve_fit_resolution(
            source,
            frequency_bin_factor=1,
            time_bin_factor=1,
            minimum_valid_fraction=0.8,
        )


def test_frequency_runs_never_cross_gaps_and_require_exact_divisibility(tmp_path) -> None:
    divisible_path, _ = _source(
        tmp_path,
        name="gapped-divisible",
        instrument="chime",
        frequency_mhz=[400.5, 401.5, 410.5, 411.5],
    )
    divisible = load_band_observation_product(divisible_path)
    resolved = resolve_fit_resolution(
        divisible,
        frequency_bin_factor=2,
        time_bin_factor=1,
        minimum_valid_fraction=1.0,
    )
    assert resolved.frequency_mhz.tolist() == pytest.approx([401.0, 411.0])
    assert resolved.channel_width_mhz.tolist() == pytest.approx([2.0, 2.0])

    indivisible_path, _ = _source(
        tmp_path,
        name="gapped-indivisible",
        instrument="chime",
        frequency_mhz=[400.5, 401.5, 402.5, 410.5, 411.5, 412.5],
    )
    indivisible = load_band_observation_product(indivisible_path)
    with pytest.raises(ValueError, match="contiguous frequency run"):
        resolve_fit_resolution(
            indivisible,
            frequency_bin_factor=2,
            time_bin_factor=1,
            minimum_valid_fraction=1.0,
        )


def test_dispersion_and_raw_hashes_preserved_exactly(tmp_path) -> None:
    source_path, dispersion = _source(
        tmp_path,
        name="dispersion",
        instrument="dsa",
        frequency_mhz=[1501.5, 1500.5],
    )
    output = tmp_path / "dispersion-fit.npz"
    materialize_fit_resolution(
        source_path,
        output,
        frequency_bin_factor=1,
        time_bin_factor=1,
        minimum_valid_fraction=1.0,
    )
    source = load_band_observation_product(source_path)
    fit = load_band_observation_product(output)
    assert fit.dispersion == dispersion
    assert fit.input_sha256 == source.input_sha256
    with np.load(output, allow_pickle=False) as archive:
        assert str(archive["source_observation_sha256"])
        assert str(archive["source_frequency_grid_sha256"])


def test_array_hash_convention_and_receipts_drift_with_source_or_factor(tmp_path) -> None:
    first_path, _ = _source(
        tmp_path,
        name="first",
        instrument="chime",
        frequency_mhz=[400.5, 401.5, 402.5, 403.5],
    )
    second_path, _ = _source(
        tmp_path,
        name="second",
        instrument="chime",
        frequency_mhz=[400.5, 401.5, 402.5, 403.5],
        offset=0.03,
    )
    first = load_band_observation_product(first_path)
    assert arrays_sha256(first.waterfall, first.valid) == workflow_arrays_sha256(
        first.waterfall,
        first.valid,
    )
    receipts = []
    for index, (source, factor) in enumerate(
        ((first_path, 1), (first_path, 2), (second_path, 1), (first_path, 1))
    ):
        receipts.append(
            materialize_fit_resolution(
                source,
                tmp_path / f"fit-{index}.npz",
                frequency_bin_factor=factor,
                time_bin_factor=1,
                minimum_valid_fraction=1.0,
            )
        )
    bindings = {
        receipt["proposal"]["arrays_and_settings_sha256"] for receipt in receipts[:3]
    }
    assert len(bindings) == 3
    assert (
        receipts[0]["proposal"]["arrays_and_settings_sha256"]
        == receipts[3]["proposal"]["arrays_and_settings_sha256"]
    )
    assert receipts[0]["source"]["sha256"] != receipts[2]["source"]["sha256"]
    with np.load(tmp_path / "fit-1.npz", allow_pickle=False) as archive:
        source_hashes = json.loads(str(archive["input_sha256_json"]))
    assert source_hashes == first.input_sha256
