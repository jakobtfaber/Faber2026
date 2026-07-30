#!/usr/bin/env python3
"""Fail closed on material frequency-resolution dependence in a joint fit."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

ACCEPTED_STATUS = "provisional_pending_owner_approval"
SHA256_RE = re.compile(r"[0-9a-f]{64}")
INSTRUMENTS = ("chime", "dsa")
CODE_KEYS = {"joint_burst", "products", "pulse_kernels", "runner"}

MODEL_KEYS = (
    "geometry",
    "components",
    "associations",
    "dm_bounds_pc_cm3",
    "morphologies",
    "scattering_tau_1ghz_bounds_s",
    "scattering_alpha_bounds",
    "gain_variance",
    "sampler",
    "acceptance",
)


def sha256_file(path: str | Path) -> str:
    """Hash one immutable verifier input."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} is not readable JSON") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def _finite_number(value: Any, label: str) -> int | float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{label} must be numeric")
    if not math.isfinite(float(value)):
        raise ValueError(f"{label} must be finite")
    return value


def _summary(value: Any, label: str) -> dict[str, int | float]:
    summary = _mapping(value, label)
    try:
        lower = _finite_number(summary["lower"], f"{label}.lower")
        median = _finite_number(summary["median"], f"{label}.median")
        upper = _finite_number(summary["upper"], f"{label}.upper")
    except KeyError as error:
        raise ValueError(f"{label} lacks lower, median, or upper") from error
    if not lower <= median <= upper or not lower < upper:
        raise ValueError(f"{label} 68% interval is invalid")
    return {"lower": lower, "median": median, "upper": upper}


def _model_identity(config: dict[str, Any]) -> dict[str, Any]:
    joint_fit = _mapping(config.get("joint_fit"), "joint_fit")
    missing = [key for key in MODEL_KEYS if key not in joint_fit]
    if missing:
        raise ValueError(f"joint_fit lacks model settings: {missing}")
    return {
        "chime": _mapping(config.get("chime"), "chime"),
        "dsa": _mapping(config.get("dsa"), "dsa"),
        "joint_fit": {key: joint_fit[key] for key in MODEL_KEYS},
        "maximum_projection_disagreement_s": joint_fit.get(
            "maximum_projection_disagreement_s",
            5.0e-7,
        ),
    }


def _matched_latent_ids(config: dict[str, Any]) -> tuple[str, ...]:
    joint_fit = _mapping(config.get("joint_fit"), "joint_fit")
    associations = joint_fit.get("associations")
    if not isinstance(associations, list) or not associations:
        raise ValueError("joint_fit.associations must be a non-empty list")
    latent_sets: list[set[str]] = []
    for hypothesis in associations:
        hypothesis = _mapping(hypothesis, "association")
        matches = hypothesis.get("matches")
        if not isinstance(matches, list) or not matches:
            raise ValueError("every association requires matched components")
        latent_ids = set()
        for match in matches:
            match = _mapping(match, "association match")
            latent_id = match.get("latent_id")
            if not isinstance(latent_id, str) or not latent_id:
                raise ValueError("association match has an invalid latent_id")
            if latent_id in latent_ids:
                raise ValueError("association reuses a latent_id")
            latent_ids.add(latent_id)
        latent_sets.append(latent_ids)
    if any(values != latent_sets[0] for values in latent_sets[1:]):
        raise ValueError("association hypotheses have different matched latent IDs")
    return tuple(sorted(latent_sets[0]))


def _expected_run_names(config: dict[str, Any]) -> set[str]:
    joint_fit = _mapping(config.get("joint_fit"), "joint_fit")
    morphologies = joint_fit.get("morphologies")
    associations = joint_fit.get("associations")
    if not isinstance(morphologies, list) or not morphologies:
        raise ValueError("joint_fit.morphologies must be a non-empty list")
    if not isinstance(associations, list) or not associations:
        raise ValueError("joint_fit.associations must be a non-empty list")
    names = []
    for hypothesis in associations:
        name = _mapping(hypothesis, "association").get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("association name must be non-empty")
        names.append(name)
    if len(names) != len(set(names)):
        raise ValueError("association names must be unique")
    return {f"{morphology}:{name}" for morphology in morphologies for name in names}


