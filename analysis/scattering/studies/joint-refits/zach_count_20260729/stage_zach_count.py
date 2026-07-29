#!/usr/bin/env python
"""Freeze and drive the strict Zach component-count contract for issue #205.

Runs 27 controlled joint fits: C2D3, C2D4 and C2D5 crossed with fixed
gain-prior variances 1, 10 and 100 and three seeds, under one hash-bound
contract with identical inputs, masks, channels, windows, priors and
environment. Everything except the component count, the gain-prior variance
and the seed is held fixed.

The controlled entrypoint refuses to sample until a contract already carries
the resolved fit identity, which is only knowable after preparation. Each rung
therefore runs twice: a freeze pass that stops before the sampler and emits the
resolved identity, then the real pass with that identity baked in.

Analysis-only. Nothing here imports or requires the retired pipeline package.
Every command sets PYTHONPATH to the analysis root, because a stale editable
install of the retired package otherwise wins the ``scattering`` package name.

Usage (from a CLEAN checkout, run in analysis/scattering/studies/joint-refits):

    python zach_count_20260729/stage_zach_count.py \
        --runs-root /path/to/run/root \
        --dsa-input  /path/to/zach_dsa_I_262_368_2500b_cntr_bpc.npy \
        --chime-input /path/to/zach_chime_I_262_3621_32000b_cntr_bpc.npy \
        --plan-only

Drop ``--plan-only`` to execute. ``--rung`` restricts execution to one label,
for example ``C2D4:s2-100:seed-20220207``.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOINT_REFITS = HERE.parent
ANALYSIS = next(p for p in HERE.parents if (p / "pyproject.toml").exists())

# Importing anything from the checkout writes __pycache__ directories into it,
# which makes the source tree dirty, which the controlled entrypoint refuses.
# Without this the first rung's freeze pass poisons the tree and every pass
# after it fails with "source worktree is dirty: ?? .../__pycache__/...". Must
# be set before the first import below.
#
# Deliberately NOT os.environ["PYTHONDONTWRITEBYTECODE"]: setting that after
# the interpreter has started does not change this process's sys.flags, but it
# IS inherited by children — including the reference interpreter the controlled
# runner spawns to check that its own flags are replayable. The two would then
# disagree and every controlled run would die with "interpreter flags or
# options cannot be replayed". The subprocess environment sets it explicitly
# instead, where the child sees it from startup and its own reference agrees.
sys.dont_write_bytecode = True

sys.path.insert(0, str(ANALYSIS))

from scattering.scat_analysis.controlled_run import (  # noqa: E402
    environment_identity,
    processing_environment_identity,
    sha256,
)

SCHEDULE = json.loads((HERE / "rungs.json").read_text(encoding="utf-8"))
BURST = SCHEDULE["burst"]
SAMPLER = SCHEDULE["sampler"]
ENTRYPOINT = "run_controlled_joint_fit.py"


def rung_label(count: dict, s2: int, seed: int) -> str:
    return f"{count['label']}:s2-{s2}:seed-{seed}"


def rungs() -> list[dict]:
    out = []
    for count in SCHEDULE["component_counts"]:
        for s2 in SCHEDULE["gain_prior_variances"]:
            for seed in SCHEDULE["seeds"]:
                out.append({"count": count, "gain_s2": s2, "seed": seed})
    return out


def band_configs(runs_root: Path, dsa_input: Path, chime_input: Path) -> None:
    """Write the two band run configurations shared by every rung."""
    cfg_dir = runs_root / "configs"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    telescopes = ANALYSIS / "radio_pipeline" / "resources" / "scattering_telescopes.yaml"
    sampler = ANALYSIS / "radio_pipeline" / "resources" / "scattering_sampler.yaml"
    common = {
        "chunk_size": 2000,
        "diagnostics": True,
        "dlogz": SAMPLER["dlogz"],
        "extend_chain": True,
        "fitting_method": "nested",
        "max_chunks": 5,
        "model_scan": True,
        "nlive": 400,
        "nlive_walks": 15,
        "nproc": 8,
        "onpulse_pad_factor": 0.5,
        "outer_trim": 0.15,
        "plot": True,
        "sampcfg_path": str(sampler),
        "steps": 10000,
        "telcfg_path": str(telescopes),
    }
    bands = {
        "dsa": {
            **common,
            "dm_init": 262.368,
            "f_factor": 384,
            "path": str(dsa_input),
            # t_factor 1 states the intent of issue #205 (native 32.768 us).
            # The automatic time-frequency selector currently overrides it; see
            # the resolution_contract block in rungs.json.
            "t_factor": 1,
            "telescope": "dsa",
        },
        "chime": {
            **common,
            "dm_init": 0.0,
            "f_factor": 16,
            "path": str(chime_input),
            "t_factor": 24,
            "telescope": "chime",
        },
    }
    for band, cfg in bands.items():
        lines = [f"{key}: {json.dumps(value)}" for key, value in sorted(cfg.items())]
        (cfg_dir / f"{BURST}_{band}_run.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def invocation(rung: dict) -> dict:
    """Mirror the invocation dictionary run_joint_fit.py builds, exactly."""
    return {
        "burst": BURST,
        "nlive": SAMPLER["nlive"],
        "nproc": SAMPLER["nproc"],
        "dlogz": SAMPLER["dlogz"],
        "sample": SAMPLER["sample"],
        "seed": rung["seed"],
        "beta_bounds": SAMPLER["beta_bounds"],
        "alpha_bounds": SAMPLER["alpha_bounds"],
        "marginalize_gain": SAMPLER["marginalize_gain"],
        "marginalize_gain_gp": SAMPLER["marginalize_gain_gp"],
        "mu_degree": SAMPLER["mu_degree"],
        "components_C": rung["count"]["components_C"],
        "components_D": rung["count"]["components_D"],
        "force_multi": SAMPLER["force_multi"],
        "gain_s2": rung["gain_s2"],
        "fixed_delta_dm_C": SAMPLER["fixed_delta_dm_C"],
        "fixed_delta_dm_D": SAMPLER["fixed_delta_dm_D"],
        # every rung is multi-component, so the runner forces this to false
        "shared_zeta": False,
    }


def runner_args(rung: dict, contract: Path, receipt: Path, resolved_out: Path | None) -> list[str]:
    args = [
        ENTRYPOINT,
        BURST,
        str(SAMPLER["nlive"]),
        str(SAMPLER["nproc"]),
        "--seed",
        str(rung["seed"]),
        "--gain-s2",
        str(rung["gain_s2"]),
        "--components-C",
        str(rung["count"]["components_C"]),
        "--components-D",
        str(rung["count"]["components_D"]),
        "--dlogz",
        str(SAMPLER["dlogz"]),
        "--contract",
        str(contract),
        "--receipt",
        str(receipt),
    ]
    if resolved_out is not None:
        args += ["--resolved-identity-output", str(resolved_out)]
    return args


def resolved_files(runs_root: Path) -> dict[str, Path]:
    cfg_dir = runs_root / "configs"
    scat = ANALYSIS / "scattering" / "scat_analysis"
    resources = ANALYSIS / "radio_pipeline" / "resources"
    chime_cfg = cfg_dir / f"{BURST}_chime_run.yaml"
    dsa_cfg = cfg_dir / f"{BURST}_dsa_run.yaml"

    def config_path(cfg: Path, key: str) -> Path:
        for line in cfg.read_text(encoding="utf-8").splitlines():
            name, _, raw = line.partition(": ")
            if name == key:
                return Path(json.loads(raw)).expanduser().resolve()
        raise KeyError(f"{key} missing from {cfg}")

    return {
        "chime_config": chime_cfg.resolve(),
        "dsa_config": dsa_cfg.resolve(),
        "chime_input": config_path(chime_cfg, "path"),
        "dsa_input": config_path(dsa_cfg, "path"),
        "chime_telescope_config": (resources / "scattering_telescopes.yaml").resolve(),
        "dsa_telescope_config": (resources / "scattering_telescopes.yaml").resolve(),
        "environment_lock": (ANALYSIS / "uv.lock").resolve(),
        "controlled_entrypoint": (JOINT_REFITS / ENTRYPOINT).resolve(),
        "fit_driver": (JOINT_REFITS / "run_joint_fit.py").resolve(),
        "joint_tf_prep_source": (JOINT_REFITS / "joint_tf_prep.py").resolve(),
        "burstfit_joint_source": (scat / "burstfit_joint.py").resolve(),
        "controlled_run_source": (scat / "controlled_run.py").resolve(),
        "model_grid_source": (scat / "joint_model_grid.py").resolve(),
        "diagnostic_source": (scat / "joint_fit_diagnostics.py").resolve(),
    }


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ANALYSIS), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def build_contract(rung: dict, runs_root: Path, python: Path, resolved_identity: str) -> dict:
    files = resolved_files(runs_root)
    contract_dir = runs_root / "contracts"
    label = rung_label(rung["count"], rung["gain_s2"], rung["seed"]).replace(":", "_")
    return {
        "schema": "flits-controlled-joint-fit-contract/v1",
        "burst": BURST,
        "source_revision": git("rev-parse", "HEAD"),
        "command": {
            "argv": [
                str(python.absolute()),
                *runner_args(
                    rung,
                    contract_dir / f"{label}.json",
                    runs_root / "receipts" / f"{label}.json",
                    None,
                ),
            ],
            "working_directory": str(JOINT_REFITS),
        },
        "environment_identity_sha256": environment_identity(files["environment_lock"])[
            "identity_sha256"
        ],
        "resolved_fit_identity_sha256": resolved_identity,
        "executed_source_files": [
            "controlled_entrypoint",
            "fit_driver",
            "joint_tf_prep_source",
            "burstfit_joint_source",
            "controlled_run_source",
            "model_grid_source",
            "diagnostic_source",
        ],
        "fit_configuration": invocation(rung),
        "files": {
            name: {"path": str(path), "sha256": sha256(path)} for name, path in sorted(files.items())
        },
        "environment_variables": processing_environment_identity(ANALYSIS, runs_root),
    }


def subprocess_env(runs_root: Path) -> dict[str, str]:
    """Environment for a controlled run.

    ``PYTHONPATH`` puts the analysis checkout ahead of a stale editable install
    of the retired pipeline package, which otherwise wins the ``scattering``
    package name. ``PYTHONDONTWRITEBYTECODE`` keeps the child from writing
    ``__pycache__`` into the source tree and tripping the dirty-tree gate.

    Note that ``-B`` on the command line would not do: the controlled runner
    records its own argv and rejects interpreter flags it cannot replay. The
    environment variable sets the same flag while staying out of argv, and the
    runner's own reference interpreter inherits it, so the two agree.
    """
    return {
        **os.environ,
        "PYTHONPATH": str(ANALYSIS),
        "PYTHONDONTWRITEBYTECODE": "1",
        **processing_environment_identity(ANALYSIS, runs_root),
    }


def run(argv: list[str], runs_root: Path, python: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(python.absolute()), *argv],
        cwd=JOINT_REFITS,
        env=subprocess_env(runs_root),
        check=False,
    )


def execute(rung: dict, runs_root: Path, python: Path) -> None:
    label = rung_label(rung["count"], rung["gain_s2"], rung["seed"]).replace(":", "_")
    contract_dir = runs_root / "contracts"
    receipt_dir = runs_root / "receipts"
    contract_dir.mkdir(parents=True, exist_ok=True)
    receipt_dir.mkdir(parents=True, exist_ok=True)
    contract = contract_dir / f"{label}.json"
    receipt = receipt_dir / f"{label}.json"
    resolved = contract_dir / f"{label}.resolved.json"

    # Freeze pass: a placeholder identity gets us past preflight and stops
    # before the sampler, emitting the identity the real pass must carry.
    contract.write_text(
        json.dumps(build_contract(rung, runs_root, python, "0" * 64), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    freeze_receipt = receipt_dir / f"{label}.freeze.json"
    freeze_receipt.unlink(missing_ok=True)
    resolved.unlink(missing_ok=True)
    run(runner_args(rung, contract, freeze_receipt, resolved), runs_root, python)
    if not resolved.is_file():
        raise SystemExit(f"[{label}] freeze pass did not emit a resolved identity")
    identity = json.loads(resolved.read_text(encoding="utf-8"))["identity_sha256"]

    # Real pass: the incomplete freeze receipt must not survive into it.
    freeze_receipt.unlink(missing_ok=True)
    receipt.unlink(missing_ok=True)
    contract.write_text(
        json.dumps(build_contract(rung, runs_root, python, identity), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    completed = run(runner_args(rung, contract, receipt, None), runs_root, python)
    if completed.returncode != 0:
        raise SystemExit(f"[{label}] controlled run failed with code {completed.returncode}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs-root", type=Path, required=True)
    ap.add_argument("--dsa-input", type=Path, required=True)
    ap.add_argument("--chime-input", type=Path, required=True)
    ap.add_argument("--python", type=Path, default=Path(sys.executable))
    ap.add_argument("--rung", action="append", help="restrict to these rung labels")
    ap.add_argument("--plan-only", action="store_true", help="print the schedule and stop")
    args = ap.parse_args()

    selected = rungs()
    if args.rung:
        wanted = set(args.rung)
        selected = [
            r for r in selected if rung_label(r["count"], r["gain_s2"], r["seed"]) in wanted
        ]
        if not selected:
            raise SystemExit("no rung matched")

    if args.plan_only:
        for rung in selected:
            print(rung_label(rung["count"], rung["gain_s2"], rung["seed"]))
        print(f"{len(selected)} rungs; run root {args.runs_root}")
        return

    if shutil.which("git") is None:
        raise SystemExit("git is required to bind the source revision")
    status = git("status", "--porcelain", "--untracked-files=all")
    if status:
        raise SystemExit(
            "the analysis checkout is dirty; the controlled entrypoint will refuse it.\n"
            f"first offending path: {status.splitlines()[0]}"
        )

    args.runs_root.mkdir(parents=True, exist_ok=True)
    band_configs(args.runs_root, args.dsa_input.resolve(), args.chime_input.resolve())
    for rung in selected:
        label = rung_label(rung["count"], rung["gain_s2"], rung["seed"])
        print(f"=== {label} ===", flush=True)
        execute(rung, args.runs_root, args.python)


if __name__ == "__main__":
    main()
