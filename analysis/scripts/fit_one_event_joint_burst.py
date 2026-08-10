#!/usr/bin/env python3
"""Run one geometry-constrained joint fit from strict observation products."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import dynesty
import numpy as np
from one_event_workflow import (
    arrays_sha256,
    load_config,
    sample_time_axis_ns,
    validate_timing_sensitivity_roster,
)

import radio_pipeline
from radio_pipeline.fitting import (
    AssociationHypothesis,
    ComponentMatch,
    ComponentWindow,
    FitSettings,
    GeometryConstraint,
    JointFitRequest,
    fit_joint_event,
    load_band_observation_product,
)
from radio_pipeline.fitting.products import sha256_file


def _require_accepted_status(status: str) -> None:
    if status != "provisional_pending_owner_approval":
        raise RuntimeError(f"joint fit failed acceptance gates: {status}")


def _arrays_sha256(*arrays: np.ndarray) -> str:
    return arrays_sha256(*arrays)


def _require_locked_array_identity(observation, resolution: dict) -> None:
    instrument = observation.instrument
    if (
        _arrays_sha256(
            observation.frequency_mhz,
            observation.channel_width_mhz,
        )
        != resolution[f"{instrument}_frequency_grid_sha256"]
    ):
        raise ValueError(f"{instrument} authoritative frequency grid changed")
    if _arrays_sha256(observation.valid) != resolution[f"{instrument}_valid_mask_sha256"]:
        raise ValueError(f"{instrument} accepted valid support changed")


def _require_locked_product_metadata(
    product,
    instrument: str,
    resolution: dict,
    *,
    expected_time0_unix_ns: int | None = None,
    expected_time_axis_sha256: str | None = None,
) -> None:
    expected_time0 = int(
        resolution[f"{instrument}_time0_unix_ns"]
        if expected_time0_unix_ns is None
        else expected_time0_unix_ns
    )
    if int(product["time0_unix_ns"]) != expected_time0:
        raise ValueError(f"{instrument} locked crop origin changed")
    if "noise_estimation_mask" not in product:
        raise ValueError(f"{instrument} product lacks off-pulse mask")
    if (
        _arrays_sha256(product["noise_estimation_mask"])
        != resolution[f"{instrument}_off_pulse_mask_sha256"]
    ):
        raise ValueError(f"{instrument} locked off-pulse support changed")
    if (
        _arrays_sha256(product["waterfall"])
        != resolution[f"{instrument}_waterfall_sha256"]
    ):
        raise ValueError(f"{instrument} locked waterfall pixels changed")
    if (
        _arrays_sha256(product["noise_std"])
        != resolution[f"{instrument}_noise_std_sha256"]
    ):
        raise ValueError(f"{instrument} locked noise estimates changed")
    time_axis_ns = sample_time_axis_ns(
        time0_unix_ns=int(product["time0_unix_ns"]),
        sample_interval_s=float(product["sample_interval_s"]),
        sample_count=int(product["waterfall"].shape[1]),
    )
    expected_axis = (
        resolution[f"{instrument}_time_axis_sha256"]
        if expected_time_axis_sha256 is None
        else expected_time_axis_sha256
    )
    if _arrays_sha256(time_axis_ns) != expected_axis:
        raise ValueError(f"{instrument} locked time axis changed")


def _runtime_preflight(repo_root: Path) -> dict[str, str]:
    expected_package = (repo_root / "radio_pipeline").resolve()
    actual_package = Path(radio_pipeline.__file__).resolve().parent
    if actual_package != expected_package:
        raise RuntimeError("radio_pipeline was not imported from this checkout")
    dynesty_path = Path(dynesty.__file__).resolve()
    if not str(dynesty.__version__).startswith("3.1."):
        raise RuntimeError("locked workflow requires dynesty 3.1.x")
    if any("dsa110-FLITS" in entry for entry in sys.path):
        raise RuntimeError("retired editable FLITS runtime detected")
    return {
        "radio_pipeline": str(actual_package),
        "dynesty": str(dynesty_path),
        "dynesty_version": str(dynesty.__version__),
    }


def _load_locked_fit_observations(
    settings: dict,
    chime_path: Path,
    dsa_path: Path,
    *,
    dsa_expected_sha256: str | None = None,
):
    resolution = settings["resolution"]
    return (
        load_band_observation_product(
            chime_path,
            expected_sha256=resolution["chime_fit_observation_sha256"],
        ),
        load_band_observation_product(
            dsa_path,
            expected_sha256=(
                resolution["dsa_fit_observation_sha256"]
                if dsa_expected_sha256 is None
                else dsa_expected_sha256
            ),
        ),
    )


def _timing_variant_contract(
    config: dict,
    dsa_path: Path,
    timing_variant: str,
    timing_sensitivity_roster: dict | None,
    timing_sensitivity_roster_path: Path | None = None,
    timing_sensitivity_roster_sha256: str | None = None,
) -> dict[str, object]:
    resolution = config["joint_fit"]["resolution"]
    if timing_variant == "primary":
        if any(
            value is not None
            for value in (
                timing_sensitivity_roster,
                timing_sensitivity_roster_path,
                timing_sensitivity_roster_sha256,
            )
        ):
            raise ValueError("primary fit does not accept a timing-sensitivity roster")
        return {
            "product_sha256": resolution["dsa_fit_observation_sha256"],
            "time0_unix_ns": int(resolution["dsa_time0_unix_ns"]),
            "time_axis_sha256": resolution["dsa_time_axis_sha256"],
        }
    if (
        timing_variant != "alternative_anchor"
        or timing_sensitivity_roster is None
        or timing_sensitivity_roster_path is None
        or timing_sensitivity_roster_sha256 is None
    ):
        raise ValueError("alternative-anchor fit requires its reviewed timing roster")
    reviewed_roster_sha256 = config["joint_fit"]["review_decision"][
        "timing_sensitivity_roster_sha256"
    ]
    if (
        sha256_file(timing_sensitivity_roster_path)
        != timing_sensitivity_roster_sha256
        or timing_sensitivity_roster_sha256 != reviewed_roster_sha256
    ):
        raise ValueError("timing-sensitivity roster differs from the reviewed input")
    validate_timing_sensitivity_roster(config, timing_sensitivity_roster)
    alternative = timing_sensitivity_roster["alternative_anchor"]
    if dsa_path.resolve() != Path(alternative["product"]).resolve():
        raise ValueError("alternative-anchor fit received the wrong DSA observation")
    time0_unix_ns = int(alternative["time0_unix_ns"])
    time_axis_sha256 = _arrays_sha256(
        sample_time_axis_ns(
            time0_unix_ns=time0_unix_ns,
            sample_interval_s=float(resolution["dsa_sample_interval_s"]),
            sample_count=int(resolution["dsa_shape"][1]),
        )
    )
    return {
        "product_sha256": alternative["sha256"],
        "time0_unix_ns": time0_unix_ns,
        "time_axis_sha256": time_axis_sha256,
        "roster_path": str(timing_sensitivity_roster_path.resolve()),
        "roster_sha256": timing_sensitivity_roster_sha256,
    }


def _variant_output_dir(config: dict, timing_variant: str) -> Path:
    primary = Path(config["paths"]["output_root"]).resolve()
    if timing_variant == "primary":
        return primary
    if timing_variant == "alternative_anchor":
        return primary.parent / f"{primary.name}-anchor-15256-sensitivity"
    raise ValueError("unknown timing variant")


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(payload, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _prepare_output_binding(output_dir: Path, binding: dict[str, object]) -> None:
    checkpoint_dir = output_dir / ".checkpoints"
    binding_path = checkpoint_dir / "timing-variant.json"
    for product_name in ("fit-result.json", "run-provenance.json"):
        product_path = output_dir / product_name
        if product_path.is_file():
            existing = json.loads(product_path.read_text())
            if existing.get("timing_binding") != binding:
                raise ValueError("fit output directory belongs to another timing variant")
    if binding_path.is_file():
        if json.loads(binding_path.read_text()) != binding:
            raise ValueError("checkpoint directory belongs to another timing variant")
    elif checkpoint_dir.is_dir() and any(checkpoint_dir.iterdir()):
        raise ValueError("checkpoint directory lacks a trusted timing-variant binding")
    _atomic_write_json(binding_path, binding)


def _request(
    config: dict,
    chime_path: Path,
    dsa_path: Path,
    geometry_path: Path,
    *,
    checkpoint_dir: Path,
    timing_variant: str,
    timing_sensitivity_roster: dict | None,
    timing_sensitivity_roster_path: Path | None,
    timing_sensitivity_roster_sha256: str | None,
) -> JointFitRequest:
    settings = config["joint_fit"]
    timing_contract = _timing_variant_contract(
        config,
        dsa_path,
        timing_variant,
        timing_sensitivity_roster,
        timing_sensitivity_roster_path,
        timing_sensitivity_roster_sha256,
    )
    observations = _load_locked_fit_observations(
        settings,
        chime_path,
        dsa_path,
        dsa_expected_sha256=str(timing_contract["product_sha256"]),
    )
    expected_inputs = config["input_sha256"]
    if observations[0].input_sha256 != {
        "raw_chime_h5": expected_inputs["raw_chime_h5"],
        "accepted_chime_reference": expected_inputs["accepted_chime_reference"],
    }:
        raise ValueError("CHIME observation input hashes differ from configuration")
    if observations[1].input_sha256 != {
        "raw_dsa_filterbank": expected_inputs["raw_dsa_filterbank"],
        "accepted_dsa_reference": expected_inputs["accepted_dsa_reference"],
    }:
        raise ValueError("DSA observation input hashes differ from configuration")
    resolution = settings["resolution"]
    for observation, product_path in zip(observations, (chime_path, dsa_path), strict=True):
        expected_shape = tuple(map(int, resolution[f"{observation.instrument}_shape"]))
        expected_sample = float(resolution[f"{observation.instrument}_sample_interval_s"])
        if observation.waterfall.shape != expected_shape:
            raise ValueError(f"{observation.instrument} locked crop shape changed")
        if not np.isclose(
            observation.sample_interval_s,
            expected_sample,
            rtol=0.0,
            atol=1.0e-15,
        ):
            raise ValueError(f"{observation.instrument} locked time resolution changed")
        with np.load(product_path, allow_pickle=False) as product:
            _require_locked_product_metadata(
                product,
                observation.instrument,
                resolution,
                **(
                    {
                        "expected_time0_unix_ns": int(
                            timing_contract["time0_unix_ns"]
                        ),
                        "expected_time_axis_sha256": str(
                            timing_contract["time_axis_sha256"]
                        ),
                    }
                    if observation.instrument == "dsa"
                    else {}
                ),
            )
            for axis in ("frequency", "time"):
                key = f"{axis}_bin_factor"
                if key not in product:
                    raise ValueError(f"{observation.instrument} product lacks {key}")
                expected = int(resolution[f"{observation.instrument}_{axis}_bin_factor"])
                if int(product[key]) != expected:
                    raise ValueError(f"{observation.instrument} locked {axis} bin factor changed")
        _require_locked_array_identity(observation, resolution)
    geometry_data = json.loads(geometry_path.read_text())
    if geometry_data["event_binding_sha256"] != config["event_binding_sha256"]:
        raise ValueError("geometry constraint belongs to another configuration")
    geometry = GeometryConstraint(
        epoch_unix_ns=int(geometry_data["epoch_unix_ns"]),
        source_icrs=geometry_data["source_icrs"],
        site_delay_s=geometry_data["site_delay_s"],
        site_delay_sigma_s=geometry_data["site_delay_sigma_s"],
        clock_sigma_s=geometry_data["clock_sigma_s"],
        projection_disagreement_s=float(geometry_data["projection_disagreement_s"]),
        reference_frequency_mhz=float(geometry_data["reference_frequency_mhz"]),
    )
    components = tuple(
        ComponentWindow(
            instrument=row["instrument"],
            component_id=row["component_id"],
            center_sample=float(row["center_sample"]),
            half_width_samples=float(row["half_width_samples"]),
            width_bounds_s=tuple(map(float, row["width_bounds_s"])),
            width_index_bounds=tuple(map(float, row.get("width_index_bounds", [-2.0, 2.0]))),
        )
        for row in settings["components"]
    )
    associations = tuple(
        AssociationHypothesis(
            name=row["name"],
            matches=tuple(
                ComponentMatch(
                    latent_id=match["latent_id"],
                    chime_component_id=match["chime_component_id"],
                    dsa_component_id=match["dsa_component_id"],
                )
                for match in row["matches"]
            ),
        )
        for row in settings["associations"]
    )
    sampler = settings["sampler"]
    fit_settings = FitSettings(
        dm_bounds_pc_cm3=tuple(map(float, settings["dm_bounds_pc_cm3"])),
        morphologies=tuple(settings["morphologies"]),
        scattering_tau_1ghz_bounds_s=tuple(map(float, settings["scattering_tau_1ghz_bounds_s"])),
        scattering_alpha_bounds=tuple(map(float, settings["scattering_alpha_bounds"])),
        gain_variance=float(settings["gain_variance"]),
        seed=int(sampler["seed"]),
        nlive=int(sampler["nlive"]),
        dlogz=float(sampler["dlogz"]),
        sample=sampler.get("sample", "rwalk"),
        pool_size=int(sampler.get("pool_size", 1)),
        checkpoint_dir=str(checkpoint_dir),
        resume=bool(sampler.get("resume", True)),
        maximum_projection_disagreement_s=float(
            settings.get("maximum_projection_disagreement_s", 5.0e-7)
        ),
        maximum_reduced_residual_power=float(
            settings["acceptance"]["maximum_reduced_residual_power"]
        ),
        maximum_structured_residual_correlation=float(
            settings["acceptance"]["maximum_structured_residual_correlation"]
        ),
        posterior_edge_fraction=float(settings["acceptance"]["posterior_edge_fraction"]),
        maximum_prior_edge_mass=float(settings["acceptance"]["maximum_prior_edge_mass"]),
    )
    return JointFitRequest(
        observations=observations,
        geometry=geometry,
        components=components,
        associations=associations,
        settings=fit_settings,
    )


def run(
    config: dict,
    *,
    chime_path: Path,
    dsa_path: Path,
    geometry_path: Path,
    output_dir: Path,
    repo_root: Path,
    timing_variant: str = "primary",
    timing_sensitivity_roster: dict | None = None,
    timing_sensitivity_roster_path: Path | None = None,
    timing_sensitivity_roster_sha256: str | None = None,
) -> dict:
    required_output_dir = _variant_output_dir(config, timing_variant)
    if output_dir.resolve() != required_output_dir:
        raise ValueError(
            f"{timing_variant} fit output must be {required_output_dir}"
        )
    runtime = _runtime_preflight(repo_root)
    request = _request(
        config,
        chime_path,
        dsa_path,
        geometry_path,
        checkpoint_dir=output_dir / ".checkpoints",
        timing_variant=timing_variant,
        timing_sensitivity_roster=timing_sensitivity_roster,
        timing_sensitivity_roster_path=timing_sensitivity_roster_path,
        timing_sensitivity_roster_sha256=timing_sensitivity_roster_sha256,
    )
    timing_contract = _timing_variant_contract(
        config,
        dsa_path,
        timing_variant,
        timing_sensitivity_roster,
        timing_sensitivity_roster_path,
        timing_sensitivity_roster_sha256,
    )
    binding = {
        "event_binding_sha256": config["event_binding_sha256"],
        "timing_variant": timing_variant,
        "dsa_observation_sha256": str(timing_contract["product_sha256"]),
        "timing_sensitivity_roster_sha256": timing_contract.get("roster_sha256"),
    }
    _prepare_output_binding(output_dir, binding)
    result = fit_joint_event(request)
    shutil.rmtree(output_dir / ".checkpoints", ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    fit_result_path = output_dir / "fit-result.json"
    posterior_path = output_dir / "posterior.npz"
    model_path = output_dir / "model-products.npz"
    np.savez_compressed(
        posterior_path,
        run_weights=result.run_weights,
        **{
            f"run_{index}_{field}": value
            for index, run in enumerate(result.runs)
            for field, value in (
                ("samples", run.samples),
                ("sample_weights", run.sample_weights),
                ("parameter_names", np.asarray(run.parameter_names)),
                ("morphology", np.asarray(run.morphology)),
                ("association", np.asarray(run.association)),
                ("log_evidence", np.asarray(run.log_evidence)),
                ("log_evidence_error", np.asarray(run.log_evidence_error)),
            )
        },
    )
    np.savez_compressed(model_path, **result.model_products)
    code_hashes = {
        "joint_burst": sha256_file(repo_root / "radio_pipeline/fitting/joint_burst.py"),
        "products": sha256_file(repo_root / "radio_pipeline/fitting/products.py"),
        "pulse_kernels": sha256_file(
            repo_root / "radio_pipeline/fitting/_pulse_kernels.py"
        ),
        "runner": sha256_file(Path(__file__)),
    }
    fit_payload = {
        "schema_version": 1,
        "status": result.status,
        "event": config["event"],
        "event_binding_sha256": config["event_binding_sha256"],
        "timing_variant": timing_variant,
        "timing_binding": binding,
        "reference_frequency_mhz": 400.0,
        "shared_absolute_dm_pc_cm3": result.dm_pc_cm3,
        "geocentric_unscattered_toa_unix_ns": (result.geocentric_toa_unix_ns),
        "topocentric_toa_unix_ns": result.topocentric_toa_unix_ns,
        "diagnostics": result.diagnostics,
        "runs": [
            {
                "morphology": run.morphology,
                "association": run.association,
                "log_evidence": run.log_evidence,
                "log_evidence_error": run.log_evidence_error,
                "diagnostics": run.diagnostics,
            }
            for run in result.runs
        ],
        "compact_products": {
            "posterior.npz": sha256_file(posterior_path),
            "model-products.npz": sha256_file(model_path),
        },
        "fit_inputs": {
            "geometry_constraint": sha256_file(geometry_path),
            "chime_observation": sha256_file(chime_path),
            "dsa_observation": sha256_file(dsa_path),
            "timing_sensitivity_roster": (
                {
                    "path": str(timing_sensitivity_roster_path.resolve()),
                    "sha256": timing_sensitivity_roster_sha256,
                }
                if timing_sensitivity_roster_path is not None
                else None
            ),
        },
        "provenance_code_sha256": code_hashes,
    }
    fit_result_path.write_text(json.dumps(fit_payload, indent=2, allow_nan=False) + "\n")
    provenance = {
        "schema_version": 1,
        "status": result.status,
        "event": config["event"],
        "event_binding_sha256": config["event_binding_sha256"],
        "timing_variant": timing_variant,
        "timing_binding": binding,
        "inputs": {
            "config": sha256_file(config["_config_path"]),
            "chime_observation": sha256_file(chime_path),
            "dsa_observation": sha256_file(dsa_path),
            "geometry_constraint": sha256_file(geometry_path),
            "timing_sensitivity_roster": (
                {
                    "path": str(timing_sensitivity_roster_path.resolve()),
                    "sha256": timing_sensitivity_roster_sha256,
                }
                if timing_sensitivity_roster_path is not None
                else None
            ),
        },
        "code": code_hashes,
        "runtime": runtime,
        "outputs": {
            "fit-result.json": sha256_file(fit_result_path),
            "posterior.npz": sha256_file(posterior_path),
            "model-products.npz": sha256_file(model_path),
        },
    }
    provenance_path = output_dir / "run-provenance.json"
    provenance_path.write_text(json.dumps(provenance, indent=2, allow_nan=False) + "\n")
    _require_accepted_status(result.status)
    return fit_payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--chime-observation", type=Path, required=True)
    parser.add_argument("--dsa-observation", type=Path, required=True)
    parser.add_argument("--geometry-constraint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--timing-variant",
        choices=("primary", "alternative_anchor"),
        default="primary",
    )
    parser.add_argument("--timing-sensitivity-roster", type=Path)
    args = parser.parse_args()
    config = load_config(args.config)
    config["_config_path"] = str(args.config.resolve())
    timing_roster = (
        json.loads(args.timing_sensitivity_roster.read_text())
        if args.timing_sensitivity_roster is not None
        else None
    )
    timing_roster_sha256 = (
        sha256_file(args.timing_sensitivity_roster)
        if args.timing_sensitivity_roster is not None
        else None
    )
    result = run(
        config,
        chime_path=args.chime_observation,
        dsa_path=args.dsa_observation,
        geometry_path=args.geometry_constraint,
        output_dir=args.output_dir,
        repo_root=Path(__file__).resolve().parents[1],
        timing_variant=args.timing_variant,
        timing_sensitivity_roster=timing_roster,
        timing_sensitivity_roster_path=args.timing_sensitivity_roster,
        timing_sensitivity_roster_sha256=timing_roster_sha256,
    )
    print(json.dumps({"status": result["status"], "event": result["event"]}))


if __name__ == "__main__":
    main()
