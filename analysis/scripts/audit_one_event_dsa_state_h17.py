#!/usr/bin/env python3
"""Audit one DSA filterbank against its accepted current reference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from blimpy import Waterfall
from scipy.signal import correlate

from absolute_dm_voltage import K_DM_S_MHZ2, sha256
from one_event_workflow import legacy_stage_config, load_config


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
) -> list[dict]:
    matches = []
    for row in rows:
        needle = np.asarray(reference[row], dtype=float)
        source = np.asarray(raw[row], dtype=float)
        needle_centered = needle - np.mean(needle)
        source_centered = source - np.median(source)
        score = correlate(
            source_centered,
            needle_centered,
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


def audit(config: dict) -> dict:
    raw_path = Path(config["raw_dsa_filterbank"])
    reference_path = Path(config["accepted_dsa_reference"])
    reader = Waterfall(str(raw_path), load_data=True)
    raw = np.asarray(reader.data[:, 0, :], dtype=np.float32).T
    reference = np.load(reference_path)
    if raw.shape[0] != reference.shape[0]:
        raise ValueError("raw and reference frequency dimensions differ")
    standard_deviation = np.nanstd(reference, axis=1)
    valid = np.isfinite(standard_deviation) & (standard_deviation > 0)
    valid_rows = np.flatnonzero(valid)
    selected_count = int(config["dsa_audit_sample_rows"])
    if valid_rows.size < selected_count:
        raise RuntimeError("accepted DSA support has too few live rows for audit")
    selected = valid_rows[
        np.linspace(0, valid_rows.size - 1, selected_count, dtype=int)
    ]
    direct = _row_matches(raw, reference, selected)
    reversed_frequency = _row_matches(raw[::-1], reference, selected)
    direct_median = float(np.median([row["correlation"] for row in direct]))
    reversed_median = float(
        np.median([row["correlation"] for row in reversed_frequency])
    )
    if direct_median <= reversed_median:
        raise RuntimeError("accepted reference does not match raw frequency order")

    starts = np.asarray([row["best_start_sample"] for row in direct], dtype=float)
    correlations = np.asarray([row["correlation"] for row in direct], dtype=float)
    frequency_mhz = float(reader.header["fch1"]) + float(
        reader.header["foff"]
    ) * selected
    delay_coordinate = (
        frequency_mhz**-2 - float(config["reference_frequency_mhz"]) ** -2
    ) / float(reader.header["tsamp"])
    use = correlations >= np.quantile(correlations, 0.50)
    coefficient = np.polyfit(delay_coordinate[use], starts[use], 1)
    inferred_residual_dm = float(coefficient[0] / K_DM_S_MHZ2)
    predicted = np.polyval(coefficient, delay_coordinate)
    residual = starts - predicted
    return {
        "schema_version": 1,
        "status": "one_event_dsa_input_state_audit",
        "event": config["event"],
        "event_binding_sha256": config["event_binding_sha256"],
        "raw_filterbank": {
            "path": str(raw_path),
            "sha256": sha256(raw_path),
            "shape": list(raw.shape),
            "header": {
                key: (
                    float(value)
                    if isinstance(value, (float, np.floating))
                    else int(value)
                    if isinstance(value, (int, np.integer))
                    else str(value)
                )
                for key, value in reader.header.items()
            },
        },
        "accepted_reference": {
            "path": str(reference_path),
            "sha256": sha256(reference_path),
            "shape": list(reference.shape),
            "valid_row_count": int(valid.sum()),
            "dead_row_count": int((~valid).sum()),
            "product_dm_pc_cm3": float(
                config["accepted_dsa_reference_dm_pc_cm3"]
            ),
            "product_dm_source": "reviewed one-event workflow configuration",
        },
        "frequency_order": {
            "raw": "descending",
            "reference": "descending",
            "direct_median_correlation": direct_median,
            "reversed_median_correlation": reversed_median,
        },
        "row_match": {
            "selected_count": int(selected.size),
            "matches": direct,
            "median_start_sample": float(np.median(starts)),
            "start_sample_min": int(np.min(starts)),
            "start_sample_max": int(np.max(starts)),
            "median_correlation": direct_median,
            "median_exact_float32_fraction": float(
                np.median([row["exact_float32_fraction"] for row in direct])
            ),
        },
        "dedispersion_state_fit": {
            "model": (
                "best raw start = common crop start + K_DM * residual_DM * "
                "(frequency^-2 - reference_frequency^-2) / sample_time"
            ),
            "reference_frequency_mhz": float(config["reference_frequency_mhz"]),
            "inferred_reference_minus_raw_dm_pc_cm3": inferred_residual_dm,
            "start_residual_median_samples": float(np.median(residual)),
            "start_residual_mad_samples": float(
                np.median(np.abs(residual - np.median(residual)))
            ),
            "fit_row_count": int(use.sum()),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(legacy_stage_config(load_config(args.config)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["dedispersion_state_fit"], indent=2))


if __name__ == "__main__":
    main()
