#!/usr/bin/env python3
"""Protected raw-voltage amplitude-tail probe for Zach CHIME coarse channels."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


EXPECTED_H5 = "215079a689c18b50a4b2cd8003529e34d531a326be677a86187be02e47d0f1a9"
DM = 262.4359033801
K_DM_S_MHZ2 = 4.148808e3
NATIVE_DT_S = 2.56e-6
OUTPUT_DT_S = 0.32768e-3
TRAINING = (55, 137)
SOURCE_CONTEXT = (149, 305)
ON_PULSE = (229, 273)
SAMPLES_PER_BLOCK = 128


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def shifts(frequency_mhz: np.ndarray, fpga_count: np.ndarray) -> np.ndarray:
    reference = int(np.argmax(frequency_mhz))
    offsets = (
        (fpga_count - fpga_count[reference]) * NATIVE_DT_S
        - K_DM_S_MHZ2
        * DM
        * (frequency_mhz**-2 - frequency_mhz[reference] ** -2)
    )
    offsets -= np.min(offsets)
    return np.rint(offsets / OUTPUT_DT_S).astype(np.int64)


def amplitude_kurtosis(values: np.ndarray) -> float:
    amplitude = np.abs(values[np.isfinite(values)]).astype(np.float64)
    if amplitude.size < 100:
        return float("nan")
    centered = amplitude - np.mean(amplitude)
    variance = np.mean(centered**2)
    return float(np.mean(centered**4) / variance**2) if variance > 0 else float("nan")


def positive_iterative_mad(values: np.ndarray, sigma: float = 5.0) -> tuple[np.ndarray, dict]:
    data = np.asarray(values, dtype=np.float64)
    selected = ~np.isfinite(data)
    iterations = 0
    for iteration in range(6):
        keep = ~selected
        center = float(np.median(data[keep]))
        spread = float(1.4826 * np.median(np.abs(data[keep] - center)))
        if spread <= 0:
            break
        new = keep & ((data - center) / spread > sigma)
        iterations = iteration + 1
        if not new.any():
            break
        selected |= new
    keep = ~selected
    center = float(np.median(data[keep]))
    spread = float(1.4826 * np.median(np.abs(data[keep] - center)))
    return selected & np.isfinite(data), {
        "sigma": sigma,
        "iterations": iterations,
        "retained_center": center,
        "retained_spread": spread,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--h5", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    actual_hash = sha256(args.h5)
    if actual_hash != EXPECTED_H5:
        raise ValueError(f"source H5 hash mismatch: {actual_hash}")

    from baseband_analysis.core.bbdata import BBData
    from baseband_analysis.core.dedispersion import coherent_dedisp

    data = BBData.from_file(str(args.h5))
    frequency = np.asarray(data.index_map["freq"]["centre"], dtype=np.float64)
    identifiers = np.asarray(data.index_map["freq"]["id"], dtype=np.int64)
    fpga = np.asarray(data["time0"]["fpga_count"], dtype=np.float64)
    row_shifts = shifts(frequency, fpga)
    voltage = coherent_dedisp(data, DM, time_shift=False)

    all_kurtosis = np.full(frequency.size, np.nan)
    training_kurtosis = np.full(frequency.size, np.nan)
    context_kurtosis = np.full(frequency.size, np.nan)
    used_blocks = np.zeros(frequency.size, dtype=np.int64)
    for row in range(frequency.size):
        protected = (
            ON_PULSE[0] - int(row_shifts[row]),
            ON_PULSE[1] - int(row_shifts[row]),
        )
        training_blocks = np.arange(*TRAINING)
        context_blocks = np.arange(*SOURCE_CONTEXT)
        context_blocks = context_blocks[
            (context_blocks < protected[0]) | (context_blocks >= protected[1])
        ]
        blocks = np.concatenate((training_blocks, context_blocks))

        def samples(selected_blocks: np.ndarray) -> np.ndarray:
            mask = np.zeros(voltage.shape[-1], dtype=bool)
            for block in selected_blocks:
                start = int(block) * SAMPLES_PER_BLOCK
                stop = min(start + SAMPLES_PER_BLOCK, mask.size)
                mask[start:stop] = True
            return voltage[row, :, mask]

        training_kurtosis[row] = amplitude_kurtosis(samples(training_blocks))
        context_kurtosis[row] = amplitude_kurtosis(samples(context_blocks))
        all_kurtosis[row] = amplitude_kurtosis(samples(blocks))
        used_blocks[row] = blocks.size

    selected, fit = positive_iterative_mad(all_kurtosis)
    center = fit["retained_center"]
    spread = fit["retained_spread"]
    robust_z = (all_kurtosis - center) / spread
    target_index = int(np.flatnonzero(identifiers == 156)[0])
    order = np.argsort(np.where(np.isfinite(all_kurtosis), all_kurtosis, -np.inf))[::-1]
    record = {
        "status": "development_only_protected_raw_voltage_tail_probe",
        "source_h5_sha256": actual_hash,
        "dm_pc_cm3": DM,
        "allowed_blocks": {
            "training": list(TRAINING),
            "source_context": list(SOURCE_CONTEXT),
            "protected_on_pulse_aligned": list(ON_PULSE),
            "sealed_intervals_opened": False,
        },
        "configuration": fit,
        "selected_coarse_channels": int(selected.sum()),
        "target": {
            "index": target_index,
            "coarse_id": int(identifiers[target_index]),
            "frequency_mhz": float(frequency[target_index]),
            "combined_kurtosis": float(all_kurtosis[target_index]),
            "training_kurtosis": float(training_kurtosis[target_index]),
            "context_offpulse_kurtosis": float(context_kurtosis[target_index]),
            "robust_z": float(robust_z[target_index]),
            "selected": bool(selected[target_index]),
            "descending_rank": int(np.flatnonzero(order == target_index)[0] + 1),
            "used_blocks": int(used_blocks[target_index]),
        },
        "channels": [
            {
                "index": int(row),
                "coarse_id": int(identifiers[row]),
                "frequency_mhz": float(frequency[row]),
                "combined_kurtosis": float(all_kurtosis[row]),
                "training_kurtosis": float(training_kurtosis[row]),
                "context_offpulse_kurtosis": float(context_kurtosis[row]),
                "robust_z": float(robust_z[row]),
                "selected": bool(selected[row]),
                "used_blocks": int(used_blocks[row]),
            }
            for row in range(frequency.size)
        ],
    }
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
