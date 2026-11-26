"""Profile the production joint log-likelihood in beta across the exponential
dispatch boundary (beta >= 3.98 -> analytic exponential, alpha := 4).

Motivation: production_path_injection.py case exp-a3.0 (true alpha = 3)
returned beta = 3.969 (-0.023/+0.009) with negligible weighted mass within 0.01 of the ceiling.
If the posterior avoids [3.98, 4.0] because the likelihood steps DOWN at the
kernel switch, the production rail rule (mass within 1 percent of the box edge)
cannot flag a structurally railed sightline. This script measures that step.

Run:  cd analysis && MPLCONFIGDIR=$TMPDIR/mpl .venv/bin/python \
        docs/rse/specs/research/method-reassessment-2026-09-11/kernel_switch_check.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import production_path_injection as ppi  # noqa: E402
from scattering.scat_analysis.burstfit_joint import _JointLogLikelihoodGainSharedZeta  # noqa: E402

plt.rcParams.update({"font.size": 9, "svg.fonttype": "none"})


def profile(case: str, kernel: str, shape: float, seed: int = 20260911):
    m_C, m_D = ppi.make_bands(kernel, shape, 32.0, seed)
    ll = _JointLogLikelihoodGainSharedZeta(m_C, m_D)
    poc = ppi._poc
    betas = np.round(np.concatenate([np.arange(3.60, 3.90, 0.02), np.arange(3.90, 4.0001, 0.002)]), 4)
    taus = ppi.TAU_TRUE * 10 ** np.linspace(-0.4, 0.4, 41)
    prof = np.empty(betas.size)
    tau_at = np.empty(betas.size)
    for i, b in enumerate(betas):
        vals = [ll(np.array([t, b, poc.ZETA1_TRUE, poc.X_ZETA_TRUE, poc.T0_C_TRUE, 0.0, poc.T0_D_TRUE, 0.0]))
                for t in taus]
        j = int(np.argmax(vals)); prof[i] = vals[j]; tau_at[i] = taus[j]
    below = prof[betas < 3.98].max(); above = prof[betas >= 3.98].max()
    return dict(case=case, kernel=kernel, shape_true=shape, betas=betas.tolist(), profile_lnL=prof.tolist(),
                tau_at_max=tau_at.tolist(), best_below_switch=float(below), best_at_or_above_switch=float(above),
                step_lnL=float(above - below), beta_at_max=float(betas[int(np.argmax(prof))]))


def branch_discontinuity(seed: int = 20260911) -> list[dict]:
    """Compare branches at beta 3.979 and 3.981. Alpha changes too.

    Raw all-channel maxima and area-normalized middle-channel shifted residuals
    use different metrics; the latter is not an isolated sampling correction.
    """
    from scattering.scat_analysis.burstfit import FRBParams, analytic_gaussian_exp_convolution
    poc = ppi._poc
    m_C, m_D = ppi.make_bands("exp", 3.0, 32.0, seed)
    rows = []
    for name, m, t0 in (("CHIME", m_C, poc.T0_C_TRUE), ("DSA", m_D, poc.T0_D_TRUE)):
        freq = np.asarray(m.freq, float); t = np.asarray(m.time, float); dt = float(np.diff(t)[0])
        z = poc.ZETA1_TRUE * freq ** poc.X_ZETA_TRUE
        mk = lambda b: m(FRBParams(c0=1.0, t0=t0, gamma=0.0, zeta=z, tau_1ghz=0.0288, beta=b, delta_dm=0.0), "M3")
        A, F, F39 = mk(3.981), mk(3.979), mk(3.90)
        ch = A.shape[0] // 2
        cen = lambda y: float((y * t).sum() / y.sum())
        tt = np.broadcast_to(t[None, :] + 0.5 * dt, A.shape).copy()
        A2 = analytic_gaussian_exp_convolution(tt, t0, np.clip(z[:, None], 1e-6, None), (0.0288 * freq ** -4.0)[:, None])
        rows.append(dict(
            band=name, dt_ms=dt, tau_centre_ms=float(0.0288 * np.median(freq) ** -4.0),
            max_diff_over_peak_3979_vs_3981=float(np.abs(F - A).max() / A.max()),
            max_diff_over_peak_390_vs_3981=float(np.abs(F39 - A).max() / A.max()),
            centroid_offset_samples_fft_minus_analytic=(cen(F[ch]) - cen(A[ch])) / dt,
            max_diff_over_peak_fft_vs_analytic_at_bin_centre=float(np.abs(A2[ch] / A2[ch].sum() - F[ch] / F[ch].sum()).max() / (F[ch] / F[ch].sum()).max()),
        ))
        r = rows[-1]
        print(f"{name}: |3.979-3.981|/peak={r['max_diff_over_peak_3979_vs_3981']:.3f}; centroid offset={r['centroid_offset_samples_fft_minus_analytic']:+.3f} samples; "
              f"after t+dt/2 sampling={r['max_diff_over_peak_fft_vs_analytic_at_bin_centre']:.3f}", flush=True)
    return rows


def _optimise_side(ll, theta0: np.ndarray, beta: float) -> tuple[float, np.ndarray]:
    """Conditionally optimize tau and arrival times at fixed beta and nuisances.

    These optima are not marginalized posterior odds or a sampler diagnosis.
    """
    from scipy.optimize import minimize
    th = theta0.copy(); th[1] = beta
    def nll(x):
        t = th.copy(); t[0] = abs(x[0]); t[4] = x[1]; t[6] = x[2]
        v = ll(t)
        return -v if np.isfinite(v) else 1e30
    x0 = np.array([th[0], th[4], th[6]])
    best = None
    for scale in (1.0, 0.5, 2.0):
        r = minimize(nll, x0 * np.array([scale, 1.0, 1.0]), method="Nelder-Mead",
                     options=dict(xatol=1e-6, fatol=1e-3, maxiter=4000))
        if best is None or r.fun < best.fun:
            best = r
    t = th.copy(); t[0] = abs(best.x[0]); t[4] = best.x[1]; t[6] = best.x[2]
    return float(-best.fun), t


def step_with_free_t0(case: str, kernel: str, shape: float, seed: int = 20260911) -> dict:
    """lnL(beta=3.981, analytic branch) - lnL(beta=3.979, FFT branch) with tau, t0_C, t0_D re-optimised
    on each side, starting from the injected truth."""
    m_C, m_D = ppi.make_bands(kernel, shape, 32.0, seed)
    ll = _JointLogLikelihoodGainSharedZeta(m_C, m_D)
    poc = ppi._poc
    th0 = np.array([ppi.TAU_TRUE, 3.98, poc.ZETA1_TRUE, poc.X_ZETA_TRUE, poc.T0_C_TRUE, 0.0, poc.T0_D_TRUE, 0.0])
    lo, th_lo = _optimise_side(ll, th0, 3.979)
    hi, th_hi = _optimise_side(ll, th0, 3.981)
    dtC = float(np.diff(np.asarray(m_C.time, float))[0]); dtD = float(np.diff(np.asarray(m_D.time, float))[0])
    return dict(case=case, kernel=kernel, shape_true=shape, start="injected truth",
                lnL_fft_3979=lo, lnL_analytic_3981=hi, step_lnL_free_t0=hi - lo,
                t0_shift_C_samples=(th_hi[4] - th_lo[4]) / dtC, t0_shift_D_samples=(th_hi[6] - th_lo[6]) / dtD,
                tau_fft=float(th_lo[0]), tau_analytic=float(th_hi[0]))


def flip_check_from_posterior() -> list[dict]:
    """For each production-path record (v2, with full percentiles): start from the posterior-median
    vector, flip beta to either side of the dispatch boundary, re-optimise tau and the two t0, and
    report a conditional profile difference, not posterior odds."""
    rows = []
    for pth in sorted((HERE / "results" / "production-path").glob("*.json")):
        if ".v1" in pth.name:
            continue
        rec = json.loads(pth.read_text())
        if "param_names" not in rec or "percentiles" not in rec:
            continue
        names = rec["param_names"]
        th0 = np.array([rec["percentiles"][n]["median"] for n in names])
        legacy = {case[0]: case for case in ppi.CASES}
        case = legacy[rec["case"]]
        tau_true = rec.get("tau_1ghz_true", case[5])
        m_C, m_D = ppi.make_bands(rec["kernel"], rec["shape_true"], case[3], rec["seed"], tau_1ghz=tau_true)
        ll = _JointLogLikelihoodGainSharedZeta(m_C, m_D)
        at_med = float(ll(th0))
        lo, th_lo = _optimise_side(ll, th0, 3.979)
        hi, th_hi = _optimise_side(ll, th0, 3.981)
        dtC = float(np.diff(np.asarray(m_C.time, float))[0]); dtD = float(np.diff(np.asarray(m_D.time, float))[0])
        rows.append(dict(case=rec["case"], tau_1ghz_true=tau_true, tau_source="record" if "tau_1ghz_true" in rec else "legacy CASES inventory", beta_median=float(th0[names.index("beta")]), lnL_at_median=at_med,
                         lnL_fft_3979=lo, lnL_analytic_3981=hi, step_lnL_free_t0=hi - lo,
                         t0_shift_C_samples=(th_hi[4] - th_lo[4]) / dtC, t0_shift_D_samples=(th_hi[6] - th_lo[6]) / dtD,
                         mass_above=rec.get("mass_above"), rail_class=rec.get("rail_class")))
        r = rows[-1]
        print(f"{r['case']}: beta_med={r['beta_median']:.3f} lnL(med)={at_med:.1f}; free-t0 step 3.979->3.981 = {r['step_lnL_free_t0']:+.1f} "
              f"(t0 shift C {r['t0_shift_C_samples']:+.2f}, D {r['t0_shift_D_samples']:+.2f} samples)", flush=True)
    return rows


def main():
    only_flip = "--flip-only" in sys.argv
    if not only_flip:
        disc = branch_discontinuity()
        (HERE / "results" / "kernel-branch-discontinuity.json").write_text(json.dumps(disc, indent=1))
        out = []
        for case, kernel, shape in (("exp-a3.0", "exp", 3.0), ("exp-a4.0", "exp", 4.0), ("thin-b3.67", "thin", 3.67)):
            r = profile(case, kernel, shape); out.append(r)
            print(f"{case}: best beta {r['beta_at_max']:.3f}; lnL(best >=3.98) - lnL(best <3.98) = {r['step_lnL']:+.1f}", flush=True)
        (HERE / "results" / "kernel-switch-check.json").write_text(json.dumps(out, indent=1))
        free = []
        for case, kernel, shape in (("exp-a3.0", "exp", 3.0), ("exp-a4.0", "exp", 4.0), ("thin-b3.67", "thin", 3.67)):
            r = step_with_free_t0(case, kernel, shape); free.append(r)
            print(f"{case}: free-t0 step 3.979->3.981 = {r['step_lnL_free_t0']:+.1f} (t0 shift C {r['t0_shift_C_samples']:+.2f}, D {r['t0_shift_D_samples']:+.2f} samples)", flush=True)
        (HERE / "results" / "kernel-switch-free-t0.json").write_text(json.dumps(free, indent=1))
    flip = flip_check_from_posterior()
    (HERE / "results" / "kernel-switch-posterior-flip.json").write_text(json.dumps(flip, indent=1))
    if only_flip:
        return
    out = json.loads((HERE / "results" / "kernel-switch-check.json").read_text())
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    for r in out:
        p = np.asarray(r["profile_lnL"]); ax.plot(r["betas"], p - p.max(), label=r["case"], lw=1)
    ax.axvline(3.98, color="C3", lw=0.8, ls="--")
    ax.set_xlabel(r"$\beta$"); ax.set_ylabel(r"$\ln L_{\mathrm{prof}}(\beta) - \max$"); ax.set_ylim(-800, 20); ax.set_xlim(3.6, 4.0)
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout(); fig.savefig(HERE / "fig-kernel-switch.svg"); plt.close(fig)


if __name__ == "__main__":
    main()
