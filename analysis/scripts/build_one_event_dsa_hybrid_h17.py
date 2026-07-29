#!/usr/bin/env python3
"""Build one event's DSA products with one residual-DM correction."""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
from absolute_dm_voltage import K_DM_S_MHZ2, REFERENCE_FREQUENCY_MHZ, sha256
from blimpy import Waterfall
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


def apply_residual_dm_absolute_crop(
    raw_waterfall: np.ndarray,
    frequency_mhz: np.ndarray,
    sample_time_s: float,
    residual_dm_pc_cm3: float,
    reference_frequency_crop_start_sample: float,
    crop_samples: int,
) -> np.ndarray:
    """Correct full raw rows and sample one fixed 400-MHz-referenced crop."""

    values = np.asarray(raw_waterfall, dtype=float)
    frequency = np.asarray(frequency_mhz, dtype=float)
    if values.ndim != 2 or frequency.shape != (values.shape[0],):
        raise ValueError("raw waterfall and frequency dimensions differ")
    if sample_time_s <= 0 or crop_samples <= 0:
        raise ValueError("sample time and crop length must be positive")
    shift_sample = (
        -K_DM_S_MHZ2
        * float(residual_dm_pc_cm3)
        * (frequency**-2 - REFERENCE_FREQUENCY_MHZ**-2)
        / float(sample_time_s)
    )
    source_axis = np.arange(values.shape[1], dtype=float)
    output_offset = np.arange(crop_samples, dtype=float)
    corrected = np.full((values.shape[0], crop_samples), np.nan, dtype=float)
    for row, shift in enumerate(shift_sample):
        source_coordinate = (
            float(reference_frequency_crop_start_sample) + output_offset - shift
        )
        corrected[row] = np.interp(
            source_coordinate,
            source_axis,
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


def _finite_correlation(left: np.ndarray, right: np.ndarray) -> float:
    use = np.isfinite(left) & np.isfinite(right)
    if use.sum() < 8:
        return 0.0
    first = np.asarray(left[use], dtype=float)
    second = np.asarray(right[use], dtype=float)
    first -= np.mean(first)
    second -= np.mean(second)
    denominator = float(np.linalg.norm(first) * np.linalg.norm(second))
    return float(np.dot(first, second) / denominator) if denominator > 0 else 0.0


def aligned_profile_metrics(
    nominal: np.ndarray,
    endpoint: np.ndarray,
    live: np.ndarray,
    *,
    maximum_lag_samples: int,
) -> dict:
    """Measure endpoint morphology after allowing only a recorded integer lag."""

    first = _profile(nominal, live)
    second = _profile(endpoint, live)
    best = {"lag_samples": 0, "correlation": _finite_correlation(first, second)}
    for lag in range(-maximum_lag_samples, maximum_lag_samples + 1):
        if lag < 0:
            left = first[:lag]
            right = second[-lag:]
        elif lag > 0:
            left = first[lag:]
            right = second[:-lag]
        else:
            left = first
            right = second
        correlation = _finite_correlation(left, right)
        if correlation > best["correlation"]:
            best = {"lag_samples": lag, "correlation": correlation}
    return best


def reference_400_timing_half_width(
    input_dm_half_width_pc_cm3: float,
    native_frequency_mhz: float,
    sample_time_s: float,
) -> dict:
    half_width_ms = (
        1000.0
        * K_DM_S_MHZ2
        * float(input_dm_half_width_pc_cm3)
        * abs(
            REFERENCE_FREQUENCY_MHZ**-2
            - float(native_frequency_mhz) ** -2
        )
    )
    return {
        "ms": half_width_ms,
        "native_samples": half_width_ms / (1000.0 * float(sample_time_s)),
    }


def endpoint_gate_summary(
    endpoint_review: dict[str, dict],
    *,
    predicted_timing_half_width_native_samples: float,
    timing_limit_native_samples: float,
    correlation_limit: float,
) -> dict:
    rows = [
        endpoint
        for target in endpoint_review.values()
        for endpoint in target.values()
    ]
    if not rows:
        raise ValueError("endpoint review is empty")
    maximum_measured_lag = max(
        abs(int(row["measured_profile_lag_native_samples"]))
        for row in rows
    )
    minimum_correlation = min(
        float(row["peak_aligned_profile_correlation"]) for row in rows
    )
    timing_passed = bool(
        predicted_timing_half_width_native_samples
        <= timing_limit_native_samples
        and maximum_measured_lag <= timing_limit_native_samples
        and all(row["timing_gate_passed"] for row in rows)
    )
    morphology_passed = bool(
        minimum_correlation >= correlation_limit
        and all(row["morphology_gate_passed"] for row in rows)
    )
    return {
        "maximum_measured_profile_lag_native_samples": maximum_measured_lag,
        "minimum_peak_aligned_profile_correlation": minimum_correlation,
        "timing_gate_passed": timing_passed,
        "morphology_gate_passed": morphology_passed,
        "gallery_alignment_conclusion": (
            "robust_with_bounded_time_envelope"
            if timing_passed and morphology_passed
            else "not_robust_to_bound_endpoints"
        ),
    }


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
    source_start_sample: float,
    input_assumption: str = "nominal",
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
        input_dm_assumption=np.asarray(input_assumption),
    )
    return {
        "path": str(path),
        "sha256": sha256(path),
        "target_total_dm_pc_cm3": target_dm,
        "input_total_dm_pc_cm3": input_dm,
        "applied_residual_dm_pc_cm3": target_dm - input_dm,
        "input_dm_assumption": input_assumption,
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
    row_match = dsa_audit["row_match"]
    uncertainty_mode = "input_dsa_dm_method" in config
    if uncertainty_mode:
        audit_contract = dsa_audit.get("input_state_contract", {})
        for key, expected in (
            ("method", config["input_dsa_dm_method"]),
            ("bound_source", config["input_dsa_dm_bound_source"]),
            ("nominal_input_dm_pc_cm3", config["input_dsa_dm_pc_cm3"]),
            (
                "input_dm_half_width_pc_cm3",
                config["input_dsa_dm_half_width_pc_cm3"],
            ),
            (
                "reconstruction_sha256",
                config["expected_dsa_state_reconstruction_sha256"],
            ),
            (
                "reference_minus_raw_dm_interval_pc_cm3",
                config["reference_minus_raw_dsa_dm_interval_pc_cm3"],
            ),
        ):
            actual = audit_contract.get(key)
            if isinstance(expected, float):
                if actual is None or abs(float(actual) - expected) > 1.0e-12:
                    raise RuntimeError(f"DSA audit {key} differs from configuration")
            elif actual != expected:
                raise RuntimeError(f"DSA audit {key} differs from configuration")
        if (
            abs(
                float(state["inferred_reference_minus_raw_dm_pc_cm3"])
                - float(config["reference_minus_raw_dsa_dm_pc_cm3"])
            )
            > 1.0e-12
        ):
            raise RuntimeError("DSA audit residual differs from configuration")
        crop_start = float(
            config["raw_dsa_reference_frequency_crop_start_sample"]
        )
    else:
        if abs(float(state["inferred_reference_minus_raw_dm_pc_cm3"])) > float(
            gates["reference_minus_raw_dm_abs_max_pc_cm3"]
        ):
            raise RuntimeError("DSA raw/reference residual DM gate failed")
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
    if uncertainty_mode and abs(
        sample_time_s - float(config["expected_dsa_native_sample_time_s"])
    ) > 1.0e-15:
        raise RuntimeError("DSA native sample time differs from configuration")
    frequency_mhz = float(reader.header["fch1"]) + float(
        reader.header["foff"]
    ) * np.arange(int(reader.header["nchans"]))
    input_dm = float(
        config["input_dsa_dm_pc_cm3"]
        if uncertainty_mode
        else config["accepted_dsa_reference_dm_pc_cm3"]
    )
    window = int(config["dsa_crop_samples"])
    if reference.shape[1] != window:
        raise RuntimeError("accepted DSA crop length changed")

    output_dir.mkdir(parents=True, exist_ok=True)
    products = {}
    if uncertainty_mode:
        raw_reference_crop = apply_residual_dm_absolute_crop(
            raw,
            frequency_mhz,
            sample_time_s,
            0.0,
            crop_start,
            window,
        )
    else:
        padding = int(config["dsa_padding_samples"])
        source_start = crop_start - padding
        source_stop = crop_start + window + padding
        source = np.asarray(raw[:, source_start:source_stop], dtype=float)
        if source.shape != (reference.shape[0], window + 2 * padding):
            raise RuntimeError("DSA padded source crop is incomplete")
        raw_reference_crop = source[:, padding : padding + window]
    if not np.all(np.isfinite(raw_reference_crop[accepted_live])):
        raise RuntimeError("DSA raw input crop reached a filterbank edge")
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
        target_dm=float(config["accepted_dsa_reference_dm_pc_cm3"]),
        input_dm=input_dm,
        source_start_sample=crop_start,
        input_assumption="external_accepted_reference",
    )
    targets = {
        "anchor_dm": float(chime_result["hybrid_method"]["anchor_dm_pc_cm3"]),
        "hybrid_fit_dm": float(chime_result["grid"]["fit"]["dm_pc_cm3"]),
        "geometry_dm": float(config["geometry_dm_pc_cm3"]),
    }
    endpoint_review: dict[str, dict] = {}
    if uncertainty_mode:
        half_width = float(config["input_dsa_dm_half_width_pc_cm3"])
        input_assumptions = {
            "low": input_dm - half_width,
            "nominal": input_dm,
            "high": input_dm + half_width,
        }
        native_frequency_mhz = float(config["dsa_native_frequency_mhz"])
        reference_timing = reference_400_timing_half_width(
            half_width,
            native_frequency_mhz,
            sample_time_s,
        )
        reference_timing_half_width_ms = float(reference_timing["ms"])
        reference_timing_half_width_native_samples = float(
            reference_timing["native_samples"]
        )
        timing_limit = float(
            gates[
                "input_dm_reference_timing_half_width_max_native_samples"
            ]
        )
        correlation_limit = float(
            gates["input_dm_aligned_profile_correlation_min"]
        )
        correlation_search_lag = min(
            window // 4,
            max(
                8,
                int(np.ceil(reference_timing_half_width_native_samples)) + 8,
            ),
        )
        for label, target_dm in targets.items():
            endpoint_arrays = {}
            endpoint_review[label] = {}
            for assumption, assumed_input_dm in input_assumptions.items():
                corrected = apply_residual_dm_absolute_crop(
                    raw,
                    frequency_mhz,
                    sample_time_s,
                    target_dm - assumed_input_dm,
                    crop_start,
                    window,
                )
                if not np.all(np.isfinite(corrected[accepted_live])):
                    raise RuntimeError(
                        f"DSA {label}/{assumption} correction reached "
                        "the fixed-crop edge"
                    )
                endpoint_arrays[assumption] = corrected
                product_key = (
                    label
                    if assumption == "nominal"
                    else f"{label}_input_{assumption}"
                )
                products[product_key] = _write_product(
                    output_dir / f"dsa_{product_key}.npz",
                    waterfall=corrected,
                    frequency_mhz=frequency_mhz,
                    accepted_live=accepted_live,
                    sample_time_s=sample_time_s,
                    target_dm=target_dm,
                    input_dm=assumed_input_dm,
                    source_start_sample=crop_start,
                    input_assumption=assumption,
                )
            for assumption in ("low", "high"):
                metrics = aligned_profile_metrics(
                    endpoint_arrays["nominal"],
                    endpoint_arrays[assumption],
                    accepted_live,
                    maximum_lag_samples=correlation_search_lag,
                )
                delta_input_dm = (
                    input_assumptions[assumption] - input_assumptions["nominal"]
                )
                predicted_shift_ms = (
                    1000.0
                    * K_DM_S_MHZ2
                    * delta_input_dm
                    * (
                        REFERENCE_FREQUENCY_MHZ**-2
                        - native_frequency_mhz**-2
                    )
                )
                predicted_shift_samples = predicted_shift_ms / (
                    1000.0 * sample_time_s
                )
                endpoint_review[label][assumption] = {
                    "input_dm_pc_cm3": input_assumptions[assumption],
                    "predicted_400_mhz_timing_shift_ms": predicted_shift_ms,
                    "predicted_400_mhz_timing_shift_native_samples": (
                        predicted_shift_samples
                    ),
                    "measured_profile_lag_native_samples": int(
                        metrics["lag_samples"]
                    ),
                    "peak_aligned_profile_correlation": float(
                        metrics["correlation"]
                    ),
                    "timing_gate_passed": bool(
                        abs(predicted_shift_samples) <= timing_limit
                        and abs(int(metrics["lag_samples"])) <= timing_limit
                    ),
                    "morphology_gate_passed": bool(
                        float(metrics["correlation"]) >= correlation_limit
                    ),
                }
        endpoint_gate = endpoint_gate_summary(
            endpoint_review,
            predicted_timing_half_width_native_samples=(
                reference_timing_half_width_native_samples
            ),
            timing_limit_native_samples=timing_limit,
            correlation_limit=correlation_limit,
        )
        gallery_robust = (
            endpoint_gate["gallery_alignment_conclusion"]
            == "robust_with_bounded_time_envelope"
        )
        uncertainty_propagation = {
            "input_dm_method": config["input_dsa_dm_method"],
            "input_dm_bound_source": config["input_dsa_dm_bound_source"],
            "nominal_input_dm_pc_cm3": input_dm,
            "input_dm_half_width_pc_cm3": half_width,
            "input_dm_interval_pc_cm3": [
                input_dm - half_width,
                input_dm + half_width,
            ],
            "reference_minus_raw_dm_interval_pc_cm3": config[
                "reference_minus_raw_dsa_dm_interval_pc_cm3"
            ],
            "reference_400_timing_half_width_ms": (
                reference_timing_half_width_ms
            ),
            "reference_400_timing_half_width_native_samples": (
                reference_timing_half_width_native_samples
            ),
            "timing_half_width_max_native_samples": timing_limit,
            "minimum_peak_aligned_profile_correlation": (
                endpoint_gate["minimum_peak_aligned_profile_correlation"]
            ),
            "aligned_profile_correlation_min": correlation_limit,
            "maximum_measured_profile_lag_native_samples": (
                endpoint_gate[
                    "maximum_measured_profile_lag_native_samples"
                ]
            ),
            "timing_gate_passed": endpoint_gate["timing_gate_passed"],
            "morphology_gate_passed": endpoint_gate[
                "morphology_gate_passed"
            ],
            "gallery_alignment_conclusion": endpoint_gate[
                "gallery_alignment_conclusion"
            ],
            "endpoints": endpoint_review,
        }
        if (
            gates["gallery_alignment_must_be_robust"]
            and not gallery_robust
        ):
            raise RuntimeError(
                "DSA input-DM endpoint timing/morphology gate failed"
            )
    else:
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
        uncertainty_propagation = None

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
            "reference_frequency_crop_start_sample": crop_start,
        },
        "accepted_reference": {
            "path": str(reference_path),
            "sha256": expected_reference_sha256,
            "shape": list(reference.shape),
            "dm_pc_cm3": float(config["accepted_dsa_reference_dm_pc_cm3"]),
            "live_row_count": int(accepted_live.sum()),
            "dead_row_count": int((~accepted_live).sum()),
            "raw_crop_profile_correlation": _profile_correlation(
                raw_reference_crop,
                reference,
                accepted_live,
            ),
        },
        "input_state": {
            "nominal_input_total_dm_pc_cm3": input_dm,
            "input_dm_method": (
                config["input_dsa_dm_method"]
                if uncertainty_mode
                else "header_independent_legacy_exact_crop_audit"
            ),
            "input_dm_half_width_pc_cm3": (
                float(config["input_dsa_dm_half_width_pc_cm3"])
                if uncertainty_mode
                else 0.0
            ),
            "raw_state_claim": (
                dsa_audit["input_state_contract"]["raw_state_claim"]
                if uncertainty_mode
                else "raw total DM equals accepted product DM under legacy audit"
            ),
            "proof": (
                "bound v3 reconstruction artifact and endpoint propagation"
                if uncertainty_mode
                else (
                    f"{row_match['selected_count']} accepted-live rows all match "
                    f"raw start sample {crop_start}; frequency-dependent residual "
                    "fit passes the configured near-zero gate"
                )
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
            "rule": "target total DM minus each bound input-DM assumption once",
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
        **(
            {"uncertainty_propagation": uncertainty_propagation}
            if uncertainty_propagation is not None
            else {}
        ),
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
        legacy_stage_config(
            load_config(args.config, require_execution_authorized=True)
        ),
        json.loads(args.chime_result.read_text()),
        json.loads(args.dsa_audit.read_text()),
        args.output_dir,
    )
    print(
        f"{result['burst']} DSA: "
        f"input {result['input_state']['nominal_input_total_dm_pc_cm3']:.6f}; "
        "canonical absolute-DM products written",
        flush=True,
    )


if __name__ == "__main__":
    main()
