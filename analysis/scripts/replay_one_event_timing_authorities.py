#!/usr/bin/env python3
"""Replay raw timing authorities without constructing fit observations."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import tempfile
import warnings
from datetime import UTC, datetime
from pathlib import Path

import h5py
import numpy as np
from one_event_workflow import load_config

K_DM_S_MHZ2 = 4148.808
REFERENCE_FREQUENCY_MHZ = 400.0
RUNTIME_PACKAGES = ("astropy", "blimpy", "h5py", "jsonschema", "numpy")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_execution_context(
    repo_root: Path,
    config_path: Path,
    candidate_manifest_path: Path,
    environment_receipt_path: Path,
) -> dict:
    manifest = json.loads(candidate_manifest_path.read_text())
    expected_paths = manifest.get("paths")
    if not isinstance(expected_paths, dict) or not expected_paths:
        raise RuntimeError("candidate manifest lacks bound paths")
    root_resolved = repo_root.resolve()
    for relative, expected_hash in expected_paths.items():
        candidate = (repo_root / relative).resolve()
        if not candidate.is_relative_to(root_resolved):
            raise RuntimeError(f"candidate manifest path leaves repo root: {relative}")
        if sha256_file(candidate) != expected_hash:
            raise RuntimeError(f"candidate manifest path changed: {relative}")
    required_controls = {
        str(config_path.resolve().relative_to(repo_root.resolve())),
        "analysis-configs/absolute-dm/schema.json",
        "radio_pipeline/fitting/products.py",
        "scripts/audit_one_event_dsa_state_h17.py",
        "scripts/build_one_event_dsa_hybrid_h17.py",
        "scripts/one_event_workflow.py",
        "scripts/replay_one_event_timing_authorities.py",
    }
    if not required_controls.issubset(expected_paths):
        raise RuntimeError("candidate manifest omits timing control paths")
    environment = json.loads(environment_receipt_path.read_text())
    runtime = environment.get("h17")
    if not isinstance(runtime, dict):
        raise RuntimeError("environment receipt lacks h17 runtime")
    if Path(runtime.get("python_executable", "")).resolve() != Path(sys.executable).resolve():
        raise RuntimeError("runtime Python differs from environment receipt")
    if runtime.get("python_version") != platform.python_version():
        raise RuntimeError("runtime Python version differs from environment receipt")
    expected_packages = runtime.get("packages")
    if not isinstance(expected_packages, dict):
        raise RuntimeError("environment receipt lacks package versions")
    for package in RUNTIME_PACKAGES:
        if expected_packages.get(package) != importlib.metadata.version(package):
            raise RuntimeError(f"runtime package differs from environment receipt: {package}")
    locks = environment.get("locks")
    if not isinstance(locks, dict):
        raise RuntimeError("environment receipt lacks lock identities")
    for name in ("pyproject.toml", "uv.lock"):
        if sha256_file(repo_root / name) != locks.get(f"{name}_sha256"):
            raise RuntimeError(f"runtime lock differs from environment receipt: {name}")
    return {
        "candidate_manifest": str(candidate_manifest_path.resolve()),
        "candidate_manifest_sha256": sha256_file(candidate_manifest_path),
        "candidate_diff_sha256": manifest["candidate_diff_sha256"],
        "base_commit": manifest["base_commit"],
        "environment_receipt": str(environment_receipt_path.resolve()),
        "environment_receipt_sha256": sha256_file(environment_receipt_path),
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "packages": {name: importlib.metadata.version(name) for name in RUNTIME_PACKAGES},
    }


def recover_trigger(entry: dict) -> dict:
    specnum = int(entry["specnum"])
    itime = specnum // 4 + 1907
    elapsed_true_s = itime * 262.144e-6
    dt_f32 = np.float32(np.float32(262.144) * np.float32(1.0e-6))
    serialized_token_s = float(format(float(np.float32(np.float32(itime) * dt_f32)), ".6g"))
    correction_s = elapsed_true_s - serialized_token_s
    recovered_mjd = float(entry["mjds_T2"]) + correction_s / 86400.0
    return {
        "specnum": specnum,
        "itime": itime,
        "elapsed_true_s": elapsed_true_s,
        "serialized_token_s": serialized_token_s,
        "correction_us": correction_s * 1.0e6,
        "recovered_mjd": recovered_mjd,
    }


def audit_chime(path: Path) -> dict:
    with h5py.File(path, "r") as handle:
        time0 = handle["time0"][:]
        frequency_mhz = np.asarray(handle["index_map/freq"][:]["centre"], dtype=float)
        seconds = time0["ctime"].astype(np.longdouble) + time0["ctime_offset"].astype(
            np.longdouble
        )
        fpga_count = time0["fpga_count"].astype(np.longdouble)
        delta_time_s = np.longdouble(str(handle.attrs["delta_time"]))
        affine_anchor_s = seconds[0] - fpga_count[0] * delta_time_s
        affine_residual_s = seconds - (affine_anchor_s + fpga_count * delta_time_s)

        x = 1.0 / frequency_mhz**2 - 1.0 / REFERENCE_FREQUENCY_MHZ**2
        design = np.column_stack((np.ones_like(x), K_DM_S_MHZ2 * x))
        centered = np.asarray(seconds - seconds.mean(), dtype=float)
        intercept_centered, capture_dm = np.linalg.lstsq(design, centered, rcond=None)[0]
        window_start_400_s = float(intercept_centered + seconds.mean())
        schedule_residual_s = np.asarray(
            seconds - (window_start_400_s + K_DM_S_MHZ2 * capture_dm * x), dtype=float
        )

        event_date = str(handle.attrs["event_date"]).replace("T ", "T")
        event_unix_s = datetime.fromisoformat(event_date).replace(tzinfo=UTC).timestamp()
        ntime = int(handle["tiedbeam_baseband"].shape[-1])
        window_stop_400_s = window_start_400_s + ntime * float(delta_time_s)
        event_inside_window = window_start_400_s <= event_unix_s <= window_stop_400_s
        if not event_inside_window:
            raise RuntimeError("CHIME event timestamp lies outside the 400 MHz capture window")
        maximum_affine_residual_ns = float(np.max(np.abs(affine_residual_s)) * 1.0e9)
        if maximum_affine_residual_ns > 1.0:
            raise RuntimeError("CHIME ctime fields disagree with the FPGA counter")
        maximum_schedule_residual_us = float(np.max(np.abs(schedule_residual_s)) * 1.0e6)
        if maximum_schedule_residual_us > 5.0:
            raise RuntimeError("CHIME channel start times do not follow a cold-plasma schedule")
        return {
            "status": "pass_internal_counter_and_capture_schedule_cross_check",
            "event_id": int(handle.attrs["event_id"]),
            "event_date_utc": event_date,
            "event_date_unix_s": event_unix_s,
            "embedded_baseband_analysis_git_sha": str(
                handle.attrs["baseband-analysis_git_sha"]
            ),
            "archive_version": str(handle.attrs["archive_version"]),
            "channel_count": int(frequency_mhz.size),
            "delta_time_s": float(delta_time_s),
            "maximum_fpga_affine_residual_ns": maximum_affine_residual_ns,
            "capture_schedule_dm_pc_cm3": float(capture_dm),
            "capture_schedule_dm_role": "window-placement diagnostic, not a fitted burst DM",
            "capture_schedule_maximum_residual_us": maximum_schedule_residual_us,
            "capture_window_start_unix_400_s": window_start_400_s,
            "capture_window_stop_unix_400_s": window_stop_400_s,
            "event_date_inside_capture_window": event_inside_window,
            "external_clock_certification": "not supplied",
        }


def _dsa_peak_sample(reader: object, accepted_reference_path: Path) -> int:
    values = np.asarray(reader.data[:, 0, :], dtype=float).T
    reference = np.load(accepted_reference_path)
    if reference.ndim != 2 or reference.shape[0] != values.shape[0]:
        raise RuntimeError("accepted DSA support does not match the filterbank channels")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        reference_std = np.nanstd(reference, axis=1)
    accepted_live = np.isfinite(reference_std) & (reference_std > 0)
    quarter = values.shape[1] // 4
    if quarter < 8:
        raise RuntimeError("DSA filterbank is too short for a robust peak audit")
    off_pulse = np.concatenate((values[:, :quarter], values[:, -quarter:]), axis=1)
    baseline = np.nanmedian(off_pulse, axis=1)
    mad = np.nanmedian(np.abs(off_pulse - baseline[:, None]), axis=1)
    live = accepted_live & np.isfinite(baseline) & np.isfinite(mad) & (mad > 0)
    if int(live.sum()) < 8:
        raise RuntimeError("DSA filterbank has insufficient live channels for a peak audit")
    normalized = (values[live] - baseline[live, None]) / (1.4826 * mad[live, None])
    profile = np.nanmean(normalized, axis=0)
    if not np.any(np.isfinite(profile)):
        raise RuntimeError("DSA filterbank peak profile is non-finite")
    return int(np.nanargmax(profile))


def audit_dsa(
    path: Path,
    trigger_entry: dict,
    time_origin: dict | None = None,
    accepted_reference_path: Path | None = None,
) -> dict:
    from blimpy import Waterfall

    replay = recover_trigger(trigger_entry)
    recorded_mjd = float(trigger_entry["mjd_trigger_exact"])
    replay_difference_ns = (replay["recovered_mjd"] - recorded_mjd) * 86400.0 * 1.0e9
    if abs(replay_difference_ns) > 1000.0:
        raise RuntimeError("DSA trigger recovery does not reproduce the locked value")
    if trigger_entry.get("status") != "VERIFIED":
        raise RuntimeError("DSA trigger authority is not verified")

    reader = Waterfall(str(path), load_data=time_origin is not None)
    header_tstart_mjd = float(reader.header["tstart"])
    sample_time_s = float(reader.header["tsamp"])
    header_to_trigger_s = (recorded_mjd - header_tstart_mjd) * 86400.0
    header_to_trigger_samples = header_to_trigger_s / sample_time_s
    result = {
        "trigger_recovery_status": "pass_tolerance_bounded_replay",
        "trigger_mjd_utc": recorded_mjd,
        "replayed_trigger_mjd_utc": replay["recovered_mjd"],
        "replay_difference_ns": replay_difference_ns,
        "trigger_replay": replay,
        "filterbank_tstart_mjd": header_tstart_mjd,
        "filterbank_sample_interval_s": sample_time_s,
        "rounded_header_to_trigger_s": header_to_trigger_s,
        "rounded_header_to_trigger_samples": header_to_trigger_samples,
        "filterbank_tstart_use": "diagnostic_only_not_an_absolute_time_authority",
    }
    if time_origin is None:
        return result | {
            "filterbank_sample_zero_status": "blocked_missing_exact_trigger_to_sample_mapping",
            "fit_observation_time_origin_eligible": False,
        }
    if time_origin.get("status") != "owner_approved_trigger_peak_anchor":
        raise RuntimeError("DSA trigger-to-peak mapping is not owner approved")
    if time_origin.get("rounded_tstart_allowed") is not False:
        raise RuntimeError("rounded DSA tstart must remain forbidden")
    if not np.isclose(
        float(time_origin["trigger_mjd_utc"]),
        recorded_mjd,
        rtol=0.0,
        atol=0.0,
    ):
        raise RuntimeError("DSA time-origin trigger MJD differs from trigger authority")
    if not np.isclose(
        float(time_origin["filterbank_peak_offset_s"]),
        int(time_origin["filterbank_peak_sample_index"]) * sample_time_s,
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise RuntimeError("DSA time-origin peak offset contradicts its sample index")
    if accepted_reference_path is None:
        raise RuntimeError("approved DSA peak audit requires accepted channel support")
    observed_peak_sample = _dsa_peak_sample(reader, accepted_reference_path)
    approved_peak_sample = int(time_origin["filterbank_peak_sample_index"])
    if observed_peak_sample != approved_peak_sample:
        raise RuntimeError("DSA filterbank peak sample differs from the approved anchor")
    alternative = time_origin["alternative_pretrigger_convention"]
    alternative_sample = int(alternative["sample_index"])
    mapping_ambiguity_s = abs(approved_peak_sample - alternative_sample) * sample_time_s
    if not np.isclose(
        mapping_ambiguity_s,
        float(time_origin["mapping_ambiguity_s"]),
        rtol=0.0,
        atol=1.0e-15,
    ):
        raise RuntimeError("DSA mapping ambiguity differs from the alternative convention")
    trigger_reference_frequency_mhz = float(
        time_origin["trigger_reference_frequency_mhz"]
    )
    product_dm_pc_cm3 = float(time_origin["filterbank_product_dm_pc_cm3"])
    trigger_to_product_reference_s = (
        K_DM_S_MHZ2
        * product_dm_pc_cm3
        * (
            REFERENCE_FREQUENCY_MHZ**-2
            - trigger_reference_frequency_mhz**-2
        )
    )
    return result | {
        "filterbank_sample_zero_status": "derived_from_owner_approved_trigger_peak_anchor",
        "fit_observation_time_origin_eligible": True,
        "joint_fit_timing_uncertainty_eligible": False,
        "filterbank_peak_sample_index": approved_peak_sample,
        "filterbank_peak_offset_s": float(time_origin["filterbank_peak_offset_s"]),
        "trigger_reference_frequency_mhz": trigger_reference_frequency_mhz,
        "filterbank_product_dm_pc_cm3": product_dm_pc_cm3,
        "product_reference_frequency_mhz": REFERENCE_FREQUENCY_MHZ,
        "trigger_to_product_reference_s": trigger_to_product_reference_s,
        "alternative_pretrigger_convention": {
            "sample_index": alternative_sample,
            "status": alternative["status"],
        },
        "mapping_ambiguity_s": mapping_ambiguity_s,
        "mapping_uncertainty_treatment": time_origin["mapping_uncertainty_treatment"],
        "trigger_reference_frequency_status": time_origin[
            "trigger_reference_frequency_status"
        ],
        "trigger_reference_frequency_sensitivity_required": time_origin[
            "trigger_reference_frequency_sensitivity_required"
        ],
        "owner_approval_date": time_origin["owner_approval_date"],
        "owner_decision_receipt_sha256": time_origin[
            "owner_decision_receipt_sha256"
        ],
    }


def build_receipt(
    config_path: Path,
    candidate_manifest_path: Path | None = None,
    environment_receipt_path: Path | None = None,
) -> dict:
    config = load_config(config_path)
    paths = {name: Path(value) for name, value in config["paths"].items()}
    required_hashes = ["raw_chime_h5", "raw_dsa_filterbank", "trigger_recovery"]
    if config.get("dsa", {}).get("time_origin") is not None:
        required_hashes.append("accepted_dsa_reference")
    for key in required_hashes:
        actual = sha256_file(paths[key])
        if actual != config["input_sha256"][key]:
            raise RuntimeError(f"{key} hash differs from configuration")
    triggers = json.loads(paths["trigger_recovery"].read_text())
    event = config["event"]
    if event not in triggers:
        raise RuntimeError(f"trigger recovery lacks event {event}")
    time_origin = config.get("dsa", {}).get("time_origin")
    if time_origin is not None:
        repo_root = Path(__file__).resolve().parents[1]
        decision_root = (repo_root / "analysis-configs/absolute-dm/decisions").resolve()
        decision_path = (repo_root / time_origin["owner_decision_receipt"]).resolve()
        if decision_path.parent != decision_root:
            raise RuntimeError("owner decision receipt path leaves the decision directory")
        if sha256_file(decision_path) != time_origin["owner_decision_receipt_sha256"]:
            raise RuntimeError("owner decision receipt hash differs from configuration")
        if candidate_manifest_path is None or environment_receipt_path is None:
            raise RuntimeError("approved timing audit requires candidate and environment receipts")
        execution_context = _verify_execution_context(
            repo_root,
            config_path,
            candidate_manifest_path,
            environment_receipt_path,
        )
    else:
        execution_context = None
    dsa = audit_dsa(
        paths["raw_dsa_filterbank"],
        triggers[event],
        time_origin,
        paths.get("accepted_dsa_reference"),
    )
    if time_origin is None:
        if dsa.get("fit_observation_time_origin_eligible") is not False:
            raise RuntimeError("DSA timing must remain ineligible without sample-zero authority")
        if dsa.get("filterbank_sample_zero_status") != (
            "blocked_missing_exact_trigger_to_sample_mapping"
        ):
            raise RuntimeError("DSA sample-zero provenance hold is absent")
        receipt_status = "timing_replayed_fit_input_blocked"
    else:
        if dsa.get("fit_observation_time_origin_eligible") is not True:
            raise RuntimeError("approved DSA trigger peak anchor was not admitted")
        if dsa.get("filterbank_sample_zero_status") != (
            "derived_from_owner_approved_trigger_peak_anchor"
        ):
            raise RuntimeError("approved DSA trigger peak anchor is absent")
        if dsa.get("joint_fit_timing_uncertainty_eligible") is not False:
            raise RuntimeError("pending DSA mapping treatment must block joint fitting")
        receipt_status = "timing_replayed_fit_input_blocked_pending_mapping_decision"
    repo_root = Path(__file__).resolve().parents[1]
    return {
        "schema_version": 1,
        "status": receipt_status,
        "event": event,
        "event_binding_sha256": config["event_binding_sha256"],
        "reference_frequency_mhz": REFERENCE_FREQUENCY_MHZ,
        "chime": audit_chime(paths["raw_chime_h5"]),
        "dsa": dsa,
        "provenance": {
            "config_path": str(config_path.resolve()),
            "config_sha256": sha256_file(config_path),
            "raw_chime_h5": str(paths["raw_chime_h5"]),
            "raw_chime_h5_sha256": config["input_sha256"]["raw_chime_h5"],
            "raw_dsa_filterbank": str(paths["raw_dsa_filterbank"]),
            "raw_dsa_filterbank_sha256": config["input_sha256"]["raw_dsa_filterbank"],
            "accepted_dsa_reference": str(paths.get("accepted_dsa_reference", "")),
            "accepted_dsa_reference_sha256": config["input_sha256"].get(
                "accepted_dsa_reference"
            ),
            "trigger_recovery": str(paths["trigger_recovery"]),
            "trigger_recovery_sha256": config["input_sha256"]["trigger_recovery"],
            "owner_decision_receipt": (
                time_origin.get("owner_decision_receipt") if time_origin else None
            ),
            "owner_decision_receipt_sha256": (
                time_origin.get("owner_decision_receipt_sha256") if time_origin else None
            ),
            "script_sha256": sha256_file(Path(__file__)),
            "execution_context": execution_context,
        },
    }


def publish_receipt(
    config_path: Path,
    output_path: Path,
    candidate_manifest_path: Path | None = None,
    environment_receipt_path: Path | None = None,
) -> dict:
    receipt = build_receipt(
        config_path,
        candidate_manifest_path,
        environment_receipt_path,
    )
    payload = json.dumps(receipt, indent=2, allow_nan=False) + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "w") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-manifest", type=Path)
    parser.add_argument("--environment-receipt", type=Path)
    args = parser.parse_args()
    publish_receipt(
        args.config,
        args.output,
        args.candidate_manifest,
        args.environment_receipt,
    )
    print(args.output)


if __name__ == "__main__":
    main()
