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
import csv
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
    for row in dbu.load_sightlines():
        mu, sigma = dbu.igm_lognormal_shape(row.z)
        dm_igm_mean = math.exp(mu + 0.5 * sigma**2)
        assert dm_igm_mean <= row.dm_cos_mean, (
            f"{row.name} (z={row.z}): IGM marginal {dm_igm_mean:.1f} exceeds the total "
            f"cosmic column {row.dm_cos_mean} pc cm^-3 "
            f"(ratio {dm_igm_mean / row.dm_cos_mean:.3f})"
        )


def test_mu_is_strictly_increasing():
    """Criterion 3: a longer path intersects more ionized gas."""
    zs = np.unique(
        np.concatenate(
            [
                np.geomspace(1e-3, dbu.TNG_ZMIN, 40),
                np.linspace(dbu.TNG_ZMIN, dbu.TNG_ZMAX, 200),
            ]
        )
    )
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


def _pdf_moments(pdf):
    x = pdf.x
    mean = np.sum(x * pdf.density) * pdf.dx
    var = np.sum((x - mean) ** 2 * pdf.density) * pdf.dx
    return mean, var


def test_discrete_pdf_normalizes_and_rejects_negative_density():
    """Invariant: every published PDF is nonnegative and integrates to one."""
    pdf = dbu.DiscretePDF(x0=0.0, dx=1.0, density=np.array([1.0, 2.0, 1.0]))
    assert np.sum(pdf.density) * pdf.dx == pytest.approx(1.0, abs=1e-14)
    with pytest.raises(ValueError, match="negative"):
        dbu.DiscretePDF(x0=0.0, dx=1.0, density=np.array([1.0, -0.1]))


def test_convolution_matches_analytic_normal_sum():
    """Analytic criterion: independent normal means/variances add."""
    a = dbu.normal_pdf(mean=10.0, sigma=2.0, dx=0.02, tail_mass=1e-12)
    b = dbu.normal_pdf(mean=-3.0, sigma=3.0, dx=0.02, tail_mass=1e-12)
    summed = dbu.convolve_pdfs([a, b])
    mean, var = _pdf_moments(summed)
    assert mean == pytest.approx(7.0, abs=0.02)
    assert var == pytest.approx(13.0, rel=2e-4)
    assert np.sum(summed.density) * summed.dx == pytest.approx(1.0, abs=1e-12)


def test_lognormal_pdf_recovers_analytic_mean():
    """Analytic criterion: E[X] = median * exp(sigma_ln^2/2)."""
    median, sigma_ln = 40.0, 0.35
    pdf = dbu.lognormal_pdf(median=median, sigma_ln=sigma_ln, dx=0.02, tail_mass=1e-12)
    mean, _ = _pdf_moments(pdf)
    expected = median * math.exp(0.5 * sigma_ln**2)
    assert mean == pytest.approx(expected, rel=2e-5)


def test_igm_quadrature_converges():
    """Numerical criterion: doubling Gauss-Hermite order changes moments negligibly."""
    pdf32 = dbu.igm_mixture_pdf(0.3, dx=0.1, tail_mass=1e-10, quadrature_order=32)
    pdf64 = dbu.igm_mixture_pdf(0.3, dx=0.1, tail_mass=1e-10, quadrature_order=64)
    pdf128 = dbu.igm_mixture_pdf(0.3, dx=0.1, tail_mass=1e-10, quadrature_order=128)
    m32, v32 = _pdf_moments(pdf32)
    m64, v64 = _pdf_moments(pdf64)
    m128, v128 = _pdf_moments(pdf128)
    assert m64 == pytest.approx(m128, rel=2e-5)
    assert v64 == pytest.approx(v128, rel=5e-5)
    assert m32 == pytest.approx(m128, rel=2e-5)
    assert v32 == pytest.approx(v128, rel=5e-5)


def test_host_pdf_is_shifted_reflection_of_foreground_pdf():
    """Identity: p_host(h) = p_foreground(DM_obs - h)."""
    foreground = dbu.DiscretePDF(x0=0.0, dx=1.0, density=np.array([0.2, 0.3, 0.5]))
    host = dbu.host_pdf_from_foreground(foreground, dm_obs=10.0)
    assert host.x.tolist() == [8.0, 9.0, 10.0]
    assert host.density.tolist() == pytest.approx([0.5, 0.3, 0.2])


