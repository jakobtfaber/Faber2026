import numpy as np
import pytest

from dispersion.chime_dm import K_DM
from dispersion.dm_campaign.adapters import _measure_dm_phase_published
from dispersion.dm_joint_phase import (
    fit_surface,
    gaussian_joint_fit,
    phase_surface,
    product_dm_from_filename,
)


def _injection(residual_dm: float, *, seed: int = 0):
    rng = np.random.default_rng(seed)
    frequency = np.linspace(400.0, 800.0, 96)
    dt = 2.0e-5
    time = np.arange(2048) * dt
    delay = K_DM * residual_dm * (frequency**-2 - frequency.max() ** -2)
    waterfall = np.exp(-0.5 * ((time[None, :] - 0.020 - delay[:, None]) / 8.0e-5) ** 2)
    waterfall += 0.12 * rng.standard_normal(waterfall.shape)
    return waterfall, frequency, dt


def test_product_dm_uses_full_filename_precision():
    assert product_dm_from_filename("casey_chime_I_491_2085_32000b_cntr_bpc.npy") == 491.2085
    assert product_dm_from_filename("casey_dsa_I_491_211_2500b_cntr_bpc.npy") == 491.211


def test_phase_surface_recovers_physical_residual():
    waterfall, frequency, dt = _injection(0.36)
    grid = np.arange(-0.2, 0.8, 0.01)
    result = fit_surface(
        phase_surface(waterfall, frequency, dt, grid, high_hz=5000.0),
        cutoff_candidates_hz=(1000.0, 2500.0, 5000.0),
    )
    assert result.dm == pytest.approx(0.36, abs=0.03)
    assert 0 < result.sigma_jackknife < 0.1


def test_peak_matches_released_dm_phase():
    waterfall, frequency, dt = _injection(0.36, seed=8)
    grid = np.arange(-0.2, 0.8, 0.01)
    controlled = fit_surface(
        phase_surface(waterfall, frequency, dt, grid, high_hz=5000.0),
        cutoff_candidates_hz=(1000.0, 2500.0, 5000.0),
    )
    released = _measure_dm_phase_published(
        waterfall,
        frequency,
        dt,
        0.0,
        1.0,
    )
    assert released.dm is not None
    assert controlled.dm == pytest.approx(released.dm, abs=0.05)


def test_joint_fit_lands_between_consistent_bands():
    result = gaussian_joint_fit(491.20, 0.03, 491.24, 0.04)
    assert 491.20 < result["dm"] < 491.24
    assert result["sigma"] > 0
    assert result["tension_sigma"] < 1
    assert result["between_band_sigma"] == 0


def test_joint_fit_adds_between_band_systematic_when_needed():
    result = gaussian_joint_fit(610.289, 0.005, 610.233, 0.007)
    assert 610.25 < result["dm"] < 610.275
    assert result["between_band_sigma"] > 0
    assert result["joint_q"] == pytest.approx(1.0)
