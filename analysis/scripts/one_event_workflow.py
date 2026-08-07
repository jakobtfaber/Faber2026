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
    "resolution_fit",
    "resolution_check",
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


def arrays_sha256(*arrays: Any) -> str:
    """Hash array values together with their exact dtype and shape."""

    import numpy as np

    digest = hashlib.sha256()
    for array in arrays:
        value = np.ascontiguousarray(array)
        digest.update(value.dtype.str.encode())
        digest.update(repr(value.shape).encode())
        digest.update(value.view(np.uint8))
    return digest.hexdigest()


def sample_time_axis_ns(
    *,
    time0_unix_ns: int,
    sample_interval_s: float,
    sample_count: int,
) -> Any:
    """Construct the reviewed integer-nanosecond sample centers."""

    import numpy as np

    offsets_ns = np.rint(
        np.arange(sample_count, dtype=np.float64) * float(sample_interval_s) * 1.0e9
    ).astype(np.int64)
    return np.asarray(int(time0_unix_ns), dtype=np.int64) + offsets_ns


def event_binding_payload(config: dict[str, Any]) -> dict[str, Any]:
    """Bind the complete canonical config except the binding's own value."""

    payload = deepcopy(config)
    payload.pop("event_binding_sha256", None)
    return payload


def event_binding_sha256(config: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(event_binding_payload(config)).encode("utf-8")).hexdigest()


FIT_SETTING_KEYS = (
    "dm_bounds_pc_cm3",
    "morphologies",
    "scattering_tau_1ghz_bounds_s",
    "scattering_alpha_bounds",
    "gain_variance",
    "sampler",
    "acceptance",
)


def _fit_settings_payload(joint_fit: dict[str, Any]) -> dict[str, Any]:
    return {key: deepcopy(joint_fit[key]) for key in FIT_SETTING_KEYS}


def fit_settings_sha256(joint_fit: dict[str, Any]) -> str:
    return hashlib.sha256(
        canonical_json(_fit_settings_payload(joint_fit)).encode("utf-8")
    ).hexdigest()


