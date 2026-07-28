#!/usr/bin/env python3
"""Configuration and receipts for the one-event absolute-DM workflow."""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
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
    "chime_hybrid",
    "dsa_products",
    "geometry",
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
    return hashlib.sha256(
        canonical_json(event_binding_payload(config)).encode("utf-8")
    ).hexdigest()


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

    paths = config["paths"]
    _require_keys(
        paths,
        (
            "raw_chime_h5",
            "accepted_chime_reference",
            "raw_dsa_filterbank",
            "accepted_dsa_reference",
            "timing_results",
            "trigger_recovery",
            "reproduction_fixture",
            "output_root",
        ),
        "paths",
    )
    for key, value in paths.items():
        if not isinstance(value, str) or not value:
            raise ValueError(f"paths.{key}: expected non-empty path")
    input_keys = (
        "raw_chime_h5",
        "accepted_chime_reference",
        "raw_dsa_filterbank",
        "accepted_dsa_reference",
        "timing_results",
        "trigger_recovery",
        "reproduction_fixture",
    )
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
            raise ValueError(
                f"cross-event path token rejected for {event!r}: {conflicts}"
            )
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
        (
            "raw_chime_h5",
            "accepted_chime_reference",
            "raw_dsa_filterbank",
            "accepted_dsa_reference",
            "timing_results",
            "trigger_recovery",
            "reproduction_fixture",
        ),
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
        or any(
            not isinstance(row, int) or row < 0 or row >= full_grid
            for row in present_dead
        )
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
    dsa_support = dsa["accepted_support"]
    _require_keys(
        dsa_support,
        ("full_grid_rows", "live_count", "dead_count", "manual_bad_channel_ids"),
        "dsa.accepted_support",
    )
    if (
        int(dsa_support["live_count"]) + int(dsa_support["dead_count"])
        != int(dsa_support["full_grid_rows"])
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
            "reference_minus_raw_dm_abs_max_pc_cm3",
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
    if float(dsa_gates["reference_minus_raw_dm_abs_max_pc_cm3"]) <= 0:
        raise ValueError("DSA residual-DM gate must be positive")

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
        raise ValueError(
            f"geometry.reference_frequency_mhz must remain {REFERENCE_FREQUENCY_MHZ}"
        )

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
    if workflow["stages"] != list(STAGES):
        raise ValueError(f"workflow.stages must equal {list(STAGES)}")
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
        "accepted_chime_reference_dm_pc_cm3": chime[
            "accepted_reference_dm_pc_cm3"
        ],
        "anchor_dm_pc_cm3": chime["anchor_dm_pc_cm3"],
        "upchannel_factor": chime["upchannel_factor"],
        "window_s": chime["window_s"],
        **grid,
        "oracle_half_width_pc_cm3": gates["oracle_half_width_pc_cm3"],
        "oracle_material_threshold_pc_cm3": gates[
            "oracle_material_threshold_pc_cm3"
        ],
        "oracle_normalised_curve_max_abs_difference": gates[
            "oracle_normalised_curve_max_abs_difference"
        ],
        "oracle_center_score_ratio_tolerance": gates[
            "oracle_center_score_ratio_tolerance"
        ],
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
        "accepted_dsa_reference_dm_pc_cm3": dsa[
            "accepted_reference_dm_pc_cm3"
        ],
        "raw_dsa_crop_start_sample": dsa["raw_crop_start_sample"],
        "dsa_crop_samples": dsa["crop_samples"],
        "dsa_padding_samples": dsa["padding_samples"],
        "dsa_audit_sample_rows": dsa["audit_sample_rows"],
        "expected_dsa_support": dsa["accepted_support"],
        "dsa_gates": dsa["gates"],
        "reference_frequency_mhz": config["geometry"]["reference_frequency_mhz"],
    }
