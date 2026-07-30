#!/usr/bin/env python3
"""Configuration and receipts for the one-event absolute-DM workflow."""

from __future__ import annotations

import hashlib
import json
import math
import re
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
REFERENCE_FREQUENCY_MHZ = 400.0
UPCHANNEL_FACTOR = 16
EVENT_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

STAGES = (
    "preflight",
    "dsa_audit",
    "chime_products",
    "dsa_products",
    "geometry_constraint",
    "joint_fit",
    "chime_oracle",
    "dsa_oracle",
    "oracle_check",
    "packet",
    "manifests",
)


def canonical_json(value: Any) -> str:
    """Return deterministic JSON used by binding and receipt hashes."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def event_binding_payload(config: dict[str, Any]) -> dict[str, Any]:
    """Bind the complete canonical config except the binding's own value."""

    payload = deepcopy(config)
    payload.pop("event_binding_sha256", None)
    return payload


def event_binding_sha256(config: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(event_binding_payload(config)).encode("utf-8")).hexdigest()


def validate_timing_uncertainties(geometry: dict[str, Any]) -> None:
    """Validate the complete owner-adopted timing prior before data access."""

    uncertainty_fields = ("site_delay_sigma_s", "clock_sigma_s")
    provenance_field = "timing_uncertainty_provenance"
    missing = [
        field for field in (*uncertainty_fields, provenance_field) if field not in geometry
    ]
    if missing:
        raise ValueError(f"geometry lacks reviewed timing fields: {missing}")
    for field in uncertainty_fields:
        values = geometry[field]
        if (
            not isinstance(values, dict)
            or set(values) != {"chime", "dsa"}
            or any(
                not math.isfinite(float(values[instrument]))
                or float(values[instrument]) <= 0
                for instrument in ("chime", "dsa")
            )
        ):
            raise ValueError(f"{field} needs positive finite CHIME and DSA values")

    provenance = geometry[provenance_field]
    required_provenance = (
        "status",
        "inter_site_clock_sigma_s",
        "clock_allocation",
        "clock_basis",
        "site_delay_basis",
        "absolute_utc_calibration_status",
        "owner_adoption_date",
    )
    if not isinstance(provenance, dict):
        raise ValueError("timing uncertainty provenance must be an object")
    extra_provenance = sorted(set(provenance) - set(required_provenance))
    if extra_provenance:
        raise ValueError(
            f"timing uncertainty provenance has unsupported fields: {extra_provenance}"
        )
    missing_provenance = [
        field for field in required_provenance if field not in provenance
    ]
    if missing_provenance:
        raise ValueError(
            f"timing uncertainty provenance lacks fields: {missing_provenance}"
        )
    if provenance["status"] != "owner_adopted_provisional_bounds":
        raise ValueError("timing uncertainties need explicit provisional owner adoption")
    if provenance["clock_allocation"] != "equal_independent_station_terms":
        raise ValueError("clock uncertainty allocation must use independent station terms")
    if provenance["absolute_utc_calibration_status"] != "not_independently_measured":
        raise ValueError("absolute UTC calibration must remain explicitly unmeasured")
    for field in ("clock_basis", "site_delay_basis", "owner_adoption_date"):
        if not isinstance(provenance[field], str) or not provenance[field].strip():
            raise ValueError(f"timing uncertainty provenance needs non-empty {field}")
    adoption_date = provenance["owner_adoption_date"]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", adoption_date) is None:
        raise ValueError("owner adoption date must use YYYY-MM-DD")
    try:
        date.fromisoformat(adoption_date)
    except ValueError as exc:
        raise ValueError("owner adoption date is not a valid date") from exc

    inter_site_clock_sigma_s = float(provenance["inter_site_clock_sigma_s"])
    if not math.isfinite(inter_site_clock_sigma_s) or inter_site_clock_sigma_s <= 0:
        raise ValueError("inter-site clock uncertainty must be positive and finite")
    allocated_clock_sigma_s = math.hypot(
        float(geometry["clock_sigma_s"]["chime"]),
        float(geometry["clock_sigma_s"]["dsa"]),
    )
    if not math.isclose(
        float(geometry["clock_sigma_s"]["chime"]),
        float(geometry["clock_sigma_s"]["dsa"]),
        rel_tol=1.0e-12,
        abs_tol=0.0,
    ):
        raise ValueError("clock uncertainty allocation must be equal between stations")
    if not math.isclose(
        allocated_clock_sigma_s,
        inter_site_clock_sigma_s,
        rel_tol=1.0e-12,
        abs_tol=0.0,
    ):
        raise ValueError(
            "station clock terms do not reproduce the adopted inter-site uncertainty"
        )


