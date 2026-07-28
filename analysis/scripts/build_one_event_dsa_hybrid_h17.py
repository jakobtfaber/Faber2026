#!/usr/bin/env python3
"""Build one event's DSA products with one residual-DM correction."""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
from blimpy import Waterfall

from absolute_dm_voltage import K_DM_S_MHZ2, REFERENCE_FREQUENCY_MHZ, sha256
from one_event_workflow import legacy_stage_config, load_config


def apply_residual_dm(
    waterfall: np.ndarray,
    frequency_mhz: np.ndarray,
    sample_time_s: float,
    residual_dm_pc_cm3: float,
) -> np.ndarray:
    """Refer an already-dedispersed intensity array to one new total DM."""

    values = np.asarray(waterfall, dtype=float)
    frequency = np.asarray(frequency_mhz, dtype=float)
    if values.ndim != 2 or frequency.shape != (values.shape[0],):
        raise ValueError("waterfall and frequency dimensions differ")
    shift_sample = (
        -K_DM_S_MHZ2
        * float(residual_dm_pc_cm3)
        * (frequency**-2 - REFERENCE_FREQUENCY_MHZ**-2)
        / float(sample_time_s)
    )
    sample = np.arange(values.shape[1], dtype=float)
    corrected = np.full(values.shape, np.nan, dtype=float)
    for row, shift in enumerate(shift_sample):
        corrected[row] = np.interp(
            sample - shift,
            sample,
            values[row],
            left=np.nan,
            right=np.nan,
        )
    return corrected


def _accepted_support(reference: np.ndarray, expected: dict) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        standard_deviation = np.nanstd(reference, axis=1)
    live = np.isfinite(standard_deviation) & (standard_deviation > 0)
    if (
        reference.shape[0] != int(expected["full_grid_rows"])
        or int(live.sum()) != int(expected["live_count"])
        or int((~live).sum()) != int(expected["dead_count"])
    ):
        raise RuntimeError("accepted DSA support changed")
    return live


def _profile(waterfall: np.ndarray, live: np.ndarray) -> np.ndarray:
    values = np.asarray(waterfall[live], dtype=float)
    median = np.nanmedian(values, axis=1)
    mad = np.nanmedian(np.abs(values - median[:, None]), axis=1)
    sigma = 1.4826 * mad
    usable = np.isfinite(sigma) & (sigma > 0)
    z = (values[usable] - median[usable, None]) / sigma[usable, None]
    return np.nanmean(np.clip(z, 0.0, None), axis=0)


def _profile_correlation(left: np.ndarray, right: np.ndarray, live: np.ndarray) -> float:
    left_profile = _profile(left, live)
    right_profile = _profile(right, live)
    return float(np.corrcoef(left_profile, right_profile)[0, 1])


def _sign_oracle(sample_time_s: float) -> dict:
    frequency = np.linspace(1311.25, 1498.75, 64)
    sample = np.arange(512, dtype=float)
    aligned = np.exp(-0.5 * ((sample - 256.0) / 4.0) ** 2)
    aligned = np.repeat(aligned[None, :], frequency.size, axis=0)
    injected_dm = 0.08
    injected = apply_residual_dm(
        aligned,
        frequency,
        sample_time_s,
        -injected_dm,
    )
    recovered = apply_residual_dm(
        injected,
        frequency,
        sample_time_s,
        injected_dm,
    )
    wrong_sign = apply_residual_dm(
        injected,
        frequency,
        sample_time_s,
        -injected_dm,
    )

    def peak_spread(values: np.ndarray) -> float:
        return float(np.ptp(np.nanargmax(values, axis=1)))

    recovered_spread = peak_spread(recovered)
    wrong_spread = peak_spread(wrong_sign)
    if recovered_spread > 1.0 or recovered_spread >= wrong_spread:
        raise RuntimeError("DSA residual-DM sign oracle failed")
    return {
        "injected_residual_dm_pc_cm3": injected_dm,
        "recovered_peak_spread_samples": recovered_spread,
        "wrong_sign_peak_spread_samples": wrong_spread,
        "passed": True,
    }


def _write_product(
    path: Path,
    *,
    waterfall: np.ndarray,
    frequency_mhz: np.ndarray,
    accepted_live: np.ndarray,
    sample_time_s: float,
    target_dm: float,
    input_dm: float,
    source_start_sample: int,
) -> dict:
    output = np.asarray(waterfall, dtype=float).copy()
    output[~accepted_live] = np.nan
    np.savez_compressed(
        path,
        waterfall=output.astype(np.float32),
        frequency_mhz=np.asarray(frequency_mhz, dtype=np.float64),
        accepted_live=np.asarray(accepted_live, dtype=bool),
        sample_time_s=np.asarray(sample_time_s),
        target_total_dm_pc_cm3=np.asarray(target_dm),
        input_total_dm_pc_cm3=np.asarray(input_dm),
        applied_residual_dm_pc_cm3=np.asarray(target_dm - input_dm),
        source_start_sample=np.asarray(source_start_sample),
    )
    return {
        "path": str(path),
        "sha256": sha256(path),
        "target_total_dm_pc_cm3": target_dm,
        "input_total_dm_pc_cm3": input_dm,
        "applied_residual_dm_pc_cm3": target_dm - input_dm,
    }


