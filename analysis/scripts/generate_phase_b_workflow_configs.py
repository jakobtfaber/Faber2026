#!/usr/bin/env python3
"""Generate configs for a paused experimental Phase B diagnostic.

Generated configs are execution-disabled and are not science authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from one_event_workflow import STAGES, event_binding_sha256, validate_config
from recompute_geometry_dm import recompute

SHARED_H17_ROOT = Path(
    "/data/Faber2026/evidence/dm-toa-geometry-20260728/"
    "phase-b-control/shared-inputs"
)
OUTPUT_H17_ROOT = Path("/data/Faber2026/evidence/dm-toa-geometry-20260728")
CONTAINER_IMAGE = (
    "chimefrb/baseband-analysis@sha256:"
    "f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41"
)
CASEY_GATES = {
    "chime": {
        "oracle_half_width_pc_cm3": 0.01,
        "oracle_material_threshold_pc_cm3": 0.005,
        "oracle_normalised_curve_max_abs_difference": 0.1,
        "oracle_center_score_ratio_tolerance": 0.2,
        "smearing_max_fraction_of_upchannel_sample": 0.1,
        "smearing_max_fraction_of_reference_pulse_fwhm": 0.05,
        "injection_max_error_pc_cm3": 0.003,
    },
    "dsa": {
        "direct_correlation_min": 0.8,
        "reversed_correlation_max": 0.1,
        "input_dm_reference_timing_half_width_max_native_samples": 16.0,
        "input_dm_aligned_profile_correlation_min": 0.98,
        "gallery_alignment_must_be_robust": True,
        "edge_fail_closed": True,
    },
}

BOUND_ONLY_EXCLUDED_CHECKS = {
    "correction_improves_match",
    "correction_improves_profile",
    "held_out_correction",
    "material_nonzero_residual",
}
SUMMARY_STATUS = (
    "phase_b_paused_experimental_diagnostic_configs_"
    "not_science_authority_execution_disabled"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_hash_manifest(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        fields = line.split(maxsplit=1)
        if len(fields) != 2 or len(fields[0]) != 64:
            raise ValueError(f"{path}:{line_number}: invalid sha256sum row")
        digest, raw_path = fields
        if raw_path in result:
            raise ValueError(f"{path}:{line_number}: duplicate path")
        result[raw_path] = digest
    return result


def _casefold_index(rows: list[dict[str, Any]], field: str) -> dict[str, dict]:
    result = {}
    for row in rows:
        key = str(row[field]).lower()
        if key in result:
            raise ValueError(f"duplicate case-folded key {key}")
        result[key] = row
    return result


def anchor_grid(
    accepted_dm: float,
    h5_coherent_dm: float,
    geometry_dm: float,
) -> dict[str, float]:
    """Cover all three reviewed CHIME coordinates with a 0.03 DM margin."""

    anchor = round(float(geometry_dm), 2)
    required = max(
        abs(float(accepted_dm) - anchor),
        abs(float(h5_coherent_dm) - anchor),
        abs(float(geometry_dm) - anchor),
    )
    half_width = max(0.1, math.ceil((required + 0.03) / 0.05) * 0.05)
    return {
        "anchor_dm_pc_cm3": anchor,
        "coarse_half_width_pc_cm3": round(half_width, 12),
    }


def window_seconds(reference_fwhm_s: float) -> float:
    """Retain Casey's floor; add a 25 percent envelope margin."""

    required = max(0.03, 1.25 * float(reference_fwhm_s))
    return round(math.ceil((required - 1.0e-15) / 0.01) * 0.01, 12)


def dsa_blockers(dsa: dict[str, Any]) -> list[str]:
    order = dsa["frequency_order"]
    gates = CASEY_GATES["dsa"]
    blockers = []
    if float(order["direct_median_correlation"]) < gates["direct_correlation_min"]:
        blockers.append("direct_frequency_order_correlation_below_casey_gate")
    if float(order["reversed_median_correlation"]) > gates["reversed_correlation_max"]:
        blockers.append("reversed_frequency_order_correlation_above_casey_gate")
    return blockers


