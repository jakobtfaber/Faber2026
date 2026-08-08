#!/usr/bin/env python3
"""Write a hash-bound, analytic fit-resolution proposal for owner review."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from radio_pipeline.fitting.products import (  # noqa: E402
    load_band_observation_product,
    sha256_file,
)
from radio_pipeline.fitting.resolution import (  # noqa: E402
    arrays_sha256,
    residual_smearing_calculation,
    sample_time_axis_ns,
)
from scripts.one_event_workflow import validate_config  # noqa: E402


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def payload_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def validate_source_contract(
    instrument: str,
    observation_path: Path,
    template: dict[str, Any],
    diagnostic: dict[str, Any],
) -> None:
    """Reject cross-event or changed high-resolution products."""

    if diagnostic["inputs"][f"{instrument}_observation"] != sha256_file(
        observation_path
    ):
        raise ValueError(f"{instrument} observation differs from component diagnostic")
    with np.load(observation_path, allow_pickle=False) as product:
        shape = list(product["waterfall"].shape)
        sample_interval_s = float(product["sample_interval_s"])
        frequency_hash = arrays_sha256(
            product["frequency_mhz"],
            product["channel_width_mhz"],
        )
        valid_hash = arrays_sha256(product["pixel_valid"])
        expected = {
            "shape": shape,
            "sample_interval_s": sample_interval_s,
            "frequency_grid_sha256": frequency_hash,
            "valid_mask_sha256": valid_hash,
        }
        if diagnostic["observation_contracts"][instrument] != expected:
            raise ValueError(
                f"{instrument} observation contract differs from component diagnostic"
            )
        time_axis = sample_time_axis_ns(
            time0_unix_ns=int(product["time0_unix_ns"]),
            sample_interval_s=sample_interval_s,
            sample_count=shape[1],
        )
        template_expected = {
            f"{instrument}_shape": shape,
            f"{instrument}_sample_interval_s": sample_interval_s,
            f"{instrument}_frequency_bin_factor": int(
                product["frequency_bin_factor"]
            ),
            f"{instrument}_time_bin_factor": int(product["time_bin_factor"]),
            f"{instrument}_frequency_grid_sha256": frequency_hash,
            f"{instrument}_valid_mask_sha256": valid_hash,
            f"{instrument}_off_pulse_mask_sha256": arrays_sha256(
                product["noise_estimation_mask"]
            ),
            f"{instrument}_waterfall_sha256": arrays_sha256(product["waterfall"]),
            f"{instrument}_noise_std_sha256": arrays_sha256(product["noise_std"]),
            f"{instrument}_time_axis_sha256": arrays_sha256(time_axis),
            f"{instrument}_time0_unix_ns": int(product["time0_unix_ns"]),
        }
    for key, value in template_expected.items():
        if template.get(key) != value:
            raise ValueError(f"{instrument} template identity changed: {key}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--component-diagnostic", type=Path, required=True)
    parser.add_argument("--chime-observation", type=Path, required=True)
    parser.add_argument("--dsa-observation", type=Path, required=True)
    parser.add_argument("--chime-frequency-factor", type=int, required=True)
    parser.add_argument("--dsa-frequency-factor", type=int, required=True)
    parser.add_argument("--output-proposal", type=Path, required=True)
    parser.add_argument("--output-calculation", type=Path, required=True)
    args = parser.parse_args()

    config = validate_config(json.loads(args.config.read_text()))
    proposal = json.loads(args.template.read_text())
    diagnostic = json.loads(args.component_diagnostic.read_text())
    if (
        diagnostic.get("event") != config["event"]
        or diagnostic.get("event_binding_sha256")
        != config["event_binding_sha256"]
        or diagnostic.get("review_plan") != config["joint_fit"]["review_plan"]
        or diagnostic.get("inputs", {}).get("config") != sha256_file(args.config)
    ):
        raise ValueError("component diagnostic belongs to another event or configuration")
    policy = config["joint_fit"]["review_plan"]["fit_resolution"]
    dm_bounds = tuple(config["joint_fit"]["dm_bounds_pc_cm3"])
    observations = {
        "chime": load_band_observation_product(args.chime_observation),
        "dsa": load_band_observation_product(args.dsa_observation),
    }
    factors = {
        "chime": args.chime_frequency_factor,
        "dsa": args.dsa_frequency_factor,
    }
    validate_source_contract(
        "chime",
        args.chime_observation,
        proposal,
        diagnostic,
    )
    validate_source_contract(
        "dsa",
        args.dsa_observation,
        proposal,
        diagnostic,
    )
    calculations: dict[str, Any] = {
        "schema_version": 1,
        "event": config["event"],
        "event_binding_sha256": config["event_binding_sha256"],
        "config_sha256": sha256_file(args.config),
        "component_diagnostic_sha256": sha256_file(args.component_diagnostic),
        "instruments": {},
    }
    for instrument, observation in observations.items():
        calculation = residual_smearing_calculation(
            observation,
            absolute_dm_bounds_pc_cm3=dm_bounds,
            frequency_bin_factor=factors[instrument],
        )
        component_widths = [
            float(row["matched_filter_width_samples"])
            * float(observation.sample_interval_s)
            for row in diagnostic["components"]
            if row["instrument"] == instrument
        ]
        if not component_widths:
            raise ValueError(f"{instrument} diagnostic has no component width")
        fit_limit = (
            float(policy["maximum_residual_smearing_fraction_of_fit_sample"])
            * float(observation.sample_interval_s)
        )
        width_limit = (
            float(policy["maximum_residual_smearing_fraction_of_component_width"])
            * min(component_widths)
        )
        calculation.update(
            {
                "source_observation_sha256": sha256_file(
                    args.chime_observation
                    if instrument == "chime"
                    else args.dsa_observation
                ),
                "narrowest_diagnostic_fwhm_s": min(component_widths),
                "fit_sample_limit_s": fit_limit,
                "component_width_limit_s": width_limit,
                "passes": calculation["maximum_smearing_s"]
                <= min(fit_limit, width_limit),
            }
        )
        if not calculation["passes"]:
            raise ValueError(f"{instrument} residual smearing exceeds reviewed limits")
        calculations["instruments"][instrument] = calculation

    args.output_calculation.parent.mkdir(parents=True, exist_ok=True)
    args.output_calculation.write_text(
        json.dumps(calculations, indent=2, sort_keys=True) + "\n"
    )
    for instrument in ("chime", "dsa"):
        calculation = calculations["instruments"][instrument]
        proposal[f"{instrument}_fit_frequency_average_factor"] = factors[instrument]
        proposal[f"{instrument}_fit_time_average_factor"] = 1
        proposal[f"{instrument}_max_residual_intra_bin_smearing_s"] = calculation[
            "maximum_smearing_s"
        ]
        proposal[f"{instrument}_smearing_calculation_sha256"] = payload_sha256(
            calculation
        )
    args.output_proposal.write_text(
        json.dumps(proposal, indent=2, sort_keys=True) + "\n"
    )
    print(args.output_proposal)


if __name__ == "__main__":
    main()
