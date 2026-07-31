"""Injection calibration of the predicted-delay profile-residual trigger.

Owner decision 2026-07-29 (ticket 04a): the rule is unavailable for model
selection until its false-escalation and detection rates are measured on
truth-known one- and two-screen examples.  Statistic: whitened
band-integrated residual profile (residual_check.py convention,
P[t] = sum_f r[f,t]/sqrt(F_valid)), matched-filter maximum restricted to
[t_peak + tau_pred*(1-w), t_peak + tau_pred*(1+w)].

Design record: docs/rse/specs/plan-predicted-delay-trigger-calibration.md.
All times in this module are milliseconds and frequencies gigahertz — the
GHz convention of burstfit/twoscreen; broaden.tau_per_freq (MHz convention)
is deliberately not used.
"""
from __future__ import annotations

import dataclasses
import importlib.util
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from scattering.scat_analysis.burstfit import analytic_gaussian_exp_convolution

_REPO_ROOT = Path(__file__).resolve().parents[1]

# residual_check.py:63 log-spaced boxcar matched-filter widths.
MATCHED_WIDTHS = (1, 2, 4, 8, 16)

# CHIME-like base-campaign geometry (plan, Implementation Approach): the
# casey-like tau_1 spans ~57 samples here; on the DSA grid it is 0.15
# samples and the campaign would be vacuous.
BAND_LO_GHZ = 0.4
BAND_HI_GHZ = 0.8
N_CHANNELS = 32
DT_MS = 0.00256
N_TIME = 4096

# Truth defaults (plan: casey sigma/tau, tau1 used directly as screen 1 —
# a recorded deviation from twoscreen_stage0_inject.py:72).
TRUTH_T0_MS = 2.0
TRUTH_SIGMA_MS = 0.055
TRUTH_TAU1_1GHZ_MS = 0.019
TRUTH_ALPHA = 4.0


