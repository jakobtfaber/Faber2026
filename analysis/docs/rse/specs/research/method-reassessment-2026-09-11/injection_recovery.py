"""Injection-recovery study for the two-band scattering method reassessment.

Ticket: docs/rse/wayfinder/tickets/method-reassessment-01-scattering-fit-method-class.md
Run:    cd analysis && MPLCONFIGDIR=$TMPDIR/mpl .venv/bin/python \
            docs/rse/specs/research/method-reassessment-2026-09-11/injection_recovery.py \
            --nproc 12 [--arm a|b|c] [--only ID ...] [--quick]

Three arms, one shared simulator and two fit models on identical synthetic
two-band dynamic spectra:

  arm a  inference check: thin-screen truths at interior beta, fitted with the
         manuscript beta-coupled power-law PBF model (F1). If an interior truth
         is not recovered interior on clean data, the inference is defective.
  arm b  model-class check: truths outside the thin-screen family (exponential
         PBF with alpha != alpha(beta), extended-medium kernel, two screens,
         unmodelled second intrinsic component) fitted with F1 and with the
         fixed-exponential free-alpha model (F2). If these reproduce the rails
         seen in the July 2026 campaign, the rails are a model-class effect.
  arm c  sensitivity: signal-to-noise and gain-prior variance sweeps on one
         interior thin-screen truth, F1 and F2, with the evidence difference.

Model equations follow the production code: the PBF shape is
faber2026.burst_models.kernels.power_law_pbf (beta-coupled crossover form),
alpha = 2 beta / (beta - 2), per-channel gains marginalised under a fixed
Gaussian prior of variance s2 as in radio_pipeline.fitting.joint_burst.
The Gaussian-PBF convolution is done by FFT on the native grid with the PBF
sampled at bin midpoints; the study's own check (`--check-kernel`) compares it
against the analytic quadrature kernel gaussian_power_law_density.

Simplifications relative to the production request, stated so they can be
weighed: one intrinsic component per band (arm b5 injects two), independent
per-band arrival times instead of a geometry-tied shared arrival time, no
channel masking, white noise with a known per-channel standard deviation.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ANALYSIS_ROOT = HERE.parents[4]
sys.path.insert(0, str(ANALYSIS_ROOT))

from faber2026.burst_models.kernels import (  # noqa: E402
    gaussian_power_law_density,
    power_law_pbf,
    scattering_index,
)

K_DM = 4148.808  # s MHz^2 / (pc cm^-3)
NU_REF_MHZ = 400.0

# Native-like grids: CHIME 400-800 MHz at 16x2.56 us; DSA 1311-1498 MHz at 32.768 us.
BANDS = {
    "C": dict(freq=np.linspace(406.25, 793.75, 32), dt=40.96e-6, nt=1024),
    "D": dict(freq=np.linspace(1315.0, 1494.0, 24), dt=32.768e-6, nt=512),
}
T0_FRAC = 0.30  # true arrival time as a fraction of the window


# ----------------------------------------------------------------------------
# kernels (all return an (nf, nt) density in 1/s on the band grid)
# ----------------------------------------------------------------------------

def _grid(band: str) -> tuple[np.ndarray, float, int, np.ndarray]:
    spec = BANDS[band]
    t = np.arange(spec["nt"]) * spec["dt"]
    return spec["freq"], spec["dt"], spec["nt"], t


def tau_nu(tau_1ghz: float, alpha: float, freq_mhz: np.ndarray) -> np.ndarray:
    return tau_1ghz * (freq_mhz / 1000.0) ** (-alpha)


def pbf_thin(t_mid: np.ndarray, taus: np.ndarray, beta: float) -> np.ndarray:
    """Production beta-coupled power-law PBF, one row per channel.

    Vectorised transcription of faber2026.burst_models.kernels.power_law_pbf
    (same crossover, tail exponent and core+tail normalisation); check_kernel()
    asserts row-wise agreement with the production function.
    """
    scattering_index(beta)
    taus = np.asarray(taus, float)[:, None]
    scaled = t_mid[None, :] / taus
    if beta == 4.0:
        return np.exp(-scaled) / taus
    crossover = 2.0 * math.log(2.0 / (4.0 - beta))
    core_mass = 1.0 - math.exp(-crossover)
    tail_mass = math.exp(-crossover) * crossover / (beta / 2.0 - 1.0)
    density = np.where(
        scaled > crossover,
        math.exp(-crossover) * (np.maximum(scaled, crossover) / crossover) ** (-beta / 2.0),
        np.exp(-scaled),
    )
    return density / (taus * (core_mass + tail_mass))


def pbf_exp(t_mid: np.ndarray, taus: np.ndarray) -> np.ndarray:
    return np.exp(-t_mid[None, :] / taus[:, None]) / taus[:, None]


def pbf_thick(t_mid: np.ndarray, taus: np.ndarray) -> np.ndarray:
    """Generic heavy-tail stress kernel; legacy identifier ``thick``.

    The implemented density integrates to 2 and has infinite mean. The retained
    1.2337 scale divisor defines the original synthetic arrays, not a mean-delay
    normalization or a verified physical medium. Keep it to preserve those arrays.
    """
    out = np.zeros((taus.size, t_mid.size))
    for i, tau in enumerate(taus):
        tau_w = float(tau) / 1.2337
        with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
            h = np.sqrt(math.pi * tau_w / (4.0 * t_mid**3)) * np.exp(
                -math.pi**2 * tau_w / (16.0 * t_mid)
            )
        out[i] = np.nan_to_num(h, nan=0.0, posinf=0.0)
    return out


def convolve_rows(g: np.ndarray, h: np.ndarray, dt: float) -> np.ndarray:
    nt = g.shape[-1]
    L = 2 * nt
    G = np.fft.rfft(g, L, axis=-1)
    H = np.fft.rfft(h, L, axis=-1)
    return np.fft.irfft(G * H, L, axis=-1)[..., :nt] * dt


def gaussian_rows(t: np.ndarray, centers: np.ndarray, sigmas: np.ndarray) -> np.ndarray:
    return np.exp(-0.5 * ((t[None, :] - centers[:, None]) / sigmas[:, None]) ** 2) / (
        math.sqrt(2.0 * math.pi) * sigmas[:, None]
    )


def model_kernel(
    band: str,
    family: str,
    tau_1ghz: float,
    shape_param: float,
    sigma: float,
    t0: float,
    ddm: float,
    width_index: float,
    *,
    alpha_override: float | None = None,
) -> np.ndarray:
    """Intrinsic Gaussian convolved with a PBF, dispersed by residual DM.

    family 'thin': shape_param = beta, alpha = alpha(beta), PBF = power_law_pbf.
    family 'exp':  shape_param = alpha, PBF = exponential.
    family 'thick': shape_param = alpha, PBF = extended medium.
    """
    freq, dt, nt, t = _grid(band)
    t_mid = t + 0.5 * dt
    if family == "thin":
        beta = shape_param
        alpha = scattering_index(beta) if alpha_override is None else alpha_override
        taus = tau_nu(tau_1ghz, alpha, freq)
        h = pbf_thin(t_mid, taus, beta)
    elif family == "exp":
        taus = tau_nu(tau_1ghz, shape_param, freq)
        h = pbf_exp(t_mid, taus)
    elif family == "thick":
        taus = tau_nu(tau_1ghz, shape_param, freq)
        h = pbf_thick(t_mid, taus)
    else:
        raise ValueError(family)
    centers = t0 + K_DM * ddm * (freq**-2 - NU_REF_MHZ**-2)
    sigmas = sigma * (freq / NU_REF_MHZ) ** width_index
    g = gaussian_rows(t, centers, sigmas)
    return convolve_rows(g, h, dt)


# ----------------------------------------------------------------------------
# truths
# ----------------------------------------------------------------------------

@dataclass
class Truth:
    kind: str            # thin | exp | thick | twoscreen | thin2comp
    tau_1ghz: float      # s (for twoscreen: screen A)
    shape: float         # beta (thin, thin2comp) or alpha (exp, thick); twoscreen: alpha_A
    sigma: float = 3.0e-4
    width_index: float = 0.0
    ddm: float = 0.0
    tau_b_1ghz: float = 0.0     # twoscreen second screen
    beta_b: float = 3.67        # twoscreen second screen (thin PBF)
    comp2_offset: float = 0.0   # thin2comp: second component offset (s)
    comp2_ratio: float = 0.0    # thin2comp: second component amplitude ratio
    comp2_spec: float = 0.0     # thin2comp: extra spectral index of 2nd component

    def alpha(self) -> float:
        if self.kind in {"thin", "thin2comp"}:
            return scattering_index(self.shape)
        return self.shape


def truth_kernel(band: str, tr: Truth) -> np.ndarray:
    freq, dt, nt, t = _grid(band)
    t0 = T0_FRAC * nt * dt
    if tr.kind == "thin":
        return model_kernel(band, "thin", tr.tau_1ghz, tr.shape, tr.sigma, t0, tr.ddm, tr.width_index)
    if tr.kind == "exp":
        return model_kernel(band, "exp", tr.tau_1ghz, tr.shape, tr.sigma, t0, tr.ddm, tr.width_index)
    if tr.kind == "thick":
        return model_kernel(band, "thick", tr.tau_1ghz, tr.shape, tr.sigma, t0, tr.ddm, tr.width_index)
    if tr.kind == "twoscreen":
        t_mid = t + 0.5 * dt
        ha = pbf_exp(t_mid, tau_nu(tr.tau_1ghz, tr.shape, freq))
        hb = pbf_thin(t_mid, tau_nu(tr.tau_b_1ghz, scattering_index(tr.beta_b), freq), tr.beta_b)
        hab = convolve_rows(ha, hb, dt)
        centers = t0 + K_DM * tr.ddm * (freq**-2 - NU_REF_MHZ**-2)
        g = gaussian_rows(t, centers, np.full(freq.size, tr.sigma))
        return convolve_rows(g, hab, dt)
    if tr.kind == "thin2comp":
        k1 = model_kernel(band, "thin", tr.tau_1ghz, tr.shape, tr.sigma, t0, tr.ddm, tr.width_index)
        k2 = model_kernel(band, "thin", tr.tau_1ghz, tr.shape, tr.sigma, t0 + tr.comp2_offset, tr.ddm, tr.width_index)
        spec2 = (freq / 600.0) ** tr.comp2_spec
        return k1 + tr.comp2_ratio * spec2[:, None] * k2
    raise ValueError(tr.kind)


def simulate(tr: Truth, snr_band: float, seed: int) -> dict:
    """Two-band injection. Per-channel gains = spectrum x scintillation-like scatter;
    noise standard deviation is 1 in every channel; snr_band is the band-summed
    peak signal-to-noise of the noiseless profile."""
    rng = np.random.default_rng(seed)
    out = {}
    for band in ("C", "D"):
        freq, dt, nt, t = _grid(band)
        K = truth_kernel(band, tr)
        gain_shape = (freq / 600.0) ** (-1.5) * np.clip(1.0 + 0.3 * rng.standard_normal(freq.size), 0.2, None)
        clean = gain_shape[:, None] * K
        profile = clean.sum(axis=0)
        scale = snr_band * math.sqrt(freq.size) / profile.max()
        clean = clean * scale
        data = clean + rng.standard_normal(clean.shape)
        out[band] = dict(data=data, clean=clean, gain=gain_shape * scale, noise=1.0)
    out["gain_rms"] = float(np.sqrt(np.mean(np.concatenate([out["C"]["gain"] ** 2, out["D"]["gain"] ** 2]))))
    return out


# ----------------------------------------------------------------------------
# likelihood (production gain-marginal form) and fit models
# ----------------------------------------------------------------------------

def band_loglike(data: np.ndarray, K: np.ndarray, s2: float, noise: float = 1.0) -> float:
    """Per-channel gain marginalised under N(0, s2), as radio_pipeline._gain_marginal_band
    (single-component branch): precision = gram + 1/s2; logdet = log1p(s2 gram)."""
    w = K / noise
    gram = np.einsum("ft,ft->f", w, w)
    proj = np.einsum("ft,ft->f", w, data / noise)
    precision = gram + 1.0 / s2
    gains = proj / precision
    quad = np.einsum("ft,ft->f", data / noise, data / noise) - proj * gains
    logdet = np.log1p(s2 * gram)
    ll = np.sum(-0.5 * quad - 0.5 * logdet)
    return float(ll) if np.isfinite(ll) else -1e300


class FitModel:
    """theta = [log10 tau_1ghz, shape(beta|alpha), log10 sigma, t0_C, t0_D, ddm, width_index]."""

    def __init__(self, family: str, inj: dict, s2: float, tau_bounds=(1e-6, 2e-2)):
        assert family in {"F1", "F2"}
        self.family = family
        self.inj = inj
        self.s2 = s2
        nt_c, dt_c = BANDS["C"]["nt"], BANDS["C"]["dt"]
        nt_d, dt_d = BANDS["D"]["nt"], BANDS["D"]["dt"]
        t0c, t0d = T0_FRAC * nt_c * dt_c, T0_FRAC * nt_d * dt_d
        shape_lo, shape_hi = (3.0, 4.0) if family == "F1" else (2.0, 6.0)
        self.names = ["log10_tau_1ghz_s", "beta" if family == "F1" else "alpha",
                      "log10_sigma_s", "t0_C_s", "t0_D_s", "ddm_pc_cm3", "width_index"]
        self.lo = np.array([math.log10(tau_bounds[0]), shape_lo, -5.0, t0c - 3e-3, t0d - 3e-3, -0.1, -2.0])
        self.hi = np.array([math.log10(tau_bounds[1]), shape_hi, -2.0, t0c + 3e-3, t0d + 3e-3, 0.1, 2.0])

    def prior_transform(self, u):
        return self.lo + u * (self.hi - self.lo)

    def __call__(self, th):
        ltau, shape, lsig, t0c, t0d, ddm, gam = (float(x) for x in th)
        tau, sig = 10.0**ltau, 10.0**lsig
        fam = "thin" if self.family == "F1" else "exp"
        ll = 0.0
        for band, t0 in (("C", t0c), ("D", t0d)):
            K = model_kernel(band, fam, tau, shape, sig, t0, ddm, gam)
            ll += band_loglike(self.inj[band]["data"], K, self.s2)
        return ll


def run_fit(model: FitModel, nlive: int, nproc: int, seed: int, dlogz: float = 0.5) -> dict:
    from dynesty import NestedSampler
    from dynesty.utils import resample_equal

    ndim = len(model.lo)
    rstate = np.random.default_rng(seed)
    t_start = time.time()
    if nproc > 1:
        import multiprocessing as mp
        try:
            mp.set_start_method("fork", force=True)
        except RuntimeError:
            pass
        from dynesty import pool as dypool
        with dypool.Pool(nproc, model, model.prior_transform) as pool:
            s = NestedSampler(pool.loglike, pool.prior_transform, ndim, nlive=nlive,
                              sample="rwalk", bound="multi", pool=pool, queue_size=nproc, rstate=rstate)
            s.run_nested(dlogz=dlogz, print_progress=False)
            r = s.results
    else:
        s = NestedSampler(model, model.prior_transform, ndim, nlive=nlive, sample="rwalk", bound="multi", rstate=rstate)
        s.run_nested(dlogz=dlogz, print_progress=False)
        r = s.results
    w = np.exp(r.logwt - r.logz[-1]); w /= w.sum()
    eq = resample_equal(r.samples, w, rstate=np.random.default_rng(seed))
    # prior-edge mass per parameter, production rule: 1% of span at either edge; railed if > 5%.
    span = model.hi - model.lo
    edge_lo = np.mean(eq <= model.lo + 0.01 * span, axis=0)
    edge_hi = np.mean(eq >= model.hi - 0.01 * span, axis=0)
    q = np.percentile(eq, [2.5, 16, 50, 84, 97.5], axis=0)
    return dict(
        logz=float(r.logz[-1]), logzerr=float(r.logzerr[-1]), ncall=int(r.ncall.sum()),
        niter=int(r.niter), runtime_s=time.time() - t_start,
        quantiles={n: dict(p2_5=float(q[0, i]), p16=float(q[1, i]), p50=float(q[2, i]),
                           p84=float(q[3, i]), p97_5=float(q[4, i])) for i, n in enumerate(model.names)},
        edge_mass={n: dict(low=float(edge_lo[i]), high=float(edge_hi[i])) for i, n in enumerate(model.names)},
        samples_shape=list(eq.shape),
        shape_samples=eq[:, 1].tolist()[:2000],
    )


# ----------------------------------------------------------------------------
# study inventory
# ----------------------------------------------------------------------------

@dataclass
class Case:
    id: str
    arm: str
    truth: Truth
    model: str          # F1 | F2
    snr: float = 100.0
    s2_factor: float = 10.0   # s2 = (s2_factor * gain_rms)^2
    seed: int = 1
    note: str = ""


def inventory() -> list[Case]:
    cases: list[Case] = []
    # arm a: interior thin-screen truths under F1
    for beta in (3.3, 3.67, 3.9):
        for tau in (1.5e-4, 1.0e-3):
            tag = "dsa-unresolved" if tau < 5e-4 else "dsa-resolved"
            cases.append(Case(f"a-thin-b{beta}-tau{tau:.0e}-F1", "a", Truth("thin", tau, beta), "F1",
                              note=f"interior truth, {tag}"))
    cases.append(Case("a-exp-a4-tau1e-03-F1", "a", Truth("exp", 1.0e-3, 4.0), "F1",
                      note="beta=4 endpoint truth; ceiling pile expected"))
    for seed in (2, 3, 4):
        cases.append(Case(f"a-thin-b3.67-tau1e-03-F1-seed{seed}", "a", Truth("thin", 1.0e-3, 3.67), "F1",
                          seed=seed, note="noise-seed repeat"))
    # arm b: model-class mismatch truths under F1 and F2
    mismatch = [
        ("exp-a3.2", Truth("exp", 1.0e-3, 3.2), "finite-screen-like alpha<4 exponential truth"),
        ("exp-a5.0", Truth("exp", 1.0e-3, 5.0), "alpha>4 exponential truth"),
        ("thick-a4", Truth("thick", 1.0e-3, 4.0), "extended-medium kernel, alpha=4"),
        ("twoscreen", Truth("twoscreen", 6.0e-4, 4.0, tau_b_1ghz=4.0e-4, beta_b=3.67),
         "two screens: exponential alpha=4 plus thin beta=3.67"),
        ("thin2comp-b3.67", Truth("thin2comp", 1.0e-3, 3.67, comp2_offset=4.5e-4, comp2_ratio=0.4, comp2_spec=-2.0),
         "thin beta=3.67 with unmodelled second component (offset 1.5 sigma, 40%, redder)"),
    ]
    for tag, tr, note in mismatch:
        for model in ("F1", "F2"):
            cases.append(Case(f"b-{tag}-{model}", "b", tr, model, note=note))
    # arm c: sensitivity on thin beta=3.67 tau=1 ms
    base = Truth("thin", 1.0e-3, 3.67)
    for snr in (30.0, 300.0):
        cases.append(Case(f"c-snr{snr:.0f}-F1", "c", base, "F1", snr=snr, note="S/N sweep"))
    for k in (0.1, 1.0, 100.0):
        cases.append(Case(f"c-s2x{k:g}-F1", "c", base, "F1", s2_factor=k, note="gain-prior sweep"))
    for k in (0.1, 1.0, 10.0, 100.0):
        cases.append(Case(f"c-s2x{k:g}-F2", "c", base, "F2", s2_factor=k, note="gain-prior sweep, free-alpha model"))
    return cases


def classify(case: Case, res: dict) -> dict:
    shape_name = "beta" if case.model == "F1" else "alpha"
    e = res["edge_mass"][shape_name]
    q = res["quantiles"][shape_name]
    railed = "interior"
    if e["high"] > 0.05:
        railed = "ceiling-rail"
    if e["low"] > 0.05:
        railed = "floor-rail" if railed == "interior" else "both-rails"
    true_alpha = float("nan") if case.truth.kind == "twoscreen" else case.truth.alpha()
    true_shape = case.truth.shape if (case.model == "F1" and case.truth.kind in {"thin", "thin2comp"}) else (
        true_alpha if case.model == "F2" else float("nan"))
    covered = (q["p2_5"] <= true_shape <= q["p97_5"]) if np.isfinite(true_shape) else None
    tq = res["quantiles"]["log10_tau_1ghz_s"]
    tau_true = float("nan") if case.truth.kind in {"thick", "twoscreen"} else math.log10(case.truth.tau_1ghz)
    return dict(shape_param=shape_name, rail_class=railed, true_shape=true_shape,
                shape_p50=q["p50"], shape_p16=q["p16"], shape_p84=q["p84"],
                shape_covered_95=covered, true_alpha=true_alpha,
                alpha_p50=(scattering_index(q["p50"]) if case.model == "F1" else q["p50"]),
                log10_tau_true=tau_true, log10_tau_p50=tq["p50"],
                tau_covered_95=(tq["p2_5"] <= tau_true <= tq["p97_5"]) if np.isfinite(tau_true) else None,
                tau_edge=res["edge_mass"]["log10_tau_1ghz_s"])


# ----------------------------------------------------------------------------
# driver
# ----------------------------------------------------------------------------

def check_kernel() -> list[dict]:
    """Compare the FFT kernel with the analytic production quadrature kernel."""
    rows = []
    freq, dt, nt, t = _grid("C")
    for beta in (3.2, 3.67, 4.0):
        taus = tau_nu(1e-3, scattering_index(beta), freq)
        vec = pbf_thin(t + 0.5 * dt, taus, beta)
        ref = np.stack([power_law_pbf(t + 0.5 * dt, float(tau), beta) for tau in taus])
        assert np.allclose(vec, ref, rtol=1e-12, atol=0.0), f"pbf_thin mismatch at beta={beta}"
    for beta, tau, sig in [(3.2, 1e-3, 3e-4), (3.5, 3e-4, 3e-4), (3.8, 5e-3, 3e-4), (4.0, 1e-3, 3e-4), (3.3, 5e-5, 3e-4)]:
        t0 = T0_FRAC * nt * dt
        h = power_law_pbf(t + 0.5 * dt, tau, beta)
        g = gaussian_rows(t, np.array([t0]), np.array([sig]))[0]
        conv = convolve_rows(g, h, dt)
        ana = gaussian_power_law_density(t + 0.5 * dt, t0, sig, tau, beta)
        rows.append(dict(beta=beta, tau_s=tau, sigma_s=sig, max_rel_err=float(np.max(np.abs(conv - ana)) / ana.max()),
                         l1_err=float(np.abs(conv - ana).sum() * dt)))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nproc", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--nlive", type=int, default=400)
    ap.add_argument("--dlogz", type=float, default=0.5)
    ap.add_argument("--arm", choices=["a", "b", "c"], action="append")
    ap.add_argument("--only", action="append")
    ap.add_argument("--quick", action="store_true", help="nlive=100, first two cases")
    ap.add_argument("--check-kernel", action="store_true")
    ap.add_argument("--refresh-classifications", action="store_true", help="Update labels from saved metadata; never run fits")
    ap.add_argument("--out", default=str(HERE / "results"))
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    if args.check_kernel:
        rows = check_kernel()
        (out / "kernel-check.json").write_text(json.dumps(rows, indent=1))
        for r in rows:
            print(r)
        return

    cases = inventory()
    if args.arm:
        cases = [c for c in cases if c.arm in args.arm]
    if args.only:
        cases = [c for c in cases if c.id in set(args.only)]
    nlive = 100 if args.quick else args.nlive
    if args.quick:
        cases = cases[:2]
    print(f"{len(cases)} cases, nlive={nlive}, nproc={args.nproc}", flush=True)

    for case in cases:
        path = out / f"{case.id}.json"
        if args.refresh_classifications:
            rec = json.loads(path.read_text())
            saved = rec["case"]
            saved_case = Case(saved["id"], saved["arm"], Truth(**saved["truth"]), saved["model"])
            rec["classification"] = classify(saved_case, rec["result"])
            path.write_text(json.dumps(rec, indent=1))
            continue
        if path.exists() and not args.quick:
            print(f"skip {case.id} (exists)", flush=True)
            continue
        inj = simulate(case.truth, case.snr, seed=1000 + case.seed)
        s2 = (case.s2_factor * inj["gain_rms"]) ** 2
        model = FitModel(case.model, inj, s2)
        print(f"run  {case.id}: truth={case.truth.kind} shape={case.truth.shape} tau={case.truth.tau_1ghz:.2e} "
              f"snr={case.snr} s2={s2:.3g}", flush=True)
        res = run_fit(model, nlive=nlive, nproc=args.nproc, seed=20260911 + case.seed, dlogz=args.dlogz)
        rec = dict(case=dict(id=case.id, arm=case.arm, model=case.model, snr=case.snr, s2_factor=case.s2_factor,
                             s2=s2, seed=case.seed, note=case.note, truth=asdict(case.truth)),
                   sampler=dict(nlive=nlive, dlogz=args.dlogz, sample="rwalk", bound="multi",
                                seed=20260911 + case.seed, sim_seed=1000 + case.seed),
                   result=res, classification=classify(case, res))
        path.write_text(json.dumps(rec, indent=1))
        c = rec["classification"]
        print(f"done {case.id}: {c['shape_param']} p50={c['shape_p50']:.3f} [{c['shape_p16']:.3f},{c['shape_p84']:.3f}] "
              f"true={c['true_shape']:.3f} {c['rail_class']} covered={c['shape_covered_95']} "
              f"logZ={res['logz']:.1f}±{res['logzerr']:.1f} {res['runtime_s']:.0f}s", flush=True)

    # summary table
    rows = []
    for p in sorted(out.glob("*.json")):
        if p.name.startswith("kernel"):
            continue
        rec = json.loads(p.read_text())
        c, cs, r = rec["classification"], rec["case"], rec["result"]
        rows.append(dict(id=cs["id"], arm=cs["arm"], model=cs["model"], truth_kind=cs["truth"]["kind"],
                         true_shape=c["true_shape"], true_alpha=c["true_alpha"], snr=cs["snr"], s2_factor=cs["s2_factor"],
                         shape_param=c["shape_param"], shape_p50=c["shape_p50"], shape_p16=c["shape_p16"], shape_p84=c["shape_p84"],
                         rail_class=c["rail_class"], shape_covered_95=c["shape_covered_95"], alpha_p50=c["alpha_p50"],
                         log10_tau_true=c["log10_tau_true"], log10_tau_p50=c["log10_tau_p50"], tau_covered_95=c["tau_covered_95"],
                         logz=r["logz"], logzerr=r["logzerr"], runtime_s=round(r["runtime_s"]), note=cs["note"]))
    if rows:
        with open(out / "summary.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        print(f"wrote {out/'summary.csv'} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