def _payload_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def validate_review_plan(review_plan: dict[str, Any]) -> None:
    """Validate the owner-selected component counts and explicit hypotheses."""

    _require_keys(
        review_plan,
        ("component_count", "association_hypotheses", "fit_resolution"),
        "joint_fit.review_plan",
    )
    counts = review_plan["component_count"]
    if (
        not isinstance(counts, dict)
        or set(counts) != {"chime", "dsa"}
        or any(not isinstance(counts[key], int) or counts[key] < 1 for key in counts)
    ):
        raise ValueError("review plan needs positive CHIME and DSA component counts")
    hypotheses = review_plan["association_hypotheses"]
    if not isinstance(hypotheses, list) or not hypotheses:
        raise ValueError("review plan needs association hypotheses")
    expected_ids = {
        "chime": {f"chime_c{index}" for index in range(1, counts["chime"] + 1)},
        "dsa": {f"dsa_c{index}" for index in range(1, counts["dsa"] + 1)},
    }
    names: set[str] = set()
    for hypothesis in hypotheses:
        _require_keys(hypothesis, ("name", "matches"), "review plan hypothesis")
        name = hypothesis["name"]
        if not isinstance(name, str) or not name or name in names:
            raise ValueError("review plan hypothesis names must be unique")
        names.add(name)
        matches = hypothesis["matches"]
        if not isinstance(matches, list) or not matches:
            raise ValueError("review plan hypothesis needs matches")
        latent_ids: set[str] = set()
        chime_ids: set[str] = set()
        dsa_ids: set[str] = set()
        for match in matches:
            _require_keys(
                match,
                ("latent_id", "chime_component_id", "dsa_component_id"),
                "review plan match",
            )
            latent_id = match["latent_id"]
            chime_id = match["chime_component_id"]
            dsa_id = match["dsa_component_id"]
            if (
                not all(isinstance(value, str) and value for value in (latent_id, chime_id, dsa_id))
                or latent_id in latent_ids
                or chime_id in chime_ids
                or dsa_id in dsa_ids
                or chime_id not in expected_ids["chime"]
                or dsa_id not in expected_ids["dsa"]
            ):
                raise ValueError("review plan match is duplicate or names an unknown component")
            latent_ids.add(latent_id)
            chime_ids.add(chime_id)
            dsa_ids.add(dsa_id)
    fit_resolution = review_plan["fit_resolution"]
    _require_keys(
        fit_resolution,
        (
            "status",
            "minimum_valid_fraction",
            "minimum_samples_per_component",
            "time_average_factor",
            "maximum_residual_smearing_fraction_of_fit_sample",
            "maximum_residual_smearing_fraction_of_component_width",
            "exact_divisor_required",
        ),
        "joint_fit.review_plan.fit_resolution",
    )
    if fit_resolution["status"] != "pending_data_driven_proposal":
        raise ValueError("fit-resolution review plan must remain proposal-only")
    if float(fit_resolution["minimum_valid_fraction"]) != 1.0:
        raise ValueError("fit-resolution products require complete rectangular support")
    if int(fit_resolution["time_average_factor"]) != 1:
        raise ValueError("formal fitting does not permit time averaging")
    if int(fit_resolution["minimum_samples_per_component"]) < 2:
        raise ValueError("fit-resolution plan needs at least two samples per component")
    if any(
        not 0 < float(fit_resolution[key]) <= 1
        for key in (
            "maximum_residual_smearing_fraction_of_fit_sample",
            "maximum_residual_smearing_fraction_of_component_width",
        )
    ):
        raise ValueError("fit-resolution smearing limits must lie in (0, 1]")
    if fit_resolution["exact_divisor_required"] is not True:
        raise ValueError("fit-resolution averaging must use exact divisors")


def build_review_decision_template(
    config: dict[str, Any],
    *,
    component_proposal: dict[str, Any],
    component_proposal_sha256: str,
    resolution_proposal: dict[str, Any],
    resolution_proposal_sha256: str,
) -> dict[str, Any]:
    """Build an inert owner decision form bound to exact preparation products."""

    validate_config(config)
    joint_fit = config["joint_fit"]
    if joint_fit["status"] != "blocked_pending_reviewed_inputs":
        raise ValueError("review template requires a blocked joint-fit config")
    if component_proposal.get("event") != config["event"]:
        raise ValueError("component proposal belongs to another event")
    if component_proposal.get("event_binding_sha256") != config["event_binding_sha256"]:
        raise ValueError("component proposal belongs to another event binding")
    if component_proposal.get("review_plan") != joint_fit["review_plan"]:
        raise ValueError("component proposal differs from the configured review plan")
    _require_sha256(component_proposal_sha256, "component proposal SHA-256")
    _require_sha256(resolution_proposal_sha256, "resolution proposal SHA-256")
    return {
        "schema_version": 1,
        "status": "pending_owner_review",
        "approved": False,
        "event": config["event"],
        "source_event_binding_sha256": config["event_binding_sha256"],
        "component_proposal_sha256": component_proposal_sha256,
        "resolution_proposal_sha256": resolution_proposal_sha256,
        "fit_settings_sha256": fit_settings_sha256(joint_fit),
        "resolution_lock": deepcopy(resolution_proposal),
        "reviewer": "",
        "review_date": "",
        "note": "",
    }


