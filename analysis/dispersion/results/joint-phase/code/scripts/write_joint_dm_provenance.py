#!/usr/bin/env python3
"""Record code and raw-product fingerprints for a joint DM-phase run."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write(results: Path, output: Path) -> None:
    events = json.loads(results.read_text())
    inputs = []
    for event in events:
        for telescope in ("chime", "dsa"):
            path = Path(event[telescope]["input_path"])
            stat = path.stat()
            inputs.append({
                "burst": event["burst"], "telescope": telescope, "path": str(path),
                "size_bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": _sha256(path),
                "product_dm": event[telescope]["product_dm"], "shape": event[telescope]["raw_shape"],
            })
    code_paths = [
        Path("dispersion/dm_joint_phase.py"), Path("scripts/run_joint_dm_phase.py"),
        Path("scripts/render_joint_dm_diagnostics.py"), Path("scripts/validate_joint_dm_phase.py"),
    ]
    payload = {
        "created_utc": datetime.now(UTC).isoformat(),
        "git_head_at_run": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "git_branch": subprocess.check_output(["git", "branch", "--show-current"], text=True).strip(),
        "python": platform.python_version(), "numpy": np.__version__,
        "configuration": {
            "coarse_dm_step": 0.01, "fine_dm_step": 0.002,
            "cutoff_candidates_hz": [500, 1000, 1500, 2500, 5000],
            "resolution_factors_frequency_time": [[1, 1], [2, 1], [1, 2], [2, 2]],
            "crop_seconds": 0.030, "jackknife_channel_blocks": 12,
            "joint_model": "two-band Gaussian random effects; tau adjusted to Q=1 when Q>1",
        },
        "code_sha256": {str(path): _sha256(path) for path in code_paths},
        "results_sha256": _sha256(results), "inputs": inputs,
    }
    output.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=Path("results/dm_joint_phase_v2/fits.json"))
    parser.add_argument("--output", type=Path, default=Path("results/dm_joint_phase_v2/run_provenance.json"))
    args = parser.parse_args()
    write(args.results, args.output)


if __name__ == "__main__":
    main()
