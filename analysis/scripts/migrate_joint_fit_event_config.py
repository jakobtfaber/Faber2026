#!/usr/bin/env python3
"""Migrate one reviewed legacy event config to the blocked joint-fit contract."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from one_event_workflow import STAGES, event_binding_sha256, validate_config

CANONICAL_TRIGGER_PATH = Path(
    "/data/Faber2026/evidence/dm-toa-geometry-20260728/"
    "phase-b-control/shared-inputs/trigger_mjd_microsecond_recovery.json"
)
CANONICAL_OUTPUT_ROOT = Path(
    "/data/Faber2026/evidence/geometry-constrained-joint-fit"
)
STATION_CLOCK_SIGMA_S = 0.001 / 2.0**0.5
SITE_DELAY_SIGMA_S = 5.0e-7

TIMING_PROVENANCE = {
    "status": "owner_adopted_provisional_bounds",
    "inter_site_clock_sigma_s": 0.001,
    "clock_allocation": "equal_independent_station_terms",
    "clock_basis": (
        "owner-adopted provisional 1 ms Gaussian standard deviation on the "
        "inter-site difference for this fit"
    ),
    "site_delay_basis": (
        "owner-adopted provisional 0.5 us Gaussian standard deviation per "
        "station; not inferred from projection agreement"
    ),
    "absolute_utc_calibration_status": "not_independently_measured",
    "owner_adoption_date": "2026-07-29",
}


def migrate_config(
    source: dict[str, Any],
    *,
    source_icrs: str,
    epoch_mjd_utc: str,
) -> dict[str, Any]:
    """Return a disabled production config while preserving reviewed inputs."""

    if not source_icrs.strip():
        raise ValueError("source_icrs must not be empty")
    if not epoch_mjd_utc.strip():
        raise ValueError("epoch_mjd_utc must not be empty")

    config = deepcopy(source)
    event = str(config["event"])
    config["$schema"] = "schema.json"
    config["result_status"] = "geometry_constrained_joint_fit_blocked_pending_review"

    config["identity"]["input_basenames"]["trigger_recovery"] = (
        CANONICAL_TRIGGER_PATH.name
    )
    config["paths"]["trigger_recovery"] = str(CANONICAL_TRIGGER_PATH)
    config["identity"]["output_root_basename"] = event
    config["paths"]["output_root"] = str(CANONICAL_OUTPUT_ROOT / event)

    config["joint_fit"] = {
        "status": "blocked_pending_reviewed_inputs",
        "execution_authorized": False,
        "reference_frequency_mhz": 400.0,
        "blockers": [
            "component_windows_and_associations_not_reviewed",
            "fit_resolution_averaging_not_reviewed_or_materialized",
            "resolution_crop_and_off_pulse_padding_not_reviewed",
            "strict_observation_products_not_regenerated",
        ],
        "geometry": {
            "source_icrs": source_icrs,
            "epoch_mjd_utc": epoch_mjd_utc,
            "site_delay_sigma_s": {
                "chime": SITE_DELAY_SIGMA_S,
                "dsa": SITE_DELAY_SIGMA_S,
            },
            "clock_sigma_s": {
                "chime": STATION_CLOCK_SIGMA_S,
                "dsa": STATION_CLOCK_SIGMA_S,
            },
            "timing_uncertainty_provenance": deepcopy(TIMING_PROVENANCE),
            "maximum_projection_disagreement_s": SITE_DELAY_SIGMA_S,
        },
        "resolution": {
            "status": "pending_owner_review",
            "chime_frequency_bin_factor": None,
            "chime_time_bin_factor": None,
            "dsa_frequency_bin_factor": None,
            "dsa_time_bin_factor": None,
            "chime_fit_frequency_average_factor": None,
            "chime_fit_time_average_factor": None,
            "dsa_fit_frequency_average_factor": None,
            "dsa_fit_time_average_factor": None,
            "chime_fit_observation_sha256": None,
            "dsa_fit_observation_sha256": None,
            "chime_max_residual_intra_bin_smearing_s": None,
            "dsa_max_residual_intra_bin_smearing_s": None,
            "chime_smearing_calculation_sha256": None,
            "dsa_smearing_calculation_sha256": None,
            "crop_and_off_pulse_padding_locked": False,
        },
        "review_plan": {
            "component_count": {"chime": 1, "dsa": 1},
            "association_hypotheses": [
                {
                    "name": "c1d1",
                    "matches": [
                        {
                            "latent_id": "c1",
                            "chime_component_id": "chime_c1",
                            "dsa_component_id": "dsa_c1",
                        }
                    ],
                }
            ],
            "fit_resolution": {
                "status": "pending_data_driven_proposal",
                "minimum_valid_fraction": 1.0,
                "minimum_samples_per_component": 8,
                "time_average_factor": 1,
                "maximum_residual_smearing_fraction_of_fit_sample": 0.1,
                "maximum_residual_smearing_fraction_of_component_width": 0.05,
                "exact_divisor_required": True,
            },
        },
        "dm_bounds_pc_cm3": [
            config["chime"]["anchor_dm_pc_cm3"]
            - config["chime"]["grid"]["coarse_half_width_pc_cm3"],
            config["chime"]["anchor_dm_pc_cm3"]
            + config["chime"]["grid"]["coarse_half_width_pc_cm3"],
        ],
        "morphologies": ["gaussian", "scattering"],
        "scattering_tau_1ghz_bounds_s": [1.0e-6, 5.0e-3],
        "scattering_alpha_bounds": [2.0, 6.0],
        "gain_variance": 100.0,
        "sampler": {
            "seed": 20260729,
            "nlive": 600,
            "dlogz": 0.5,
            "sample": "rwalk",
            "pool_size": 1,
            "resume": True,
        },
        "acceptance": {
            "maximum_reduced_residual_power": 2.0,
            "maximum_structured_residual_correlation": 0.2,
            "posterior_edge_fraction": 0.01,
            "maximum_prior_edge_mass": 0.05,
            "resolution_convergence_required": True,
            "maximum_resolution_dm_shift_combined_sigma": 0.5,
            "maximum_resolution_dm_shift_pc_cm3": 0.005,
            "maximum_resolution_toa_shift_combined_sigma": 0.5,
            "resolution_interval_width_ratio": [0.8, 1.25],
            "maximum_resolution_model_weight_l1_difference": 0.1,
        },
    }
    config["workflow"]["execution_authorized"] = False
    config["workflow"]["regression_fixture"] = False
    config["workflow"]["stages"] = list(STAGES)

    config["event_binding_sha256"] = event_binding_sha256(config)
    return validate_config(config)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-icrs", required=True)
    parser.add_argument("--epoch-mjd-utc", required=True)
    args = parser.parse_args()

    source = json.loads(args.source.read_text())
    config = migrate_config(
        source,
        source_icrs=args.source_icrs,
        epoch_mjd_utc=args.epoch_mjd_utc,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(config, indent=2, allow_nan=False) + "\n")
    print(config["event_binding_sha256"])


if __name__ == "__main__":
    main()