def apply_review_decision(
    config: dict[str, Any],
    decision: dict[str, Any],
    *,
    component_proposal: dict[str, Any],
    component_proposal_sha256: str,
    resolution_proposal: dict[str, Any],
    resolution_proposal_sha256: str,
) -> dict[str, Any]:
    """Create a locked, reviewed, execution-disabled config."""

    validate_config(config)
    joint_fit = config["joint_fit"]
    if joint_fit["status"] != "blocked_pending_reviewed_inputs":
        raise ValueError("review decisions apply only to blocked configs")
    expected_identity = {
        "event": config["event"],
        "source_event_binding_sha256": config["event_binding_sha256"],
        "component_proposal_sha256": component_proposal_sha256,
        "resolution_proposal_sha256": resolution_proposal_sha256,
        "fit_settings_sha256": fit_settings_sha256(joint_fit),
    }
    for key, expected in expected_identity.items():
        if decision.get(key) != expected:
            raise ValueError(f"review decision {key} differs from reviewed inputs")
    if decision.get("status") != "approved" or decision.get("approved") is not True:
        raise PermissionError("review decision is not explicitly approved")
    for field in ("reviewer", "review_date", "note"):
        if not isinstance(decision.get(field), str) or not decision[field].strip():
            raise ValueError(f"approved review decision needs {field}")
    try:
        date.fromisoformat(decision["review_date"])
    except ValueError as exc:
        raise ValueError("review decision date must use YYYY-MM-DD") from exc
    if component_proposal.get("event_binding_sha256") != config["event_binding_sha256"]:
        raise ValueError("component proposal belongs to another event binding")
    if component_proposal.get("review_plan") != joint_fit["review_plan"]:
        raise ValueError("component proposal differs from configured review plan")
    if component_proposal.get("status") != "proposal_pending_owner_review":
        raise ValueError("component proposal status is invalid")
    components = component_proposal.get("components")
    associations = component_proposal.get("association_hypotheses")
    counts = joint_fit["review_plan"]["component_count"]
    if (
        not isinstance(components, list)
        or len(components) != counts["chime"] + counts["dsa"]
        or associations != joint_fit["review_plan"]["association_hypotheses"]
    ):
        raise ValueError("component proposal does not implement the review plan")

    approved_resolution = deepcopy(resolution_proposal)
    approved_resolution["status"] = "reviewed"
    approved_resolution["crop_and_off_pulse_padding_locked"] = True
    if decision.get("resolution_lock") != approved_resolution:
        raise ValueError("review decision does not exactly approve the proposed resolution lock")
    resolution_policy = joint_fit["review_plan"]["fit_resolution"]
    observation_contracts = component_proposal.get("observation_contracts", {})
    reviewed_components: list[dict[str, Any]] = []
    for instrument in ("chime", "dsa"):
        instrument_components = [
            row for row in components if row.get("instrument") == instrument
        ]
        expected_component_ids = {
            f"{instrument}_c{index}"
            for index in range(
                1,
                joint_fit["review_plan"]["component_count"][instrument] + 1,
            )
        }
        if {row.get("component_id") for row in instrument_components} != (
            expected_component_ids
        ):
            raise ValueError(f"{instrument} component IDs differ from the review plan")
        try:
            contract = observation_contracts[instrument]
            fit_sample_s = float(contract["sample_interval_s"])
            fit_shape = [int(value) for value in contract["shape"]]
            narrowest_fwhm_s = min(
                float(row["matched_filter_width_samples"]) * fit_sample_s
                for row in instrument_components
            )
            smearing_s = float(
                approved_resolution[
                    f"{instrument}_max_residual_intra_bin_smearing_s"
                ]
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"{instrument} lacks analytic fit-resolution smearing evidence"
            ) from exc
        if (
            fit_shape != approved_resolution[f"{instrument}_shape"]
            or not math.isclose(
                fit_sample_s,
                float(approved_resolution[f"{instrument}_sample_interval_s"]),
                rel_tol=0.0,
                abs_tol=1.0e-15,
            )
            or contract["frequency_grid_sha256"]
            != approved_resolution[f"{instrument}_frequency_grid_sha256"]
            or contract["valid_mask_sha256"]
            != approved_resolution[f"{instrument}_valid_mask_sha256"]
        ):
            raise ValueError(
                f"{instrument} component proposal belongs to another fit grid"
            )
        if smearing_s > (
            float(
                resolution_policy[
                    "maximum_residual_smearing_fraction_of_fit_sample"
                ]
            )
            * fit_sample_s
        ) or smearing_s > (
            float(
                resolution_policy[
                    "maximum_residual_smearing_fraction_of_component_width"
                ]
            )
            * narrowest_fwhm_s
        ):
            raise ValueError(
                f"{instrument} fit-resolution smearing exceeds reviewed limits"
            )
        sample_count = fit_shape[1]
        for row in instrument_components:
            center = float(row["center_sample"])
            half_width = float(row["half_width_samples"])
            width_bounds = [float(value) for value in row["width_bounds_s"]]
            if (
                not math.isfinite(center)
                or not math.isfinite(half_width)
                or half_width <= 0
                or center - half_width < 0
                or center + half_width > sample_count
                or len(width_bounds) != 2
                or not 0 < width_bounds[0] < width_bounds[1]
            ):
                raise ValueError(
                    f"{instrument} component window lies outside the approved fit grid"
                )
            reviewed_components.append(
                {
                    "instrument": instrument,
                    "component_id": row["component_id"],
                    "center_sample": center,
                    "half_width_samples": half_width,
                    "width_bounds_s": width_bounds,
                    "width_index_bounds": [
                        float(value)
                        for value in row.get("width_index_bounds", [-2.0, 2.0])
                    ],
                }
            )
    validate_resolution_lock(approved_resolution)

    reviewed = deepcopy(config)
    reviewed_joint = reviewed["joint_fit"]
    reviewed_joint.update(
        {
            "status": "reviewed_execution_disabled",
            "execution_authorized": False,
            "blockers": [],
            "resolution": approved_resolution,
            "components": reviewed_components,
            "associations": deepcopy(associations),
            "review_decision": {
                "status": "approved",
                **expected_identity,
                "components_sha256": _payload_sha256(reviewed_components),
                "associations_sha256": _payload_sha256(associations),
                "approved_resolution_sha256": _payload_sha256(approved_resolution),
                "reviewer": decision["reviewer"],
                "review_date": decision["review_date"],
                "note": decision["note"],
            },
        }
    )
    reviewed["workflow"]["execution_authorized"] = False
    reviewed["result_status"] = "geometry_constrained_joint_fit_reviewed_execution_disabled"
    if reviewed["workflow"]["regression_fixture"] is not True and "review" in reviewed:
        reviewed["review"]["configuration_status"] = "reviewed"
        reviewed["review"]["blockers"] = []
    reviewed["event_binding_sha256"] = event_binding_sha256(reviewed)
    return validate_config(reviewed)


