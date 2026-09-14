"""Independent deterministic oracles; no sampler or burst-data access."""
import mpmath as mp
import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import norm

from scattering.scat_analysis.burstfit import FRBParams
from scattering.scat_analysis.burstfit_joint import _gain_marginal_multi_band_impl


class MatrixModel:
    def __init__(self, k, d, sigma=1.0):
        self.k = np.asarray(k, dtype=float)
        self.data = np.asarray(d, dtype=float)[None, :]
        self.noise_std = np.array([sigma])
        self.valid = np.array([True])

    def __call__(self, params, key, freq_subset):
        return self.k[:, int(key)][None, :]


def evaluate(k, d, s2, sigma=1.0):
    model = MatrixModel(k, d, sigma)
    n = model.k.shape[1]
    return _gain_marginal_multi_band_impl(
        model, [FRBParams(c0=1., t0=0., gamma=0.)] * n, [str(i) for i in range(n)],
        s2=s2,
    )


def covariance_oracle(k, d, s2, sigma):
    covariance = sigma**2 * np.eye(len(d)) + s2 * k @ k.T
    solved = np.linalg.solve(covariance, d)
    logdet = np.linalg.slogdet(covariance)[1]
    return (-0.5 * (d @ solved + logdet + len(d) * np.log(2 * np.pi)),
            s2 * k.T @ solved)


@pytest.mark.parametrize('k', [
    np.array([[1., .2], [.3, 1.], [.1, .4]]),
    np.array([[1., 1.], [2., 2.], [3., 3.]]),
    np.array([[1., 1.], [2., 2.00001], [3., 3.]]),
    np.zeros((3, 2)),
    np.array([[1., 0., 1.], [0., 1., 1.]]),
])
@pytest.mark.parametrize('s2', [1e-8, 1., 1e4])
def test_covariance_and_posterior_mean(k, s2):
    d = np.arange(k.shape[0], dtype=float) + .4
    actual, _, gains = evaluate(k, d, s2, sigma=.7)
    expected, expected_gains = covariance_oracle(k, d, s2, .7)
    np.testing.assert_allclose(actual, expected, atol=1e-8, rtol=0)
    np.testing.assert_allclose(gains[0], expected_gains, atol=1e-8, rtol=0)


def test_audit_counterexample_and_diagnostic_threshold_invariance():
    k = np.diag([1., 1e-4])
    d = np.array([0., 100.])
    expected, expected_gain = covariance_oracle(k, d, 1e12, 1.)
    model = MatrixModel(k, d)
    params = [FRBParams(c0=1., t0=0., gamma=0.)] * 2
    for floor in [0., 1e-6, 1.]:
        actual, _, gain = _gain_marginal_multi_band_impl(
            model, params, ["0", "1"], s2=1e12, eig_rel_floor=floor,
        )
        np.testing.assert_allclose(actual, expected, atol=1e-8, rtol=0)
        np.testing.assert_allclose(gain[0], expected_gain, atol=1e-8, rtol=0)


@pytest.mark.parametrize('small', [0., 1e-20, 1e-8, .0009999, .001, .0010001])
def test_old_cutoffs_and_broad_prior(small):
    k = np.diag([1., small])
    d = np.array([2., 100.])
    actual, _, _ = evaluate(k, d, 1e40)
    expected, _ = covariance_oracle(k, d, 1e40, 1.)
    np.testing.assert_allclose(actual, expected, atol=1e-8, rtol=0)


def test_scalar_gain_integral():
    k = np.array([[.4], [1.2]])
    d = np.array([.2, -.8])
    s2 = 1.7
    sigma = .6
    integral, _ = quad(lambda g: norm.pdf(g, scale=np.sqrt(s2)) *
                       np.prod(norm.pdf(d, loc=k[:, 0] * g, scale=sigma)),
                       -np.inf, np.inf, epsabs=1e-12)
    actual, _, _ = evaluate(k, d, s2, sigma)
    np.testing.assert_allclose(actual, np.log(integral), atol=1e-8, rtol=0)


def test_template_units_and_large_variance_penalty():
    k = np.diag([1., .5])
    d = np.array([.3, -.2])
    base, _, gain = evaluate(k, d, 1e8)
    scaled, _, scaled_gain = evaluate(k * 10, d, 1e6)
    np.testing.assert_allclose(base, scaled, atol=1e-8, rtol=0)
    np.testing.assert_allclose(gain, scaled_gain * 10, atol=1e-8, rtol=0)
    broad, _, _ = evaluate(k, d, 1e10)
    np.testing.assert_allclose(broad - base, -np.log(100), atol=1e-7, rtol=0)


@pytest.mark.parametrize('s2', [0., -1., np.inf, np.nan])
def test_invalid_prior_variance(s2):
    with pytest.raises(ValueError, match='finite and positive'):
        evaluate(np.eye(2), [1., 2.], s2)


@pytest.mark.parametrize("s2", [None, 1e-6, 1e6])
def test_multichannel_float32_noise(s2):
    class MultiChannelModel:
        valid = np.array([True, True, True])
        noise_std = np.array([.13, .71, 1.3], dtype=np.float32)
        data = np.array([[1., 2., 3.], [-.3, .2, 2.], [.4, -.1, .7]])
        kernels = np.array([
            [[1., .1], [.2, 1.], [.5, .3]],
            [[1., 1.], [.2, .20001], [.5, .5]],
            [[.3, .6], [1., .1], [.2, .7]],
        ])

        def __call__(self, params, key, freq_subset):
            return self.kernels[:, :, int(key)]

    model = MultiChannelModel()
    actual, diag, gains = _gain_marginal_multi_band_impl(
        model, [FRBParams(c0=1., t0=0., gamma=0.)] * 2, ["0", "1"], s2=s2,
    )
    expected = 0.
    for channel in range(3):
        # High precision avoids cancellation in the independent covariance solve
        # when the prior is broad. Preserve the established float32 variance.
        with mp.workdps(60):
            k = mp.matrix(model.kernels[channel].tolist())
            d = mp.matrix(model.data[channel].tolist())
            variance = float(model.noise_std[channel] ** np.float32(2))
            covariance = variance * mp.eye(3) + diag["s2"] * k * k.T
            solved = mp.lu_solve(covariance, d)
            lnz = float(-mp.mpf("0.5") * (
                (d.T * solved)[0] + mp.log(mp.det(covariance))
                + 3 * mp.log(2 * mp.pi)
            ))
            gain = np.array(list(diag["s2"] * k.T * solved), dtype=float)
        expected += lnz
        np.testing.assert_allclose(gains[channel], gain, atol=1e-8, rtol=0)
    np.testing.assert_allclose(actual, expected, atol=1e-8, rtol=0)
    if s2 is None:
        # The profiled solution must beat nearby fixed-variance evaluations.
        for factor in [.9, 1.1]:
            nearby = sum(covariance_oracle(
                model.kernels[c], model.data[c], diag["s2"] * factor,
                np.sqrt(float(model.noise_std[c] ** np.float32(2))),
            )[0] for c in range(3))
            assert actual >= nearby