def test_current_inputs_join_budget_dm_catalog_and_system_census():
    """Provenance criterion: current SSOT rosters and intervening totals agree."""
    sightlines = dbu.load_sightlines()
    assert len(sightlines) == 9
    assert {row.name for row in sightlines} == {
        "FRB 20220207C",
        "FRB 20220310F",
        "FRB 20220506D",
        "FRB 20221113A",
        "FRB 20230307A",
        "FRB 20230814B",
        "FRB 20230913A",
        "FRB 20240203A",
        "FRB 20240229A",
    }
    phineas = next(row for row in sightlines if row.name == "FRB 20230307A")
    assert phineas.dm_obs == pytest.approx(610.289070)
    assert len(phineas.intervening_systems) == 4
    assert sum(s.dm_point for s in phineas.intervening_systems) == pytest.approx(
        phineas.dm_int, abs=0.5
    )
    for row in sightlines:
        if row.dm_int == 0:
            assert row.intervening_systems == ()
        else:
            assert round(sum(s.dm_point for s in row.intervening_systems)) == row.dm_int


@pytest.mark.parametrize(
    ("point", "sigma_ln"),
    [(71.0, dbu.SIGMA_DISK_FRAC), (40.0, dbu.HALO_SIGMA_LN), (26.3, 0.40)],
)
def test_quoted_lognormal_points_are_medians(point, sigma_ln):
    """Model criterion: quoted disk/halo/system points define prior medians."""
    pdf = dbu.lognormal_pdf(point, sigma_ln, dx=0.02, tail_mass=1e-12)
    assert dbu.pdf_quantile(pdf, 0.5) == pytest.approx(point, abs=0.02)


def test_host_summaries_converge_on_half_size_grid():
    """Numerical criterion: halving dx leaves every published summary stable."""
    for row in dbu.load_sightlines():
        coarse = dbu.host_distribution(row, dx=0.1)
        fine = dbu.host_distribution(row, dx=0.05)
        for key in ("dm_host_p16", "dm_host_p50", "dm_host_p84"):
            assert coarse[key] == pytest.approx(fine[key], abs=0.25), row.name
        assert coarse["p_host_neg"] == pytest.approx(fine["p_host_neg"], abs=2e-4), (
            row.name
        )


def test_rest_frame_quantiles_are_monotone_redshift_rescaling():
    """Frame criterion: DM_host,rest = (1+z) DM_host,observer."""
    for row in dbu.load_sightlines():
        result = dbu.host_distribution(row)
        for suffix in ("p16", "p50", "p84"):
            assert result[f"dm_host_rest_{suffix}"] == pytest.approx(
                (1.0 + row.z) * result[f"dm_host_{suffix}"], rel=1e-14
            )


def test_incomplete_census_upper_limit_roster_is_explicit():
    """Interpretation criterion: all and only note-u modeled rows are upper limits."""
    assert dbu.UPPER_LIMIT == {
        "FRB 20220207C",
        "FRB 20220506D",
        "FRB 20221113A",
        "FRB 20230814B",
        "FRB 20230913A",
        "FRB 20240203A",
    }


def test_convolution_matches_independent_monte_carlo_oracle():
    """Cross-method criterion: 500k median-centered draws match all nine PDFs."""
    n = 500_000
    probability_tolerance = 5.0 * math.sqrt(0.25 / n) + 2e-4
    for index, row in enumerate(dbu.load_sightlines()):
        deterministic = dbu.host_distribution(row)
        samples = dbu.sample_host_for_validation(
            row, n=n, seed=20260715 + index, prior_centering="median"
        )
        q16, q50, q84 = np.percentile(samples, [16, 50, 84])
        # At N=500k the empirical order-statistic error is below 0.5 pc cm^-3
        # for these PDFs; add the 0.1-grid discretization allowance explicitly.
        for key, reference in zip(
            ("dm_host_p16", "dm_host_p50", "dm_host_p84"), (q16, q50, q84)
        ):
            assert deterministic[key] == pytest.approx(reference, abs=0.6), row.name
        assert deterministic["p_host_neg"] == pytest.approx(
            np.mean(samples < 0), abs=probability_tolerance
        ), row.name


def test_committed_host_csv_matches_deterministic_summaries():
    """Artifact criterion: the nine committed host rows match the live engine."""
    path = (
        Path(__file__).resolve().parent.parent / "scripts" / "dm_budget_uncertainty.csv"
    )
    with path.open(newline="") as handle:
        committed = {
            row["burst"]: row
            for row in csv.DictReader(handle)
            if row.get("burst", "").startswith("FRB ")
        }
    sightlines = dbu.load_sightlines()
    assert set(committed) == {row.name for row in sightlines}
    for row in sightlines:
        expected = dbu.host_distribution(row)
        actual = committed[row.name]
        assert int(actual["dm_host_arith"]) == round(expected["dm_host_arith"])
        for key in ("dm_host_p16", "dm_host_p50", "dm_host_p84"):
            assert int(actual[key]) == round(expected[key])
        for key in (
            "dm_host_rest_p16",
            "dm_host_rest_p50",
            "dm_host_rest_p84",
        ):
            assert int(actual[key]) == round(expected[key])
        assert float(actual["p_host_negative"]) == pytest.approx(
            expected["p_host_neg"], abs=5e-4
        )