def authorize_reviewed_config(
    config: dict[str, Any],
    *,
    note: str,
    authorization_date: str | None = None,
) -> dict[str, Any]:
    """Create a separately bound config that explicitly permits execution."""

    validate_config(config)
    if config["joint_fit"]["status"] != "reviewed_execution_disabled":
        raise ValueError("authorization requires a reviewed execution-disabled config")
    if not note.strip():
        raise ValueError("authorization note must not be empty")
    authorization_date = authorization_date or date.today().isoformat()
    try:
        date.fromisoformat(authorization_date)
    except ValueError as exc:
        raise ValueError("authorization date must use YYYY-MM-DD") from exc
    authorized = deepcopy(config)
    authorized["joint_fit"]["status"] = "ready"
    authorized["joint_fit"]["execution_authorized"] = True
    authorized["joint_fit"]["authorization"] = {
        "status": "explicitly_authorized",
        "source_reviewed_event_binding_sha256": config["event_binding_sha256"],
        "date": authorization_date,
        "note": note,
        "requires_receipt_rebuild": [
            "preflight",
            "dsa_audit",
            "chime_products",
            "dsa_products",
            "geometry_constraint",
        ],
    }
    authorized["workflow"]["execution_authorized"] = True
    authorized["result_status"] = "geometry_constrained_joint_fit_ready_for_science_execution"
    authorized["event_binding_sha256"] = event_binding_sha256(authorized)
    return validate_config(authorized, require_execution_authorized=True)


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