def _load_twoscreen():
    """scattering/studies/joint-refits is not a package; load by path
    (pattern of likelihood_equivalence.py:72). Its internal
    `from scattering.scat_analysis...` import resolves via the repo root."""
    if "twoscreen" in sys.modules:
        return sys.modules["twoscreen"]
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    path = _REPO_ROOT / "scattering" / "studies" / "joint-refits" / "twoscreen.py"
    spec = importlib.util.spec_from_file_location("twoscreen", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["twoscreen"] = mod
    spec.loader.exec_module(mod)
    return mod


@dataclasses.dataclass(frozen=True)
class TriggerStatistic:
    matched_snr: float
    best_width: int
    window_ms: tuple[float, float]
    n_window_samples: int


def predicted_delay_statistic(residual, valid, time_ms, t_peak_ms,
                              tau_pred_ms, window_frac):
    whitened = np.where(valid, residual, 0.0)
    n_valid = np.maximum(valid.sum(axis=0), 1)
    profile = whitened.sum(axis=0) / np.sqrt(n_valid)
    lo = t_peak_ms + tau_pred_ms * (1.0 - window_frac)
    hi = t_peak_ms + tau_pred_ms * (1.0 + window_frac)
    sel = (time_ms >= lo) & (time_ms <= hi)
    if not sel.any():
        return TriggerStatistic(float("nan"), 0, (lo, hi), 0)
    best_snr, best_w = -np.inf, 0
    window = profile[sel]
    for w in MATCHED_WIDTHS:
        if w > window.size:
            break
        kernel = np.ones(w) / np.sqrt(w)
        scanned = np.convolve(window, kernel, mode="valid")
        peak = float(scanned.max()) if scanned.size else -np.inf
        if peak > best_snr:
            best_snr, best_w = peak, w
    if not np.isfinite(best_snr):
        return TriggerStatistic(float("nan"), 0, (lo, hi), int(sel.sum()))
    return TriggerStatistic(best_snr, best_w, (lo, hi), int(sel.sum()))


@dataclasses.dataclass(frozen=True)
class TruthWaterfall:
    clean: np.ndarray
    data: np.ndarray
    noise_std: np.ndarray
    valid: np.ndarray
    time_ms: np.ndarray
    freq_ghz: np.ndarray
    truth: dict


def _band_kernels(time_ms, freq_ghz, t0_ms, sigma_ms, tau1_1ghz_ms, r):
    """(nf, nt) area-normalized kernel; tau(f) = tau1 * f_ghz**-alpha."""
    nf = freq_ghz.size
    mu = np.full((nf, 1), t0_ms)
    sig = np.full((nf, 1), sigma_ms)
    tau = (tau1_1ghz_ms * freq_ghz ** (-TRUTH_ALPHA)).reshape(nf, 1)
    t2d = np.broadcast_to(time_ms, (nf, time_ms.size))
    if r <= 0.0:
        return analytic_gaussian_exp_convolution(t2d, mu, sig, tau)
    return _load_twoscreen().two_screen_perchan(time_ms, mu, sig, tau, r)


def make_truth_waterfall(seed, r, snr):
    """One-screen (r=0) or two-screen truth on the CHIME-like grid, with the
    run_beta_poc.py:101-107 gain-envelope and noise recipe."""
    rng = np.random.default_rng(seed)
    time_ms = np.arange(N_TIME) * DT_MS
    freq_ghz = np.linspace(BAND_LO_GHZ, BAND_HI_GHZ, N_CHANNELS)
    kernel = _band_kernels(time_ms, freq_ghz, TRUTH_T0_MS, TRUTH_SIGMA_MS,
                           TRUTH_TAU1_1GHZ_MS, r)
    envelope = (freq_ghz / np.median(freq_ghz)) ** -1.5
    scint = np.exp(rng.normal(0.0, 0.2, N_CHANNELS))
    gain = envelope * scint
    clean = gain[:, None] * kernel
    sigma = clean.max() / snr
    data = clean + rng.normal(0.0, sigma, clean.shape)
    band_center = 0.5 * (BAND_LO_GHZ + BAND_HI_GHZ)
    truth = {
        "t0_ms": TRUTH_T0_MS,
        "sigma_ms": TRUTH_SIGMA_MS,
        "tau1_ms": TRUTH_TAU1_1GHZ_MS,
        "tau1_band_ms": TRUTH_TAU1_1GHZ_MS * band_center ** (-TRUTH_ALPHA),
        "r": float(r),
        "snr": float(snr),
    }
    return TruthWaterfall(
        clean=clean, data=data,
        noise_std=np.full(N_CHANNELS, sigma),
        valid=np.ones(clean.shape, bool),
        time_ms=time_ms, freq_ghz=freq_ghz, truth=truth)


@dataclasses.dataclass(frozen=True)
class FittedModel:
    t0_ms: float
    sigma_ms: float
    tau1_ms: float
    tau1_band_ms: float
    model: np.ndarray
    converged: bool


def _ols_gains(data, kernel, valid):
    """Per-row amplitude by least squares against the unit-area kernel
    (the joint_model_grid.py:15 recovery)."""
    k = np.where(valid, kernel, 0.0)
    d = np.where(valid, data, 0.0)
    denom = (k * k).sum(axis=1)
    denom = np.where(denom > 0, denom, 1.0)
    return (d * k).sum(axis=1) / denom


def fit_one_screen(tw: TruthWaterfall) -> FittedModel:
    """Nelder-Mead ML fit of the one-screen model, alpha fixed at 4.0;
    per-row analytic amplitudes; parameters (t0, log sigma, log tau1)."""
    profile = tw.data.sum(axis=0)
    t0_init = float(tw.time_ms[int(np.argmax(profile))])

    def nll(theta):
        t0, log_sig, log_tau = theta
        sig, tau = float(np.exp(log_sig)), float(np.exp(log_tau))
        if not (1e-4 < sig < 5.0 and 1e-3 < tau < 5.0):
            return 1e12
        kernel = _band_kernels(tw.time_ms, tw.freq_ghz, t0, sig, tau, 0.0)
        gains = _ols_gains(tw.data, kernel, tw.valid)
        model = gains[:, None] * kernel
        resid = (tw.data - model) / tw.noise_std[:, None]
        return float((resid[tw.valid] ** 2).sum())

    x0 = np.array([t0_init, np.log(0.05), np.log(0.02)])
    result = minimize(nll, x0, method="Nelder-Mead",
                      options={"xatol": 1e-5, "fatol": 1e-3,
                               "maxiter": 4000, "maxfev": 6000})
    t0, sig, tau = float(result.x[0]), float(np.exp(result.x[1])), float(np.exp(result.x[2]))
    kernel = _band_kernels(tw.time_ms, tw.freq_ghz, t0, sig, tau, 0.0)
    gains = _ols_gains(tw.data, kernel, tw.valid)
    band_center = 0.5 * (BAND_LO_GHZ + BAND_HI_GHZ)
    return FittedModel(
        t0_ms=t0, sigma_ms=sig, tau1_ms=tau,
        tau1_band_ms=tau * band_center ** (-TRUTH_ALPHA),
        model=gains[:, None] * kernel,
        converged=bool(result.success))


def _model_peak_time_ms(fit: FittedModel, time_ms) -> float:
    return float(time_ms[int(np.argmax(fit.model.sum(axis=0)))])


def trigger_pvalue(tw: TruthWaterfall, fit: FittedModel, tau_pred_ms,
                   window_frac, n_replicates, seed) -> float:
    """Exceedance fraction of the windowed statistic under no-refit
    replicates (fitted model + noise; ppc.py:63 recipe).  The replicate arm
    deliberately does not re-fit; the empirical null quantiles across
    injections are rate-calibrated by construction (plan, Implementation
    Approach)."""
    rng = np.random.default_rng(seed)
    t_peak = _model_peak_time_ms(fit, tw.time_ms)
    noise = tw.noise_std[:, None]

    def stat(dataset):
        resid = (dataset - fit.model) / noise
        return predicted_delay_statistic(
            resid, tw.valid, tw.time_ms, t_peak, tau_pred_ms,
            window_frac).matched_snr

    observed = stat(tw.data)
    if not np.isfinite(observed):
        return float("nan")
    exceed = 0
    for _ in range(n_replicates):
        replicate = fit.model + rng.normal(0.0, 1.0, tw.data.shape) * noise
        if stat(replicate) >= observed:
            exceed += 1
    return exceed / n_replicates
