#!/usr/bin/env python3
"""Re-harvest JointTF v2 jobs 169-182 and bind the result to h17 artifacts.

Run locally. The script sends its worker mode to h17 over SSH, performs only
read-only inspection there, and writes one JSON manifest locally.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


RUNS = Path("/home/ubuntu/flits-runs")
WORKTREE = Path("/home/ubuntu/worktrees/joint-tf-fits")
PYTHON = "/home/ubuntu/anaconda3/envs/flits-a1-312/bin/python"

JOBS = {
    169: ("jtf", "oran", "C1D1", 10, False),
    170: ("jtf", "oran", "C2D1", 10, False),
    171: ("jtf", "oran", "C1D1", 100, False),
    172: ("jtf", "oran", "C2D1", 100, False),
    173: ("jtf", "johndoeII", "C1D2", 10, False),
    174: ("jtf", "johndoeII", "C2D2", 10, False),
    175: ("jtf", "johndoeII", "C1D2", 100, False),
    176: ("jtf", "johndoeII", "C2D2", 100, False),
    177: ("jtfzf", "zach", "C2D3", 10, True),
    178: ("jtfzf", "zach", "C2D3", 100, True),
    179: ("jtfzf", "zach", "C2D4", 10, True),
    180: ("jtfzf", "zach", "C2D4", 100, True),
    181: ("jtfzf", "zach", "C2D5", 10, True),
    182: ("jtfzf", "zach", "C2D5", 100, True),
}

CODE_PATHS = [
    WORKTREE / "analysis/scattering-refit-2026-06/run_joint_fit.py",
    WORKTREE / "analysis/scattering-refit-2026-06/run_joint_fit_zachfine.py",
    WORKTREE / "analysis/scattering-refit-2026-06/joint_tf_prep.py",
    WORKTREE / "scattering/scat_analysis/burstfit_joint.py",
    RUNS / "jobs/fit.sbatch",
    RUNS / "jobs/fit_zachfine.sbatch",
]

FIGURES = [
    RUNS / "data/joint/_v2_harvest_20260719/v2_harvest_vet.png",
    RUNS / "data/joint/_v2_harvest_20260719/zach_v2_ladder_vet.png",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: Path) -> dict:
    stat = path.stat()
    return {
        "path": str(path),
        "size_bytes": stat.st_size,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "sha256": sha256(path),
    }


def parse_path_from_config(path: Path) -> Path:
    for line in path.read_text().splitlines():
        if line.startswith("path:"):
            return Path(line.split(":", 1)[1].strip())
    raise ValueError(f"no input path in {path}")


def output_paths(burst: str, config: str, gain_s2: int, fine: bool) -> tuple[Path, Path]:
    suffix = f"{config}_s2-{gain_s2}" + ("_fine" if fine else "")
    root = RUNS / "data/joint"
    return (
        root / f"{burst}_joint_fit_{suffix}.json",
        root / f"{burst}_joint_samples_{suffix}.npz",
    )


def parse_log(path: Path) -> dict:
    text = path.read_text(errors="replace")
    header = text.splitlines()[0]
    done = text.splitlines()[-1]
    result = {
        "header": header,
        "done": done,
        "rc": int(re.search(r"\bRC=(\d+)", done).group(1)),
        "wall_seconds": int(re.search(r"\bWALL_SEC=(\d+)", done).group(1)),
        "start": re.search(r"\bSTART=(\S+)", header).group(1),
        "end": re.search(r"\bEND=(\S+)", done).group(1),
        "nlive": int(re.search(r"\bNLIVE=(\d+)", header).group(1)),
        "nproc": int(re.search(r"\bNPROC=(\d+)", header).group(1))
        if "NPROC=" in header
        else 1,
        "extra_args": re.search(r"\bEARGS=\[(.*?)\]", header).group(1),
        "bands": {},
    }
    band_re = re.compile(
        r"AUTO-TF (CHIME|DSA)\s*: (\d+) ch x ([0-9.]+) MHz, dt=([0-9.]+) us "
        r"\(f(\d+)/t(\d+)\); window ([0-9.]+) ms; peak S/N ([0-9.]+)/px"
    )
    for match in band_re.finditer(text):
        result["bands"][match.group(1)] = {
            "channels": int(match.group(2)),
            "channel_width_mhz": float(match.group(3)),
            "dt_us": float(match.group(4)),
            "frequency_factor": int(match.group(5)),
            "time_factor": int(match.group(6)),
            "window_ms": float(match.group(7)),
            "peak_snr_per_pixel": float(match.group(8)),
        }
    return result


def interval(record: dict) -> list[float]:
    return [record["lower"], record["median"], record["upper"]]


def worker() -> dict:
    job_records = []
    for job_id, (prefix, burst, config, gain_s2, fine) in JOBS.items():
        log_path = RUNS / f"logs/{prefix}_{job_id}.out"
        err_path = RUNS / f"logs/{prefix}_{job_id}.err"
        fit_path, samples_path = output_paths(burst, config, gain_s2, fine)
        fit = json.loads(fit_path.read_text())
        parsed_log = parse_log(log_path)
        t0 = {}
        zeta = {}
        containment = {}
        for name, record in fit["percentiles"].items():
            if name.startswith("t0_"):
                band = name.split("_", 1)[1][0]
                window = parsed_log["bands"]["CHIME" if band == "C" else "DSA"]["window_ms"]
                values = interval(record)
                t0[name] = values
                containment[name] = {
                    "window_ms": [0.0, window],
                    "median_in_window": 0.0 <= values[1] <= window,
                    "central_interval_in_window": 0.0 <= values[0] and values[2] <= window,
                }
            elif name.startswith("zeta_"):
                zeta[name] = interval(record)
        artifacts = [file_record(log_path), file_record(fit_path), file_record(samples_path)]
        if err_path.exists():
            artifacts.append(file_record(err_path))
        job_records.append(
            {
                "job_id": job_id,
                "burst": burst,
                "config": config,
                "gain_s2": gain_s2,
                "fine": fine,
                "log": parsed_log,
                "fit": {
                    "log_evidence": fit["log_evidence"],
                    "log_evidence_err": fit["log_evidence_err"],
                    "beta": interval(fit["percentiles"]["beta"]),
                    "beta_bounds": fit["beta_bounds"],
                    "alpha": interval(fit["percentiles"]["alpha"]),
                    "tau_1ghz_ms": interval(fit["percentiles"]["tau_1ghz"]),
                    "ncall": fit["ncall"],
                    "t0_ms": t0,
                    "zeta": zeta,
                    "containment": containment,
                },
                "artifacts": artifacts,
            }
        )

    by_id = {item["job_id"]: item for item in job_records}
    pairs = [
        ("oran C2-C1 s2=10", 170, 169),
        ("oran C2-C1 s2=100", 172, 171),
        ("johndoeII C2-C1 s2=10", 174, 173),
        ("johndoeII C2-C1 s2=100", 176, 175),
        ("zach D4-D3 s2=10", 179, 177),
        ("zach D5-D4 s2=10", 181, 179),
        ("zach D5-D3 s2=10", 181, 177),
        ("zach D4-D3 s2=100", 180, 178),
        ("zach D5-D4 s2=100", 182, 180),
        ("zach D5-D3 s2=100", 182, 178),
    ]
    comparisons = []
    for label, new_id, base_id in pairs:
        new = by_id[new_id]["fit"]
        base = by_id[base_id]["fit"]
        new_beta, base_beta = new["beta"], base["beta"]
        comparisons.append(
            {
                "label": label,
                "new_job": new_id,
                "base_job": base_id,
                "delta_log_evidence": new["log_evidence"] - base["log_evidence"],
                "delta_log_evidence_err_quadrature": math.hypot(
                    new["log_evidence_err"], base["log_evidence_err"]
                ),
                "delta_beta_median": new_beta[1] - base_beta[1],
                "beta_central_intervals_overlap": not (
                    new_beta[2] < base_beta[0] or base_beta[2] < new_beta[0]
                ),
            }
        )

    configs = []
    inputs_seen = set()
    inputs = []
    for burst in ("oran", "johndoeII", "zach"):
        for band in ("chime", "dsa"):
            config_path = RUNS / f"configs/{burst}_{band}_run.yaml"
            input_path = parse_path_from_config(config_path)
            configs.append(file_record(config_path))
            if input_path not in inputs_seen:
                inputs_seen.add(input_path)
                inputs.append(file_record(input_path))

    git_status = subprocess.check_output(
        ["git", "status", "--short", "--", *map(str, CODE_PATHS[:4])],
        cwd=WORKTREE,
        text=True,
    ).splitlines()
    git_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=WORKTREE, text=True
    ).strip()
    from importlib.metadata import distributions

    packages = {
        dist.metadata["Name"]: dist.version
        for dist in distributions()
        if dist.metadata["Name"]
    }
    conda_explicit = subprocess.check_output(
        ["/home/ubuntu/anaconda3/bin/conda", "list", "--explicit", "-n", "flits-a1-312"],
        text=True,
    ).splitlines()
    cpu_model = "unknown"
    for line in Path("/proc/cpuinfo").read_text().splitlines():
        if line.startswith("model name"):
            cpu_model = line.split(":", 1)[1].strip()
            break
    sampler_source = (WORKTREE / "scattering/scat_analysis/burstfit_joint.py").read_text()
    production_sampler_has_rstate = "rstate=" in sampler_source

    return {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Independent read-only re-harvest of JointTF prior-spec v2 jobs 169-182",
        "host": {"hostname": platform.node(), "user": os.environ.get("USER")},
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "cpu_model": cpu_model,
            "cpu_count": os.cpu_count(),
            "python_distributions": dict(sorted(packages.items(), key=lambda item: item[0].lower())),
            "conda_explicit": conda_explicit,
            "conda_explicit_sha256": hashlib.sha256(
                ("\n".join(conda_explicit) + "\n").encode()
            ).hexdigest(),
        },
        "code": {
            "worktree": str(WORKTREE),
            "git_sha": git_sha,
            "tracked_state_for_executed_paths": git_status,
            "files_at_revalidation": [file_record(path) for path in CODE_PATHS],
            "production_sampler_has_rstate": production_sampler_has_rstate,
            "seed_status": "ABSENT: no seed in logs/results; production sampler call has no rstate"
            if not production_sampler_has_rstate
            else "REVIEW REQUIRED: sampler source contains rstate",
            "warning": "Hashes describe files at revalidation. Uncommitted files are not proven immutable since execution.",
        },
        "configs": configs,
        "inputs": inputs,
        "jobs": job_records,
        "comparisons": comparisons,
        "figures": [file_record(path) for path in FIGURES],
        "checks": {
            "jobs_present": len(job_records),
            "all_rc_zero": all(item["log"]["rc"] == 0 for item in job_records),
            "all_json_npz_present": all(len(item["artifacts"]) >= 3 for item in job_records),
            "all_t0_medians_in_window": all(
                check["median_in_window"]
                for item in job_records
                for check in item["fit"]["containment"].values()
            ),
            "all_t0_central_intervals_in_window": all(
                check["central_interval_in_window"]
                for item in job_records
                for check in item["fit"]["containment"].values()
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--host", default="h17")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        json.dump(worker(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return
    if args.output is None:
        parser.error("--output is required outside worker mode")
    source = Path(__file__).read_bytes()
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", args.host, PYTHON, "-", "--worker"],
        input=source,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    manifest = json.loads(result.stdout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"wrote {args.output}")
    print(json.dumps(manifest["checks"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
