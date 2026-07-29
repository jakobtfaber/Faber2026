#!/usr/bin/env python3
"""Audit one DSA filterbank against its accepted current reference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from absolute_dm_voltage import K_DM_S_MHZ2, sha256
from blimpy import Waterfall
from one_event_workflow import legacy_stage_config, load_config
from scipy.signal import correlate

BOUND_ONLY_EXCLUDED_CHECKS = {
    "correction_improves_match",
    "correction_improves_profile",
    "held_out_correction",
    "material_nonzero_residual",
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


def _reconstruction_event(config: dict) -> tuple[dict, dict, dict | None]:
    path = Path(config["dsa_state_reconstruction"])
    expected_sha256 = config["expected_dsa_state_reconstruction_sha256"]
    actual_sha256 = sha256(path)
    if actual_sha256 != expected_sha256:
        raise RuntimeError("DSA reconstruction SHA-256 mismatch")
    reconstruction = json.loads(path.read_text())
    if (
        reconstruction.get("synthetic_sign_oracle", {}).get("passed") is not True
        or reconstruction.get("known_zero_control", {}).get(
            "zero_covered_by_systematic_model"
        )
        is not True
    ):
        raise RuntimeError("DSA reconstruction global controls did not pass")
    matches = [
        row
        for row in reconstruction.get("events", [])
        if str(row.get("event", "")).lower() == config["event"]
    ]
    if len(matches) != 1:
        raise RuntimeError("DSA reconstruction does not contain exactly one event")
    row = matches[0]
    residual = float(row["reference_minus_raw_dm_pc_cm3"])
    accepted_dm = float(row["accepted_reference_dm_pc_cm3"])
    uncertainty = float(row["conservative_uncertainty_pc_cm3"])
    expected_interval = [
        residual - uncertainty,
        residual + uncertainty,
    ]
    calibration_event = None
    method = config["input_dsa_dm_method"]
    if abs(residual - float(config["reference_minus_raw_dsa_dm_pc_cm3"])) > 1.0e-12:
        raise RuntimeError("DSA reconstruction residual differs from configuration")
    if (
        abs(
            float(row["full_window_fit"]["reference_frequency_crop_start_sample"])
            - float(config["raw_dsa_reference_frequency_crop_start_sample"])
        )
        > 1.0e-9
    ):
        raise RuntimeError("DSA reconstruction crop coordinate differs from configuration")
    if method == "inferred_raw_reference_row_timing":
        expected_nominal = accepted_dm - residual
        expected_half_width = uncertainty
        admissible = bool(row["accepted_for_config_review"])
    elif method == "accepted_product_dm_nominal_with_residual_bound":
        expected_nominal = accepted_dm
        failed_base = sorted(
            key
            for key, passed in row["checks"].items()
            if key not in BOUND_ONLY_EXCLUDED_CHECKS and not passed
        )
        admissible = not failed_base and not row["material_nonzero_residual_proven"]
    else:
        raise RuntimeError("unknown DSA input-DM method")
    if not admissible:
        raise RuntimeError("DSA reconstruction does not admit configured method")
    if abs(float(config["input_dsa_dm_pc_cm3"]) - expected_nominal) > 1.0e-12:
        raise RuntimeError("DSA nominal input DM differs from reconstruction")
    if (
        config["input_dsa_dm_bound_source"]
        == "calibrated_v3_integer_interval_intersection"
    ):
        calibration_path = Path(config["dsa_state_calibration"])
        calibration_sha256 = sha256(calibration_path)
        if calibration_sha256 != config["expected_dsa_state_calibration_sha256"]:
            raise RuntimeError("DSA calibration SHA-256 mismatch")
        calibration = json.loads(calibration_path.read_text())
        if (
            calibration.get("source_reconstruction", {}).get("sha256")
            != expected_sha256
            or calibration.get("zero_control", {}).get("passed") is not True
        ):
            raise RuntimeError("DSA calibration source or zero control failed")
        calibration_matches = [
            value
            for value in calibration.get("events", [])
            if str(value.get("event", "")).lower() == config["event"]
        ]
        if len(calibration_matches) != 1:
            raise RuntimeError("DSA calibration lacks exactly one event")
        calibration_event = calibration_matches[0]
        if (
            calibration_event.get(
                "calibration_accepted_for_bound_narrowing"
            )
            is not True
        ):
            raise RuntimeError("DSA calibration is not accepted for narrowing")
        expected_interval = [
            float(value)
            for value in calibration_event[
                "selected_residual_interval_pc_cm3"
            ]
        ]
    configured_interval = [
        float(value)
        for value in config["reference_minus_raw_dsa_dm_interval_pc_cm3"]
    ]
    if not np.allclose(
        configured_interval,
        expected_interval,
        rtol=0.0,
        atol=1.0e-12,
    ):
        raise RuntimeError("DSA residual interval differs from bound evidence")
    expected_half_width = (
        max(
            abs(residual - expected_interval[0]),
            abs(expected_interval[1] - residual),
        )
        if method == "inferred_raw_reference_row_timing"
        else max(abs(expected_interval[0]), abs(expected_interval[1]))
    )
    if abs(
        float(config["input_dsa_dm_half_width_pc_cm3"])
        - expected_half_width
    ) > 1.0e-12:
        raise RuntimeError("DSA input-DM half-width differs from reconstruction")
    return reconstruction, row, calibration_event


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
    if "input_dsa_dm_method" in config:
        (
            reconstruction,
            reconstruction_event,
            calibration_event,
        ) = _reconstruction_event(config)
        inferred_residual_dm = float(
            reconstruction_event["reference_minus_raw_dm_pc_cm3"]
        )
        crop_coordinate = float(
            reconstruction_event["full_window_fit"][
                "reference_frequency_crop_start_sample"
            ]
        )
        predicted = (
            crop_coordinate
            + K_DM_S_MHZ2 * inferred_residual_dm * delay_coordinate
        )
        use_count = int(
            reconstruction_event["full_window_fit"]["used_count"]
        )
        fit_source = "bound_v3_reconstruction_artifact"
        for index, match in enumerate(direct):
            match["predicted_start_sample"] = float(predicted[index])
            match["start_residual_sample"] = float(
                starts[index] - predicted[index]
            )
    else:
        use = correlations >= np.quantile(correlations, 0.50)
        coefficient = np.polyfit(delay_coordinate[use], starts[use], 1)
        inferred_residual_dm = float(coefficient[0] / K_DM_S_MHZ2)
        predicted = np.polyval(coefficient, delay_coordinate)
        use_count = int(use.sum())
        crop_coordinate = float(coefficient[1])
        fit_source = "legacy_sampled_integer_row_start_fit"
        reconstruction = None
        reconstruction_event = None
        calibration_event = None
    residual = starts - predicted
    result = {
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
            "reference_frequency_crop_start_sample": crop_coordinate,
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
            "fit_row_count": use_count,
            "source": fit_source,
        },
    }
    if reconstruction_event is not None and reconstruction is not None:
        result["input_state_contract"] = {
            "method": config["input_dsa_dm_method"],
            "bound_source": config["input_dsa_dm_bound_source"],
            "nominal_input_dm_pc_cm3": float(config["input_dsa_dm_pc_cm3"]),
            "input_dm_half_width_pc_cm3": float(
                config["input_dsa_dm_half_width_pc_cm3"]
            ),
            "input_dm_interval_pc_cm3": [
                float(config["input_dsa_dm_pc_cm3"])
                - float(config["input_dsa_dm_half_width_pc_cm3"]),
                float(config["input_dsa_dm_pc_cm3"])
                + float(config["input_dsa_dm_half_width_pc_cm3"]),
            ],
            "reference_minus_raw_dm_pc_cm3": inferred_residual_dm,
            "reference_minus_raw_dm_interval_pc_cm3": config[
                "reference_minus_raw_dsa_dm_interval_pc_cm3"
            ],
            "reconstruction_path": config["dsa_state_reconstruction"],
            "reconstruction_sha256": config[
                "expected_dsa_state_reconstruction_sha256"
            ],
            "accepted_for_config_review": bool(
                reconstruction_event["accepted_for_config_review"]
            ),
            "material_nonzero_residual_proven": bool(
                reconstruction_event["material_nonzero_residual_proven"]
            ),
            "known_zero_systematic_floor_pc_cm3": float(
                reconstruction["known_zero_control"][
                    "derived_systematic_floor_pc_cm3"
                ]
            ),
            "raw_header_dm_certified": False,
            "raw_state_claim": (
                "inferred value with conservative uncertainty"
                if config["input_dsa_dm_method"]
                == "inferred_raw_reference_row_timing"
                else "accepted-product nominal with conservative residual bound; "
                "exact raw state remains ambiguous"
            ),
            **(
                {
                    "calibration_path": config["dsa_state_calibration"],
                    "calibration_sha256": config[
                        "expected_dsa_state_calibration_sha256"
                    ],
                    "calibration_accepted_for_bound_narrowing": True,
                }
                if calibration_event is not None
                else {}
            ),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(
        legacy_stage_config(
            load_config(args.config, require_execution_authorized=True)
        )
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["dedispersion_state_fit"], indent=2))


if __name__ == "__main__":
    main()