def run(
    config: dict,
    chime_result: dict,
    dsa_audit: dict,
    output_dir: Path,
) -> dict:
    event = config["event"]
    expected_status = config["result_status"]
    if chime_result["burst"] != event:
        raise ValueError("CHIME result event does not match configuration")
    if chime_result.get("event_binding_sha256") != config["event_binding_sha256"]:
        raise ValueError("CHIME result binding does not match configuration")
    if chime_result["status"] != expected_status:
        raise RuntimeError("DSA products require the matching CHIME result")
    raw_path = Path(config["raw_dsa_filterbank"])
    reference_path = Path(config["accepted_dsa_reference"])
    expected_raw_sha256 = config["expected_dsa_raw_sha256"]
    expected_reference_sha256 = config["expected_dsa_reference_sha256"]
    if sha256(raw_path) != expected_raw_sha256:
        raise RuntimeError("raw DSA filterbank SHA-256 mismatch")
    if sha256(reference_path) != expected_reference_sha256:
        raise RuntimeError("accepted DSA reference SHA-256 mismatch")
    if dsa_audit.get("event") != event:
        raise RuntimeError("DSA audit event does not match configuration")
    if dsa_audit.get("event_binding_sha256") != config["event_binding_sha256"]:
        raise RuntimeError("DSA audit binding does not match configuration")
    if dsa_audit["raw_filterbank"]["sha256"] != expected_raw_sha256:
        raise RuntimeError("DSA audit refers to another raw filterbank")
    if dsa_audit["accepted_reference"]["sha256"] != expected_reference_sha256:
        raise RuntimeError("DSA audit refers to another accepted reference")
    frequency_order = dsa_audit["frequency_order"]
    direct_correlation = float(frequency_order["direct_median_correlation"])
    reversed_correlation = float(frequency_order["reversed_median_correlation"])
    gates = config["dsa_gates"]
    if (
        direct_correlation < float(gates["direct_correlation_min"])
        or reversed_correlation > float(gates["reversed_correlation_max"])
        or direct_correlation <= reversed_correlation
    ):
        raise RuntimeError("DSA direct-frequency-order oracle failed")
    state = dsa_audit["dedispersion_state_fit"]
    if abs(float(state["inferred_reference_minus_raw_dm_pc_cm3"])) > float(
        gates["reference_minus_raw_dm_abs_max_pc_cm3"]
    ):
        raise RuntimeError("DSA raw/reference residual DM gate failed")
    row_match = dsa_audit["row_match"]
    crop_start = int(config["raw_dsa_crop_start_sample"])
    if (
        int(row_match["start_sample_min"]) != crop_start
        or int(row_match["start_sample_max"]) != crop_start
    ):
        raise RuntimeError("DSA accepted crop start changed")

    reader = Waterfall(str(raw_path), load_data=True)
    raw = np.asarray(reader.data[:, 0, :], dtype=np.float32).T
    reference = np.load(reference_path)
    accepted_live = _accepted_support(reference, config["expected_dsa_support"])
    sample_time_s = float(reader.header["tsamp"])
    frequency_mhz = float(reader.header["fch1"]) + float(
        reader.header["foff"]
    ) * np.arange(int(reader.header["nchans"]))
    input_dm = float(config["accepted_dsa_reference_dm_pc_cm3"])
    window = int(config["dsa_crop_samples"])
    if reference.shape[1] != window:
        raise RuntimeError("accepted DSA crop length changed")
    padding = int(config["dsa_padding_samples"])
    source_start = crop_start - padding
    source_stop = crop_start + window + padding
    source = np.asarray(raw[:, source_start:source_stop], dtype=float)
    if source.shape != (reference.shape[0], window + 2 * padding):
        raise RuntimeError("DSA padded source crop is incomplete")

    output_dir.mkdir(parents=True, exist_ok=True)
    products = {}
    raw_reference_crop = source[:, padding : padding + window]
    products["input_dm"] = _write_product(
        output_dir / "dsa_input_dm.npz",
        waterfall=raw_reference_crop,
        frequency_mhz=frequency_mhz,
        accepted_live=accepted_live,
        sample_time_s=sample_time_s,
        target_dm=input_dm,
        input_dm=input_dm,
        source_start_sample=crop_start,
    )
    products["accepted_reference_dm"] = _write_product(
        output_dir / "dsa_accepted_reference_dm.npz",
        waterfall=reference,
        frequency_mhz=frequency_mhz,
        accepted_live=accepted_live,
        sample_time_s=sample_time_s,
        target_dm=input_dm,
        input_dm=input_dm,
        source_start_sample=crop_start,
    )
    targets = {
        "anchor_dm": float(chime_result["hybrid_method"]["anchor_dm_pc_cm3"]),
        "hybrid_fit_dm": float(chime_result["grid"]["fit"]["dm_pc_cm3"]),
        "geometry_dm": float(config["geometry_dm_pc_cm3"]),
    }
    for label, target_dm in targets.items():
        corrected = apply_residual_dm(
            source,
            frequency_mhz,
            sample_time_s,
            target_dm - input_dm,
        )
        fixed_crop = corrected[:, padding : padding + window]
        if not np.all(np.isfinite(fixed_crop[accepted_live])):
            raise RuntimeError(
                f"DSA {label} correction reached the fixed-crop edge"
            )
        products[label] = _write_product(
            output_dir / f"dsa_{label}.npz",
            waterfall=fixed_crop,
            frequency_mhz=frequency_mhz,
            accepted_live=accepted_live,
            sample_time_s=sample_time_s,
            target_dm=target_dm,
            input_dm=input_dm,
            source_start_sample=crop_start,
        )

    result = {
        "schema_version": 1,
        "status": expected_status,
        "burst": event,
        "event_binding_sha256": config["event_binding_sha256"],
        "scope": f"{event} one-event workflow only",
        "raw_filterbank": {
            "path": str(raw_path),
            "sha256": expected_raw_sha256,
            "frequency_order": "descending",
            "sample_time_s": sample_time_s,
            "crop_start_sample": crop_start,
        },
        "accepted_reference": {
            "path": str(reference_path),
            "sha256": expected_reference_sha256,
            "shape": list(reference.shape),
            "dm_pc_cm3": input_dm,
            "live_row_count": int(accepted_live.sum()),
            "dead_row_count": int((~accepted_live).sum()),
            "raw_crop_profile_correlation": _profile_correlation(
                raw_reference_crop,
                reference,
                accepted_live,
            ),
        },
        "input_state": {
            "raw_total_dm_pc_cm3": input_dm,
            "proof": (
                f"{row_match['selected_count']} accepted-live rows all match "
                f"raw start sample {crop_start}; frequency-dependent residual "
                "fit passes the configured near-zero gate"
            ),
            "sampled_row_count": int(row_match["selected_count"]),
            "matched_start_sample_min": int(row_match["start_sample_min"]),
            "matched_start_sample_max": int(row_match["start_sample_max"]),
            "inferred_reference_minus_raw_dm_pc_cm3": float(
                state["inferred_reference_minus_raw_dm_pc_cm3"]
            ),
            "direct_frequency_order_median_correlation": direct_correlation,
            "reversed_frequency_order_median_correlation": reversed_correlation,
            "row_start_residual_mad_samples": float(
                state["start_residual_mad_samples"]
            ),
        },
        "dedispersion": {
            "coordinate": "absolute total DM in pc cm^-3",
            "rule": f"target total DM minus {input_dm} exactly once",
            "reference_frequency_mhz": float(config["reference_frequency_mhz"]),
            "dispersion_constant_s_mhz2": K_DM_S_MHZ2,
            "nonwrapping_fractional_sample_interpolation": True,
            "fixed_absolute_crop": True,
            "sign_oracle": _sign_oracle(sample_time_s),
        },
        "support": {
            "accepted_live_count": int(accepted_live.sum()),
            "accepted_dead_count": int((~accepted_live).sum()),
            "manual_event_mask_applied": False,
            "proposed_extra_bad_rows": [],
        },
        "products": products,
        "display": {
            "normalization": "per-row median and median absolute deviation",
            "time_crop": (
                f"accepted {window}-sample {event} crop at raw sample {crop_start}"
            ),
            "normalization_role": "display only; does not alter row support",
            "upchannelization": "none; native 0.03051757812 MHz rows",
        },
    }
    result_path = output_dir / "dsa_hybrid_result.json"
    result_path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--chime-result", type=Path, required=True)
    parser.add_argument("--dsa-audit", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(
        legacy_stage_config(load_config(args.config)),
        json.loads(args.chime_result.read_text()),
        json.loads(args.dsa_audit.read_text()),
        args.output_dir,
    )
    print(
        f"{result['burst']} DSA: "
        f"input {result['input_state']['raw_total_dm_pc_cm3']:.6f}; "
        "canonical absolute-DM products written",
        flush=True,
    )


if __name__ == "__main__":
    main()
