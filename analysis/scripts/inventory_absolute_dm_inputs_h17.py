#!/usr/bin/env python3
"""Inventory Phase B inputs for a paused experimental diagnostic.

This inventory is not science authority.
"""

from __future__ import annotations

import argparse
import csv
import json
import warnings
from pathlib import Path
from typing import Any

import h5py
import numpy as np
from absolute_dm_voltage import K_DM_S_MHZ2
from scipy.signal import correlate

ROLES = (
    "raw_chime_h5",
    "accepted_chime_reference",
    "raw_dsa_filterbank",
    "accepted_dsa_reference",
)
REFERENCE_FREQUENCY_MHZ = 400.0
RESULT_STATUS = (
    "phase_b_paused_experimental_diagnostic_input_inventory_"
    "not_science_authority"
)


def load_path_manifest(path: Path) -> dict[str, dict[str, Path]]:
    """Load and strictly validate event/role/path triples."""

    events: dict[str, dict[str, Path]] = {}
    with path.open(newline="") as handle:
        for row_number, row in enumerate(
            csv.reader(handle, delimiter="\t"),
            start=1,
        ):
            if len(row) != 3:
                raise ValueError(f"{path}:{row_number}: expected three columns")
            event, role, raw_path = row
            if not event or role not in ROLES or not Path(raw_path).is_absolute():
                raise ValueError(f"{path}:{row_number}: invalid event, role, or path")
            if role in events.setdefault(event, {}):
                raise ValueError(f"{path}:{row_number}: duplicate {event}/{role}")
            events[event][role] = Path(raw_path)
    for event, paths in events.items():
        missing = sorted(set(ROLES) - set(paths))
        if missing:
            raise ValueError(f"{event}: missing roles {missing}")
    return events


def _support_masks(reference: np.ndarray) -> dict[str, np.ndarray]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        standard_deviation = np.nanstd(reference, axis=1)
    all_nan = ~np.isfinite(reference).any(axis=1)
    finite_flat = ~all_nan & np.isfinite(standard_deviation) & (
        standard_deviation == 0
    )
    live = np.isfinite(standard_deviation) & (standard_deviation > 0)
    if np.any(all_nan & finite_flat) or np.any((all_nan | finite_flat) & live):
        raise RuntimeError("support masks overlap")
    if not np.all(all_nan | finite_flat | live):
        raise RuntimeError("support masks do not partition reference rows")
    return {"all_nan": all_nan, "finite_flat": finite_flat, "live": live}


def chime_support(h5_path: Path, reference_path: Path) -> dict[str, Any]:
    reference = np.load(reference_path, mmap_mode="r")
    if reference.ndim != 2 or reference.shape[0] != 1024:
        raise ValueError(f"{reference_path}: expected 1024 frequency rows")
    support = _support_masks(reference)
    with h5py.File(h5_path, "r") as handle:
        frequency = handle["index_map/freq"][:]
        if frequency.dtype.names is None or "id" not in frequency.dtype.names:
            raise ValueError(f"{h5_path}: index_map/freq has no id field")
        frequency_id = np.asarray(frequency["id"], dtype=np.int64)
    if (
        np.unique(frequency_id).size != frequency_id.size
        or np.any(frequency_id < 0)
        or np.any(frequency_id >= reference.shape[0])
    ):
        raise ValueError(f"{h5_path}: invalid frequency IDs")
    h5_present = np.zeros(reference.shape[0], dtype=bool)
    h5_present[frequency_id] = True
    present_dead = np.flatnonzero(h5_present & ~support["live"])
    return {
        "full_grid_rows": int(reference.shape[0]),
        "reference_samples": int(reference.shape[1]),
        "all_nan_count": int(support["all_nan"].sum()),
        "finite_flat_count": int(support["finite_flat"].sum()),
        "live_count": int(support["live"].sum()),
        "h5_present_count": int(h5_present.sum()),
        "h5_missing_count": int((~h5_present).sum()),
        "h5_present_accepted_dead_ids": present_dead.tolist(),
        "manual_bad_channel_ids": [],
        "historical_row_sum_replay": False,
    }


def _normalised_correlation(reference: np.ndarray, candidate: np.ndarray) -> float:
    left = np.asarray(reference, dtype=float)
    right = np.asarray(candidate, dtype=float)
    left -= np.mean(left)
    right -= np.mean(right)
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return float(np.dot(left, right) / denominator) if denominator > 0 else 0.0


def _row_matches(
    raw: np.ndarray,
    reference: np.ndarray,
    rows: np.ndarray,
) -> list[dict[str, Any]]:
    matches = []
    for row in rows:
        needle = np.asarray(reference[row], dtype=float)
        source = np.asarray(raw[row], dtype=float)
        score = correlate(
            source - np.median(source),
            needle - np.mean(needle),
            mode="valid",
            method="fft",
        )
        start = int(np.argmax(score))
        candidate = source[start : start + needle.size]
        matches.append(
            {
                "row": int(row),
                "best_start_sample": start,
                "correlation": _normalised_correlation(needle, candidate),
                "exact_float32_fraction": float(
                    np.mean(
                        np.asarray(needle, dtype=np.float32)
                        == np.asarray(candidate, dtype=np.float32)
                    )
                ),
            }
        )
    return matches


