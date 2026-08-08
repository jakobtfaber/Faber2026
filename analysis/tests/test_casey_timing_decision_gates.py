"""Owner-decision-required timing gates for the Casey DSA anchor.

Encodes the tests demanded by the two 2026-08-03 owner-decision receipts
(`analysis-configs/absolute-dm/decisions/casey-sample-15256-sensitivity.json`
and `casey-trigger-reference-frequency.json`): the exact 98,304 ns discrete
sensitivity shift, the two cold-plasma referral values, the infinite-frequency
coordinate invariance, and fail-closed reference-frequency serialization.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal

import numpy as np
import pytest

from radio_pipeline.fitting import (
    DispersionState,
    load_band_observation_product,
    write_band_observation_product,
)
from radio_pipeline.fitting.products import trigger_anchor_crop_time0_unix_ns

TRIGGER_MJD = "60369.37095221912"
SAMPLE_INTERVAL_S = 32.768e-6
PRODUCT_DM_PC_CM3 = 491.211
PRIMARY_ANCHOR_SAMPLE = 15259
SENSITIVITY_ANCHOR_SAMPLE = 15256
TRIGGER_REFERENCE_FREQUENCY_MHZ = 1530.0
# Owner-decision receipt values (17 significant figures).
REFERRAL_1530_TO_400_S = Decimal("11.866546044944464")
REFERRAL_INFINITY_TO_1530_S = Decimal("0.8705797456055364")
K_DM_S_MHZ2 = Decimal("4148.808")
MJD_UNIX_EPOCH = Decimal("40587")
SECONDS_PER_DAY = Decimal("86400")


def _to_ns(seconds: Decimal) -> int:
    return int((seconds * Decimal("1000000000")).to_integral_value(rounding=ROUND_HALF_EVEN))


@pytest.mark.parametrize("crop_start_sample", [0, 1, 13998, 15259, 30518])
def test_sample_15256_branch_shifts_every_crop_epoch_by_exactly_98304_ns(
    crop_start_sample,
) -> None:
    primary = trigger_anchor_crop_time0_unix_ns(
        TRIGGER_MJD,
        PRIMARY_ANCHOR_SAMPLE,
        crop_start_sample,
        SAMPLE_INTERVAL_S,
        PRODUCT_DM_PC_CM3,
        TRIGGER_REFERENCE_FREQUENCY_MHZ,
    )
    sensitivity = trigger_anchor_crop_time0_unix_ns(
        TRIGGER_MJD,
        SENSITIVITY_ANCHOR_SAMPLE,
        crop_start_sample,
        SAMPLE_INTERVAL_S,
        PRODUCT_DM_PC_CM3,
        TRIGGER_REFERENCE_FREQUENCY_MHZ,
    )
    assert sensitivity - primary == 98_304


def test_sample_15256_branch_changes_only_the_epoch_in_the_product(tmp_path) -> None:
    rng = np.random.default_rng(11)
    values = rng.normal(size=(4, 64))
    valid = np.ones(values.shape, dtype=bool)
    valid[2, 5] = False
    common = {
        "instrument": "dsa",
        "waterfall": values,
        "valid": valid,
        "frequency_mhz": np.array([1311.0, 1400.0, 1450.0, 1498.0]),
        "channel_width_mhz": 0.030517578125,
        "sample_interval_s": SAMPLE_INTERVAL_S,
        "dispersion": DispersionState(0.0, PRODUCT_DM_PC_CM3, 0.0, PRODUCT_DM_PC_CM3, "coherent"),
        "input_sha256": {"raw_fil": "b" * 64},
    }
    epochs = {}
    for name, anchor in (
        ("primary", PRIMARY_ANCHOR_SAMPLE),
        ("sensitivity", SENSITIVITY_ANCHOR_SAMPLE),
    ):
        path = tmp_path / f"{name}.npz"
        write_band_observation_product(
            path,
            time0_unix_ns=trigger_anchor_crop_time0_unix_ns(
                TRIGGER_MJD,
                anchor,
                13998,
                SAMPLE_INTERVAL_S,
                PRODUCT_DM_PC_CM3,
                TRIGGER_REFERENCE_FREQUENCY_MHZ,
            ),
            **common,
        )
        epochs[name] = path
    with (
        np.load(epochs["primary"], allow_pickle=False) as primary,
        np.load(epochs["sensitivity"], allow_pickle=False) as sensitivity,
    ):
        assert set(primary.files) == set(sensitivity.files)
        for field in primary.files:
            if field == "time0_unix_ns":
                assert int(sensitivity[field]) - int(primary[field]) == 98_304
            else:
                assert np.array_equal(primary[field], sensitivity[field]), field


def test_referral_1530_to_400_mhz_is_the_receipt_value() -> None:
    exact = (
        K_DM_S_MHZ2 * Decimal(str(PRODUCT_DM_PC_CM3)) * (Decimal(400) ** -2 - Decimal(1530) ** -2)
    )
    assert abs(exact - REFERRAL_1530_TO_400_S) < Decimal("5e-16")
    with_referral = trigger_anchor_crop_time0_unix_ns(
        TRIGGER_MJD,
        PRIMARY_ANCHOR_SAMPLE,
        0,
        SAMPLE_INTERVAL_S,
        PRODUCT_DM_PC_CM3,
        TRIGGER_REFERENCE_FREQUENCY_MHZ,
    )
    without_referral = trigger_anchor_crop_time0_unix_ns(
        TRIGGER_MJD,
        PRIMARY_ANCHOR_SAMPLE,
        0,
        SAMPLE_INTERVAL_S,
        PRODUCT_DM_PC_CM3,
        400.0,
    )
    assert with_referral - without_referral == _to_ns(exact)


def test_referral_infinity_to_1530_mhz_is_the_receipt_value() -> None:
    exact = K_DM_S_MHZ2 * Decimal(str(PRODUCT_DM_PC_CM3)) * Decimal(1530) ** -2
    # The receipt value is the float64 evaluation of the same formula, which
    # sits one ulp above the correctly rounded exact value; the exact Decimal
    # must agree with it to within 1.2e-16 s (0.12 ns).
    assert float(REFERRAL_INFINITY_TO_1530_S) == 4148.808 * 491.211 / 1530.0**2
    assert abs(exact - REFERRAL_INFINITY_TO_1530_S) < Decimal("1.2e-16")


def test_infinite_frequency_epoch_representation_is_coordinate_invariant() -> None:
    """The invariance demanded by the reference-frequency decision, at the
    epoch layer: an infinite-frequency trigger epoch shifted by exactly the
    receipt's transformation must give the identical 400 MHz nanosecond
    origin as the 1530 MHz representation."""

    via_1530 = trigger_anchor_crop_time0_unix_ns(
        TRIGGER_MJD,
        PRIMARY_ANCHOR_SAMPLE,
        0,
        SAMPLE_INTERVAL_S,
        PRODUCT_DM_PC_CM3,
        TRIGGER_REFERENCE_FREQUENCY_MHZ,
    )
    infinite_frequency_mjd = Decimal(TRIGGER_MJD) - REFERRAL_INFINITY_TO_1530_S / SECONDS_PER_DAY
    via_infinity = _to_ns(
        (infinite_frequency_mjd - MJD_UNIX_EPOCH) * SECONDS_PER_DAY
        + (Decimal(0) - Decimal(PRIMARY_ANCHOR_SAMPLE)) * Decimal(str(SAMPLE_INTERVAL_S))
        + K_DM_S_MHZ2 * Decimal(str(PRODUCT_DM_PC_CM3)) * Decimal(400) ** -2
    )
    assert via_infinity == via_1530


def test_product_load_fails_closed_without_reference_frequency(tmp_path) -> None:
    path = tmp_path / "product.npz"
    write_band_observation_product(
        path,
        instrument="dsa",
        waterfall=np.random.default_rng(3).normal(size=(4, 64)),
        valid=np.ones((4, 64), dtype=bool),
        frequency_mhz=np.array([1311.0, 1400.0, 1450.0, 1498.0]),
        channel_width_mhz=0.030517578125,
        sample_interval_s=SAMPLE_INTERVAL_S,
        time0_unix_ns=1_709_196_861_638_271_101,
        dispersion=DispersionState(0.0, PRODUCT_DM_PC_CM3, 0.0, PRODUCT_DM_PC_CM3, "coherent"),
        input_sha256={"raw_fil": "b" * 64},
    )
    with np.load(path, allow_pickle=False) as archive:
        stripped = {
            field: archive[field] for field in archive.files if field != "reference_frequency_mhz"
        }
    truncated = tmp_path / "no-reference-frequency.npz"
    np.savez_compressed(truncated, **stripped)
    with pytest.raises(ValueError, match="incomplete"):
        load_band_observation_product(truncated)