def _resolution(config: dict[str, Any], label: str) -> dict[str, Any]:
    joint_fit = _mapping(config.get("joint_fit"), f"{label}.joint_fit")
    return _mapping(joint_fit.get("resolution"), f"{label}.joint_fit.resolution")


def _factor(
    resolution: dict[str, Any],
    instrument: str,
    axis: str,
    label: str,
) -> int:
    key = f"{instrument}_fit_{axis}_average_factor"
    value = resolution.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{label}.{key} must be a positive integer")
    return value


def _validate_fit_identity(
    fit: dict[str, Any],
    config: dict[str, Any],
    label: str,
) -> None:
    if fit.get("event") != config.get("event"):
        raise ValueError(f"{label} fit and config name different events")
    binding = _require_sha256(
        config.get("event_binding_sha256"),
        f"{label} config event binding",
    )
    if fit.get("event_binding_sha256") != binding:
        raise ValueError(f"{label} fit and config event bindings differ")
    if fit.get("reference_frequency_mhz") != 400.0:
        raise ValueError(f"{label} fit does not use geocentric 400 MHz arrival times")
    if fit.get("status") != ACCEPTED_STATUS:
        raise ValueError(f"{label} fit is not provisional accepted")


def _provenance_code_identity(fit: dict[str, Any], label: str) -> dict[str, str]:
    code = _mapping(
        fit.get("provenance_code_sha256"),
        f"{label}.provenance_code_sha256",
    )
    if set(code) != CODE_KEYS:
        raise ValueError(f"{label} fit provenance code set differs")
    return {
        key: _require_sha256(value, f"{label} code hash {key}")
        for key, value in code.items()
    }


def _model_adequacy(
    fit: dict[str, Any],
    config: dict[str, Any],
    label: str,
) -> dict[str, float | bool]:
    diagnostics = _mapping(fit.get("diagnostics"), f"{label}.diagnostics")
    if diagnostics.get("model_adequate") is not True:
        raise ValueError(f"{label} fit failed model adequacy")
    acceptance = _mapping(
        _mapping(config.get("joint_fit"), f"{label}.joint_fit").get("acceptance"),
        f"{label}.joint_fit.acceptance",
    )
    residual = float(
        _finite_number(
            diagnostics.get("maximum_reduced_residual_power"),
            f"{label} maximum reduced residual power",
        )
    )
    correlation = abs(
        float(
            _finite_number(
                diagnostics.get("maximum_structured_residual_correlation"),
                f"{label} maximum structured residual correlation",
            )
        )
    )
    residual_limit = float(
        _finite_number(
            acceptance.get("maximum_reduced_residual_power"),
            f"{label} residual-power limit",
        )
    )
    correlation_limit = float(
        _finite_number(
            acceptance.get("maximum_structured_residual_correlation"),
            f"{label} structured-correlation limit",
        )
    )
    if residual > residual_limit or correlation > correlation_limit:
        raise ValueError(f"{label} fit failed model adequacy thresholds")
    return {
        "passed": True,
        "maximum_reduced_residual_power": residual,
        "maximum_structured_residual_correlation": correlation,
    }


def _receipt_source_identity(receipt: dict[str, Any], label: str) -> dict[str, Any]:
    source = dict(_mapping(receipt.get("source"), f"{label}.source"))
    source.pop("path", None)
    for key, value in source.items():
        if key.endswith("sha256"):
            _require_sha256(value, f"{label}.source.{key}")
    _require_sha256(source.get("sha256"), f"{label}.source.sha256")
    return source


