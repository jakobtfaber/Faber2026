"""Production-path injection: does the July 2026 campaign fitter rail at beta=4
when the true frequency scaling is shallower than nu^-4?

This is the code audit's "cheapest decisive test" (code-audit.md, Section 8,
row 9). Unlike injection_recovery.py, which re-implements the model, this
script pushes synthetic two-band data through the exact production entry point
`scattering.scat_analysis.burstfit_joint.fit_joint_scattering` on the
shared-zeta path with the campaign beta prior [3, 4].

Cases (all exponential-kernel truths except the control):
  exp-a3.0   tau(nu) = tau_1GHz nu^-3.0    -> model cannot express; rail at 4 expected
  exp-a4.0   tau(nu) = tau_1GHz nu^-4.0    -> exponential endpoint; rail at 4 expected
  thin-b3.67 production power-law PBF, beta = 3.67 (alpha 4.40) -> interior expected
  exp-a4.4   exponential kernel with alpha 4.40 (same scaling as the control but
             no power-law tail) -> tests whether beta is read from the tau ratio
             rather than tail shape (code-audit.md Section 6)
  thin-b3.67-tau0.2  the thin control with tau_1GHz = 0.2 ms so the DSA-band tau is
             resolved (2.4 samples) -> resolution control for the low-beta bias
             seen in thin-b3.67 (DSA-band tau 0.6 sample)

Run:  cd analysis && MPLCONFIGDIR=$TMPDIR/mpl .venv/bin/python \
        docs/rse/specs/research/method-reassessment-2026-09-11/production_path_injection.py --nproc 4
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ANALYSIS_ROOT = HERE.parents[4]
sys.path.insert(0, str(ANALYSIS_ROOT))

from scattering.scat_analysis.burstfit import (  # noqa: E402
    FRBModel,
    FRBParams,
    analytic_gaussian_exp_convolution,
)
from scattering.scat_analysis.burstfit_init import data_driven_initial_guess  # noqa: E402
from scattering.scat_analysis.burstfit_joint import fit_joint_scattering  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "run_beta_poc", ANALYSIS_ROOT / "scattering" / "studies" / "beta-proof-of-concept" / "run_beta_poc.py"
)
_poc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_poc)

BETA_BOUNDS = (3.0, 4.0)
TAU_TRUE = 0.05  # tau_1GHz [ms], as in the proof-of-concept (freya-like)

CASES = [
    # name, kernel, shape (alpha for exp, beta for thin), chime window [ms], expect, tau_1GHz [ms]
    ("exp-a3.0", "exp", 3.0, 32.0, "rail-ceiling", TAU_TRUE),
    ("exp-a4.0", "exp", 4.0, 32.0, "rail-ceiling", TAU_TRUE),
    ("thin-b3.67", "thin", 3.67, 32.0, "interior", TAU_TRUE),
    ("exp-a4.4", "exp", 4.4, 32.0, "interior-if-ratio-driven", TAU_TRUE),
    # resolution control: same thin truth with the DSA-band tau resolved (about 2.4 samples at 1.4 GHz)
    ("thin-b3.67-tau0.2", "thin", 3.67, 32.0, "interior", 0.2),
]


def _inject_exp(m: FRBModel, tau_1ghz: float, alpha: float, z1: float, x: float, t0: float, rng):
    """Same gains and noise as run_beta_poc._inject, exponential kernel with free alpha."""
    freq = np.asarray(m.freq, float)
    tau_nu = tau_1ghz * freq ** (-alpha)
    zeta_nu = z1 * freq ** x
    t2d = np.broadcast_to(np.asarray(m.time, float)[None, :], (freq.size, m.time.size)).copy()
    kernel = analytic_gaussian_exp_convolution(t2d, t0, zeta_nu[:, None], tau_nu[:, None])
    envelope = (freq / np.median(freq)) ** -1.5
    scint = np.exp(rng.normal(0.0, 0.2, size=freq.size))
    gain = 20.0 * envelope * scint
    clean = gain[:, None] * kernel
    sigma = float(np.max(clean)) / 20.0
    data = clean + rng.normal(0.0, sigma, size=clean.shape)
    return FRBModel(time=m.time, freq=m.freq, data=data, dm_init=0.0, df_MHz=m.df_MHz,
                    noise_std=np.full(freq.size, sigma))


def make_bands(kernel: str, shape: float, t_max_C: float, seed: int, tau_1ghz: float = TAU_TRUE):
    rng = np.random.default_rng(seed)
    n_time_C = int(448 * t_max_C / 32.0)
    m_C0 = _poc._build_band(_poc.CHIME, n_freq=48, t_max=t_max_C, n_time=n_time_C)
    m_D0 = _poc._build_band(_poc.DSA, n_freq=48, t_max=6.0, n_time=320)
    if kernel == "thin":
        m_C = _poc._inject(m_C0, tau_1ghz, shape, _poc.ZETA1_TRUE, _poc.X_ZETA_TRUE, _poc.T0_C_TRUE, rng)
        m_D = _poc._inject(m_D0, tau_1ghz, shape, _poc.ZETA1_TRUE, _poc.X_ZETA_TRUE, _poc.T0_D_TRUE, rng)
    else:
        m_C = _inject_exp(m_C0, tau_1ghz, shape, _poc.ZETA1_TRUE, _poc.X_ZETA_TRUE, _poc.T0_C_TRUE, rng)
        m_D = _inject_exp(m_D0, tau_1ghz, shape, _poc.ZETA1_TRUE, _poc.X_ZETA_TRUE, _poc.T0_D_TRUE, rng)
    return m_C, m_D


def _init_for(m):
    return data_driven_initial_guess(data=m.data, freq=m.freq, time=m.time, dm=0.0, verbose=False).params


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nproc", type=int, default=4)
    ap.add_argument("--nlive", type=int, default=200)
    ap.add_argument("--maxcall", type=int, default=400_000)
    ap.add_argument("--only", action="append")
    ap.add_argument("--out", default=str(HERE / "results" / "production-path"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    seed = 20260911
    for name, kernel, shape, t_max_C, expect, tau_1ghz in CASES:
        if args.only and name not in args.only:
            continue
        path = out / f"{name}.json"
        if path.exists():
            print(f"skip {name}", flush=True)
            continue
        m_C, m_D = make_bands(kernel, shape, t_max_C, seed, tau_1ghz)
        print(f"run  {name}: kernel={kernel} shape={shape} expect={expect}", flush=True)
        t_start = time.time()
        res = fit_joint_scattering(
            model_C=m_C, init_C=_init_for(m_C), model_D=m_D, init_D=_init_for(m_D),
            beta_bounds=BETA_BOUNDS, nlive=args.nlive, nproc=args.nproc, shared_zeta=True,
            verbose=False, rstate=np.random.default_rng(seed + 1), maxcall=args.maxcall,
        )
        names = list(res["param_names"])
        w = np.asarray(res["weights"], float)
        s = np.asarray(res["samples"], float)
        ib = names.index("beta")
        edge_hi = float(np.sum(w[s[:, ib] >= BETA_BOUNDS[1] - 0.01]) / w.sum())
        edge_lo = float(np.sum(w[s[:, ib] <= BETA_BOUNDS[0] + 0.01]) / w.sum())
        b = res["percentiles"]["beta"]
        from dynesty.utils import resample_equal
        eq = resample_equal(s, w / w.sum(), rstate=np.random.default_rng(0))
        beta_eq = eq[:, ib]
        mass_above = {str(thr): float(np.mean(beta_eq >= thr)) for thr in (3.90, 3.95, 3.98, 3.99)}
        beta_q = {str(q): float(np.percentile(beta_eq, q)) for q in (2.5, 16, 50, 84, 97.5)}
        rec = dict(
            case=name, kernel=kernel, shape_true=shape, tau_1ghz_true=tau_1ghz,
            alpha_true=(shape if kernel == "exp" else 2 * shape / (shape - 2)),
            expect=expect, beta_bounds=BETA_BOUNDS, nlive=args.nlive, maxcall=args.maxcall, seed=seed,
            beta=dict(median=b["median"], err_minus=b["err_minus"], err_plus=b["err_plus"]),
            alpha_derived=res["percentiles"]["alpha"]["median"],
            tau_1ghz=res["percentiles"]["tau_1ghz"],
            param_names=names, percentiles=res["percentiles"],
            max_loglike_sample=[float(v) for v in s[int(np.argmax(np.asarray(res["logl"], float)))]] if "logl" in res else None,
            edge_mass_beta=dict(low=edge_lo, high=edge_hi),
            rail_class=("ceiling-rail" if edge_hi > 0.05 else "floor-rail" if edge_lo > 0.05 else "interior"),
            near_ceiling=bool(mass_above["3.95"] > 0.5),
            mass_above=mass_above, beta_quantiles=beta_q,
            beta_samples=[round(float(v), 5) for v in beta_eq[:: max(1, beta_eq.size // 4000)]],
            log_evidence=res["log_evidence"], log_evidence_err=res["log_evidence_err"],
            ncall=int(np.asarray(res["ncall_history"]).sum()), runtime_s=time.time() - t_start,
            entry_point="scattering.scat_analysis.burstfit_joint.fit_joint_scattering(shared_zeta=True)",
        )
        path.write_text(json.dumps(rec, indent=1))
        print(f"done {name}: beta={b['median']:.3f} -{b['err_minus']:.3f}/+{b['err_plus']:.3f} "
              f"edge_hi={edge_hi:.2f} mass>=3.95={mass_above['3.95']:.2f} {rec['rail_class']} alpha_derived={rec['alpha_derived']:.2f} "
              f"logZ={rec['log_evidence']:.1f} {rec['runtime_s']:.0f}s", flush=True)


if __name__ == "__main__":
    main()
