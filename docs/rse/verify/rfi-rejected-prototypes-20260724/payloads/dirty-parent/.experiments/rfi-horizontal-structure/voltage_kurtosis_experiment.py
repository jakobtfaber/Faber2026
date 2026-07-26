#!/usr/bin/env python3
"""Known-truth test for protected raw-voltage kurtosis selection."""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
from pathlib import Path

import numpy as np


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("candidate", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(args: argparse.Namespace) -> dict:
    candidate = load_module(args.candidate_script)
    rng = np.random.default_rng(args.seed)
    shape = (871, 2, 4096)
    clean = (
        rng.standard_normal(shape) + 1j * rng.standard_normal(shape)
    ).astype(np.complex64)
    allowed = np.ones((shape[0], shape[2]), dtype=bool)
    protected = (1600, 2400)
    allowed[:, protected[0] : protected[1]] = False
    burst = clean.copy()
    burst[:, :, protected[0] : protected[1]] += 30.0 + 30.0j

    broadband = burst.copy()
    broadband_columns = np.array([400, 900, 3000])
    broadband[:, :, broadband_columns] += 50.0 + 50.0j

    contaminated = broadband.copy()
    truth_channels = np.linspace(7, shape[0] - 8, 28, dtype=int)
    allowed_columns = np.flatnonzero(allowed[0])
    for channel in truth_channels:
        row_columns = rng.choice(allowed_columns, size=20, replace=False)
        contaminated[channel, :, row_columns] += 80.0 + 80.0j

    valid = np.ones(shape[0], dtype=bool)
    selected, diagnostics = candidate.select_voltage_kurtosis_channels(
        contaminated, valid, allowed
    )
    clean_selected, _ = candidate.select_voltage_kurtosis_channels(
        burst, valid, allowed
    )
    broadband_selected, _ = candidate.select_voltage_kurtosis_channels(
        broadband, valid, allowed
    )
    changed = contaminated.copy()
    changed[:, :, protected[0] : protected[1]] = 1e12 + 1e12j
    changed_selected, _ = candidate.select_voltage_kurtosis_channels(
        changed, valid, allowed
    )

    truth = np.zeros(shape[0], dtype=bool)
    truth[truth_channels] = True
    return {
        "status": "throwaway_known_truth_protected_voltage_kurtosis",
        "seed": args.seed,
        "shape": list(shape),
        "protected": list(protected),
        "configuration": {
            "sigma": candidate.KURTOSIS_SIGMA,
            "iterations": candidate.KURTOSIS_ITERATIONS,
            "minimum_voltage_samples": candidate.MINIMUM_VOLTAGE_SAMPLES,
            "broadband_voltage_sigma": candidate.BROADBAND_VOLTAGE_SIGMA,
            "maximum_broadband_channel_fraction": candidate.MAXIMUM_BROADBAND_CHANNEL_FRACTION,
        },
        "truth_channels": int(truth.sum()),
        "recovered_truth_channels": int(np.sum(selected & truth)),
        "missed_truth_channels": int(np.sum(~selected & truth)),
        "additional_nontruth_channels": int(np.sum(selected & ~truth)),
        "selected_clean_control_channels": int(clean_selected.sum()),
        "selected_broadband_control_channels": int(broadband_selected.sum()),
        "protected_values_invariant": bool(np.array_equal(selected, changed_selected)),
        "burst_support_loss_fraction": float(selected.sum() / selected.size),
        "diagnostics": {
            key: value
            for key, value in diagnostics.items()
            if not isinstance(value, np.ndarray)
        },
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-script", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = run(args)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