def dsa_state(
    filterbank_path: Path,
    reference_path: Path,
    *,
    sampled_rows: int,
) -> dict[str, Any]:
    from blimpy import Waterfall

    reader = Waterfall(str(filterbank_path), load_data=True)
    raw = np.asarray(reader.data[:, 0, :], dtype=np.float32).T
    reference = np.load(reference_path)
    if raw.shape[0] != reference.shape[0]:
        raise ValueError("raw and accepted DSA frequency dimensions differ")
    support = _support_masks(reference)
    live_rows = np.flatnonzero(support["live"])
    if live_rows.size < sampled_rows:
        raise ValueError("accepted DSA support has too few live rows")
    selected = live_rows[
        np.linspace(0, live_rows.size - 1, sampled_rows, dtype=int)
    ]
    direct = _row_matches(raw, reference, selected)
    reversed_frequency = _row_matches(raw[::-1], reference, selected)
    direct_median = float(np.median([row["correlation"] for row in direct]))
    reversed_median = float(
        np.median([row["correlation"] for row in reversed_frequency])
    )
    starts = np.asarray([row["best_start_sample"] for row in direct], dtype=float)
    correlations = np.asarray([row["correlation"] for row in direct], dtype=float)
    frequency_mhz = float(reader.header["fch1"]) + float(
        reader.header["foff"]
    ) * selected
    delay_coordinate = (
        frequency_mhz**-2 - REFERENCE_FREQUENCY_MHZ**-2
    ) / float(reader.header["tsamp"])
    use = correlations >= np.quantile(correlations, 0.50)
    coefficient = np.polyfit(delay_coordinate[use], starts[use], 1)
    residual = starts - np.polyval(coefficient, delay_coordinate)
    return {
        "raw_shape": list(raw.shape),
        "reference_shape": list(reference.shape),
        "support": {
            "full_grid_rows": int(reference.shape[0]),
            "live_count": int(support["live"].sum()),
            "dead_count": int((~support["live"]).sum()),
            "manual_bad_channel_ids": [],
        },
        "frequency_order": {
            "raw": "descending" if float(reader.header["foff"]) < 0 else "ascending",
            "accepted_reference": (
                "direct"
                if direct_median > reversed_median
                else "reversed_or_unresolved"
            ),
            "direct_median_correlation": direct_median,
            "reversed_median_correlation": reversed_median,
        },
        "row_match": {
            "selected_count": int(selected.size),
            "median_start_sample": float(np.median(starts)),
            "start_sample_min": int(np.min(starts)),
            "start_sample_max": int(np.max(starts)),
            "reference_frequency_crop_start_sample": float(coefficient[1]),
            "median_correlation": direct_median,
            "median_exact_float32_fraction": float(
                np.median([row["exact_float32_fraction"] for row in direct])
            ),
            "matches": direct,
        },
        "dedispersion_state_fit": {
            "reference_frequency_mhz": REFERENCE_FREQUENCY_MHZ,
            "inferred_reference_minus_raw_dm_pc_cm3": float(
                coefficient[0] / K_DM_S_MHZ2
            ),
            "start_residual_median_samples": float(np.median(residual)),
            "start_residual_mad_samples": float(
                np.median(np.abs(residual - np.median(residual)))
            ),
            "start_residual_max_abs_samples": float(np.max(np.abs(residual))),
            "fit_row_count": int(use.sum()),
        },
        "filterbank_header": {
            "tsamp_s": float(reader.header["tsamp"]),
            "fch1_mhz": float(reader.header["fch1"]),
            "foff_mhz": float(reader.header["foff"]),
            "nchans": int(reader.header["nchans"]),
            "nifs": int(reader.header["nifs"]),
        },
    }


def inventory(
    paths_by_event: dict[str, dict[str, Path]],
    *,
    sampled_rows: int,
) -> dict[str, Any]:
    results = []
    for event, paths in paths_by_event.items():
        for role, path in paths.items():
            if not path.is_file():
                raise FileNotFoundError(f"{event}/{role}: {path}")
        results.append(
            {
                "event": event,
                "paths": {role: str(paths[role]) for role in ROLES},
                "sizes_bytes": {
                    role: int(paths[role].stat().st_size) for role in ROLES
                },
                "chime": chime_support(
                    paths["raw_chime_h5"],
                    paths["accepted_chime_reference"],
                ),
                "dsa": dsa_state(
                    paths["raw_dsa_filterbank"],
                    paths["accepted_dsa_reference"],
                    sampled_rows=sampled_rows,
                ),
            }
        )
    return {
        "schema_version": 1,
        "status": RESULT_STATUS,
        "sampled_dsa_rows_per_event": sampled_rows,
        "events": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-paths", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sampled-dsa-rows", type=int, default=96)
    args = parser.parse_args()
    if args.sampled_dsa_rows < 8:
        raise ValueError("--sampled-dsa-rows must be at least 8")
    result = inventory(
        load_path_manifest(args.input_paths),
        sampled_rows=args.sampled_dsa_rows,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
