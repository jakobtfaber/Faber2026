"""Deterministic equation checks; no fitting, sampling campaign or data access."""
from pathlib import Path
import json
import sys

import numpy as np
from scipy.integrate import quad
from scipy.special import j0

ANALYSIS = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ANALYSIS))
from scattering.scat_analysis.burstfit import FRBParams, analytic_gaussian_exp_convolution
from scattering.scat_analysis.burstfit_joint import _gain_marginal_multi_band_impl


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def covariance_loglike(K, d, variance):
    covariance = np.eye(d.size) + variance * K @ K.T
    return float(-0.5 * (d @ np.linalg.solve(covariance, d)
                        + np.linalg.slogdet(covariance)[1] + d.size*np.log(2*np.pi)))


class MatrixModel:
    def __init__(self, K, d):
        self.K = K
        self.data = d[None, :]
        self.noise_std = np.ones(1)
        self.valid = np.ones(1, dtype=bool)

    def __call__(self, params, key, freq_subset=None):
        return self.K[:, int(key)][None, :]


def implemented(K, d, variance):
    return _gain_marginal_multi_band_impl(
        MatrixModel(K, d), [FRBParams(c0=1., t0=0., gamma=0.) for _ in range(K.shape[1])],
        [str(i) for i in range(K.shape[1])], s2=variance)[0]


def main():
    K = np.array([[1., 0.2], [0.3, 1.], [0.5, -0.4]])
    d = np.array([0.2, 0.7, -0.5])
    proper_error = abs(implemented(K, d, 2.)-covariance_loglike(K, d, 2.))
    require(proper_error < 1e-12, "Full-rank marginal disagrees with covariance")
    weak_K = np.diag([1., 1e-4]); weak_d = np.array([0., 100.])
    exact = covariance_loglike(weak_K, weak_d, 1e12)
    approximate = implemented(weak_K, weak_d, 1e12)
    weak_variance = 1 + 1e12 * (1e-4)**2
    expected_gap = -0.5 * (weak_d[1]**2 * (1-1/weak_variance) - np.log(weak_variance))
    require(abs((approximate-exact)-expected_gap) < 1e-9,
            "Rank fallback no longer matches the analytically derived omitted-mode error")
    large_variance_step = covariance_loglike(K,d,1e10)-covariance_loglike(K,d,1e8)
    expected_step = -K.shape[1]/2*np.log(100.)
    require(abs(large_variance_step-expected_step) < 1e-5, "Large-variance determinant limit failed")
    sigma, tau, mu, t = 0.3, 0.8, 0.2, 0.7
    integral = quad(lambda u: np.exp(-u/tau)/tau*np.exp(-0.5*((t-mu-u)/sigma)**2)/(np.sqrt(2*np.pi)*sigma),0,np.inf)[0]
    closed = float(analytic_gaussian_exp_convolution(np.array([t,t+0.1]),mu,np.array([[sigma]]),np.array([[tau]]))[0,0])
    require(abs(integral-closed)<1e-12, "Exponential convolution quadrature failed")
    beta=3.67; sc=2*np.log(2/(4-beta)); norm=1-np.exp(-sc)+np.exp(-sc)*sc/(beta/2-1)
    area=quad(lambda x:(np.exp(-x) if x<=sc else np.exp(-sc)*(x/sc)**(-beta/2))/norm,0,np.inf,points=None)[0]
    require(abs(area-1)<1e-7, "Continuous infinite-domain piecewise normalization failed")
    def williamson(t):
        if t <= 0:
            return 0.
        n = np.arange(1, 100, 2, dtype=float)
        signs = (-1.)**np.arange(n.size)
        if t < 1:
            return float(np.sqrt(np.pi/(4*t**3))*np.sum(signs*n*np.exp(-n*n*np.pi**2/(16*t))))
        return float(4/np.pi*np.sum(signs*n*np.exp(-n*n*t)))
    w_area = quad(williamson,0,1)[0]+quad(williamson,1,np.inf)[0]
    w_mean = quad(lambda t:t*williamson(t),0,1)[0]+quad(lambda t:t*williamson(t),1,np.inf)[0]
    laplace_errors = []
    for rate in [0.1,1.,4.]:
        numerical = quad(lambda t:np.exp(-rate*t)*williamson(t),0,1)[0]+quad(lambda t:np.exp(-rate*t)*williamson(t),1,np.inf)[0]
        laplace_errors.append(abs(numerical-1/np.cosh(np.pi/2*np.sqrt(rate))))
    require(abs(w_area-1)<1e-10 and abs(w_mean-np.pi**2/8)<1e-10, "Williamson moments failed")
    require(max(laplace_errors)<1e-10, "Williamson Laplace transform failed")
    beta3_errors = []
    for delay in [0.1,1.,4.]:
        transformed = 0.5*quad(lambda x:x*j0(np.sqrt(delay)*x)*np.exp(-x/2),0,np.inf,epsabs=1e-10)[0]
        exact_beta3 = 2*(1+4*delay)**(-1.5)
        beta3_errors.append(abs(transformed-exact_beta3))
    require(max(beta3_errors)<1e-9, "Beta=3 Hankel transform failed")
    result=dict(williamson_area=w_area,williamson_mean=w_mean,
                williamson_laplace_errors=laplace_errors,beta3_transform_errors=beta3_errors,proper_full_rank_error=proper_error,rank_fallback_exact_loglike=exact,
                rank_fallback_implemented_loglike=approximate,rank_fallback_error=approximate-exact,
                large_gain_variance_loglike_step=large_variance_step,expected_step=expected_step,
                gaussian_exponential_quadrature_error=abs(integral-closed),normalized_piecewise_kernel_area=area,
                scope='Deterministic algebra/counterexamples only; no scientific calibration or campaign')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
