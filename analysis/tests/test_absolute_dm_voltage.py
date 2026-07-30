from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from scripts.one_event_hybrid_dm import injected_absolute_dm_recovery

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/absolute_dm_voltage.py"
SPEC = importlib.util.spec_from_file_location("absolute_dm_voltage", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_absolute_interface_subtracts_input_coordinate_once() -> None:
    assert MODULE.differential_dm(491.25, 491.0) == pytest.approx(0.25)


def test_absolute_interface_rejects_nonfinite_values() -> None:
    with pytest.raises(ValueError, match="finite"):
        MODULE.differential_dm(np.nan, 0.0)


def test_package_argument_preserves_physical_phase_scale() -> None:
    target = 500.0
    package_constant = 4149.377593360996
    argument = MODULE.package_dm_argument(
        target,
        0.0,
        package_dispersion_constant=package_constant,
    )
    assert package_constant * argument == pytest.approx(
        MODULE.K_DM_S_MHZ2 * target,
        abs=1.0e-10,
    )


def test_h5_package_dm_attribute_maps_to_physical_phase_coordinate() -> None:
    package_constant = 4149.377593360996
    physical = MODULE.physical_dm_from_package_coordinate(
        491.2,
        package_dispersion_constant=package_constant,
    )
    assert physical * MODULE.K_DM_S_MHZ2 == pytest.approx(491.2 * package_constant)


def test_fine_frequency_centres_follow_authoritative_h5_centres() -> None:
    frequency_id = np.asarray([3, 4], dtype=np.int64)
    frequency_mhz = np.asarray([798.828125, 798.4375])

    fine = MODULE.authoritative_fine_frequency_centres(
        frequency_id,
        frequency_mhz,
        16,
    ).reshape(2, 16)

    fft_bin = np.arange(-16, 16, dtype=float)
    grouped_fft_bin_centres = fft_bin.reshape(16, 2).mean(axis=1)
    expected_offsets = -grouped_fft_bin_centres * 0.390625 / 32.0
    np.testing.assert_allclose(fine[0], frequency_mhz[0] + expected_offsets)
    np.testing.assert_allclose(
        fine.mean(axis=1),
        frequency_mhz + 0.390625 / 64.0,
        atol=1.0e-12,
    )
    np.testing.assert_allclose(np.diff(fine[0]), -0.390625 / 16.0)
    assert fine[0, -1] - fine[1, 0] == pytest.approx(0.390625 / 16.0)


def test_fine_frequency_centres_preserve_authoritative_h5_id_gaps() -> None:
    frequency_id = np.asarray([3, 5, 37], dtype=np.int64)
    frequency_mhz = 800.0 - 0.390625 * frequency_id

    fine = MODULE.authoritative_fine_frequency_centres(
        frequency_id,
        frequency_mhz,
        16,
    ).reshape(3, 16)

    assert fine[0, -1] - fine[1, 0] == pytest.approx(
        (frequency_id[1] - frequency_id[0] - 1) * 0.390625
        + 0.390625 / 16.0
    )
    assert fine[1, -1] - fine[2, 0] == pytest.approx(
        (frequency_id[2] - frequency_id[1] - 1) * 0.390625
        + 0.390625 / 16.0
    )


def test_nonzero_h5_dm0_is_subtracted_once_by_coherent_pipeline() -> None:
    package_constant = 4149.377593360996
    package_input_dm = 491.2
    target_physical_dm = 491.28
    input_physical_dm = MODULE.physical_dm_from_package_coordinate(
        package_input_dm,
        package_dispersion_constant=package_constant,
    )
    package_target = MODULE.package_dm_argument(
        target_physical_dm,
        0.0,
        package_dispersion_constant=package_constant,
    )
    applied_physical_correction = (
        package_constant * (package_target - package_input_dm) / MODULE.K_DM_S_MHZ2
    )
    assert applied_physical_correction == pytest.approx(
        target_physical_dm - input_physical_dm,
        abs=1.0e-12,
    )


def _fourier_shift(signal: np.ndarray, sample_shift: float) -> np.ndarray:
    frequency = np.fft.fftfreq(signal.size)
    return np.fft.ifft(np.fft.fft(signal) * np.exp(-2j * np.pi * frequency * sample_shift))


def test_injected_dispersed_voltage_recovers_dm_exactly_once() -> None:
    package_constant = 4149.377593360996
    physical_constant = MODULE.K_DM_S_MHZ2
    injected_dm = 0.36
    sample_time_s = 2.56e-6
    frequency_mhz = np.linspace(410.0, 790.0, 48)
    sample = np.arange(4096)
    pulse = np.exp(-0.5 * ((sample - 2048.0) / 11.0) ** 2).astype(complex)
    delay_s = physical_constant * injected_dm * (frequency_mhz**-2 - 400.0**-2)
    dispersed = np.asarray([_fourier_shift(pulse, delay / sample_time_s) for delay in delay_s])

    def score(target_total_dm: float, applications: int = 1) -> float:
        argument = MODULE.package_dm_argument(
            target_total_dm,
            0.0,
            package_dispersion_constant=package_constant,
        )
        correction_s = package_constant * argument * (frequency_mhz**-2 - 400.0**-2)
        recovered = np.asarray(
            [
                _fourier_shift(row, -applications * shift / sample_time_s)
                for row, shift in zip(dispersed, correction_s, strict=True)
            ]
        )
        return float(np.max(np.abs(np.sum(recovered, axis=0)) ** 2))

    grid = np.arange(0.20, 0.521, 0.01)
    recovered_dm = float(grid[np.argmax([score(dm) for dm in grid])])
    assert recovered_dm == pytest.approx(injected_dm, abs=1.0e-12)
    assert score(injected_dm) > 10.0 * score(injected_dm, applications=2)


def test_hybrid_campaign_injection_uses_input_anchor_total_identity() -> None:
    result = injected_absolute_dm_recovery(
        491.28,
        491.211,
        81.92e-6,
        0.005,
    )
    assert result["passed"] is True
    identity = result["exactly_once_identity"]
    assert identity["reconstructed_trial_dm_pc_cm3"] == pytest.approx(
        result["injected_absolute_dm_pc_cm3"]
    )


def test_frequency_map_preserves_h5_identity() -> None:
    order = MODULE.validate_frequency_map(
        np.array([12, 10, 11], dtype=np.uint32),
        np.array([500.0, 400.0, 450.0]),
        3,
    )
    np.testing.assert_array_equal(order, [1, 2, 0])


def test_frequency_map_rejects_duplicate_ids() -> None:
    with pytest.raises(ValueError, match="unique"):
        MODULE.validate_frequency_map(
            np.array([1, 1]),
            np.array([400.0, 401.0]),
            2,
        )


def test_trusted_rfi_mask_replays_strict_noise_window_and_thresholds() -> None:
    intensity = np.tile(np.array([0.0, 0.0, 1.0, 2.0, 1.0, 0.0, 1.0, 2.0]), (3, 1))
    intensity[0, 4] = 100.0
    intensity[1, 4] = -100.0
    keep, audit = MODULE.trusted_notebook_rfi_mask(
        intensity,
        time_limits=(0, 4),
        rfi_limits=(10.0, -10.0),
    )
    np.testing.assert_array_equal(keep, [False, False, True])
    assert audit["noise_sample_count"] == 3


def test_full_grid_mask_maps_by_integer_channel_id() -> None:
    full = np.array([True, False, True, False], dtype=bool)
    np.testing.assert_array_equal(
        MODULE.map_full_grid_mask_to_h5(
            full,
            np.array([2, 0, 3], dtype=np.uint32),
        ),
        [True, True, False],
    )


def test_nonwrapping_placement_does_not_wrap_edges() -> None:
    values = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    placed, _ = MODULE.nonwrapping_row_placement(
        values,
        np.array([400.0, 800.0]),
        np.array([0.0, 0.0]),
        1.0e-3,
        0.1,
    )
    assert placed.shape[1] > values.shape[1]
    assert np.isnan(placed[0, -1])
    assert np.isnan(placed[1, 0])
    np.testing.assert_allclose(placed[0, :3], values[0])
    np.testing.assert_allclose(placed[1, -3:], values[1])


def test_fixed_crop_fails_closed_at_edge() -> None:
    with pytest.raises(ValueError, match="extends"):
        MODULE.fixed_peak_crop(np.ones((2, 10)), center=1, width=6)