def validate_resolution_lock(resolution: dict[str, Any]) -> None:
    """Require every reviewed grid, support, and science-array identity."""

    keys = (
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
        "chime_waterfall_sha256",
        "dsa_waterfall_sha256",
        "chime_noise_std_sha256",
        "dsa_noise_std_sha256",
        "chime_time_axis_sha256",
        "dsa_time_axis_sha256",
        "chime_time0_unix_ns",
        "dsa_time0_unix_ns",
        "chime_fit_frequency_average_factor",
        "chime_fit_time_average_factor",
        "dsa_fit_frequency_average_factor",
        "dsa_fit_time_average_factor",
        "chime_fit_observation_sha256",
        "dsa_fit_observation_sha256",
        "chime_max_residual_intra_bin_smearing_s",
        "dsa_max_residual_intra_bin_smearing_s",
        "chime_smearing_calculation_sha256",
        "dsa_smearing_calculation_sha256",
    )
    _require_keys(resolution, keys, "joint_fit.resolution")
    if resolution.get("crop_and_off_pulse_padding_locked") is not True:
        raise ValueError("joint fit requires locked crop and padding")
    for key in keys:
        if key.endswith("_sha256"):
            _require_sha256(resolution[key], f"joint_fit.resolution.{key}")
        elif key.endswith("_average_factor") and (
            not isinstance(resolution[key], int) or resolution[key] < 1
        ):
            raise ValueError(f"joint_fit.resolution.{key} must be a positive integer")
        elif key.endswith("_smearing_s") and (
            not math.isfinite(float(resolution[key])) or float(resolution[key]) < 0
        ):
            raise ValueError(f"joint_fit.resolution.{key} must be finite and non-negative")
    if (
        resolution["chime_fit_time_average_factor"] != 1
        or resolution["dsa_fit_time_average_factor"] != 1
    ):
        raise ValueError("formal fit-resolution products must retain native time sampling")


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
    if config.get("joint_fit") is not None and "time_origin" in dsa:
        time_origin = dsa["time_origin"]
        _require_keys(
            time_origin,
            (
                "status",
                "trigger_mjd_utc",
                "trigger_reference_frequency_mhz",
                "trigger_reference_frequency_status",
                "trigger_reference_frequency_sensitivity_required",
                "filterbank_product_dm_pc_cm3",
                "filterbank_peak_sample_index",
                "filterbank_peak_offset_s",
                "alternative_pretrigger_convention",
                "mapping_ambiguity_s",
                "mapping_uncertainty_treatment",
                "rounded_tstart_allowed",
                "owner_approval_date",
                "owner_decision_receipt",
                "owner_decision_receipt_sha256",
            ),
            "dsa.time_origin",
        )
        if time_origin["status"] != "owner_approved_trigger_peak_anchor":
            raise ValueError("DSA time origin needs an owner-approved trigger peak anchor")
        if time_origin["rounded_tstart_allowed"] is not False:
            raise ValueError("rounded DSA tstart must remain forbidden")
        if int(time_origin["filterbank_peak_sample_index"]) < 0:
            raise ValueError("DSA trigger peak sample must be non-negative")
        expected_peak_offset_s = int(time_origin["filterbank_peak_sample_index"]) * float(
            dsa.get("native_sample_time_s", 32.768e-6)
        )
        if not math.isclose(
            float(time_origin["filterbank_peak_offset_s"]),
            expected_peak_offset_s,
            rel_tol=0.0,
            abs_tol=1.0e-15,
        ):
            raise ValueError("DSA peak offset contradicts its sample index")
        alternative = time_origin["alternative_pretrigger_convention"]
        if alternative.get("status") != "unverified_alternative_for_sensitivity_only":
            raise ValueError("DSA alternative pretrigger convention status is invalid")
        expected_mapping_ambiguity_s = abs(
            int(time_origin["filterbank_peak_sample_index"])
            - int(alternative["sample_index"])
        ) * float(dsa.get("native_sample_time_s", 32.768e-6))
        if not math.isclose(
            float(time_origin["mapping_ambiguity_s"]),
            expected_mapping_ambiguity_s,
            rel_tol=0.0,
            abs_tol=1.0e-15,
        ):
            raise ValueError("DSA mapping ambiguity contradicts the alternative convention")
        if time_origin["mapping_uncertainty_treatment"] != (
            "pending_owner_decision_discrete_two_anchor_sensitivity"
        ):
            raise ValueError("DSA mapping uncertainty treatment is unsupported")
        if time_origin["trigger_reference_frequency_status"] != (
            "proposed_modeling_convention_pending_owner_decision"
        ):
            raise ValueError("DSA trigger reference-frequency status is invalid")
        if time_origin["trigger_reference_frequency_sensitivity_required"] is not True:
            raise ValueError("DSA trigger reference-frequency sensitivity must remain required")
        if not re.fullmatch(
            r"[0-9a-f]{64}", str(time_origin["owner_decision_receipt_sha256"])
        ):
            raise ValueError("DSA owner decision receipt hash is invalid")
        if not math.isclose(
            float(time_origin["trigger_reference_frequency_mhz"]),
            float(config["geometry"]["dsa_native_frequency_mhz"]),
            rel_tol=0.0,
            abs_tol=0.0,
        ):
            raise ValueError("DSA trigger reference differs from the geometry timing reference")
        if not math.isclose(
            float(time_origin["filterbank_product_dm_pc_cm3"]),
            float(dsa["accepted_reference_dm_pc_cm3"]),
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ):
            raise ValueError("DSA time-origin product DM differs from the input state")
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
                "review_plan",
                *FIT_SETTING_KEYS,
            ),
            "joint_fit",
        )
        if float(joint_fit["reference_frequency_mhz"]) != REFERENCE_FREQUENCY_MHZ:
            raise ValueError("joint_fit reference frequency must remain 400 MHz")
        validate_timing_uncertainties(joint_fit["geometry"])
        validate_review_plan(joint_fit["review_plan"])
        blockers = joint_fit["blockers"]
        if (
            not isinstance(blockers, list)
            or blockers != sorted(set(blockers))
            or any(not isinstance(value, str) or not value for value in blockers)
        ):
            raise ValueError("joint_fit blockers must be sorted unique strings")
        _require_keys(joint_fit["sampler"], ("seed", "nlive", "dlogz"), "joint_fit.sampler")
        _require_keys(
            joint_fit["acceptance"],
            (
                "maximum_reduced_residual_power",
                "maximum_structured_residual_correlation",
                "posterior_edge_fraction",
                "maximum_prior_edge_mass",
                "resolution_convergence_required",
                "maximum_resolution_dm_shift_combined_sigma",
                "maximum_resolution_dm_shift_pc_cm3",
                "maximum_resolution_toa_shift_combined_sigma",
                "resolution_interval_width_ratio",
                "maximum_resolution_model_weight_l1_difference",
            ),
            "joint_fit.acceptance",
        )
        acceptance = joint_fit["acceptance"]
        if acceptance["resolution_convergence_required"] is not True:
            raise ValueError("post-fit resolution convergence must remain required")
        width_ratio = acceptance["resolution_interval_width_ratio"]
        if (
            not isinstance(width_ratio, list)
            or len(width_ratio) != 2
            or not 0 < float(width_ratio[0]) <= 1 <= float(width_ratio[1])
        ):
            raise ValueError("resolution interval-width ratio must bracket one")
        if joint_fit["status"] in {"reviewed_execution_disabled", "ready"}:
            if blockers:
                raise ValueError("reviewed joint fit must be unblocked")
            expected_authorization = joint_fit["status"] == "ready"
            if joint_fit["execution_authorized"] is not expected_authorization:
                raise ValueError("joint-fit authorization contradicts its status")
            _require_keys(
                joint_fit,
                (
                    "components",
                    "associations",
                    "review_decision",
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
            validate_resolution_lock(joint_fit["resolution"])
            review_decision = joint_fit["review_decision"]
            _require_keys(
                review_decision,
                (
                    "status",
                    "event",
                    "source_event_binding_sha256",
                    "component_proposal_sha256",
                    "resolution_proposal_sha256",
                    "fit_settings_sha256",
                    "components_sha256",
                    "associations_sha256",
                    "approved_resolution_sha256",
                    "reviewer",
                    "review_date",
                    "note",
                ),
                "joint_fit.review_decision",
            )
            if review_decision["status"] != "approved":
                raise ValueError("joint-fit review decision is not approved")
            if review_decision["event"] != event:
                raise ValueError("joint-fit review decision belongs to another event")
            for key in (
                "source_event_binding_sha256",
                "component_proposal_sha256",
                "resolution_proposal_sha256",
                "fit_settings_sha256",
                "components_sha256",
                "associations_sha256",
                "approved_resolution_sha256",
            ):
                _require_sha256(review_decision[key], f"joint_fit.review_decision.{key}")
            if review_decision["fit_settings_sha256"] != fit_settings_sha256(joint_fit):
                raise ValueError("reviewed fit settings changed after approval")
            for key, value in (
                ("components_sha256", joint_fit["components"]),
                ("associations_sha256", joint_fit["associations"]),
                ("approved_resolution_sha256", joint_fit["resolution"]),
            ):
                if review_decision[key] != _payload_sha256(value):
                    raise ValueError(f"reviewed {key.removesuffix('_sha256')} changed")
            if joint_fit["status"] == "ready":
                _require_keys(joint_fit, ("authorization",), "joint_fit")
                authorization = joint_fit["authorization"]
                _require_keys(
                    authorization,
                    (
                        "status",
                        "source_reviewed_event_binding_sha256",
                        "date",
                        "note",
                        "requires_receipt_rebuild",
                    ),
                    "joint_fit.authorization",
                )
                if (
                    authorization["status"] != "explicitly_authorized"
                    or not authorization["note"]
                    or authorization["requires_receipt_rebuild"]
                    != [
                        "preflight",
                        "dsa_audit",
                        "chime_products",
                        "dsa_products",
                        "geometry_constraint",
                    ]
                ):
                    raise ValueError("joint-fit authorization receipt is invalid")
                reviewed_source = deepcopy(config)
                reviewed_source["joint_fit"].pop("authorization")
                reviewed_source["joint_fit"]["status"] = "reviewed_execution_disabled"
                reviewed_source["joint_fit"]["execution_authorized"] = False
                reviewed_source["workflow"]["execution_authorized"] = False
                reviewed_source["result_status"] = (
                    "geometry_constrained_joint_fit_reviewed_execution_disabled"
                )
                reviewed_source["event_binding_sha256"] = event_binding_sha256(
                    reviewed_source
                )
                if (
                    authorization["source_reviewed_event_binding_sha256"]
                    != reviewed_source["event_binding_sha256"]
                ):
                    raise ValueError("authorization belongs to another reviewed binding")
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
    if joint_fit is not None:
        expected_workflow_authorization = joint_fit["status"] == "ready"
        if workflow["execution_authorized"] is not expected_workflow_authorization:
            raise ValueError("workflow authorization contradicts joint-fit status")
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
        "trigger_recovery": paths["trigger_recovery"],
        "accepted_dsa_reference": paths["accepted_dsa_reference"],
        "expected_dsa_raw_sha256": hashes["raw_dsa_filterbank"],
        "expected_trigger_recovery_sha256": hashes["trigger_recovery"],
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
        "dsa_time_origin": dsa.get("time_origin"),
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