def _validate_receipt(
    receipt: dict[str, Any],
    *,
    instrument: str,
    factor: int,
    config: dict[str, Any],
    fit: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    if receipt.get("schema_version") != 1:
        raise ValueError(f"{label} receipt schema is unsupported")
    if receipt.get("status") != "candidate_fit_grid_pending_resolution_review":
        raise ValueError(f"{label} receipt status is invalid")
    if receipt.get("instrument") != instrument:
        raise ValueError(f"{label} receipt instrument differs")
    settings = _mapping(receipt.get("settings"), f"{label}.settings")
    if settings.get("frequency_bin_factor") != factor:
        raise ValueError(f"{label} receipt frequency factor differs from config")
    if settings.get("time_bin_factor") != 1:
        raise ValueError(f"{label} receipt time factor must be one")
    if settings.get("minimum_valid_fraction") != 1.0:
        raise ValueError(f"{label} receipt does not require complete support")

    output = _mapping(receipt.get("output"), f"{label}.output")
    output_sha256 = _require_sha256(
        output.get("sha256"),
        f"{label}.output.sha256",
    )
    resolution = _resolution(config, label)
    configured_sha256 = _require_sha256(
        resolution.get(f"{instrument}_fit_observation_sha256"),
        f"{label} configured fit observation hash",
    )
    fit_inputs = _mapping(fit.get("fit_inputs"), f"{label}.fit_inputs")
    fit_sha256 = _require_sha256(
        fit_inputs.get(f"{instrument}_observation"),
        f"{label} fit observation hash",
    )
    if output_sha256 != configured_sha256 or output_sha256 != fit_sha256:
        raise ValueError(f"{label} fit observation hash differs from receipt or config")
    return {
        "source": _receipt_source_identity(receipt, label),
        "settings_without_frequency_factor": {
            key: value for key, value in settings.items() if key != "frequency_bin_factor"
        },
        "output_sha256": output_sha256,
    }


def _posterior_comparison(
    coarse_value: Any,
    fine_value: Any,
    *,
    label: str,
    absolute_tolerance: float | None,
    sigma_multiple: float,
    interval_width_ratio: tuple[float, float],
) -> dict[str, Any]:
    coarse = _summary(coarse_value, f"coarse {label}")
    fine = _summary(fine_value, f"fine {label}")
    coarse_width = coarse["upper"] - coarse["lower"]
    fine_width = fine["upper"] - fine["lower"]
    coarse_sigma = coarse_width / 2.0
    fine_sigma = fine_width / 2.0
    combined_sigma = math.hypot(float(coarse_sigma), float(fine_sigma))
    if not math.isfinite(combined_sigma) or combined_sigma <= 0:
        raise ValueError(f"{label} combined posterior sigma is invalid")
    delta = abs(coarse["median"] - fine["median"])
    ratio = float(coarse_width / fine_width)
    sigma_passed = float(delta) <= sigma_multiple * combined_sigma
    width_passed = interval_width_ratio[0] <= ratio <= interval_width_ratio[1]
    absolute_passed = True if absolute_tolerance is None else float(delta) <= absolute_tolerance
    return {
        "absolute_median_delta": delta,
        "combined_68_percent_sigma": combined_sigma,
        "delta_over_combined_sigma": float(delta) / combined_sigma,
        "interval_width_ratio": ratio,
        "absolute_limit_passed": absolute_passed,
        "sigma_limit_passed": sigma_passed,
        "interval_width_passed": width_passed,
        "passed": absolute_passed and sigma_passed and width_passed,
    }


def _convergence_thresholds(config: dict[str, Any]) -> dict[str, Any]:
    acceptance = _mapping(
        _mapping(config.get("joint_fit"), "joint_fit").get("acceptance"),
        "joint_fit.acceptance",
    )
    ratio = acceptance.get("resolution_interval_width_ratio")
    if not isinstance(ratio, list) or len(ratio) != 2:
        raise ValueError("resolution interval-width ratio must contain two values")
    thresholds = {
        "dm_absolute_pc_cm3": float(
            _finite_number(
                acceptance.get("maximum_resolution_dm_shift_pc_cm3"),
                "maximum resolution DM shift",
            )
        ),
        "dm_sigma_multiple": float(
            _finite_number(
                acceptance.get("maximum_resolution_dm_shift_combined_sigma"),
                "maximum resolution DM shift in combined sigma",
            )
        ),
        "toa_sigma_multiple": float(
            _finite_number(
                acceptance.get("maximum_resolution_toa_shift_combined_sigma"),
                "maximum resolution arrival-time shift in combined sigma",
            )
        ),
        "interval_width_ratio": tuple(
            float(_finite_number(value, "resolution interval-width ratio"))
            for value in ratio
        ),
        "run_weight_l1": float(
            _finite_number(
                acceptance.get("maximum_resolution_model_weight_l1_difference"),
                "maximum resolution model-weight difference",
            )
        ),
    }
    if (
        thresholds["dm_absolute_pc_cm3"] <= 0
        or thresholds["dm_sigma_multiple"] <= 0
        or thresholds["toa_sigma_multiple"] <= 0
        or thresholds["run_weight_l1"] <= 0
        or not 0 < thresholds["interval_width_ratio"][0] <= 1
        or thresholds["interval_width_ratio"][1] < 1
    ):
        raise ValueError("resolution convergence thresholds are invalid")
    return thresholds


def _run_weights(
    fit: dict[str, Any],
    expected_names: set[str],
    label: str,
) -> dict[str, float]:
    diagnostics = _mapping(fit.get("diagnostics"), f"{label}.diagnostics")
    values = _mapping(diagnostics.get("run_weights"), f"{label}.run_weights")
    if set(values) != expected_names:
        raise ValueError(f"{label} association and morphology run names differ")
    output = {}
    for name, value in values.items():
        weight = float(_finite_number(value, f"{label} run weight {name}"))
        if weight < 0:
            raise ValueError(f"{label} run weights must be non-negative")
        output[name] = weight
    if not math.isclose(math.fsum(output.values()), 1.0, rel_tol=0.0, abs_tol=1.0e-8):
        raise ValueError(f"{label} run weights must sum to one")
    return output


def verify(
    *,
    coarse_fit_result_path: Path,
    fine_fit_result_path: Path,
    coarse_config_path: Path,
    fine_config_path: Path,
    coarse_receipt_paths: dict[str, Path],
    fine_receipt_paths: dict[str, Path],
) -> dict[str, Any]:
    """Compare a reviewed frequency factor with the factor-halved fit."""

    paths = {
        "coarse_fit_result": Path(coarse_fit_result_path),
        "fine_fit_result": Path(fine_fit_result_path),
        "coarse_config": Path(coarse_config_path),
        "fine_config": Path(fine_config_path),
        **{
            f"coarse_{instrument}_receipt": Path(coarse_receipt_paths[instrument])
            for instrument in INSTRUMENTS
        },
        **{
            f"fine_{instrument}_receipt": Path(fine_receipt_paths[instrument])
            for instrument in INSTRUMENTS
        },
    }
    input_hashes = {name: sha256_file(path) for name, path in paths.items()}
    coarse_fit = _load_json(paths["coarse_fit_result"], "coarse fit result")
    fine_fit = _load_json(paths["fine_fit_result"], "fine fit result")
    coarse_config = _load_json(paths["coarse_config"], "coarse config")
    fine_config = _load_json(paths["fine_config"], "fine config")
    receipts = {
        run: {
            instrument: _load_json(
                paths[f"{run}_{instrument}_receipt"],
                f"{run} {instrument} receipt",
            )
            for instrument in INSTRUMENTS
        }
        for run in ("coarse", "fine")
    }

    if coarse_config.get("event") != fine_config.get("event"):
        raise ValueError("configs name different events")
    if coarse_config.get("input_sha256") != fine_config.get("input_sha256"):
        raise ValueError("coarse and fine raw input hashes differ")
    raw_hashes = _mapping(coarse_config.get("input_sha256"), "input_sha256")
    for key, value in raw_hashes.items():
        _require_sha256(value, f"input_sha256.{key}")
    if _model_identity(coarse_config) != _model_identity(fine_config):
        raise ValueError("coarse and fine model, priors, or sampler differ")
    thresholds = _convergence_thresholds(coarse_config)
    if _matched_latent_ids(coarse_config) != _matched_latent_ids(fine_config):
        raise ValueError("coarse and fine matched components differ")

    _validate_fit_identity(coarse_fit, coarse_config, "coarse")
    _validate_fit_identity(fine_fit, fine_config, "fine")
    code_identity = _provenance_code_identity(coarse_fit, "coarse")
    if _provenance_code_identity(fine_fit, "fine") != code_identity:
        raise ValueError("coarse and fine fits used different scientific code")
    coarse_inputs = _mapping(coarse_fit.get("fit_inputs"), "coarse.fit_inputs")
    fine_inputs = _mapping(fine_fit.get("fit_inputs"), "fine.fit_inputs")
    if coarse_inputs.get("geometry_constraint") != fine_inputs.get("geometry_constraint"):
        raise ValueError("coarse and fine geometry inputs differ")
    _require_sha256(
        coarse_inputs.get("geometry_constraint"),
        "geometry constraint hash",
    )
    adequacy = {
        "coarse": _model_adequacy(coarse_fit, coarse_config, "coarse"),
        "fine": _model_adequacy(fine_fit, fine_config, "fine"),
    }

    factors: dict[str, dict[str, int]] = {"coarse": {}, "fine": {}}
    for run, config in (("coarse", coarse_config), ("fine", fine_config)):
        resolution = _resolution(config, run)
        for instrument in INSTRUMENTS:
            factors[run][instrument] = _factor(
                resolution,
                instrument,
                "frequency",
                run,
            )
            if _factor(resolution, instrument, "time", run) != 1:
                raise ValueError("coarse and fine time averaging factors must both be one")
    for instrument in INSTRUMENTS:
        coarse_factor = factors["coarse"][instrument]
        fine_factor = factors["fine"][instrument]
        if coarse_factor == 1:
            if fine_factor != 1:
                raise ValueError("unit coarse factor requires a unit fine factor")
        elif coarse_factor != 2 * fine_factor:
            raise ValueError("coarse frequency factor must be exactly twice the fine factor")

    receipt_identities: dict[str, dict[str, dict[str, Any]]] = {
        "coarse": {},
        "fine": {},
    }
    for run, fit, config in (
        ("coarse", coarse_fit, coarse_config),
        ("fine", fine_fit, fine_config),
    ):
        for instrument in INSTRUMENTS:
            receipt_identities[run][instrument] = _validate_receipt(
                receipts[run][instrument],
                instrument=instrument,
                factor=factors[run][instrument],
                config=config,
                fit=fit,
                label=f"{run} {instrument}",
            )
    for instrument in INSTRUMENTS:
        coarse_receipt = receipt_identities["coarse"][instrument]
        fine_receipt = receipt_identities["fine"][instrument]
        if coarse_receipt["source"] != fine_receipt["source"]:
            raise ValueError(f"{instrument} coarse and fine receipt sources differ")
        if (
            coarse_receipt["settings_without_frequency_factor"]
            != fine_receipt["settings_without_frequency_factor"]
        ):
            raise ValueError(
                f"{instrument} materialization settings other than frequency factor differ"
            )

    failures: list[str] = []
    dm = _posterior_comparison(
        coarse_fit.get("shared_absolute_dm_pc_cm3"),
        fine_fit.get("shared_absolute_dm_pc_cm3"),
        label="shared dispersion measure",
        absolute_tolerance=thresholds["dm_absolute_pc_cm3"],
        sigma_multiple=thresholds["dm_sigma_multiple"],
        interval_width_ratio=thresholds["interval_width_ratio"],
    )
    dm["absolute_median_delta_pc_cm3"] = dm.pop("absolute_median_delta")
    dm["combined_68_percent_sigma_pc_cm3"] = dm.pop("combined_68_percent_sigma")
    if not dm["passed"]:
        failures.append("shared_dispersion_measure")

    latent_ids = _matched_latent_ids(coarse_config)
    coarse_toas = _mapping(
        coarse_fit.get("geocentric_unscattered_toa_unix_ns"),
        "coarse geocentric arrival times",
    )
    fine_toas = _mapping(
        fine_fit.get("geocentric_unscattered_toa_unix_ns"),
        "fine geocentric arrival times",
    )
    if set(coarse_toas) != set(latent_ids) or set(fine_toas) != set(latent_ids):
        raise ValueError("fit results do not contain exactly the matched geocentric arrival times")
    toas = {}
    for latent_id in latent_ids:
        comparison = _posterior_comparison(
            coarse_toas[latent_id],
            fine_toas[latent_id],
            label=f"geocentric arrival time {latent_id}",
            absolute_tolerance=None,
            sigma_multiple=thresholds["toa_sigma_multiple"],
            interval_width_ratio=thresholds["interval_width_ratio"],
        )
        comparison["absolute_median_delta_ns"] = comparison.pop("absolute_median_delta")
        comparison["combined_68_percent_sigma_ns"] = comparison.pop("combined_68_percent_sigma")
        toas[latent_id] = comparison
        if not comparison["passed"]:
            failures.append(f"geocentric_toa:{latent_id}")

    expected_runs = _expected_run_names(coarse_config)
    coarse_weights = _run_weights(coarse_fit, expected_runs, "coarse")
    fine_weights = _run_weights(fine_fit, expected_runs, "fine")
    run_weight_l1 = math.fsum(
        abs(coarse_weights[name] - fine_weights[name]) for name in sorted(expected_runs)
    )
    if run_weight_l1 > thresholds["run_weight_l1"]:
        failures.append("association_morphology_run_weights")

    passed = not failures
    return {
        "schema_version": 1,
        "status": "passed" if passed else "failed",
        "passed": passed,
        "event": coarse_config["event"],
        "input_sha256": input_hashes,
        "provenance_code_sha256": code_identity,
        "frequency_average_factors": factors,
        "thresholds": {
            "dm_absolute_pc_cm3": thresholds["dm_absolute_pc_cm3"],
            "dm_combined_sigma_multiple": thresholds["dm_sigma_multiple"],
            "toa_combined_sigma_multiple": thresholds["toa_sigma_multiple"],
            "interval_width_ratio": list(thresholds["interval_width_ratio"]),
            "run_weight_l1": thresholds["run_weight_l1"],
        },
        "model_adequacy": adequacy,
        "dm": dm,
        "toas": toas,
        "run_weight_l1": run_weight_l1,
        "failures": failures,
    }


def _input_paths(args: argparse.Namespace) -> dict[str, Path]:
    return {
        "coarse_fit_result": args.coarse_fit_result,
        "fine_fit_result": args.fine_fit_result,
        "coarse_config": args.coarse_config,
        "fine_config": args.fine_config,
        "coarse_chime_receipt": args.coarse_chime_receipt,
        "coarse_dsa_receipt": args.coarse_dsa_receipt,
        "fine_chime_receipt": args.fine_chime_receipt,
        "fine_dsa_receipt": args.fine_dsa_receipt,
    }


def _failure_report(
    paths: dict[str, Path],
    error: Exception,
) -> dict[str, Any]:
    hashes = {}
    for name, path in paths.items():
        try:
            hashes[name] = sha256_file(path)
        except OSError:
            hashes[name] = None
    return {
        "schema_version": 1,
        "status": "failed",
        "passed": False,
        "input_sha256": hashes,
        "error": str(error),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coarse-fit-result", type=Path, required=True)
    parser.add_argument("--fine-fit-result", type=Path, required=True)
    parser.add_argument("--coarse-config", type=Path, required=True)
    parser.add_argument("--fine-config", type=Path, required=True)
    parser.add_argument("--coarse-chime-receipt", type=Path, required=True)
    parser.add_argument("--coarse-dsa-receipt", type=Path, required=True)
    parser.add_argument("--fine-chime-receipt", type=Path, required=True)
    parser.add_argument("--fine-dsa-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    paths = _input_paths(args)
    try:
        if args.output.suffix.lower() != ".json":
            raise ValueError("convergence output must use the .json extension")
        report = verify(
            coarse_fit_result_path=args.coarse_fit_result,
            fine_fit_result_path=args.fine_fit_result,
            coarse_config_path=args.coarse_config,
            fine_config_path=args.fine_config,
            coarse_receipt_paths={
                "chime": args.coarse_chime_receipt,
                "dsa": args.coarse_dsa_receipt,
            },
            fine_receipt_paths={
                "chime": args.fine_chime_receipt,
                "dsa": args.fine_dsa_receipt,
            },
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        report = _failure_report(paths, error)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"], "output": str(args.output)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