def _require_keys(mapping: dict[str, Any], keys: tuple[str, ...], label: str) -> None:
    missing = [key for key in keys if key not in mapping]
    if missing:
        raise ValueError(f"{label}: missing required keys {missing}")


def _require_sha256(value: Any, label: str) -> None:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{label}: expected lowercase SHA-256")


def _path_mentions_event(value: str, event: str) -> bool:
    tokens = re.split(r"[^a-z0-9]+", value.lower())
    return event in tokens


def validate_config(
    config: dict[str, Any],
    *,
    require_execution_authorized: bool = False,
) -> dict[str, Any]:
    """Fail closed on incomplete or cross-event configuration."""

    if not isinstance(config, dict):
        raise ValueError("configuration must be a JSON object")
    _require_keys(
        config,
        (
            "schema_version",
            "event",
            "result_status",
            "identity",
            "paths",
            "input_sha256",
            "chime",
            "dsa",
            "geometry",
            "workflow",
            "event_binding_sha256",
        ),
        "config",
    )
    if config["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    event = config["event"]
    if not isinstance(event, str) or EVENT_RE.fullmatch(event) is None:
        raise ValueError("event must be a lowercase filesystem-safe slug")
    if not isinstance(config["result_status"], str) or not config["result_status"]:
        raise ValueError("result_status must be a non-empty string")

    identity = config["identity"]
    _require_keys(
        identity,
        (
            "reviewed_event",
            "input_basenames",
            "output_root_basename",
            "disallowed_event_tokens",
        ),
        "identity",
    )
    if identity["reviewed_event"] != event:
        raise ValueError("identity.reviewed_event must exactly match event")

    is_regression_fixture = (
        isinstance(config.get("workflow"), dict)
        and config["workflow"].get("regression_fixture") is True
    )
    paths = config["paths"]
    input_keys = (
        "raw_chime_h5",
        "accepted_chime_reference",
        "raw_dsa_filterbank",
        "accepted_dsa_reference",
        "timing_results",
        "trigger_recovery",
        "reproduction_fixture",
    )
    if not is_regression_fixture:
        input_keys += ("dsa_state_reconstruction",)
        if (
            config["dsa"].get("input_dm_bound_source")
            == "calibrated_v3_integer_interval_intersection"
        ):
            input_keys += ("dsa_state_calibration",)
    _require_keys(
        paths,
        input_keys + ("output_root",),
        "paths",
    )
    for key, value in paths.items():
        if not isinstance(value, str) or not value:
            raise ValueError(f"paths.{key}: expected non-empty path")
    basenames = identity["input_basenames"]
    _require_keys(basenames, input_keys, "identity.input_basenames")
    for key in input_keys:
        if Path(paths[key]).name != basenames[key]:
            raise ValueError(f"paths.{key}: basename differs from reviewed identity")
    if Path(paths["output_root"]).name != identity["output_root_basename"]:
        raise ValueError("paths.output_root: basename differs from reviewed identity")
    disallowed = identity["disallowed_event_tokens"]
    if (
        not isinstance(disallowed, list)
        or disallowed != sorted(set(disallowed))
        or event in disallowed
        or any(EVENT_RE.fullmatch(token) is None for token in disallowed)
    ):
        raise ValueError("identity.disallowed_event_tokens must be sorted unique slugs")
    identity_paths = [paths[key] for key in input_keys] + [paths["output_root"]]
    for value in identity_paths:
        tokens = set(re.split(r"[^a-z0-9]+", value.lower()))
        conflicts = sorted(tokens.intersection(disallowed))
        if conflicts:
            raise ValueError(f"cross-event path token rejected for {event!r}: {conflicts}")
    for key in (
        "raw_chime_h5",
        "accepted_chime_reference",
        "raw_dsa_filterbank",
        "accepted_dsa_reference",
        "output_root",
    ):
        if not _path_mentions_event(paths[key], event):
            raise ValueError(f"paths.{key}: does not bind to event {event!r}")

    hashes = config["input_sha256"]
    _require_keys(
        hashes,
        input_keys,
        "input_sha256",
    )
    for key, value in hashes.items():
        _require_sha256(value, f"input_sha256.{key}")

    chime = config["chime"]
    _require_keys(
        chime,
        (
            "accepted_reference_dm_pc_cm3",
            "anchor_dm_pc_cm3",
            "reference_pulse_fwhm_s",
            "upchannel_factor",
            "window_s",
            "grid",
            "gates",
            "accepted_support",
        ),
        "chime",
    )
    if chime["upchannel_factor"] != UPCHANNEL_FACTOR:
        raise ValueError(f"chime.upchannel_factor must remain {UPCHANNEL_FACTOR}")
    if float(chime["window_s"]) <= 0:
        raise ValueError("chime.window_s must be positive")
    support = chime["accepted_support"]
    _require_keys(
        support,
        (
            "full_grid_rows",
            "all_nan_count",
            "finite_flat_count",
            "live_count",
            "h5_present_count",
            "h5_missing_count",
            "h5_present_accepted_dead_ids",
            "manual_bad_channel_ids",
            "historical_row_sum_replay",
        ),
        "chime.accepted_support",
    )
    full_grid = int(support["full_grid_rows"])
    all_nan = int(support["all_nan_count"])
    finite_flat = int(support["finite_flat_count"])
    live = int(support["live_count"])
    present = int(support["h5_present_count"])
    missing = int(support["h5_missing_count"])
    present_dead = support["h5_present_accepted_dead_ids"]
    if all_nan + finite_flat + live != full_grid:
        raise ValueError("CHIME accepted support does not partition the full grid")
    if present + missing != full_grid:
        raise ValueError("CHIME H5 present/missing counts do not partition the full grid")
    if (
        not isinstance(present_dead, list)
        or present_dead != sorted(set(present_dead))
        or any(not isinstance(row, int) or row < 0 or row >= full_grid for row in present_dead)
    ):
        raise ValueError("CHIME H5-present accepted-dead IDs must be sorted unique IDs")
    if len(present_dead) + live != present:
        raise ValueError("CHIME present-dead plus live rows does not equal H5 present rows")
    if support["manual_bad_channel_ids"] != []:
        raise ValueError("manual CHIME masks are not authorized by this workflow")
    if support["historical_row_sum_replay"] is not False:
        raise ValueError("historical CHIME row-sum replay must remain disabled")

    grid = chime["grid"]
    _require_keys(
        grid,
        (
            "coarse_half_width_pc_cm3",
            "coarse_step_pc_cm3",
            "fine_half_width_pc_cm3",
            "fine_step_pc_cm3",
        ),
        "chime.grid",
    )
    if any(float(grid[key]) <= 0 for key in grid):
        raise ValueError("CHIME grid widths and steps must be positive")

    gates = chime["gates"]
    _require_keys(
        gates,
        (
            "oracle_half_width_pc_cm3",
            "oracle_material_threshold_pc_cm3",
            "oracle_normalised_curve_max_abs_difference",
            "oracle_center_score_ratio_tolerance",
            "smearing_max_fraction_of_upchannel_sample",
            "smearing_max_fraction_of_reference_pulse_fwhm",
            "injection_max_error_pc_cm3",
        ),
        "chime.gates",
    )
    if any(float(value) <= 0 for value in gates.values()):
        raise ValueError("CHIME gate thresholds must be positive")

    dsa = config["dsa"]
    _require_keys(
        dsa,
        (
            "accepted_reference_dm_pc_cm3",
            "raw_crop_start_sample",
            "crop_samples",
            "padding_samples",
            "audit_sample_rows",
            "accepted_support",
            "gates",
        ),
        "dsa",
    )
    if int(dsa["raw_crop_start_sample"]) < 0:
        raise ValueError("dsa.raw_crop_start_sample must be non-negative")
    if int(dsa["crop_samples"]) <= 0 or int(dsa["padding_samples"]) <= 0:
        raise ValueError("DSA crop and padding samples must be positive")
    if not is_regression_fixture:
        _require_keys(
            dsa,
            (
                "input_dm_pc_cm3",
                "input_dm_method",
                "input_dm_bound_source",
                "input_dm_half_width_pc_cm3",
                "reference_minus_raw_dm_pc_cm3",
                "reference_minus_raw_dm_interval_pc_cm3",
                "input_dm_reconstruction_sha256",
                "raw_reference_frequency_crop_start_sample",
                "native_sample_time_s",
            ),
            "dsa",
        )
        if dsa["input_dm_method"] not in {
            "inferred_raw_reference_row_timing",
            "accepted_product_dm_nominal_with_residual_bound",
        }:
            raise ValueError("dsa.input_dm_method is invalid")
        if dsa["input_dm_bound_source"] not in {
            "v3_inferred_value",
            "v3_conservative_residual_bound",
            "calibrated_v3_integer_interval_intersection",
        }:
            raise ValueError("dsa.input_dm_bound_source is invalid")
        interval = dsa["reference_minus_raw_dm_interval_pc_cm3"]
        if (
            not isinstance(interval, list)
            or len(interval) != 2
            or any(not isinstance(value, int | float) for value in interval)
            or float(interval[0]) > float(interval[1])
        ):
            raise ValueError("DSA residual-DM interval must be ordered endpoints")
        if float(dsa["input_dm_half_width_pc_cm3"]) <= 0:
            raise ValueError("dsa.input_dm_half_width_pc_cm3 must be positive")
        if float(dsa["raw_reference_frequency_crop_start_sample"]) < 0:
            raise ValueError("dsa.raw_reference_frequency_crop_start_sample must be non-negative")
        if float(dsa["native_sample_time_s"]) <= 0:
            raise ValueError("dsa.native_sample_time_s must be positive")
        _require_sha256(
            dsa["input_dm_reconstruction_sha256"],
            "dsa.input_dm_reconstruction_sha256",
        )
        if dsa["input_dm_reconstruction_sha256"] != hashes["dsa_state_reconstruction"]:
            raise ValueError("DSA reconstruction hash differs from reviewed input")
        if dsa["input_dm_bound_source"] == "calibrated_v3_integer_interval_intersection":
            _require_keys(
                dsa,
                ("input_dm_calibration_sha256",),
                "dsa",
            )
            _require_sha256(
                dsa["input_dm_calibration_sha256"],
                "dsa.input_dm_calibration_sha256",
            )
            if dsa["input_dm_calibration_sha256"] != hashes["dsa_state_calibration"]:
                raise ValueError("DSA calibration hash differs from reviewed input")
            if dsa["input_dm_method"] != "accepted_product_dm_nominal_with_residual_bound":
                raise ValueError("calibrated DSA interval is bound-only")
        accepted_dm = float(dsa["accepted_reference_dm_pc_cm3"])
        residual_dm = float(dsa["reference_minus_raw_dm_pc_cm3"])
        nominal_dm = float(dsa["input_dm_pc_cm3"])
        if dsa["input_dm_method"] == "inferred_raw_reference_row_timing":
            expected_nominal = accepted_dm - residual_dm
        else:
            expected_nominal = accepted_dm
        if abs(nominal_dm - expected_nominal) > 1.0e-12:
            raise ValueError("DSA nominal input DM contradicts its method")
    dsa_support = dsa["accepted_support"]
    _require_keys(
        dsa_support,
        ("full_grid_rows", "live_count", "dead_count", "manual_bad_channel_ids"),
        "dsa.accepted_support",
    )
    if int(dsa_support["live_count"]) + int(dsa_support["dead_count"]) != int(
        dsa_support["full_grid_rows"]
    ):
        raise ValueError("DSA accepted support does not partition the full grid")
    if dsa_support["manual_bad_channel_ids"] != []:
        raise ValueError("manual DSA masks are not authorized by this workflow")
    dsa_gates = dsa["gates"]
    _require_keys(
        dsa_gates,
        (
            "direct_correlation_min",
            "reversed_correlation_max",
            "edge_fail_closed",
        ),
        "dsa.gates",
    )
    if dsa_gates["edge_fail_closed"] is not True:
        raise ValueError("DSA edge handling must fail closed")
    if not 0.0 <= float(dsa_gates["direct_correlation_min"]) <= 1.0:
        raise ValueError("DSA direct correlation gate must lie in [0, 1]")
    if not 0.0 <= float(dsa_gates["reversed_correlation_max"]) <= 1.0:
        raise ValueError("DSA reversed correlation gate must lie in [0, 1]")
    if is_regression_fixture:
        _require_keys(
            dsa_gates,
            ("reference_minus_raw_dm_abs_max_pc_cm3",),
            "dsa.gates",
        )
        if float(dsa_gates["reference_minus_raw_dm_abs_max_pc_cm3"]) <= 0:
            raise ValueError("DSA residual-DM gate must be positive")
    else:
        _require_keys(
            dsa_gates,
            (
                "input_dm_reference_timing_half_width_max_native_samples",
                "input_dm_aligned_profile_correlation_min",
                "gallery_alignment_must_be_robust",
            ),
            "dsa.gates",
        )
        if float(dsa_gates["input_dm_reference_timing_half_width_max_native_samples"]) <= 0:
            raise ValueError("DSA input-DM timing gate must be positive")
        if not 0.0 <= float(dsa_gates["input_dm_aligned_profile_correlation_min"]) <= 1.0:
            raise ValueError("DSA input-DM morphology gate must lie in [0, 1]")
        if dsa_gates["gallery_alignment_must_be_robust"] is not True:
            raise ValueError("DSA gallery alignment must fail closed")

    geometry = config["geometry"]
    _require_keys(
        geometry,
        (
            "geometry_dm_pc_cm3",
            "reference_frequency_mhz",
            "dsa_native_frequency_mhz",
        ),
        "geometry",
    )
    if float(geometry["reference_frequency_mhz"]) != REFERENCE_FREQUENCY_MHZ:
        raise ValueError(f"geometry.reference_frequency_mhz must remain {REFERENCE_FREQUENCY_MHZ}")

    joint_fit = config.get("joint_fit")
    if joint_fit is not None:
        _require_keys(
            joint_fit,
            (
                "status",
                "execution_authorized",
                "reference_frequency_mhz",
                "blockers",
                "geometry",
                "resolution",
            ),
            "joint_fit",
        )
        if float(joint_fit["reference_frequency_mhz"]) != REFERENCE_FREQUENCY_MHZ:
            raise ValueError("joint_fit reference frequency must remain 400 MHz")
        blockers = joint_fit["blockers"]
        if (
            not isinstance(blockers, list)
            or blockers != sorted(set(blockers))
            or any(not isinstance(value, str) or not value for value in blockers)
        ):
            raise ValueError("joint_fit blockers must be sorted unique strings")
        if joint_fit["status"] == "ready":
            if blockers or joint_fit["execution_authorized"] is not True:
                raise ValueError("ready joint fit must be unblocked and authorized")
            _require_keys(
                joint_fit,
                (
                    "components",
                    "associations",
                    "dm_bounds_pc_cm3",
                    "morphologies",
                    "scattering_tau_1ghz_bounds_s",
                    "scattering_alpha_bounds",
                    "gain_variance",
                    "sampler",
                    "acceptance",
                ),
                "joint_fit",
            )
            _require_keys(
                joint_fit["geometry"],
                (
                    "source_icrs",
                    "epoch_mjd_utc",
                    "site_delay_sigma_s",
                    "clock_sigma_s",
                    "timing_uncertainty_provenance",
                ),
                "joint_fit.geometry",
            )
            validate_timing_uncertainties(joint_fit["geometry"])
            if joint_fit["resolution"].get("crop_and_off_pulse_padding_locked") is not True:
                raise ValueError("joint fit requires locked crop and padding")
            _require_keys(
                joint_fit["resolution"],
                (
                    "chime_shape",
                    "dsa_shape",
                    "chime_sample_interval_s",
                    "dsa_sample_interval_s",
                    "chime_frequency_bin_factor",
                    "chime_time_bin_factor",
                    "dsa_frequency_bin_factor",
                    "dsa_time_bin_factor",
                    "chime_frequency_grid_sha256",
                    "dsa_frequency_grid_sha256",
                    "chime_valid_mask_sha256",
                    "dsa_valid_mask_sha256",
                    "chime_off_pulse_mask_sha256",
                    "dsa_off_pulse_mask_sha256",
                    "chime_time0_unix_ns",
                    "dsa_time0_unix_ns",
                ),
                "joint_fit.resolution",
            )
            for key in (
                "chime_frequency_grid_sha256",
                "dsa_frequency_grid_sha256",
                "chime_valid_mask_sha256",
                "dsa_valid_mask_sha256",
                "chime_off_pulse_mask_sha256",
                "dsa_off_pulse_mask_sha256",
            ):
                if SHA256_RE.fullmatch(joint_fit["resolution"][key]) is None:
                    raise ValueError(f"joint_fit.resolution.{key} must be SHA-256")
            _require_keys(
                joint_fit["sampler"],
                ("seed", "nlive", "dlogz"),
                "joint_fit.sampler",
            )
            _require_keys(
                joint_fit["acceptance"],
                (
                    "maximum_reduced_residual_power",
                    "maximum_structured_residual_correlation",
                    "posterior_edge_fraction",
                    "maximum_prior_edge_mass",
                ),
                "joint_fit.acceptance",
            )
        elif joint_fit["status"] != "blocked_pending_reviewed_inputs":
            raise ValueError("joint_fit status is invalid")
        elif not blockers or joint_fit["execution_authorized"] is not False:
            raise ValueError("blocked joint fit needs blockers and disabled execution")

    workflow = config["workflow"]
    _require_keys(
        workflow,
        (
            "execution_authorized",
            "regression_fixture",
            "chime_container_image",
            "container_data_mount",
            "stages",
        ),
        "workflow",
    )
    legacy_stages = [
        "preflight",
        "dsa_audit",
        "chime_hybrid",
        "dsa_products",
        "geometry",
        "packet",
        "manifests",
    ]
    allowed_stages = [list(STAGES)]
    if joint_fit is None:
        allowed_stages.append(legacy_stages)
    if workflow["stages"] not in allowed_stages:
        raise ValueError(f"workflow.stages must equal one of {allowed_stages}")
    if not isinstance(workflow["execution_authorized"], bool):
        raise ValueError("workflow.execution_authorized must be boolean")
    if (
        not isinstance(workflow["chime_container_image"], str)
        or "@sha256:" not in workflow["chime_container_image"]
    ):
        raise ValueError("workflow.chime_container_image must use a pinned digest")
    if (
        not isinstance(workflow["container_data_mount"], str)
        or not Path(workflow["container_data_mount"]).is_absolute()
    ):
        raise ValueError("workflow.container_data_mount must be an absolute path")
    review = config.get("review")
    if workflow["regression_fixture"] is not True and review is None:
        raise ValueError("non-regression configuration requires review state")
    if review is not None:
        _require_keys(
            review,
            ("configuration_status", "blockers", "dsa_input_state"),
            "review",
        )
        if review["configuration_status"] not in {"blocked", "reviewed"}:
            raise ValueError("review.configuration_status is invalid")
        blockers = review["blockers"]
        if (
            not isinstance(blockers, list)
            or blockers != sorted(set(blockers))
            or any(not isinstance(value, str) or not value for value in blockers)
        ):
            raise ValueError("review.blockers must be sorted unique non-empty strings")
        if review["configuration_status"] == "blocked" and not blockers:
            raise ValueError("blocked review state requires at least one blocker")
        if review["configuration_status"] == "reviewed" and blockers:
            raise ValueError("reviewed configuration cannot retain blockers")
        dsa_input_state = review["dsa_input_state"]
        _require_keys(
            dsa_input_state,
            (
                "authority",
                "reconstruction_sha256",
                "independent_uncertainty_review_status",
                "accepted_for_config_review",
                "conservative_bound_accepted_for_config_review",
                "material_nonzero_residual_proven",
                "inferred_raw_input_dm_pc_cm3",
                "conservative_uncertainty_pc_cm3",
            ),
            "review.dsa_input_state",
        )
        if dsa_input_state["authority"] != "raw_reference_row_timing_v3_value_or_bound":
            raise ValueError("review.dsa_input_state.authority is invalid")
        if dsa_input_state["independent_uncertainty_review_status"] not in {
            "pending",
            "passed",
        }:
            raise ValueError("review DSA uncertainty review status is invalid")
        _require_sha256(
            dsa_input_state["reconstruction_sha256"],
            "review.dsa_input_state.reconstruction_sha256",
        )
        if (
            not isinstance(
                dsa_input_state["accepted_for_config_review"],
                bool,
            )
            or not isinstance(
                dsa_input_state["conservative_bound_accepted_for_config_review"],
                bool,
            )
            or not isinstance(
                dsa_input_state["material_nonzero_residual_proven"],
                bool,
            )
        ):
            raise ValueError("review DSA decisions must be boolean")
        if float(dsa_input_state["conservative_uncertainty_pc_cm3"]) <= 0:
            raise ValueError("review DSA uncertainty must be positive")
        if not is_regression_fixture:
            if dsa_input_state["reconstruction_sha256"] != dsa["input_dm_reconstruction_sha256"]:
                raise ValueError("review and DSA reconstruction hashes differ")
            if dsa_input_state["material_nonzero_residual_proven"] != (
                dsa["input_dm_method"] == "inferred_raw_reference_row_timing"
            ):
                raise ValueError("review material flag contradicts DSA input method")
            residual_dm = float(dsa["reference_minus_raw_dm_pc_cm3"])
            inferred_raw_dm = float(dsa_input_state["inferred_raw_input_dm_pc_cm3"])
            accepted_dm = float(dsa["accepted_reference_dm_pc_cm3"])
            if abs(inferred_raw_dm - (accepted_dm - residual_dm)) > 1.0e-12:
                raise ValueError("review inferred raw DSA DM contradicts residual")
            if dsa["input_dm_method"] == "inferred_raw_reference_row_timing":
                expected_half_width = max(
                    abs(residual_dm - float(interval[0])),
                    abs(float(interval[1]) - residual_dm),
                )
                method_accepted = dsa_input_state["accepted_for_config_review"]
            else:
                expected_half_width = max(
                    abs(float(interval[0])),
                    abs(float(interval[1])),
                )
                method_accepted = dsa_input_state["conservative_bound_accepted_for_config_review"]
            if abs(float(dsa["input_dm_half_width_pc_cm3"]) - expected_half_width) > 1.0e-12:
                raise ValueError("DSA input-DM half-width contradicts review evidence")
            if not method_accepted:
                raise ValueError("selected DSA input-DM method is not review-admissible")
        if review["configuration_status"] == "reviewed" and not (
            dsa_input_state["accepted_for_config_review"]
            or dsa_input_state["conservative_bound_accepted_for_config_review"]
        ):
            raise ValueError("reviewed DSA state has neither value nor bound")
        if workflow["execution_authorized"] and (
            review["configuration_status"] != "reviewed"
            or dsa_input_state["independent_uncertainty_review_status"] != "passed"
            or not (
                dsa_input_state["accepted_for_config_review"]
                or dsa_input_state["conservative_bound_accepted_for_config_review"]
            )
        ):
            raise PermissionError("execution requires reviewed, unblocked DSA value or bound")
    if require_execution_authorized and joint_fit is not None and joint_fit["status"] != "ready":
        raise PermissionError("joint fit is blocked pending reviewed inputs")
    if require_execution_authorized and workflow["execution_authorized"] is not True:
        raise PermissionError("event execution is not authorized by this config")

    expected_binding = event_binding_sha256(config)
    recorded_binding = config["event_binding_sha256"]
    _require_sha256(recorded_binding, "event_binding_sha256")
    if recorded_binding != expected_binding:
        raise ValueError(
            "event binding mismatch: event-sensitive paths, DMs, support, or geometry "
            "changed without a fresh reviewed binding"
        )
    return config


def load_config(
    path: str | Path,
    *,
    require_execution_authorized: bool = False,
) -> dict[str, Any]:
    config = json.loads(Path(path).read_text())
    return validate_config(
        config,
        require_execution_authorized=require_execution_authorized,
    )


def legacy_stage_config(config: dict[str, Any]) -> dict[str, Any]:
    """Flatten the canonical schema for the validated numerical stage code."""

    validate_config(config)
    paths = config["paths"]
    hashes = config["input_sha256"]
    chime = config["chime"]
    dsa = config["dsa"]
    grid = chime["grid"]
    gates = chime["gates"]
    is_regression_fixture = config["workflow"]["regression_fixture"] is True
    return {
        "schema_version": config["schema_version"],
        "event": config["event"],
        "burst": config["event"],
        "result_status": config["result_status"],
        "event_binding_sha256": config["event_binding_sha256"],
        "h5_path": paths["raw_chime_h5"],
        "accepted_chime_reference": paths["accepted_chime_reference"],
        "expected_h5_sha256": hashes["raw_chime_h5"],
        "expected_chime_reference_sha256": hashes["accepted_chime_reference"],
        "accepted_chime_reference_dm_pc_cm3": chime["accepted_reference_dm_pc_cm3"],
        "anchor_dm_pc_cm3": chime["anchor_dm_pc_cm3"],
        "upchannel_factor": chime["upchannel_factor"],
        "window_s": chime["window_s"],
        **grid,
        "oracle_half_width_pc_cm3": gates["oracle_half_width_pc_cm3"],
        "oracle_material_threshold_pc_cm3": gates["oracle_material_threshold_pc_cm3"],
        "oracle_normalised_curve_max_abs_difference": gates[
            "oracle_normalised_curve_max_abs_difference"
        ],
        "oracle_center_score_ratio_tolerance": gates["oracle_center_score_ratio_tolerance"],
        "reference_pulse_fwhm_s": chime["reference_pulse_fwhm_s"],
        "smearing_max_fraction_of_upchannel_sample": gates[
            "smearing_max_fraction_of_upchannel_sample"
        ],
        "smearing_max_fraction_of_reference_pulse_fwhm": gates[
            "smearing_max_fraction_of_reference_pulse_fwhm"
        ],
        "injection_max_error_pc_cm3": gates["injection_max_error_pc_cm3"],
        "expected_chime_support": chime["accepted_support"],
        "geometry_dm_pc_cm3": config["geometry"]["geometry_dm_pc_cm3"],
        "raw_dsa_filterbank": paths["raw_dsa_filterbank"],
        "accepted_dsa_reference": paths["accepted_dsa_reference"],
        "expected_dsa_raw_sha256": hashes["raw_dsa_filterbank"],
        "expected_dsa_reference_sha256": hashes["accepted_dsa_reference"],
        "accepted_dsa_reference_dm_pc_cm3": dsa["accepted_reference_dm_pc_cm3"],
        "raw_dsa_crop_start_sample": dsa["raw_crop_start_sample"],
        "dsa_crop_samples": dsa["crop_samples"],
        "dsa_padding_samples": dsa["padding_samples"],
        "dsa_audit_sample_rows": dsa["audit_sample_rows"],
        "expected_dsa_support": dsa["accepted_support"],
        "dsa_gates": dsa["gates"],
        "reference_frequency_mhz": config["geometry"]["reference_frequency_mhz"],
        "dsa_native_frequency_mhz": config["geometry"]["dsa_native_frequency_mhz"],
        **(
            {
                "dsa_state_reconstruction": paths["dsa_state_reconstruction"],
                "expected_dsa_state_reconstruction_sha256": hashes["dsa_state_reconstruction"],
                "input_dsa_dm_pc_cm3": dsa["input_dm_pc_cm3"],
                "input_dsa_dm_method": dsa["input_dm_method"],
                "input_dsa_dm_bound_source": dsa["input_dm_bound_source"],
                "input_dsa_dm_half_width_pc_cm3": dsa["input_dm_half_width_pc_cm3"],
                "reference_minus_raw_dsa_dm_pc_cm3": dsa["reference_minus_raw_dm_pc_cm3"],
                "reference_minus_raw_dsa_dm_interval_pc_cm3": dsa[
                    "reference_minus_raw_dm_interval_pc_cm3"
                ],
                "raw_dsa_reference_frequency_crop_start_sample": dsa[
                    "raw_reference_frequency_crop_start_sample"
                ],
                "expected_dsa_native_sample_time_s": dsa["native_sample_time_s"],
                **(
                    {
                        "dsa_state_calibration": paths["dsa_state_calibration"],
                        "expected_dsa_state_calibration_sha256": hashes["dsa_state_calibration"],
                    }
                    if dsa["input_dm_bound_source"] == "calibrated_v3_integer_interval_intersection"
                    else {}
                ),
            }
            if not is_regression_fixture
            else {}
        ),
    }
