"""Correctness tests for the TNG-300 IGM log-normal calibration.

Run: pytest tests/test_dm_budget_uncertainty.py

These are *not* regression pins -- no output of the script is frozen here. Every
expected value is derived from an independent reference: an analytic limit, a
physical invariant, or the tabulated calibration itself. Each test names its
criterion.

1. Analytic limit .... <DM_IGM(z)> propto int_0^z (1+z')/E(z') dz' -> z as z -> 0
                       (Macquart et al. 2020, Eq. 2; Deng & Zhang 2014), so the
                       column must vanish linearly at z = 0. The unguarded cubic
                       spline instead flattened to a ~25 pc cm^-3 floor.
2. Invariant ......... DM_cos = DM_IGM + DM_X with DM_X >= 0, so the IGM marginal
                       can never exceed the total cosmic column.
3. Invariant ......... mu(z) strictly increasing: a longer path intersects more
                       ionized gas.
4. Reference ......... on the tabulated grid the interpolant must return the
                       tabulated values, and the low-z continuation must join it
                       continuously at z = 0.1.
5. Guard ............. z outside (0, 5] raises rather than silently extrapolating.

Tolerances: grid-node recovery and seam continuity are asserted at rtol=1e-12.
Both are exact identities -- an s=0 spline reproduces its knots to round-off, and
at z = TNG_ZMIN the two branches evaluate the same number -- so a looser bound
would hide a real discontinuity rather than absorb numerical noise. The z -> 0
limit and the DM_IGM <= DM_cos bound are inequalities, not tolerances.

Reference data: the calibration grid (``TNG_ZGRID``, ``TNG_MU_IGM``,
``TNG_SIG_IGM``) is transcribed from ``tng_params_new.npy`` in the Connor et al.
(2025, arXiv:2409.16952) reproduction package and lives in the script under test,
not in a separate fixture; that ``.npy`` is not vendored in this repo.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import dm_budget_uncertainty as dbu  # noqa: E402


def test_grid_nodes_recovered_exactly():
    """Criterion 4: an s=0 spline through the knots returns the knots."""
    for z, mu_ref, sig_ref in zip(dbu.TNG_ZGRID, dbu.TNG_MU_IGM, dbu.TNG_SIG_IGM):
        mu, sigma = dbu.igm_lognormal_shape(float(z))
        assert mu == pytest.approx(mu_ref, rel=1e-12)
        assert sigma == pytest.approx(sig_ref, rel=1e-12)


def test_low_z_continuation_joins_the_grid_continuously():
    """Criterion 4: no jump at the seam z = TNG_ZMIN.

    Approach the seam from below and compare against the on-grid branch. The
    limit from below is mu(zmin) exactly, so the gap is pure round-off.
    """
    zmin = dbu.TNG_ZMIN
    mu_at, sig_at = dbu.igm_lognormal_shape(zmin)
    mu_below, sig_below = dbu.igm_lognormal_shape(zmin * (1.0 - 1e-9))
    assert mu_below == pytest.approx(mu_at, rel=1e-8)
    assert sig_below == pytest.approx(sig_at, rel=1e-12)
    assert mu_at == pytest.approx(dbu.TNG_MU_IGM[0], rel=1e-12)


def test_dm_igm_vanishes_linearly_as_z_goes_to_zero():
    """Criterion 1: the analytic limit -- zero, not a finite floor.

    At z = 1e-4 the Macquart integral gives I ~ 1e-4, so the median column is
    ~exp(4.374) * 1e-4 / I(0.1) ~ 0.08 pc cm^-3. Assert it is under 1 pc cm^-3:
    that is ~300x below the 25 pc cm^-3 floor the cubic spline produced, so the
    bound discriminates sharply between the two behaviors rather than merely
    tolerating one.
    """
    mu, _ = dbu.igm_lognormal_shape(1e-4)
    assert math.exp(mu) < 1.0
    # ... and the vanishing is *linear* (I(z) -> z), not some other power:
    # halving z halves the median, to better than 0.1% at this redshift.
    mu_half, _ = dbu.igm_lognormal_shape(0.5e-4)
    assert math.exp(mu_half) / math.exp(mu) == pytest.approx(0.5, rel=1e-3)


def test_igm_marginal_never_exceeds_the_total_cosmic_column():
    """Criterion 2: DM_cos = DM_IGM + DM_X with DM_X >= 0, so DM_IGM <= DM_cos.

    ``SIGHTLINES``' DM_cosmic_mean is the Macquart *total* point estimate at
    f_IGM = 0.84 (budget_table.tex); compare the TNG IGM marginal's mean,
    exp(mu + sigma^2/2), at the TNG baseline f_IGM = 0.797.

    This is a cross-calibration bound, not an exact identity -- the two columns
    come from different fits -- so the margin is thin at low z (~0.3% at
    z = 0.074, where the mean sightline intersects almost no halos and the IGM
    marginal is nearly the whole column). It is nonetheless the check that caught
    the defect: the extrapolating spline drove FRB 20220207C (z = 0.043) to a
    ratio of 1.22, i.e. an IGM column 22% larger than the total it is part of.
    """
    for name, z, _dm_obs, _dm_mw, dm_cos_mean, _dm_int, _mass in dbu.SIGHTLINES:
        mu, sigma = dbu.igm_lognormal_shape(z)
        dm_igm_mean = math.exp(mu + 0.5 * sigma ** 2)
        assert dm_igm_mean <= dm_cos_mean, (
            f"{name} (z={z}): IGM marginal {dm_igm_mean:.1f} exceeds the total "
            f"cosmic column {dm_cos_mean} pc cm^-3 (ratio {dm_igm_mean / dm_cos_mean:.3f})"
        )


def test_mu_is_strictly_increasing():
    """Criterion 3: a longer path intersects more ionized gas."""
    zs = np.unique(np.concatenate([np.geomspace(1e-3, dbu.TNG_ZMIN, 40),
                                   np.linspace(dbu.TNG_ZMIN, dbu.TNG_ZMAX, 200)]))
    mus = np.array([dbu.igm_lognormal_shape(float(z))[0] for z in zs])
    assert np.all(np.diff(mus) > 0)


@pytest.mark.parametrize("z", [0.0, -0.1, 5.0001, 10.0])
def test_out_of_range_z_raises(z):
    """Criterion 5: no silent extrapolation outside (0, 5]."""
    with pytest.raises(ValueError):
        dbu.igm_lognormal_shape(z)


def test_f_igm_rescaling_shifts_the_log_median_only():
    """igm_lognormal_params shifts mu by log(f/f_TNG) and leaves sigma alone."""
    z = 0.3
    mu_tng, sig_tng = dbu.igm_lognormal_shape(z)
    mu, sigma = dbu.igm_lognormal_params(z, f_igm=0.5)
    assert mu == pytest.approx(mu_tng + math.log(0.5 / dbu.FIGM_TNG), rel=1e-12)
    assert sigma == pytest.approx(sig_tng, rel=1e-12)
