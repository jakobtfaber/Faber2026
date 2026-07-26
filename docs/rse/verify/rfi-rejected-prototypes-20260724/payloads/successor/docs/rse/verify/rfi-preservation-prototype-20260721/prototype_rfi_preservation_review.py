#!/usr/bin/env python3
"""Development-only known-truth review of the rejected CHIME RFI cleaner.

This script must never read observed burst intensity or sealed benchmark data.
It uses only hash-whitelisted frequency, support, bandpass, and audit-code files.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import platform
import shutil
import sys
import warnings
from pathlib import Path
from typing import Any

import numpy as np
from scipy.signal import find_peaks
from scipy.special import erfc


STATUS = "development_only_not_cleaner_validation"
SEED = 2026072101
K_DM_MS_GHZ2 = 4.148808
EXPECTED_INPUTS = {
    "products/zach_chime_freq.npy": "02c794745bd79ca235d1d3e18d46b2f43f7529616a5747ccab2a5db094a9cba2",
    "products/zach_chime_source_valid.npy": "b183f4aaed375ae78da8000cd5cb8bc3b8c4500c9ff23e56bb9555b0b85ba39e",
    "diagnostics/audit-v2/zach_bandpass_mean.npy": "472a58567d60221dd8fa2f91eb3fd855f7893cc28dff112b52c911c04900b753",
    "diagnostics/audit-v2/zach_bandpass_scale.npy": "e3082210b0ec2d49ed86517446f662b56f01ab14ec03b3903cb890cbaf30027c",
    "code/audit_chime_preprocessing_v2.py": "5df48f411c6d9f9ce59873b6ccb147de30e22fa8306b3543bb06632212340c83",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_inputs(root: Path) -> dict[str, str]:
    observed: dict[str, str] = {}
    for relative, expected in EXPECTED_INPUTS.items():
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f"input hash mismatch: {relative}: {actual} != {expected}")
        observed[relative] = actual
    return observed


def _emg(delta_ms: np.ndarray, sigma_ms: float, tau_ms: np.ndarray) -> np.ndarray:
    """Unnormalized exponentially modified Gaussian, evaluated stably."""
    tau = np.maximum(tau_ms, 1e-3)
    exponent = 0.5 * (sigma_ms / tau) ** 2 - delta_ms / tau
    argument = (sigma_ms / tau - delta_ms / sigma_ms) / math.sqrt(2.0)
    values = np.exp(np.clip(exponent, -80.0, 60.0)) * erfc(argument)
    return values


def _burst_signal(
    frequency_mhz: np.ndarray,
    source_valid: np.ndarray,
    ntime: int,
    dt_ms: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    nfreq = frequency_mhz.size
    signal = np.full((nfreq, ntime), np.nan, dtype=np.float32)
    t_ms = np.arange(ntime, dtype=np.float64) * dt_ms
    t0_ms = 0.50 * ntime * dt_ms
    separation_ms = min(6.0, 0.10 * ntime * dt_ms)
    sigma_ms = min(0.9, max(0.55, 0.012 * ntime * dt_ms))
    tau_1ghz_ms = 0.035
    dm_offset = 0.05
    gamma = -1.2
    amplitude = 2.8
    ratio = 0.68
    nu_ref_ghz = float(np.nanmax(frequency_mhz[source_valid]) / 1000.0)

    valid_indices = np.flatnonzero(source_valid)
    for start in range(0, valid_indices.size, 2048):
        indices = valid_indices[start : start + 2048]
        nu_ghz = frequency_mhz[indices, None] / 1000.0
        delay_ms = K_DM_MS_GHZ2 * dm_offset * (nu_ghz**-2 - nu_ref_ghz**-2)
        tau_ms = tau_1ghz_ms * nu_ghz**-4
        spectral = (nu_ghz / nu_ref_ghz) ** gamma
        spectral *= 1.0 + 0.18 * np.sin(2.0 * np.pi * (frequency_mhz[indices, None] - 400.0) / 47.0)
        first = _emg(t_ms[None, :] - t0_ms - delay_ms, sigma_ms, tau_ms)
        second = _emg(
            t_ms[None, :] - (t0_ms + separation_ms) - delay_ms,
            sigma_ms * 0.85,
            tau_ms,
        )
        combined = first + ratio * second
        peak = np.max(combined, axis=1, keepdims=True)
        combined /= np.maximum(peak, 1e-20)
        signal[indices] = (amplitude * spectral * combined).astype(np.float32)

    parameters = {
        "components": 2,
        "component_amplitude_ratio": ratio,
        "separation_ms": separation_ms,
        "t0_ms": t0_ms,
        "gaussian_sigma_ms": sigma_ms,
        "tau_1ghz_ms": tau_1ghz_ms,
        "dm_offset_pc_cm3": dm_offset,
        "spectral_index": gamma,
        "amplitude_standardized": amplitude,
    }
    return signal, parameters


def _add_component(
    values: np.ndarray,
    mask: np.ndarray,
    rows: np.ndarray,
    columns: np.ndarray,
    amplitude: float,
) -> None:
    if rows.size == 0 or columns.size == 0:
        return
    values[np.ix_(rows, columns)] += amplitude
    mask[np.ix_(rows, columns)] = True


def _synthetic_rfi(
    shape: tuple[int, int],
    source_valid: np.ndarray,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray], dict[str, Any]]:
    nfreq, ntime = shape
    values = np.zeros(shape, dtype=np.float32)
    masks = {
        name: np.zeros(shape, dtype=bool)
        for name in ("persistent_lines", "coarse_comb", "broadband_impulse", "drifting_line")
    }
    valid_rows = np.flatnonzero(source_valid)

    centers = valid_rows[np.linspace(0, valid_rows.size - 1, 10, dtype=int)]
    line_half_width = max(0, nfreq // 65536)
    line_rows = np.unique(
        np.concatenate(
            [np.arange(max(0, c - line_half_width), min(nfreq, c + line_half_width + 1)) for c in centers]
        )
    )
    line_rows = line_rows[source_valid[line_rows]]
    _add_component(values, masks["persistent_lines"], line_rows, np.arange(ntime), 17.0)

    spacing = max(4, nfreq // 1024)
    comb_rows = np.arange(spacing // 3, nfreq, spacing)
    comb_rows = comb_rows[source_valid[comb_rows]]
    comb_amplitude = 6.5 + rng.uniform(-0.5, 0.5, comb_rows.size)
    for row, amplitude in zip(comb_rows, comb_amplitude, strict=True):
        _add_component(
            values,
            masks["coarse_comb"],
            np.array([row]),
            np.arange(ntime),
            float(amplitude),
        )

    impulse_center = int(round(0.82 * (ntime - 1)))
    impulse_cols = np.arange(max(0, impulse_center - 1), min(ntime, impulse_center + 2))
    _add_component(values, masks["broadband_impulse"], valid_rows, impulse_cols, 9.0)

    drift_start = int(round(0.16 * ntime))
    drift_stop = int(round(0.70 * ntime))
    drift_half_width = max(1, nfreq // 65536)
    for column in range(drift_start, drift_stop):
        fraction = (column - drift_start) / max(1, drift_stop - drift_start - 1)
        center = int(round((0.82 - 0.64 * fraction) * (nfreq - 1)))
        rows = np.arange(max(0, center - drift_half_width), min(nfreq, center + drift_half_width + 1))
        rows = rows[source_valid[rows]]
        _add_component(values, masks["drifting_line"], rows, np.array([column]), 13.0)

    combined = np.logical_or.reduce(list(masks.values()))
    values[~source_valid] = np.nan
    for mask in masks.values():
        mask[~source_valid] = False
    parameters = {
        "persistent_line_rows": line_rows.tolist(),
        "persistent_line_amplitude_standardized": 17.0,
        "comb_spacing_rows": spacing,
        "comb_rows": comb_rows.tolist(),
        "comb_amplitude_standardized_range": [6.0, 7.0],
        "broadband_impulse_columns": impulse_cols.tolist(),
        "broadband_impulse_amplitude_standardized": 9.0,
        "drift_columns": [drift_start, drift_stop],
        "drift_amplitude_standardized": 13.0,
    }
    return values, combined, masks, parameters


def generate_case(
    frequency_mhz: np.ndarray,
    source_valid: np.ndarray,
    bandpass_mean: np.ndarray,
    bandpass_scale: np.ndarray,
    ntime: int,
    dt_ms: float,
    seed: int,
) -> dict[str, Any]:
    frequency_mhz = np.asarray(frequency_mhz, dtype=np.float64)
    source_valid = np.asarray(source_valid, dtype=bool).copy()
    mean = np.asarray(bandpass_mean, dtype=np.float64).copy()
    scale = np.asarray(bandpass_scale, dtype=np.float64).copy()
    if not (frequency_mhz.shape == source_valid.shape == mean.shape == scale.shape):
        raise ValueError("frequency, support, mean, and scale must share one shape")
    source_valid &= np.isfinite(frequency_mhz)
    if source_valid.sum() < 16:
        raise ValueError("insufficient valid channels")
    measured_bandpass = source_valid & np.isfinite(mean) & np.isfinite(scale) & (scale > 0)
    missing_bandpass = source_valid & ~measured_bandpass
    if measured_bandpass.sum() < 16:
        raise ValueError("insufficient finite development bandpass rows")
    row = np.arange(frequency_mhz.size)
    mean[missing_bandpass] = np.interp(
        row[missing_bandpass], row[measured_bandpass], mean[measured_bandpass]
    )
    scale[missing_bandpass] = np.interp(
        row[missing_bandpass], row[measured_bandpass], scale[measured_bandpass]
    )
    mean[~source_valid] = np.nan
    scale[~source_valid] = np.nan

    seed_sequence = np.random.SeedSequence(seed)
    noise_seed, rfi_seed, bootstrap_seed = seed_sequence.spawn(3)
    noise_rng = np.random.default_rng(noise_seed)
    rfi_rng = np.random.default_rng(rfi_seed)

    signal, burst_parameters = _burst_signal(frequency_mhz, source_valid, ntime, dt_ms)
    noise = np.full((frequency_mhz.size, ntime), np.nan, dtype=np.float32)
    noise[source_valid] = noise_rng.standard_normal((int(source_valid.sum()), ntime)).astype(np.float32)
    truth = noise + signal
    rfi_standardized, rfi_mask, component_masks, rfi_parameters = _synthetic_rfi(
        truth.shape, source_valid, rfi_rng
    )
    rfi_raw = (scale[:, None] * rfi_standardized).astype(np.float32)
    raw = (mean[:, None] + scale[:, None] * truth + rfi_raw).astype(np.float32)
    raw[~source_valid] = np.nan

    burst_start = int(round(0.40 * ntime))
    burst_stop = int(round(0.72 * ntime))
    parameters = {
        "seed": int(seed),
        "seed_entropy": seed_sequence.entropy,
        "seed_streams": {
            "noise": noise_seed.spawn_key,
            "rfi": rfi_seed.spawn_key,
            "measurement_bootstrap": bootstrap_seed.spawn_key,
        },
        "burst": burst_parameters,
        "rfi": rfi_parameters,
        "windows": {
            "training": [0, int(round(0.30 * ntime))],
            "burst": [burst_start, burst_stop],
            "display": [0, ntime],
        },
        "dt_ms": float(dt_ms),
        "bandpass_shape_interpolated_rows": int(missing_bandpass.sum()),
        "bandpass_shape_note": (
            "Development audit arrays contain cleaner-induced NaNs; values are row-index "
            "interpolated only to shape synthetic raw data and never redefine source support."
        ),
    }
    return {
        "frequency_mhz": frequency_mhz,
        "source_valid": source_valid,
        "truth": truth,
        "signal": signal,
        "raw": raw,
        "rfi": rfi_raw,
        "rfi_standardized": rfi_standardized,
        "rfi_mask": rfi_mask,
        "component_masks": component_masks,
        "parameters": parameters,
        "bandpass_mean": mean,
        "bandpass_scale": scale,
    }


def oracle_normalize(
    raw: np.ndarray,
    mean: np.ndarray,
    scale: np.ndarray,
    valid: np.ndarray,
) -> np.ndarray:
    result = np.full(np.asarray(raw).shape, np.nan, dtype=np.float64)
    use = np.asarray(valid, dtype=bool) & np.isfinite(mean) & np.isfinite(scale) & (scale > 0)
    result[use] = (np.asarray(raw)[use] - np.asarray(mean)[use, None]) / np.asarray(scale)[use, None]
    return result


def _load_audit(path: Path):
    spec = importlib.util.spec_from_file_location("exact_audit_v2", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_rejected_cleaner(
    raw: np.ndarray,
    source_valid: np.ndarray,
    training: tuple[int, int],
    audit_path: Path,
) -> dict[str, np.ndarray]:
    audit = _load_audit(audit_path)
    initial = audit._package_rfi_mask(
        raw,
        source_valid,
        training,
        threshold_mean=5.0,
        threshold_std=3.0,
    )
    rfi_valid = source_valid & ~initial
    mean, scale, model_valid = audit._bandpass_model(raw, rfi_valid, training)
    normalized = audit._normalize(raw, mean, scale, model_valid)
    post = audit._package_rfi_mask(
        normalized,
        model_valid,
        training,
        threshold_mean=5.0,
        threshold_std=3.0,
    )
    final_valid = model_valid & ~post
    cleaned = np.asarray(normalized, dtype=np.float32)
    cleaned[~final_valid] = np.nan
    return {
        "initial_rfi_rows": initial,
        "post_bandpass_rfi_rows": post,
        "bandpass_mean": mean,
        "bandpass_scale": scale,
        "final_valid": final_valid,
        "cleaned": cleaned,
    }


def mask_confusion(
    truth_mask: np.ndarray,
    predicted_rows: np.ndarray,
    valid_pixels: np.ndarray,
) -> dict[str, int]:
    truth = np.asarray(truth_mask, dtype=bool)
    valid = np.broadcast_to(np.asarray(valid_pixels, dtype=bool), truth.shape)
    predicted = np.broadcast_to(np.asarray(predicted_rows, dtype=bool)[:, None], truth.shape)
    return {
        "tp": int(np.sum(valid & truth & predicted)),
        "fp": int(np.sum(valid & ~truth & predicted)),
        "fn": int(np.sum(valid & truth & ~predicted)),
        "tn": int(np.sum(valid & ~truth & ~predicted)),
    }


def coarsen(
    values: np.ndarray,
    frequency_mhz: np.ndarray,
    row_valid: np.ndarray,
    factor: int = 64,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values = np.asarray(values, dtype=np.float64)
    frequency = np.asarray(frequency_mhz, dtype=np.float64)
    row_valid = np.asarray(row_valid, dtype=bool)
    if values.shape[0] % factor:
        raise ValueError("frequency dimension is not divisible by factor")
    ngroup = values.shape[0] // factor
    grouped = values.reshape(ngroup, factor, values.shape[1])
    valid_group = row_valid.reshape(ngroup, factor)
    finite = np.isfinite(grouped) & valid_group[:, :, None]
    counts_time = finite.sum(axis=1)
    sums = np.where(finite, grouped, 0.0).sum(axis=1)
    coarse = np.full((ngroup, values.shape[1]), np.nan, dtype=np.float64)
    np.divide(sums, counts_time, out=coarse, where=counts_time > 0)
    counts = valid_group.sum(axis=1)
    freq_values = frequency.reshape(ngroup, factor)
    freq_sum = np.where(valid_group, freq_values, 0.0).sum(axis=1)
    coarse_frequency = np.full(ngroup, np.nan, dtype=np.float64)
    np.divide(freq_sum, counts, out=coarse_frequency, where=counts > 0)
    return coarse, coarse_frequency, counts


def _profile(values: np.ndarray, valid_rows: np.ndarray, burst_start: int) -> np.ndarray:
    data = np.asarray(values, dtype=np.float64)
    valid = np.asarray(valid_rows, dtype=bool) & np.any(np.isfinite(data), axis=1)
    off_stop = max(4, min(burst_start // 2, data.shape[1] // 4))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        baseline = np.nanmedian(data[:, :off_stop], axis=1)
    corrected = data - baseline[:, None]
    with np.errstate(invalid="ignore"):
        return np.nanmean(corrected[valid], axis=0)


def _spectral_fluence(
    values: np.ndarray,
    valid_rows: np.ndarray,
    burst_window: tuple[int, int],
) -> np.ndarray:
    data = np.asarray(values, dtype=np.float64)
    valid = np.asarray(valid_rows, dtype=bool)
    b0, b1 = burst_window
    off_stop = max(4, min(b0 // 2, data.shape[1] // 4))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        baseline = np.nanmedian(data[:, :off_stop], axis=1)
    spectrum = np.nansum(data[:, b0:b1] - baseline[:, None], axis=1)
    spectrum[~valid] = np.nan
    return spectrum


def _component_peaks(profile: np.ndarray, dt_ms: float, window: tuple[int, int]) -> np.ndarray:
    b0, b1 = window
    section = np.asarray(profile[b0:b1], dtype=np.float64)
    section = np.nan_to_num(section, nan=0.0)
    distance = max(2, int(round(2.5 / dt_ms)))
    prominence = max(1e-8, 0.12 * float(np.max(section)))
    peaks, properties = find_peaks(section, distance=distance, prominence=prominence)
    if peaks.size > 2:
        order = np.argsort(properties["prominences"])[-2:]
        peaks = np.sort(peaks[order])
    return peaks + b0


def measure_summary(
    values: np.ndarray,
    frequency_mhz: np.ndarray,
    valid_rows: np.ndarray,
    dt_ms: float,
    burst_window: tuple[int, int],
    signal_template: np.ndarray,
) -> dict[str, float | int | None]:
    data = np.asarray(values, dtype=np.float64)
    frequency = np.asarray(frequency_mhz, dtype=np.float64)
    valid = np.asarray(valid_rows, dtype=bool) & np.isfinite(frequency)
    b0, b1 = burst_window
    profile = _profile(data, valid, b0)
    time_ms = np.arange(data.shape[1]) * dt_ms
    weights = np.clip(profile[b0:b1], 0.0, None)
    weight_sum = float(np.sum(weights))
    if weight_sum <= 0:
        raise ValueError("nonpositive burst-profile weight")
    arrival = float(np.sum(time_ms[b0:b1] * weights) / weight_sum)
    width = float(np.sqrt(np.sum(weights * (time_ms[b0:b1] - arrival) ** 2) / weight_sum))
    peaks = _component_peaks(profile, dt_ms, burst_window)
    separation = float((peaks[1] - peaks[0]) * dt_ms) if peaks.size == 2 else None

    off_stop = max(4, min(b0 // 2, data.shape[1] // 4))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        row_baseline = np.nanmedian(data[:, :off_stop], axis=1)
    row_corrected = data - row_baseline[:, None]
    row_centroids = np.full(data.shape[0], np.nan)
    for row in np.flatnonzero(valid):
        row_weights = np.clip(row_corrected[row, b0:b1], 0.0, None)
        total = np.sum(row_weights)
        if total > 0:
            row_centroids[row] = np.sum(time_ms[b0:b1] * row_weights) / total
    regression_rows = valid & np.isfinite(row_centroids)
    x = (frequency[regression_rows] / 1000.0) ** -2
    if x.size >= 8:
        x -= np.min(x)
        slope = np.polyfit(x, row_centroids[regression_rows], 1)[0]
        dm_offset = float(slope / K_DM_MS_GHZ2)
    else:
        dm_offset = None

    template = np.asarray(signal_template, dtype=np.float64)
    common = np.isfinite(row_corrected[:, b0:b1]) & np.isfinite(template[:, b0:b1]) & valid[:, None]
    if common.sum() >= 16:
        morphology = float(np.corrcoef(row_corrected[:, b0:b1][common], template[:, b0:b1][common])[0, 1])
        residual_norm = float(
            np.linalg.norm(row_corrected[:, b0:b1][common] - template[:, b0:b1][common])
            / max(np.linalg.norm(template[:, b0:b1][common]), 1e-12)
        )
    else:
        morphology = None
        residual_norm = None

    spectrum = _spectral_fluence(data, valid, burst_window)
    finite_spectrum = spectrum[valid & np.isfinite(spectrum)]
    modulation = float(np.std(finite_spectrum) / max(abs(np.mean(finite_spectrum)), 1e-12))
    centered = finite_spectrum - np.mean(finite_spectrum)
    acf = np.correlate(centered, centered, mode="full")[centered.size - 1 :]
    acf /= max(acf[0], 1e-20)
    below = np.flatnonzero(acf <= 0.5)
    spacing = float(np.nanmedian(np.abs(np.diff(frequency[valid])))) if valid.sum() > 1 else float("nan")
    acf_halfwidth = float(below[0] * spacing) if below.size else None

    if peaks.size:
        tail_start = int(peaks[-1])
        tail_weights = np.clip(profile[tail_start:b1], 0.0, None)
        tail_total = np.sum(tail_weights)
        tail_proxy = (
            float(np.sum((time_ms[tail_start:b1] - time_ms[tail_start]) * tail_weights) / tail_total)
            if tail_total > 0
            else None
        )
    else:
        tail_proxy = None

    return {
        "normalized_fluence_proxy": float(np.sum(profile[b0:b1]) * dt_ms),
        "arrival_time_ms": arrival,
        "width_ms": width,
        "component_count": int(peaks.size),
        "component_separation_ms": separation,
        "dm_offset_pc_cm3": dm_offset,
        "morphology_correlation": morphology,
        "normalized_residual": residual_norm,
        "tail_scale_proxy_ms": tail_proxy,
        "spectral_modulation_strength": modulation,
        "frequency_acf_halfwidth_mhz": acf_halfwidth,
    }


def broad_slice_fluence(
    values: np.ndarray,
    frequency_mhz: np.ndarray,
    valid_rows: np.ndarray,
    burst_window: tuple[int, int],
) -> tuple[list[str], list[float | None]]:
    spectrum = _spectral_fluence(values, valid_rows, burst_window)
    edges = np.arange(400.0, 800.0 + 50.0, 50.0)
    labels: list[str] = []
    output: list[float | None] = []
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        selection = (
            np.asarray(valid_rows, dtype=bool)
            & np.isfinite(frequency_mhz)
            & (frequency_mhz >= lo)
            & (frequency_mhz < hi + (1e-9 if hi == 800.0 else 0.0))
        )
        labels.append(f"{int(lo)}-{int(hi)}")
        output.append(float(np.nanmean(spectrum[selection])) if selection.any() else None)
    return labels, output


def bootstrap_uncertainties(
    signal_template: np.ndarray,
    frequency_mhz: np.ndarray,
    counts: np.ndarray,
    dt_ms: float,
    burst_window: tuple[int, int],
    seed: int,
    nrealizations: int = 48,
) -> dict[str, float | None]:
    valid = counts > 0
    rng = np.random.default_rng(np.random.SeedSequence(seed, spawn_key=(2,)))
    names: dict[str, list[float]] = {}
    noise_scale = np.full(counts.shape, np.nan, dtype=float)
    noise_scale[valid] = 1.0 / np.sqrt(counts[valid])
    for _ in range(nrealizations):
        noise = rng.normal(size=signal_template.shape) * noise_scale[:, None]
        realization = signal_template + noise
        measurement = measure_summary(
            realization,
            frequency_mhz,
            valid,
            dt_ms,
            burst_window,
            signal_template,
        )
        for name, value in measurement.items():
            if name == "component_count" or value is None or not np.isfinite(value):
                continue
            names.setdefault(name, []).append(float(value))
    return {
        name: (float(np.std(values, ddof=1)) if len(values) >= 3 else None)
        for name, values in names.items()
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, float):
        return None if not math.isfinite(value) else value
    return value


def _coarse_mask_rgb(
    source_valid: np.ndarray,
    truth_rfi: np.ndarray,
    predicted_rows: np.ndarray,
    factor: int = 64,
) -> np.ndarray:
    ncoarse = source_valid.size // factor
    source = source_valid.reshape(ncoarse, factor)
    truth = truth_rfi.reshape(ncoarse, factor, truth_rfi.shape[1])
    predicted = np.broadcast_to(predicted_rows[:, None], truth_rfi.shape).reshape(
        ncoarse, factor, truth_rfi.shape[1]
    )
    source_pixels = np.broadcast_to(source[:, :, None], truth.shape)
    denominator = np.maximum(source.sum(axis=1)[:, None], 1)
    tp = np.sum(source_pixels & truth & predicted, axis=1) / denominator
    fp = np.sum(source_pixels & ~truth & predicted, axis=1) / denominator
    fn = np.sum(source_pixels & truth & ~predicted, axis=1) / denominator
    saturation = 0.10
    weights = np.stack([fn, fp, tp], axis=-1) / saturation
    total = np.sum(weights, axis=-1, keepdims=True)
    weights /= np.maximum(total, 1.0)
    colors = np.array(
        [
            [0.85, 0.37, 0.01],  # false negative: orange
            [0.46, 0.44, 0.70],  # false positive: purple
            [0.10, 0.62, 0.47],  # true positive: green
        ]
    )
    rgb = 1.0 - np.sum(weights, axis=-1, keepdims=True) + np.einsum("...k,kc->...c", weights, colors)
    rgb = np.clip(rgb, 0.0, 1.0)
    rgb[~np.any(source, axis=1), :, :] = 0.72
    return rgb


def make_figure(
    path: Path,
    case: dict[str, Any],
    cleaned: dict[str, np.ndarray],
    measurements: dict[str, Any],
    slices: dict[str, Any],
) -> None:
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    mpl.rcParams.update(
        {
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "legend.fontsize": 8,
            "svg.hashsalt": "faber2026-rfi-preservation-prototype",
        }
    )
    freq = case["frequency_mhz"]
    source_valid = case["source_valid"]
    final_valid = cleaned["final_valid"]
    truth_coarse, coarse_freq, _ = coarsen(case["truth"], freq, source_valid)
    contaminated = oracle_normalize(
        case["raw"],
        case["bandpass_mean"],
        case["bandpass_scale"],
        source_valid,
    )
    contaminated_coarse = coarsen(contaminated, freq, source_valid)[0]
    cleaned_coarse = coarsen(cleaned["cleaned"], freq, final_valid)[0]
    truth_common = coarsen(case["truth"], freq, final_valid)[0]
    residual = cleaned_coarse - truth_common
    dt_ms = case["parameters"]["dt_ms"]
    time_ms = np.arange(truth_coarse.shape[1]) * dt_ms
    extent = [time_ms[0], time_ms[-1] + dt_ms, float(np.nanmin(coarse_freq)), float(np.nanmax(coarse_freq))]
    finite_truth = truth_coarse[np.isfinite(truth_coarse)]
    limit = max(4.0, float(np.percentile(np.abs(finite_truth), 99.7)))
    cmap = mpl.colormaps["RdBu_r"].copy()
    cmap.set_bad("0.78")

    fig = plt.figure(figsize=(18, 10), constrained_layout=True)
    grid = fig.add_gridspec(2, 4, height_ratios=[1.05, 0.85])
    top_data = [
        (truth_coarse, "Known truth: noise + two-component burst"),
        (contaminated_coarse, "Truth + known synthetic RFI"),
        (cleaned_coarse, "Rejected cleaner output"),
        (residual, "Cleaner output − truth on common support"),
    ]
    images = []
    for column, (data, title) in enumerate(top_data):
        ax = fig.add_subplot(grid[0, column])
        image = ax.imshow(
            np.ma.masked_invalid(data),
            aspect="auto",
            origin="upper",
            extent=extent,
            cmap=cmap,
            vmin=-limit,
            vmax=limit,
            interpolation="nearest",
        )
        images.append(image)
        ax.set_title(title)
        ax.set_xlabel("Time (ms)")
        if column == 0:
            ax.set_ylabel("Frequency (MHz)")
        burst = case["parameters"]["windows"]["burst"]
        ax.axvspan(burst[0] * dt_ms, burst[1] * dt_ms, color="gold", alpha=0.08)
    fig.colorbar(images[0], ax=[fig.axes[i] for i in range(4)], shrink=0.75, label="Standardized intensity")

    predicted_rows = source_valid & ~final_valid
    mask_rgb = _coarse_mask_rgb(source_valid, case["rfi_mask"], predicted_rows)
    ax_mask = fig.add_subplot(grid[1, 0])
    ax_mask.imshow(
        mask_rgb,
        aspect="auto",
        origin="upper",
        extent=extent,
        interpolation="nearest",
    )
    ax_mask.set_title("Mask outcome")
    ax_mask.set_xlabel("Time (ms)")
    ax_mask.set_ylabel("Frequency (MHz)")
    legend_text = (
        "white clean   gray missing   orange false negative\n"
        "purple false positive   green true positive; saturation reaches full color at 10% of fine rows"
    )
    ax_mask.text(
        0.01,
        0.01,
        legend_text,
        transform=ax_mask.transAxes,
        va="bottom",
        fontsize=6.5,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 2.0},
    )

    ax_profile = fig.add_subplot(grid[1, 1])
    burst_start = case["parameters"]["windows"]["burst"][0]
    truth_profile = _profile(truth_coarse, np.isfinite(coarse_freq), burst_start)
    retained_profile = _profile(truth_common, np.any(np.isfinite(truth_common), axis=1), burst_start)
    cleaned_profile = _profile(cleaned_coarse, np.any(np.isfinite(cleaned_coarse), axis=1), burst_start)
    ax_profile.plot(time_ms, truth_profile, label="truth, full support", lw=1.0)
    ax_profile.plot(time_ms, retained_profile, label="truth, retained support", lw=1.0)
    ax_profile.plot(time_ms, cleaned_profile, label="cleaned, retained support", lw=1.0)
    burst = case["parameters"]["windows"]["burst"]
    ax_profile.axvspan(burst[0] * dt_ms, burst[1] * dt_ms, color="gold", alpha=0.12)
    ax_profile.set_title("Frequency-averaged time profile")
    ax_profile.set_xlabel("Time (ms)")
    ax_profile.set_ylabel("Standardized intensity")
    ax_profile.legend(frameon=False)

    ax_slices = fig.add_subplot(grid[1, 2])
    labels = slices["labels"]
    x = np.arange(len(labels))
    width = 0.26
    for offset, key, label in (
        (-width, "truth_full", "truth, full support"),
        (0.0, "truth_retained", "truth, retained support"),
        (width, "cleaned_retained", "cleaned, retained support"),
    ):
        values = np.array([np.nan if value is None else value for value in slices[key]], dtype=float)
        ax_slices.bar(x + offset, values, width=width, label=label)
    ax_slices.set_xticks(x, labels, rotation=45, ha="right")
    ax_slices.set_title("Fluence proxy by fixed 50-MHz slice")
    ax_slices.set_xlabel("Frequency (MHz)")
    ax_slices.set_ylabel("Mean normalized fluence proxy")
    ax_slices.legend(frameon=False)

    ax_table = fig.add_subplot(grid[1, 3])
    ax_table.axis("off")
    lines = [
        "Tentative single-case limit: |shift| ≤ 1 measurement uncertainty",
        "Distribution limits (median, 95th percentile): not exercised here",
        "",
    ]
    display_names = {
        "normalized_fluence_proxy": "total fluence proxy",
        "arrival_time_ms": "arrival time",
        "width_ms": "profile width",
        "component_separation_ms": "component separation",
        "dm_offset_pc_cm3": "dispersion measure offset",
        "morphology_correlation": "2D morphology correlation",
        "tail_scale_proxy_ms": "tail-scale proxy",
        "spectral_modulation_strength": "spectral modulation",
        "frequency_acf_halfwidth_mhz": "frequency ACF half-width",
    }
    for name, label in display_names.items():
        effect = measurements["effects"].get(name, {})
        z = effect.get("absolute_shift_sigma")
        status = effect.get("status", "not exercised")
        relative = effect.get("relative_shift_percent")
        relative_text = "" if relative is None else f" ({relative:+.2f}%)"
        z_text = "n/a" if z is None else f"{z:.2f}σ{relative_text}"
        lines.append(f"{label}: {z_text} — {status}")
    stable = measurements["component_count_stable"]
    lines.extend(
        [
            f"component count stable: {'yes' if stable else 'no'}",
            "",
            f"retained source rows: {measurements['retained_row_fraction']:.1%}",
            f"RFI pixel recall: {measurements['mask']['pixel_recall']:.1%}",
            f"RFI pixel precision: {measurements['mask']['pixel_precision']:.1%}",
            "",
            "DEVELOPMENT ONLY — this does not validate a cleaner",
        ]
    )
    ax_table.text(0.0, 1.0, "\n".join(lines), va="top", family="monospace", fontsize=8)

    fig.savefig(path, format="svg", metadata={"Date": None, "Creator": "Faber2026 controlled RFI prototype"})
    plt.close(fig)
    svg_text = path.read_text()
    path.write_text("\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n")


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_root = args.input_root.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(output_dir)
    verified_inputs = verify_inputs(input_root)
    output_dir.mkdir(parents=True, exist_ok=False)

    frequency = np.load(input_root / "products/zach_chime_freq.npy")
    source_valid = np.load(input_root / "products/zach_chime_source_valid.npy").astype(bool)
    bandpass_mean = np.load(input_root / "diagnostics/audit-v2/zach_bandpass_mean.npy")
    bandpass_scale = np.load(input_root / "diagnostics/audit-v2/zach_bandpass_scale.npy")
    case = generate_case(
        frequency,
        source_valid,
        bandpass_mean,
        bandpass_scale,
        args.ntime,
        args.dt_ms,
        args.seed,
    )
    training = tuple(case["parameters"]["windows"]["training"])
    cleaned = run_rejected_cleaner(
        case["raw"],
        case["source_valid"],
        training,
        input_root / "code/audit_chime_preprocessing_v2.py",
    )

    final_valid = cleaned["final_valid"]
    predicted_rows = case["source_valid"] & ~final_valid
    valid_pixels = np.broadcast_to(case["source_valid"][:, None], case["rfi_mask"].shape)
    confusion = mask_confusion(case["rfi_mask"], predicted_rows, valid_pixels)
    precision = confusion["tp"] / max(confusion["tp"] + confusion["fp"], 1)
    recall = confusion["tp"] / max(confusion["tp"] + confusion["fn"], 1)

    truth_full, coarse_frequency, full_counts = coarsen(
        case["truth"], frequency, case["source_valid"]
    )
    truth_common, _, retained_counts = coarsen(case["truth"], frequency, final_valid)
    cleaned_common, _, _ = coarsen(cleaned["cleaned"], frequency, final_valid)
    signal_common, _, _ = coarsen(case["signal"], frequency, final_valid)
    burst_window = tuple(case["parameters"]["windows"]["burst"])
    full_measurements = measure_summary(
        truth_full,
        coarse_frequency,
        full_counts > 0,
        args.dt_ms,
        burst_window,
        coarsen(case["signal"], frequency, case["source_valid"])[0],
    )
    truth_measurements = measure_summary(
        truth_common,
        coarse_frequency,
        retained_counts > 0,
        args.dt_ms,
        burst_window,
        signal_common,
    )
    cleaned_measurements = measure_summary(
        cleaned_common,
        coarse_frequency,
        retained_counts > 0,
        args.dt_ms,
        burst_window,
        signal_common,
    )
    uncertainties = bootstrap_uncertainties(
        signal_common,
        coarse_frequency,
        retained_counts,
        args.dt_ms,
        burst_window,
        args.seed,
    )
    effects: dict[str, Any] = {}
    for name, truth_value in truth_measurements.items():
        cleaned_value = cleaned_measurements.get(name)
        uncertainty = uncertainties.get(name)
        if name == "component_count":
            continue
        if truth_value is None or cleaned_value is None or uncertainty is None or uncertainty <= 0:
            effects[name] = {"absolute_shift_sigma": None, "status": "not exercised"}
            continue
        z = abs(float(cleaned_value) - float(truth_value)) / uncertainty
        effects[name] = {
            "absolute_shift_sigma": z,
            "relative_shift_percent": (
                100.0 * (float(cleaned_value) - float(truth_value)) / float(truth_value)
                if float(truth_value) != 0.0
                else None
            ),
            "status": "within proposed bound" if z <= 1.0 else "outside proposed bound",
        }

    labels, slice_full = broad_slice_fluence(
        truth_full, coarse_frequency, full_counts > 0, burst_window
    )
    _, slice_retained = broad_slice_fluence(
        truth_common, coarse_frequency, retained_counts > 0, burst_window
    )
    _, slice_cleaned = broad_slice_fluence(
        cleaned_common, coarse_frequency, retained_counts > 0, burst_window
    )
    slices = {
        "labels": labels,
        "truth_full": slice_full,
        "truth_retained": slice_retained,
        "cleaned_retained": slice_cleaned,
    }
    measurement_record = {
        "truth_full_support": full_measurements,
        "truth_common_support": truth_measurements,
        "cleaned_common_support": cleaned_measurements,
        "bootstrap_uncertainty": uncertainties,
        "effects": effects,
        "component_count_stable": (
            truth_measurements["component_count"] == cleaned_measurements["component_count"]
        ),
        "retained_row_fraction": float(final_valid.sum() / max(case["source_valid"].sum(), 1)),
        "mask": {
            "counts": confusion,
            "pixel_precision": precision,
            "pixel_recall": recall,
        },
    }

    svg_path = output_dir / "rfi_preservation_review.svg"
    make_figure(svg_path, case, cleaned, measurement_record, slices)
    script_copy = output_dir / Path(__file__).name
    shutil.copy2(Path(__file__).resolve(), script_copy)
    record = {
        "status": STATUS,
        "warning": "One controlled development example; distribution limits and cleaner validation are not exercised.",
        "provenance": {
            "input_hashes": verified_inputs,
            "pipeline_revision": args.pipeline_revision,
            "script_sha256": sha256(script_copy),
            "container_digest": args.container_digest,
            "container_image_id": args.container_image_id,
            "python": platform.python_version(),
            "numpy": np.__version__,
            "command": (
                "python /work/prototype_rfi_preservation_review.py "
                "--input-root /evidence --output-dir /output/run --ntime 512 "
                "--dt-ms 0.32768 --seed 2026072101"
            ),
        },
        "grid": {
            "nominal_fine_positions": int(frequency.size),
            "source_valid_positions": int(case["source_valid"].sum()),
            "cleaner_retained_positions": int(final_valid.sum()),
            "nominal_coarse_channels": int(frequency.size // 64),
            "dt_ms": args.dt_ms,
        },
        "parameters": case["parameters"],
        "cleaner": {
            "function": "baseband_analysis.core.flagging.get_RFI_channels",
            "threshold_mean": 5.0,
            "threshold_standard_deviation": 3.0,
            "order": ["package RFI", "learn mean and scale", "normalize", "package RFI"],
            "initial_rejected_rows": int(cleaned["initial_rfi_rows"].sum()),
            "post_bandpass_rejected_rows": int(cleaned["post_bandpass_rfi_rows"].sum()),
        },
        "measurements": measurement_record,
        "broad_frequency_slice_fluence": slices,
        "tentative_limits": {
            "interference_free_median_shift_sigma": 0.25,
            "interference_free_95_percent_shift_sigma": 0.5,
            "single_example_max_shift_sigma": 1.0,
            "contaminated_fraction_within_one_sigma": 0.95,
            "median_systematic_offset_sigma": 0.25,
            "distribution_limits_status": "not_exercised_by_one_example",
        },
        "outputs": {"figure_sha256": sha256(svg_path)},
    }
    json_path = output_dir / "rfi_preservation_review.json"
    json_path.write_text(json.dumps(_json_safe(record), indent=2, sort_keys=True) + "\n")
    checksum_path = output_dir / "SHA256SUMS"
    checksum_lines = [
        f"{sha256(path)}  {path.name}"
        for path in (svg_path, json_path, script_copy)
    ]
    checksum_path.write_text("\n".join(checksum_lines) + "\n")
    return record


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--ntime", type=int, default=512)
    parser.add_argument("--dt-ms", type=float, default=0.32768)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--pipeline-revision", default="ab6af1f713496abd2ff2d71bf11edf4100871e94")
    parser.add_argument(
        "--container-digest",
        default="chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41",
    )
    parser.add_argument(
        "--container-image-id",
        default="sha256:8c903ec6a5a836e8a97fe3468fd3ee02177c220ead84e6d1d25e8f41b735db4b",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
