#!/usr/bin/env python3
"""Experimental DSA row-timing calibration diagnostic; not science authority."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from reconstruct_dsa_input_state_h17 import (
    K_DM_S_MHZ2,
    REFERENCE_FREQUENCY_MHZ,
    WINDOW_SAMPLES,
    _candidate_rows,
    _fit_rows,
    row_match,
)

SLOPE_RANGE = (0.8, 1.2)
MINIMUM_R_SQUARED = 0.999
MAXIMUM_HELD_OUT_ERROR_PC_CM3 = 0.005
ZERO_CONTROL_MAX_ERROR_PC_CM3 = 0.005
INTEGER_LAG_QUANTILE = 0.95
INTEGER_LAG_MAX_RESIDUAL_SAMPLES = 0.75
INTEGER_DM_GRID_STEP_PC_CM3 = 0.0001


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fit_free_intercept_calibration(
    injected_dm: np.ndarray,
    training_measured_dm: np.ndarray,
    validation_measured_dm: np.ndarray,
) -> dict[str, Any]:
    """Fit measured = intercept + slope * injected, then test held-out rows."""

    injected = np.asarray(injected_dm, dtype=float)
    training = np.asarray(training_measured_dm, dtype=float)
    validation = np.asarray(validation_measured_dm, dtype=float)
    if injected.ndim != 1 or injected.size < 5:
        raise ValueError("calibration requires at least five injection values")
    if training.shape != injected.shape or validation.shape != injected.shape:
        raise ValueError("calibration vectors differ")
    slope, intercept = np.polyfit(injected, training, 1)
    predicted = intercept + slope * injected
    residual = training - predicted
    denominator = float(np.sum((training - np.mean(training)) ** 2))
    r_squared = (
        1.0 - float(np.sum(residual**2)) / denominator
        if denominator > 0
        else 0.0
    )
    monotonic = bool(
        slope > 0
        and np.all(np.diff(training) > 0)
        and np.all(np.diff(validation) > 0)
    )
    if slope == 0:
        inverted_validation = np.full(validation.shape, np.nan)
    else:
        inverted_validation = (validation - intercept) / slope
    held_out_error = inverted_validation - injected
    checks = {
        "monotonic": monotonic,
        "slope": bool(SLOPE_RANGE[0] <= slope <= SLOPE_RANGE[1]),
        "r_squared": bool(r_squared >= MINIMUM_R_SQUARED),
        "held_out_accuracy": bool(
            np.all(np.isfinite(held_out_error))
            and np.max(np.abs(held_out_error))
            <= MAXIMUM_HELD_OUT_ERROR_PC_CM3
        ),
    }
    return {
        "model": "measured_DM = intercept + slope * injected_DM",
        "zero_intercept_forced": False,
        "slope": float(slope),
        "intercept_pc_cm3": float(intercept),
        "r_squared": r_squared,
        "training_residual_max_abs_pc_cm3": float(
            np.max(np.abs(residual))
        ),
        "held_out_inverted_dm_pc_cm3": inverted_validation.tolist(),
        "held_out_error_pc_cm3": held_out_error.tolist(),
        "held_out_max_abs_error_pc_cm3": float(
            np.max(np.abs(held_out_error))
        ),
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def integer_lag_consistent_interval(
    delay_coordinate: np.ndarray,
    integer_start_sample: np.ndarray,
    correlation: np.ndarray,
    *,
    dm_min: float,
    dm_max: float,
) -> dict[str, Any]:
    """Find DMs whose line is compatible with quantized integer row starts."""

    delay = np.asarray(delay_coordinate, dtype=float)
    start = np.asarray(integer_start_sample, dtype=float)
    weight = np.asarray(correlation, dtype=float)
    use = (
        np.isfinite(delay)
        & np.isfinite(start)
        & np.isfinite(weight)
        & (weight >= np.quantile(weight[np.isfinite(weight)], 0.25))
    )
    if use.sum() < 32:
        raise RuntimeError("integer-lag interval has fewer than 32 usable rows")
    grid = np.arange(
        float(dm_min),
        float(dm_max) + 0.5 * INTEGER_DM_GRID_STEP_PC_CM3,
        INTEGER_DM_GRID_STEP_PC_CM3,
    )
    score = np.empty(grid.size, dtype=float)
    intercept = np.empty(grid.size, dtype=float)
    used_delay = delay[use]
    used_start = start[use]
    for index, dm in enumerate(grid):
        row_intercept = float(
            np.median(used_start - K_DM_S_MHZ2 * dm * used_delay)
        )
        residual = used_start - (
            row_intercept + K_DM_S_MHZ2 * dm * used_delay
        )
        intercept[index] = row_intercept
        score[index] = float(
            np.quantile(np.abs(residual), INTEGER_LAG_QUANTILE)
        )
    consistent = score <= INTEGER_LAG_MAX_RESIDUAL_SAMPLES
    if np.any(consistent):
        lower = float(grid[consistent][0] - 0.5 * INTEGER_DM_GRID_STEP_PC_CM3)
        upper = float(grid[consistent][-1] + 0.5 * INTEGER_DM_GRID_STEP_PC_CM3)
        interval: list[float] | None = [lower, upper]
    else:
        interval = None
    best = int(np.argmin(score))
    return {
        "estimator": (
            "integer row-start line with a free common intercept; accepted "
            "when the 95th-percentile absolute residual is at most 0.75 sample"
        ),
        "same_data_independent_estimator": True,
        "used_row_count": int(use.sum()),
        "dm_grid_step_pc_cm3": INTEGER_DM_GRID_STEP_PC_CM3,
        "best_dm_pc_cm3": float(grid[best]),
        "best_intercept_sample": float(intercept[best]),
        "best_quantile_abs_residual_samples": float(score[best]),
        "consistent_interval_pc_cm3": interval,
        "accepted": interval is not None,
    }


def intersect_intervals(*intervals: list[float]) -> list[float] | None:
    lower = max(float(interval[0]) for interval in intervals)
    upper = min(float(interval[1]) for interval in intervals)
    return [lower, upper] if lower <= upper else None


def _injection_grid(row: dict[str, Any]) -> np.ndarray:
    extent = max(
        0.12,
        2.0
        * (
            abs(float(row["reference_minus_raw_dm_pc_cm3"]))
            + float(row["conservative_uncertainty_pc_cm3"])
        ),
    )
    extent = min(extent, 0.30)
    return np.linspace(-extent, extent, 9)


def _window_estimate(
    raw: np.ndarray,
    synthetic_reference: np.ndarray,
    selected_rows: np.ndarray,
    selected_frequency_mhz: np.ndarray,
    sample_time_s: float,
    *,
    window_samples: int,
    training: np.ndarray,
) -> tuple[float, float]:
    left = (synthetic_reference.shape[1] - window_samples) // 2
    right = left + window_samples
    matches = [
        {
            "row": int(row),
            **row_match(
                raw[row],
                synthetic_reference[index, left:right],
                reference_left=left,
            ),
        }
        for index, row in enumerate(selected_rows)
    ]
    training_fit = _fit_rows(
        [match for index, match in enumerate(matches) if training[index]],
        selected_frequency_mhz[training],
        sample_time_s,
    )
    validation_fit = _fit_rows(
        [match for index, match in enumerate(matches) if not training[index]],
        selected_frequency_mhz[~training],
        sample_time_s,
    )
    return (
        float(training_fit["reference_minus_raw_dm_pc_cm3"]),
        float(validation_fit["reference_minus_raw_dm_pc_cm3"]),
    )


def calibrate_event(
    event: str,
    raw_path: Path,
    reference_path: Path,
    reconstruction_row: dict[str, Any],
    *,
    sampled_rows: int,
) -> dict[str, Any]:
    from blimpy import Waterfall

    reader = Waterfall(str(raw_path), load_data=True)
    raw = np.asarray(reader.data[:, 0, :], dtype=np.float32).T
    reference = np.load(reference_path)
    standard_deviation = np.nanstd(reference, axis=1)
    live_rows = np.flatnonzero(
        np.isfinite(standard_deviation) & (standard_deviation > 0)
    )
    selected_rows = live_rows[
        np.linspace(0, live_rows.size - 1, sampled_rows, dtype=int)
    ]
    all_frequency_mhz = float(reader.header["fch1"]) + float(
        reader.header["foff"]
    ) * np.arange(int(reader.header["nchans"]))
    selected_frequency_mhz = all_frequency_mhz[selected_rows]
    sample_time_s = float(reader.header["tsamp"])
    crop_start = float(
        reconstruction_row["full_window_fit"][
            "reference_frequency_crop_start_sample"
        ]
    )
    injected_dm = _injection_grid(reconstruction_row)
    training = np.arange(selected_rows.size) % 2 == 0
    window_measurements = {
        window: {"training": [], "validation": []}
        for window in WINDOW_SAMPLES
        if window <= reference.shape[1]
    }
    for injected in injected_dm:
        synthetic_reference = _candidate_rows(
            raw,
            selected_rows,
            selected_frequency_mhz,
            sample_time_s,
            residual_dm=float(injected),
            crop_start=crop_start,
            samples=reference.shape[1],
        )
        for window in window_measurements:
            training_dm, validation_dm = _window_estimate(
                raw,
                synthetic_reference,
                selected_rows,
                selected_frequency_mhz,
                sample_time_s,
                window_samples=window,
                training=training,
            )
            window_measurements[window]["training"].append(training_dm)
            window_measurements[window]["validation"].append(validation_dm)
    observed_window_dm = {
        int(row["window_samples"]): float(
            row["fit"]["reference_minus_raw_dm_pc_cm3"]
        )
        for row in reconstruction_row["window_fits"]
    }
    windows = []
    calibrated_observed = []
    calibration_errors = []
    for window, measurements in window_measurements.items():
        calibration = fit_free_intercept_calibration(
            injected_dm,
            np.asarray(measurements["training"]),
            np.asarray(measurements["validation"]),
        )
        observed = observed_window_dm[window]
        corrected = (
            (observed - calibration["intercept_pc_cm3"])
            / calibration["slope"]
        )
        calibrated_observed.append(corrected)
        calibration_errors.append(
            calibration["held_out_max_abs_error_pc_cm3"]
        )
        windows.append(
            {
                "window_samples": window,
                "injected_dm_pc_cm3": injected_dm.tolist(),
                "training_measured_dm_pc_cm3": measurements["training"],
                "validation_measured_dm_pc_cm3": measurements["validation"],
                "calibration": calibration,
                "observed_measured_dm_pc_cm3": observed,
                "calibrated_observed_dm_pc_cm3": corrected,
            }
        )
    calibrated_center = float(np.median(calibrated_observed))
    preliminary_uncertainty = max(
        max(calibration_errors),
        0.5 * float(np.ptp(calibrated_observed)),
        0.003,
    )
    actual_matches = [
        {
            "row": int(row),
            **row_match(raw[row], reference[row], reference_left=0),
        }
        for row in selected_rows
    ]
    delay_coordinate = (
        selected_frequency_mhz**-2 - REFERENCE_FREQUENCY_MHZ**-2
    ) / sample_time_s
    integer_start = np.asarray(
        [row["integer_reference_origin_sample"] for row in actual_matches],
        dtype=float,
    )
    correlation = np.asarray(
        [row["correlation"] for row in actual_matches],
        dtype=float,
    )
    v3_center = float(reconstruction_row["reference_minus_raw_dm_pc_cm3"])
    v3_uncertainty = float(
        reconstruction_row["conservative_uncertainty_pc_cm3"]
    )
    search_extent = max(0.2, abs(v3_center) + 4.0 * v3_uncertainty)
    integer_interval = integer_lag_consistent_interval(
        delay_coordinate,
        integer_start,
        correlation,
        dm_min=v3_center - search_extent,
        dm_max=v3_center + search_extent,
    )
    checks = {
        "all_windows_calibrated": bool(
            len(windows) == len(WINDOW_SAMPLES)
            and all(row["calibration"]["passed"] for row in windows)
        ),
        "window_observed_consistency": bool(
            np.ptp(calibrated_observed) <= 0.02
        ),
        "integer_lag_interval": bool(integer_interval["accepted"]),
    }
    return {
        "event": event,
        "raw_filterbank": {
            "path": str(raw_path),
            "sha256": sha256_file(raw_path),
        },
        "accepted_reference": {
            "path": str(reference_path),
            "sha256": sha256_file(reference_path),
        },
        "sampled_live_rows": sampled_rows,
        "training_rows": int(training.sum()),
        "validation_rows": int((~training).sum()),
        "windows": windows,
        "calibrated_observed_residual_dm_pc_cm3": calibrated_center,
        "preliminary_calibration_uncertainty_pc_cm3": preliminary_uncertainty,
        "integer_lag_interval": integer_interval,
        "checks_before_zero_control": checks,
    }


def finalize_bounds(
    events: list[dict[str, Any]],
    reconstruction_by_event: dict[str, dict[str, Any]],
    *,
    zero_control_event: str,
) -> dict[str, Any]:
    controls = [
        row for row in events if row["event"].lower() == zero_control_event
    ]
    if len(controls) != 1:
        raise RuntimeError("calibration requires exactly one zero-control event")
    control = controls[0]
    control_residual = float(
        control["calibrated_observed_residual_dm_pc_cm3"]
    )
    zero_passed = bool(
        all(control["checks_before_zero_control"].values())
        and abs(control_residual) <= ZERO_CONTROL_MAX_ERROR_PC_CM3
    )
    systematic_floor = abs(control_residual) + ZERO_CONTROL_MAX_ERROR_PC_CM3
    zero_summary = {
        "event": zero_control_event,
        "expected_residual_dm_pc_cm3": 0.0,
        "calibrated_residual_dm_pc_cm3": control_residual,
        "maximum_absolute_error_pc_cm3": ZERO_CONTROL_MAX_ERROR_PC_CM3,
        "passed": zero_passed,
        "derived_systematic_floor_pc_cm3": systematic_floor,
    }
    for row in events:
        reconstruction = reconstruction_by_event[row["event"].lower()]
        v3_center = float(reconstruction["reference_minus_raw_dm_pc_cm3"])
        v3_uncertainty = float(reconstruction["conservative_uncertainty_pc_cm3"])
        v3_interval = [
            v3_center - v3_uncertainty,
            v3_center + v3_uncertainty,
        ]
        calibrated_center = float(
            row["calibrated_observed_residual_dm_pc_cm3"]
        )
        calibrated_uncertainty = max(
            float(row["preliminary_calibration_uncertainty_pc_cm3"]),
            systematic_floor,
        )
        calibrated_interval = [
            calibrated_center - calibrated_uncertainty,
            calibrated_center + calibrated_uncertainty,
        ]
        integer_interval = row["integer_lag_interval"][
            "consistent_interval_pc_cm3"
        ]
        if integer_interval is None:
            selected_interval = None
        else:
            selected_interval = intersect_intervals(
                v3_interval,
                calibrated_interval,
                integer_interval,
            )
        checks = {
            **row.pop("checks_before_zero_control"),
            "zero_control": zero_passed,
            "three_interval_overlap": selected_interval is not None,
        }
        narrowing_accepted = bool(all(checks.values()))
        row.update(
            {
                "v3_residual_interval_pc_cm3": v3_interval,
                "calibrated_residual_interval_pc_cm3": calibrated_interval,
                "selected_residual_interval_pc_cm3": (
                    selected_interval if narrowing_accepted else v3_interval
                ),
                "calibrated_uncertainty_pc_cm3": calibrated_uncertainty,
                "checks": checks,
                "calibration_accepted_for_bound_narrowing": narrowing_accepted,
                "fallback": (
                    None
                    if narrowing_accepted
                    else "retain original v3 residual interval"
                ),
            }
        )
    return zero_summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--dsa-reconstruction", type=Path, required=True)
    parser.add_argument("--event", action="append", required=True)
    parser.add_argument("--zero-control-event", required=True)
    parser.add_argument("--sampled-rows", type=int, default=128)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.sampled_rows < 64 or args.sampled_rows % 2:
        raise ValueError("--sampled-rows must be an even integer of at least 64")
    requested = [event.lower() for event in args.event]
    zero_control_event = args.zero_control_event.lower()
    if zero_control_event not in requested:
        requested.append(zero_control_event)
    inventory = {
        str(row["event"]).lower(): row
        for row in json.loads(args.inventory.read_text())["events"]
    }
    reconstruction = json.loads(args.dsa_reconstruction.read_text())
    reconstruction_by_event = {
        str(row["event"]).lower(): row for row in reconstruction["events"]
    }
    if len(set(requested)) != len(requested):
        raise ValueError("duplicate calibration event")
    events = []
    for event in requested:
        try:
            paths = inventory[event]["paths"]
            reconstruction_row = reconstruction_by_event[event]
        except KeyError as error:
            raise ValueError(f"missing calibration input for {event}") from error
        events.append(
            calibrate_event(
                event,
                Path(paths["raw_dsa_filterbank"]),
                Path(paths["accepted_dsa_reference"]),
                reconstruction_row,
                sampled_rows=args.sampled_rows,
            )
        )
        print(
            json.dumps(
                {
                    "event": event,
                    "calibrated_residual": events[-1][
                        "calibrated_observed_residual_dm_pc_cm3"
                    ],
                }
            ),
            flush=True,
        )
    zero_control = finalize_bounds(
        events,
        reconstruction_by_event,
        zero_control_event=zero_control_event,
    )
    result = {
        "schema_version": 1,
        "status": "diagnostic_only_dsa_estimator_calibration",
        "source_reconstruction": {
            "path": str(args.dsa_reconstruction),
            "sha256": sha256_file(args.dsa_reconstruction),
        },
        "method": {
            "injection": (
                "sample the event raw filterbank at known residual-DM row "
                "coordinates, then recover with the exact v3 row estimator"
            ),
            "calibration_model": (
                "free-intercept measured-versus-injected line; zero bias is "
                "not forced"
            ),
            "row_holdout": "alternating selected rows, disjoint fit and validation",
            "window_samples": list(WINDOW_SAMPLES),
            "integer_bound": (
                "same raw/reference data but independent quantized row-lag "
                "estimator; used only as an interval-overlap constraint"
            ),
            "gates": {
                "slope_range": list(SLOPE_RANGE),
                "minimum_r_squared": MINIMUM_R_SQUARED,
                "maximum_held_out_error_pc_cm3": (
                    MAXIMUM_HELD_OUT_ERROR_PC_CM3
                ),
                "zero_control_max_error_pc_cm3": (
                    ZERO_CONTROL_MAX_ERROR_PC_CM3
                ),
                "integer_lag_quantile": INTEGER_LAG_QUANTILE,
                "integer_lag_max_residual_samples": (
                    INTEGER_LAG_MAX_RESIDUAL_SAMPLES
                ),
            },
        },
        "zero_control": zero_control,
        "events": events,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