def reconstruction_contract(
    reconstruction: dict[str, Any],
    calibration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    residual = float(reconstruction["reference_minus_raw_dm_pc_cm3"])
    uncertainty = float(reconstruction["conservative_uncertainty_pc_cm3"])
    material = bool(reconstruction["material_nonzero_residual_proven"])
    if material:
        method = "inferred_raw_reference_row_timing"
        nominal = float(reconstruction["inferred_raw_input_dm_pc_cm3"])
        half_width = uncertainty
        value_accepted = bool(reconstruction["accepted_for_config_review"])
        bound_accepted = False
        failed = sorted(
            key
            for key, passed in reconstruction["checks"].items()
            if not passed
        )
        admissible = value_accepted
        residual_interval = [residual - uncertainty, residual + uncertainty]
        bound_source = "v3_inferred_value"
    else:
        method = "accepted_product_dm_nominal_with_residual_bound"
        nominal = float(reconstruction["accepted_reference_dm_pc_cm3"])
        residual_interval = [residual - uncertainty, residual + uncertainty]
        bound_source = "v3_conservative_residual_bound"
        if (
            calibration is not None
            and calibration.get(
                "calibration_accepted_for_bound_narrowing"
            )
            is True
        ):
            residual_interval = [
                float(value)
                for value in calibration[
                    "selected_residual_interval_pc_cm3"
                ]
            ]
            bound_source = "calibrated_v3_integer_interval_intersection"
        half_width = max(abs(value) for value in residual_interval)
        failed = sorted(
            key
            for key, passed in reconstruction["checks"].items()
            if key not in BOUND_ONLY_EXCLUDED_CHECKS and not passed
        )
        value_accepted = False
        bound_accepted = not failed
        admissible = bound_accepted
    return {
        "method": method,
        "nominal_input_dm_pc_cm3": nominal,
        "input_dm_half_width_pc_cm3": half_width,
        "accepted_for_config_review": value_accepted,
        "conservative_bound_accepted_for_config_review": bound_accepted,
        "admissible": admissible,
        "failed_checks": failed,
        "reference_minus_raw_dm_interval_pc_cm3": residual_interval,
        "bound_source": bound_source,
    }


def reconstruction_blockers(contract: dict[str, Any]) -> list[str]:
    if contract["admissible"]:
        return []
    if contract["failed_checks"]:
        return [
            f"dsa_reconstruction_failed:{check}"
            for check in contract["failed_checks"]
        ]
    return ["dsa_reconstruction_method_not_admissible"]


def _h5_coherent_dm(row: dict[str, Any]) -> float:
    values = {
        float(obj["dispersion_attrs"]["DM_coherent"])
        for obj in row["power_objects"]
        if "DM_coherent" in obj["dispersion_attrs"]
    }
    if len(values) != 1:
        raise ValueError(f"{row['file']}: expected one coherent-power DM")
    return values.pop()


def generate(args: argparse.Namespace) -> dict[str, Any]:
    fixture = json.loads(args.fixture.read_text())
    fits = _casefold_index(json.loads(args.coherent_fits.read_text()), "burst")
    h5_audit_rows = json.loads(args.h5_audit.read_text())["files"]
    h5_audit = {
        Path(row["file"]).stem.removeprefix("singlebeam_"): row
        for row in h5_audit_rows
    }
    inventory_raw = json.loads(args.inventory.read_text())
    inventory = _casefold_index(inventory_raw["events"], "event")
    reconstruction_raw = json.loads(args.dsa_reconstruction.read_text())
    reconstruction = _casefold_index(reconstruction_raw["events"], "event")
    reconstruction_sha256 = sha256_file(args.dsa_reconstruction)
    if args.dsa_calibration is not None:
        calibration_raw = json.loads(args.dsa_calibration.read_text())
        calibration = _casefold_index(calibration_raw["events"], "event")
        calibration_sha256 = sha256_file(args.dsa_calibration)
    else:
        calibration_raw = None
        calibration = {}
        calibration_sha256 = None
    input_hashes = load_hash_manifest(args.hash_manifest)
    geometry_raw = recompute(
        args.timing_results,
        args.trigger_recovery,
        args.fixture,
    )
    geometry = _casefold_index(geometry_raw["results"], "burst")
    shared_paths = {
        "timing_results": SHARED_H17_ROOT / args.timing_results.name,
        "trigger_recovery": SHARED_H17_ROOT / args.trigger_recovery.name,
        "reproduction_fixture": SHARED_H17_ROOT / args.fixture.name,
        "dsa_state_reconstruction": (
            args.h17_control_root / args.dsa_reconstruction.name
        ),
    }
    shared_hashes = {
        "timing_results": sha256_file(args.timing_results),
        "trigger_recovery": sha256_file(args.trigger_recovery),
        "reproduction_fixture": sha256_file(args.fixture),
        "dsa_state_reconstruction": reconstruction_sha256,
    }
    known_events = [str(row["name"]).lower() for row in fixture["bursts"]]
    requested_authorization = {
        str(event).lower() for event in args.authorize_event
    }
    if requested_authorization:
        raise PermissionError(
            "Phase B campaign is paused; this generator cannot authorize events"
        )
    summaries = []
    for burst in fixture["bursts"]:
        event = str(burst["name"]).lower()
        if event == "casey":
            continue
        fit = fits[event]
        inv = inventory[event]
        dsa_reconstruction = reconstruction[event]
        geom = geometry[event]
        h5_row = h5_audit[str(burst["chime_id"])]
        paths = {key: Path(value) for key, value in inv["paths"].items()}
        role_hashes = {}
        for role, path in paths.items():
            try:
                role_hashes[role] = input_hashes[str(path)]
            except KeyError as error:
                raise ValueError(f"{event}/{role}: missing H17 hash") from error
        h5_dm = _h5_coherent_dm(h5_row)
        geometry_dm = float(geom["geometry_aligning_dm_pc_cm3"])
        chime_grid = anchor_grid(
            float(fit["chime"]["product_dm"]),
            h5_dm,
            geometry_dm,
        )
        fwhm_s = float(burst["fwhm_ms"]) / 1000.0
        crop_coordinate = float(
            dsa_reconstruction["full_window_fit"][
                "reference_frequency_crop_start_sample"
            ]
        )
        crop_start = int(round(crop_coordinate))
        dsa_calibration = calibration.get(event)
        dsa_contract = reconstruction_contract(
            dsa_reconstruction,
            dsa_calibration,
        )
        sample_time_s = float(inv["dsa"]["filterbank_header"]["tsamp_s"])
        native_frequency_mhz = float(burst["dsa"]["native_frequency_mhz"])
        timing_half_width_samples = (
            1000.0
            * 4148.808
            * float(dsa_contract["input_dm_half_width_pc_cm3"])
            * abs(400.0**-2 - native_frequency_mhz**-2)
            / (1000.0 * sample_time_s)
        )
        output_basename = f"{event}-one-event-workflow"
        blockers = dsa_blockers(inv["dsa"])
        blockers.extend(reconstruction_blockers(dsa_contract))
        if timing_half_width_samples > float(
            CASEY_GATES["dsa"][
                "input_dm_reference_timing_half_width_max_native_samples"
            ]
        ):
            blockers.append(
                "dsa_input_dm_bound_exceeds_timing_resolution_gate"
            )
            if dsa_calibration is not None and not dsa_calibration[
                "calibration_accepted_for_bound_narrowing"
            ]:
                blockers.append(
                    "dsa_calibration_not_accepted_for_bound_narrowing"
                )
        if args.review_status == "pending":
            blockers.append("pending_independent_chime_config_review")
            blockers.append("pending_independent_dsa_uncertainty_review")
        execution_authorized = False
        blockers.append("campaign_paused_no_execution_authorization")
        blockers = sorted(set(blockers))
        configuration_status = "blocked"
        event_paths = {**paths, **shared_paths}
        event_hashes = {**role_hashes, **shared_hashes}
        if (
            dsa_contract["bound_source"]
            == "calibrated_v3_integer_interval_intersection"
        ):
            if args.dsa_calibration is None or calibration_sha256 is None:
                raise RuntimeError("calibrated interval lacks calibration artifact")
            event_paths["dsa_state_calibration"] = (
                args.h17_control_root / args.dsa_calibration.name
            )
            event_hashes["dsa_state_calibration"] = calibration_sha256
        config: dict[str, Any] = {
            "$schema": "../../schema.json",
            "schema_version": 1,
            "event": event,
            "result_status": (
                "experimental_one_event_hybrid_diagnostic_"
                "not_science_authority_no_manuscript_adoption"
            ),
            "identity": {
                "reviewed_event": event,
                "input_basenames": {
                    key: value.name
                    for key, value in event_paths.items()
                },
                "output_root_basename": output_basename,
                "disallowed_event_tokens": sorted(
                    candidate for candidate in known_events if candidate != event
                ),
            },
            "paths": {
                **{key: str(value) for key, value in event_paths.items()},
                "output_root": str(OUTPUT_H17_ROOT / output_basename),
            },
            "input_sha256": event_hashes,
            "chime": {
                "accepted_reference_dm_pc_cm3": float(
                    fit["chime"]["product_dm"]
                ),
                "anchor_dm_pc_cm3": chime_grid["anchor_dm_pc_cm3"],
                "reference_pulse_fwhm_s": fwhm_s,
                "upchannel_factor": 16,
                "window_s": window_seconds(fwhm_s),
                "grid": {
                    "coarse_half_width_pc_cm3": chime_grid[
                        "coarse_half_width_pc_cm3"
                    ],
                    "coarse_step_pc_cm3": 0.01,
                    "fine_half_width_pc_cm3": 0.015,
                    "fine_step_pc_cm3": 0.001,
                },
                "gates": dict(CASEY_GATES["chime"]),
                "accepted_support": {
                    key: value
                    for key, value in inv["chime"].items()
                    if key
                    in {
                        "full_grid_rows",
                        "all_nan_count",
                        "finite_flat_count",
                        "live_count",
                        "h5_present_count",
                        "h5_missing_count",
                        "h5_present_accepted_dead_ids",
                        "manual_bad_channel_ids",
                        "historical_row_sum_replay",
                    }
                },
            },
            "dsa": {
                "accepted_reference_dm_pc_cm3": float(
                    fit["dsa"]["product_dm"]
                ),
                "input_dm_pc_cm3": dsa_contract[
                    "nominal_input_dm_pc_cm3"
                ],
                "input_dm_method": dsa_contract["method"],
                "input_dm_bound_source": dsa_contract["bound_source"],
                "input_dm_half_width_pc_cm3": dsa_contract[
                    "input_dm_half_width_pc_cm3"
                ],
                "reference_minus_raw_dm_pc_cm3": float(
                    dsa_reconstruction["reference_minus_raw_dm_pc_cm3"]
                ),
                "reference_minus_raw_dm_interval_pc_cm3": dsa_contract[
                    "reference_minus_raw_dm_interval_pc_cm3"
                ],
                "input_dm_reconstruction_sha256": reconstruction_sha256,
                "raw_reference_frequency_crop_start_sample": float(
                    dsa_reconstruction["full_window_fit"][
                        "reference_frequency_crop_start_sample"
                    ]
                ),
                "native_sample_time_s": sample_time_s,
                **(
                    {"input_dm_calibration_sha256": calibration_sha256}
                    if dsa_contract["bound_source"]
                    == "calibrated_v3_integer_interval_intersection"
                    else {}
                ),
                "raw_crop_start_sample": crop_start,
                "crop_samples": int(inv["dsa"]["reference_shape"][1]),
                "padding_samples": 64,
                "audit_sample_rows": int(
                    inventory_raw["sampled_dsa_rows_per_event"]
                ),
                "accepted_support": inv["dsa"]["support"],
                "gates": dict(CASEY_GATES["dsa"]),
            },
            "geometry": {
                "geometry_dm_pc_cm3": geometry_dm,
                "reference_frequency_mhz": 400.0,
                "dsa_native_frequency_mhz": float(
                    burst["dsa"]["native_frequency_mhz"]
                ),
            },
            "workflow": {
                "execution_authorized": execution_authorized,
                "regression_fixture": False,
                "chime_container_image": CONTAINER_IMAGE,
                "container_data_mount": "/data/Faber2026",
                "stages": list(STAGES),
            },
            "review": {
                "configuration_status": configuration_status,
                "blockers": blockers,
                "dsa_input_state": {
                    "authority": "raw_reference_row_timing_v3_value_or_bound",
                    "reconstruction_sha256": reconstruction_sha256,
                    "independent_uncertainty_review_status": args.review_status,
                    "accepted_for_config_review": dsa_contract[
                        "accepted_for_config_review"
                    ],
                    "conservative_bound_accepted_for_config_review": (
                        dsa_contract[
                            "conservative_bound_accepted_for_config_review"
                        ]
                    ),
                    "material_nonzero_residual_proven": bool(
                        dsa_reconstruction["material_nonzero_residual_proven"]
                    ),
                    "inferred_raw_input_dm_pc_cm3": float(
                        dsa_reconstruction["inferred_raw_input_dm_pc_cm3"]
                    ),
                    "conservative_uncertainty_pc_cm3": float(
                        dsa_reconstruction["conservative_uncertainty_pc_cm3"]
                    ),
                },
            },
            "event_binding_sha256": "0" * 64,
        }
        config["event_binding_sha256"] = event_binding_sha256(config)
        validate_config(config)
        event_dir = args.output_root / event
        event_dir.mkdir(parents=True, exist_ok=True)
        config_path = event_dir / "workflow-config.json"
        config_path.write_text(json.dumps(config, indent=2) + "\n")
        summaries.append(
            {
                "event": event,
                "config": str(config_path),
                "event_binding_sha256": config["event_binding_sha256"],
                "execution_authorized": execution_authorized,
                "chime_config_review": {
                    "accepted_reference_dm_pc_cm3": float(
                        fit["chime"]["product_dm"]
                    ),
                    "h5_coherent_power_dm_pc_cm3": h5_dm,
                    "geometry_dm_pc_cm3": geometry_dm,
                    "anchor_dm_pc_cm3": chime_grid["anchor_dm_pc_cm3"],
                    "coarse_half_width_pc_cm3": chime_grid[
                        "coarse_half_width_pc_cm3"
                    ],
                    "reference_pulse_fwhm_s": fwhm_s,
                    "window_s": config["chime"]["window_s"],
                    "status": args.review_status,
                },
                "dsa_config_review": {
                    "accepted_reference_dm_pc_cm3": float(
                        fit["dsa"]["product_dm"]
                    ),
                    "crop_start_candidate_sample": crop_start,
                    "crop_start_at_400_mhz_fit_sample": crop_coordinate,
                    "input_dm_method": dsa_contract["method"],
                    "input_dm_bound_source": dsa_contract["bound_source"],
                    "nominal_input_dm_pc_cm3": dsa_contract[
                        "nominal_input_dm_pc_cm3"
                    ],
                    "input_dm_half_width_pc_cm3": dsa_contract[
                        "input_dm_half_width_pc_cm3"
                    ],
                    "reference_minus_raw_dm_interval_pc_cm3": dsa_contract[
                        "reference_minus_raw_dm_interval_pc_cm3"
                    ],
                    "calibration_attempt": (
                        {
                            "sha256": calibration_sha256,
                            "accepted_for_bound_narrowing": bool(
                                dsa_calibration[
                                    "calibration_accepted_for_bound_narrowing"
                                ]
                            ),
                            "failed_checks": sorted(
                                key
                                for key, passed in dsa_calibration[
                                    "checks"
                                ].items()
                                if not passed
                            ),
                        }
                        if dsa_calibration is not None
                        else None
                    ),
                    "reference_400_timing_half_width_native_samples": (
                        timing_half_width_samples
                    ),
                    "matched_start_sample_min": int(
                        inv["dsa"]["row_match"]["start_sample_min"]
                    ),
                    "matched_start_sample_max": int(
                        inv["dsa"]["row_match"]["start_sample_max"]
                    ),
                    "direct_median_correlation": float(
                        inv["dsa"]["frequency_order"][
                            "direct_median_correlation"
                        ]
                    ),
                    "reversed_median_correlation": float(
                        inv["dsa"]["frequency_order"][
                            "reversed_median_correlation"
                        ]
                    ),
                    "inferred_reference_minus_raw_dm_pc_cm3": float(
                        inv["dsa"]["dedispersion_state_fit"][
                            "inferred_reference_minus_raw_dm_pc_cm3"
                        ]
                    ),
                    "blockers": blockers,
                    "status": configuration_status,
                },
            }
        )
    summary = {
        "schema_version": 1,
        "status": SUMMARY_STATUS,
        "source_receipts": {
            "h17_control_root": str(args.h17_control_root),
            "inventory_sha256": sha256_file(args.inventory),
            "hash_manifest_sha256": sha256_file(args.hash_manifest),
            "dsa_reconstruction_sha256": reconstruction_sha256,
            **(
                {"dsa_calibration_sha256": calibration_sha256}
                if calibration_sha256 is not None
                else {}
            ),
            "timing_results_sha256": shared_hashes["timing_results"],
            "trigger_recovery_sha256": shared_hashes["trigger_recovery"],
            "reproduction_fixture_sha256": shared_hashes[
                "reproduction_fixture"
            ],
        },
        "selection_rules": {
            "chime_anchor": "geometry DM rounded to 0.01 pc cm^-3",
            "chime_grid": (
                "minimum 0.10 pc cm^-3 half-width, widened in 0.05 steps to "
                "cover accepted CHIME DM, H5 coherent-power DM, and geometry "
                "DM with 0.03 pc cm^-3 margin"
            ),
            "chime_window": (
                "minimum 0.03 s, widened in 0.01 s steps to at least 1.25 "
                "times the fixture pulse width"
            ),
            "dsa_input_state": (
                "material residuals use inferred raw DM with v3 uncertainty; "
                "nonmaterial residuals use accepted-product DM as nominal with "
                "half-width abs(fitted residual) plus v3 uncertainty"
            ),
            "dsa_endpoint_gates": (
                "both bound endpoints must remain within 16 native time samples "
                "at 400 MHz and peak-aligned profile correlation must be at "
                "least 0.98 for anchor, hybrid-fit, and geometry products"
            ),
            "authorization": (
                "campaign paused; generated configs are always execution-disabled; "
                "a separately reviewed tracked campaign-state receipt is required "
                "before any future launch"
            ),
        },
        "configs": summaries,
    }
    summary_path = args.output_root / "phase-b-config-review.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--timing-results", type=Path, required=True)
    parser.add_argument("--trigger-recovery", type=Path, required=True)
    parser.add_argument("--coherent-fits", type=Path, required=True)
    parser.add_argument("--h5-audit", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--hash-manifest", type=Path, required=True)
    parser.add_argument("--dsa-reconstruction", type=Path, required=True)
    parser.add_argument("--dsa-calibration", type=Path)
    parser.add_argument(
        "--review-status",
        choices=("pending", "passed"),
        default="pending",
    )
    parser.add_argument("--authorize-event", action="append", default=[])
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument(
        "--h17-control-root",
        type=Path,
        default=Path(
            "/data/Faber2026/evidence/dm-toa-geometry-20260728/phase-b-control"
        ),
    )
    args = parser.parse_args()
    summary = generate(args)
    blocked = sum(
        bool(row["dsa_config_review"]["blockers"]) for row in summary["configs"]
    )
    authorized = sum(
        bool(row["execution_authorized"]) for row in summary["configs"]
    )
    print(
        json.dumps(
            {
                "configs_written": len(summary["configs"]),
                "dsa_blocked": blocked,
                "execution_authorized": authorized,
            }
        )
    )


if __name__ == "__main__":
    main()
