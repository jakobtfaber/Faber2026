#!/usr/bin/env python
"""Whitney C2D2 refit with per-component t0/zeta windows.

This is a scratch science run, not a pipeline API. It keeps the same likelihood
as the current multi-component joint fit but narrows each temporal component to
the visible sub-burst it is intended to model.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import sys
from pathlib import Path

import numpy as np
import yaml

REPO = Path(os.environ.get("FLITS_REPO", "/Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026/pipeline"))
RUNS = Path(os.environ.get("FLITS_RUNS", "/Users/jakobfaber/Developer/scratch/flits-whitney-c2d2-cwin-20260707"))
sys.path.insert(0, str(REPO / "scattering"))

from dynesty import NestedSampler  # noqa: E402
from scat_analysis.burstfit import FRBParams  # noqa: E402
from scat_analysis.burstfit_init import data_driven_initial_guess  # noqa: E402
from scat_analysis.burstfit_joint import (  # noqa: E402
    _JointLogLikelihoodGainMulti,
    _JointPriorTransform,
    _append_derived_alpha_percentiles,
    _weighted_percentiles,
    alpha_from_beta,
)
from scat_analysis.config_utils import load_telescope_block  # noqa: E402
from scat_analysis.pipeline.io import BurstDataset  # noqa: E402
from scat_analysis.pipeline.optimization import refine_initial_guess_mle  # noqa: E402


BURST = "whitney_c2d2_cwin_20260707"
SOURCE_BURST = "whitney_multid_20260707"
SRC_RUNS = Path("/Users/jakobfaber/Developer/scratch/flits-whitney-multiplicity-20260707")


def prepare(cfg_path: Path, name: str, outdir: Path):
    cfg = yaml.safe_load(cfg_path.read_text())
    tel = load_telescope_block(cfg["telcfg_path"], cfg["telescope"])
    ds = BurstDataset(
        cfg["path"],
        str(outdir),
        name=name,
        telescope=tel,
        f_factor=int(cfg["f_factor"]),
        t_factor=int(cfg["t_factor"]),
        outer_trim=float(cfg.get("outer_trim", 0.15)),
        onpulse_crop=True,
        onpulse_pad_factor=0.5,
    )
    model = ds.model
    model.dm_init = float(cfg.get("dm_init", 0.0))
    init = data_driven_initial_guess(
        data=model.data,
        freq=model.freq,
        time=model.time,
        dm=model.dm_init,
        verbose=False,
    ).params
    init = refine_initial_guess_mle(model, init)
    return model, init


def write_configs() -> None:
    cfg_dir = RUNS / "configs"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    for band in ("chime", "dsa"):
        src = SRC_RUNS / "configs" / f"{SOURCE_BURST}_{band}_run.yaml"
        dst = cfg_dir / f"{BURST}_{band}_run.yaml"
        cfg = yaml.safe_load(src.read_text())
        dst.write_text(yaml.safe_dump(cfg, sort_keys=False))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nlive", type=int, default=120)
    ap.add_argument("--nproc", type=int, default=4)
    ap.add_argument("--dlogz", type=float, default=0.5)
    ap.add_argument("--suffix", default="_C2D2_cwin")
    args = ap.parse_args()

    write_configs()
    out = RUNS / "data" / "joint"
    out.mkdir(parents=True, exist_ok=True)
    model_C, init_C = prepare(RUNS / "configs" / f"{BURST}_chime_run.yaml", f"{BURST}_chime", out)
    model_D, init_D = prepare(RUNS / "configs" / f"{BURST}_dsa_run.yaml", f"{BURST}_dsa", out)

    names = (
        "tau_1ghz",
        "beta",
        "t0_C1",
        "zeta_C1",
        "t0_C2",
        "zeta_C2",
        "delta_dm_C",
        "t0_D1",
        "zeta_D1",
        "t0_D2",
        "zeta_D2",
        "delta_dm_D",
    )
    # Windows from the formatted prototype/profile inspection:
    # CHIME data peaks near 1.60 and 2.21 ms; DSA near 28.64 and 28.97 ms.
    spec = [
        ("tau_1ghz", (0.005, 0.12), True),
        ("beta", (3.0, 4.0), False),
        ("t0_C1", (1.45, 1.80), False),
        ("zeta_C1", (0.03, 0.12), True),
        ("t0_C2", (2.16, 2.32), False),
        ("zeta_C2", (0.025, 0.09), True),
        ("delta_dm_C", (-0.08, 0.08), False),
        ("t0_D1", (28.56, 28.70), False),
        ("zeta_D1", (0.025, 0.09), True),
        ("t0_D2", (28.88, 29.05), False),
        ("zeta_D2", (0.035, 0.13), True),
        ("delta_dm_D", (-0.08, 0.08), False),
    ]
    ptform = _JointPriorTransform(spec)
    loglike = _JointLogLikelihoodGainMulti(model_C, model_D, n_C=2, n_D=2, s2=None)

    if args.nproc > 1:
        with mp.Pool(args.nproc) as pool:
            sampler = NestedSampler(
                loglike,
                ptform,
                ndim=len(names),
                nlive=args.nlive,
                sample="rwalk",
                queue_size=args.nproc,
                pool=pool,
            )
            sampler.run_nested(dlogz=args.dlogz, print_progress=True)
            res = sampler.results
    else:
        sampler = NestedSampler(
            loglike,
            ptform,
            ndim=len(names),
            nlive=args.nlive,
            sample="rwalk",
            queue_size=1,
            pool=None,
        )
        sampler.run_nested(dlogz=args.dlogz, print_progress=True)
        res = sampler.results
    samples = np.asarray(res.samples)
    weights = np.exp(np.asarray(res.logwt) - float(res.logz[-1]))
    pct = _weighted_percentiles(samples, weights, names)
    pct = _append_derived_alpha_percentiles(pct, samples, weights, names)

    fit = {
        "burst": BURST,
        "source_burst": SOURCE_BURST,
        "fit_note": "Whitney C2D2 diagnostic resolved-CHIME prior; CHIME components kept narrow and tau allowed lower to test two-pulse morphology",
        "marginalize_gain": False,
        "marginalize_gain_gp": False,
        "shared_zeta": False,
        "beta": pct["beta"],
        "beta_bounds": [3.0, 4.0],
        "alpha": pct["alpha"],
        "tau_1ghz": pct["tau_1ghz"],
        "log_evidence": float(res.logz[-1]),
        "log_evidence_err": float(res.logzerr[-1]),
        "alpha_bounds": [alpha_from_beta(4.0), alpha_from_beta(3.0)],
        "components_C": 2,
        "components_D": 2,
        "component_windows": {name: list(bounds) for name, bounds, _ in spec},
        "gain_s2": None,
        "percentiles": {name: pct[name] for name in names + ("alpha",)},
        "ncall": int(np.sum(res.ncall)),
    }
    fit_path = out / f"{BURST}_joint_fit{args.suffix}.json"
    fit_path.write_text(json.dumps(fit, indent=2))
    np.savez_compressed(
        out / f"{BURST}_joint_samples{args.suffix}.npz",
        samples=samples,
        weights=weights,
        param_names=np.asarray(names, dtype=object),
        alpha_bounds=np.asarray(fit["alpha_bounds"]),
        freq_C=np.asarray(model_C.freq),
        freq_D=np.asarray(model_D.freq),
    )
    print(f"wrote {fit_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
