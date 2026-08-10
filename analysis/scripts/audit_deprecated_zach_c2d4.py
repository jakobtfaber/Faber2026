#!/usr/bin/env python3
"""Reconstruct the deprecated Zach C2D4 failure from producing artifacts."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import sys
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ArtifactBundle:
    fit: Path
    samples: Path
    model: Path
    comparison_fit: Path
    comparison_model: Path
    stdout_log: Path
    stderr_log: Path
    review_manifest: Path | None = None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def array_sha256(array: np.ndarray) -> str:
    canonical = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(canonical.dtype.str.encode("ascii"))
    digest.update(json.dumps(canonical.shape).encode("ascii"))
    digest.update(canonical.tobytes())
    return digest.hexdigest()


def weighted_quantiles(
    values: np.ndarray, weights: np.ndarray, probabilities: tuple[float, ...]
) -> list[float]:
    order = np.argsort(values)
    sorted_values = np.asarray(values, dtype=float)[order]
    cumulative = np.cumsum(np.asarray(weights, dtype=float)[order])
    cumulative /= cumulative[-1]
    return [
        float(sorted_values[np.searchsorted(cumulative, probability)])
        for probability in probabilities
    ]


def posterior_scale(summary: dict[str, Any]) -> float:
    return 0.5 * (float(summary["err_minus"]) + float(summary["err_plus"]))


def sigma_separation(left: dict[str, Any], right: dict[str, Any]) -> float:
    denominator = np.hypot(posterior_scale(left), posterior_scale(right))
    if denominator == 0:
        return 0.0 if left["median"] == right["median"] else float("inf")
    return float(abs(float(left["median"]) - float(right["median"])) / denominator)


def parse_log_header(path: Path) -> dict[str, Any]:
    first_line = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    match = re.search(
        r"HOST=(?P<host>\S+) JOB=(?P<job>\d+) START=(?P<start>\S+) "
        r"BURST=(?P<burst>\S+) NLIVE=(?P<nlive>\d+) NPROC=(?P<nproc>\d+) "
        r"EARGS=\[(?P<extra_args>.*)\] MAXCH=(?P<max_channels>\S+) "
        r"SNRT=(?P<snr_target>\S+)",
        first_line,
    )
    if not match:
        raise ValueError(f"unrecognized fit log header: {first_line}")
    parsed = match.groupdict()
    for name in ("job", "nlive", "nproc"):
        parsed[name] = int(parsed[name])
    return parsed


def load_samples(path: Path) -> tuple[list[str], np.ndarray, np.ndarray]:
    with np.load(path, allow_pickle=True) as sample_file:
        names = [str(name) for name in sample_file["param_names"]]
        samples = np.asarray(sample_file["samples"], dtype=float)
        weights = np.asarray(sample_file["weights"], dtype=float)
    if samples.shape != (weights.size, len(names)):
        raise ValueError("posterior sample dimensions do not match names/weights")
    if not np.isclose(weights.sum(), 1.0, rtol=0.0, atol=1e-12):
        raise ValueError("posterior weights do not sum to one")
    return names, samples, weights


def load_model(path: Path) -> dict[str, np.ndarray]:
    with np.load(path, allow_pickle=True) as model_file:
        return {name: np.asarray(model_file[name]).copy() for name in model_file.files}


def expected_component_parameters(components_c: int, components_d: int) -> list[str]:
    return [
        parameter
        for band, count in (("C", components_c), ("D", components_d))
        for index in range(1, count + 1)
        for parameter in (f"t0_{band}{index}", f"zeta_{band}{index}")
    ]


def verify_component_identity(
    *,
    fit: dict[str, Any],
    sample_names: list[str],
    model: dict[str, np.ndarray],
    artifacts: ArtifactBundle,
) -> dict[str, Any]:
    fit_counts = [int(fit["components_C"]), int(fit["components_D"])]
    required_parameters = expected_component_parameters(*fit_counts)
    sample_missing = sorted(set(required_parameters) - set(sample_names))
    sample_extras = sorted(
        name
        for name in sample_names
        if re.fullmatch(r"(?:t0|zeta)_[CD]\d+", name)
        and name not in required_parameters
    )
    sample_duplicates = sorted(
        name for name in set(sample_names) if sample_names.count(name) > 1
    )
    sample_counts = [
        sum(name.startswith(f"t0_{band}") for name in sample_names)
        for band in ("C", "D")
    ]
    model_counts = [int(model["nC"]), int(model["nD"])]
    artifact_labels_match = bool(
        fit.get("burst") == "zach" and str(model.get("burst")) == "zach"
    )

    review_counts = None
    review_hashes_match = False
    if artifacts.review_manifest is not None:
        review = json.loads(artifacts.review_manifest.read_text(encoding="utf-8"))
        review_counts = [int(review["components_C"]), int(review["components_D"])]
        review_hashes_match = bool(
            review.get("fit_sha256") == sha256(artifacts.fit)
            and review.get("samples_sha256") == sha256(artifacts.samples)
            and review.get("model_grid_sha256") == sha256(artifacts.model)
        )

    component_structure_matches = bool(
        not sample_missing
        and not sample_extras
        and not sample_duplicates
        and fit_counts == sample_counts == model_counts
        and artifact_labels_match
    )
    complete = bool(
        component_structure_matches
        and review_counts == fit_counts
        and review_hashes_match
    )
    return {
        "fit_counts_C_D": fit_counts,
        "sample_counts_C_D": sample_counts,
        "model_grid_counts_C_D": model_counts,
        "review_manifest_counts_C_D": review_counts,
        "sample_missing_component_parameters": sample_missing,
        "sample_extra_component_parameters": sample_extras,
        "sample_duplicate_parameters": sample_duplicates,
        "artifact_labels_match": artifact_labels_match,
        "component_structure_matches": component_structure_matches,
        "review_manifest_hashes_match": review_hashes_match,
        "content_identity_complete_across_review_manifest": complete,
    }


def reconstruct_component_diagnostics(
    *,
    fit: dict[str, Any],
    names: list[str],
    samples: np.ndarray,
    weights: np.ndarray,
    model: dict[str, np.ndarray],
    broad_width_ratio: float,
    low_fluence_fraction: float,
) -> tuple[dict[str, Any], dict[str, list[float]]]:
    components_c = int(fit["components_C"])
    components_d = int(fit["components_D"])
    parameters = expected_component_parameters(components_c, components_d)
    quantiles: dict[str, list[float]] = {}
    for name in parameters:
        if name not in names:
            raise ValueError(f"posterior samples lack parameter: {name}")
        quantiles[name] = weighted_quantiles(
            samples[:, names.index(name)], weights, (0.16, 0.50, 0.84)
        )
        recorded = fit["percentiles"][name]
        expected = [recorded["lower"], recorded["median"], recorded["upper"]]
        if not np.array_equal(np.asarray(quantiles[name]), np.asarray(expected)):
            raise ValueError(f"sample-derived {name} quantiles disagree with fit")

    by_band: dict[str, Any] = {}
    for band, count in (("C", components_c), ("D", components_d)):
        time = np.asarray(model[f"time{band}"], dtype=float)
        fluence = np.asarray(model[f"fluence{band}"], dtype=float)
        if fluence.shape != (count,):
            raise ValueError(f"unexpected {band} fluence vector shape")
        span = float(np.ptp(time))
        fractions = fluence / fluence.sum()
        rows = []
        for index in range(1, count + 1):
            arrival = quantiles[f"t0_{band}{index}"][1]
            arrival_interval = quantiles[f"t0_{band}{index}"]
            width = quantiles[f"zeta_{band}{index}"][1]
            ratio = float(width / span)
            fraction = float(fractions[index - 1])
            rows.append(
                {
                    "component": index,
                    "arrival_quantiles_ms": quantiles[f"t0_{band}{index}"],
                    "width_quantiles_ms": quantiles[f"zeta_{band}{index}"],
                    "arrival_median_inside_window": bool(
                        float(time.min()) <= arrival <= float(time.max())
                    ),
                    "arrival_16_84_interval_inside_window": bool(
                        float(time.min()) <= arrival_interval[0]
                        and arrival_interval[2] <= float(time.max())
                    ),
                    "width_to_window_ratio": ratio,
                    "modeled_fluence": float(fluence[index - 1]),
                    "modeled_fluence_fraction": fraction,
                    "broad_vs_window": bool(ratio >= broad_width_ratio),
                    "low_fluence": bool(fraction <= low_fluence_fraction),
                    "broad_low_fluence_pedestal": bool(
                        ratio >= broad_width_ratio and fraction <= low_fluence_fraction
                    ),
                }
            )
        by_band[band] = {
            "fitted_window_ms": [float(time.min()), float(time.max())],
            "fitted_window_span_ms": span,
            "components": rows,
        }
    return by_band, quantiles


def residual_morphology(model: dict[str, np.ndarray], band: str) -> dict[str, Any]:
    data = np.asarray(model[f"data{band}"], dtype=float)
    prediction = np.asarray(model[f"model{band}"], dtype=float)
    noise = np.asarray(model[f"noise{band}"], dtype=float)
    valid = np.asarray(model[f"valid{band}"], dtype=bool)
    if data.shape != prediction.shape or data.shape[0] != noise.size:
        raise ValueError(f"{band} residual arrays have incompatible shapes")
    if not valid.any() or np.any(noise[valid] <= 0):
        raise ValueError(
            f"{band} residual arrays have no valid positive-noise channels"
        )

    normalized = (data[valid] - prediction[valid]) / noise[valid, None]
    profile = normalized.sum(axis=0) / np.sqrt(normalized.shape[0])
    if profile.size > 1 and np.std(profile[:-1]) > 0 and np.std(profile[1:]) > 0:
        lag1 = float(np.corrcoef(profile[:-1], profile[1:])[0, 1])
    else:
        lag1 = 0.0
    peak_index = int(np.argmax(np.abs(profile)))
    time = np.asarray(model[f"time{band}"], dtype=float)
    return {
        "recorded_reduced_residual_statistic": float(model[f"chi2{band}"]),
        "normalized_map_shape": list(normalized.shape),
        "normalized_map_sha256": array_sha256(normalized.astype("<f8")),
        "normalized_map_mean": float(normalized.mean()),
        "normalized_map_std": float(normalized.std()),
        "normalized_map_max_abs": float(np.max(np.abs(normalized))),
        "band_summed_profile_sha256": array_sha256(profile.astype("<f8")),
        "band_summed_profile_mean": float(profile.mean()),
        "band_summed_profile_std": float(profile.std()),
        "band_summed_profile_max_abs": float(abs(profile[peak_index])),
        "band_summed_profile_peak_time_ms": float(time[peak_index]),
        "band_summed_profile_lag1_correlation": lag1,
        "profile_samples_over_abs_3": int(np.sum(np.abs(profile) > 3.0)),
    }


def supports_match(
    left: dict[str, np.ndarray], right: dict[str, np.ndarray]
) -> dict[str, bool]:
    return {
        name: bool(np.array_equal(left[name], right[name]))
        for name in (
            "timeC",
            "freqC",
            "timeD",
            "freqD",
            "dataC",
            "dataD",
            "noiseC",
            "noiseD",
            "validC",
            "validD",
        )
    }


def evidence_assessment(
    *,
    fit: dict[str, Any],
    comparison_fit: dict[str, Any],
    model: dict[str, np.ndarray],
    comparison_model: dict[str, np.ndarray],
) -> dict[str, Any]:
    support = supports_match(model, comparison_model)
    recorded_fields_match = bool(
        fit.get("gain_s2") == comparison_fit.get("gain_s2")
        and fit.get("beta_bounds") == comparison_fit.get("beta_bounds")
        and fit.get("components_C") == comparison_fit.get("components_C")
        and fit.get("components_D") == comparison_fit.get("components_D") + 1
    )
    reasons = [
        "job-time likelihood source identity was not recorded",
        "the fit driver was untracked in a dirty worktree",
        "similar beta/tau marginals do not prove posterior-mode identity",
    ]
    if not all(support.values()):
        reasons.append("fitted data/support arrays differ")
    return {
        "recorded_configuration_fields_match": recorded_fields_match,
        "fitted_support_and_data_match": support,
        "common_parameter_sigma_separation_diagnostic_only": {
            "beta": sigma_separation(fit["beta"], comparison_fit["beta"]),
            "tau_1ghz": sigma_separation(fit["tau_1ghz"], comparison_fit["tau_1ghz"]),
        },
        "likelihood_identity": "unproven",
        "posterior_mode_identity": "unproven",
        "comparison_admissible": False,
        "rejection_reasons": reasons,
        "raw_log_evidence_C2D4_minus_C2D3_diagnostic_only": float(
            fit["log_evidence"] - comparison_fit["log_evidence"]
        ),
    }


def audit(
    artifacts: ArtifactBundle,
    *,
    broad_width_ratio: float = 5.0,
    low_fluence_fraction: float = 0.05,
) -> dict[str, Any]:
    fit = json.loads(artifacts.fit.read_text(encoding="utf-8"))
    comparison_fit = json.loads(artifacts.comparison_fit.read_text(encoding="utf-8"))
    if (fit.get("components_C"), fit.get("components_D")) != (2, 4):
        raise ValueError("deprecated fit is not C2D4")
    if (
        comparison_fit.get("components_C"),
        comparison_fit.get("components_D"),
    ) != (2, 3):
        raise ValueError("comparison fit is not C2D3")

    names, samples, weights = load_samples(artifacts.samples)
    model = load_model(artifacts.model)
    comparison_model = load_model(artifacts.comparison_model)
    identity = verify_component_identity(
        fit=fit,
        sample_names=names,
        model=model,
        artifacts=artifacts,
    )
    if not identity["component_structure_matches"]:
        raise ValueError("component identity mismatch across fit, samples, and model")

    components, quantiles = reconstruct_component_diagnostics(
        fit=fit,
        names=names,
        samples=samples,
        weights=weights,
        model=model,
        broad_width_ratio=broad_width_ratio,
        low_fluence_fraction=low_fluence_fraction,
    )
    fourth = components["D"]["components"][3]
    residuals = {
        "C2D4": {band: residual_morphology(model, band) for band in ("C", "D")},
        "C2D3_comparison": {
            band: residual_morphology(comparison_model, band) for band in ("C", "D")
        },
    }

    paths = {
        "fit": artifacts.fit,
        "samples": artifacts.samples,
        "model_grid": artifacts.model,
        "comparison_fit": artifacts.comparison_fit,
        "comparison_model_grid": artifacts.comparison_model,
        "stdout_log": artifacts.stdout_log,
        "stderr_log": artifacts.stderr_log,
    }
    if artifacts.review_manifest is not None:
        paths["review_manifest"] = artifacts.review_manifest

    return {
        "schema": "faber2026-deprecated-joint-fit-audit/v2",
        "subject": {
            "burst": "zach",
            "tns": "FRB 20220207C",
            "model": "C2D4",
            "disposition": "deprecated_reject",
        },
        "artifacts": {
            name: {"name": path.name, "sha256": sha256(path)}
            for name, path in paths.items()
        },
        "execution": parse_log_header(artifacts.stdout_log),
        "posterior_reconstruction": {
            "sample_count": int(samples.shape[0]),
            "weight_sum": float(weights.sum()),
            "component_quantiles_16_50_84": quantiles,
            "component_quantiles_match_fit_summary_exactly": True,
        },
        "component_identity": identity,
        "component_diagnostics": components,
        "failure": {
            "fourth_DSA_component_width_ms": fourth["width_quantiles_ms"][1],
            "fourth_DSA_component_width_to_window_ratio": fourth[
                "width_to_window_ratio"
            ],
            "fourth_DSA_component_fluence_fraction": fourth["modeled_fluence_fraction"],
            "broad_low_fluence_pedestal": fourth["broad_low_fluence_pedestal"],
            "all_flagged_component_degeneracies": [
                {
                    "band": band,
                    "component": row["component"],
                    "broad_vs_window": row["broad_vs_window"],
                    "low_fluence": row["low_fluence"],
                }
                for band, diagnostic in components.items()
                for row in diagnostic["components"]
                if row["broad_vs_window"] or row["low_fluence"]
            ],
            "thresholds": {
                "minimum_width_to_window_ratio": broad_width_ratio,
                "maximum_low_fluence_fraction": low_fluence_fraction,
            },
        },
        "residual_morphology": residuals,
        "evidence_comparison": evidence_assessment(
            fit=fit,
            comparison_fit=comparison_fit,
            model=model,
            comparison_model=comparison_model,
        ),
        "guard_contract": {
            "component_arrival_intervals_inside_fitted_window": bool(
                all(
                    row["arrival_16_84_interval_inside_window"]
                    for band in components.values()
                    for row in band["components"]
                )
            ),
            "broad_low_fluence_flag_triggered": bool(
                any(
                    row["broad_low_fluence_pedestal"]
                    for band in components.values()
                    for row in band["components"]
                )
            ),
            "any_low_fluence_component_flag_triggered": bool(
                any(
                    row["low_fluence"]
                    for band in components.values()
                    for row in band["components"]
                )
            ),
            "any_component_degeneracy_flag_triggered": bool(
                any(
                    row["broad_vs_window"] or row["low_fluence"]
                    for band in components.values()
                    for row in band["components"]
                )
            ),
            "component_structure_consistent": identity["component_structure_matches"],
            "content_identity_complete_across_review_manifest": identity[
                "content_identity_complete_across_review_manifest"
            ],
            "evidence_comparison_admissible": False,
            "residual_morphology_reconstructed": True,
        },
        "verdict": {
            "guard_triggered": bool(
                any(
                    row["broad_vs_window"] or row["low_fluence"]
                    for band in components.values()
                    for row in band["components"]
                )
            ),
            "deprecated_panel_review_eligible": False,
            "deprecated_fit_value_trusted": False,
        },
    }


def render_residual_svg(
    model: dict[str, np.ndarray],
    comparison_model: dict[str, np.ndarray],
    output: Path,
) -> None:
    """Write a deterministic four-panel signed residual-profile diagnostic."""
    panels = []
    for model_name, arrays in (("C2D4", model), ("C2D3", comparison_model)):
        for band in ("C", "D"):
            valid = np.asarray(arrays[f"valid{band}"], dtype=bool)
            normalized = (
                np.asarray(arrays[f"data{band}"])[valid]
                - np.asarray(arrays[f"model{band}"])[valid]
            ) / np.asarray(arrays[f"noise{band}"])[valid, None]
            profile = normalized.sum(axis=0) / np.sqrt(normalized.shape[0])
            panels.append(
                (
                    model_name,
                    band,
                    np.asarray(arrays[f"time{band}"], dtype=float),
                    profile,
                )
            )

    band_limits = {
        band: (
            min(
                0.0,
                *(
                    float(profile.min())
                    for _, candidate, _, profile in panels
                    if candidate == band
                ),
            ),
            max(
                0.0,
                *(
                    float(profile.max())
                    for _, candidate, _, profile in panels
                    if candidate == band
                ),
            ),
        )
        for band in ("C", "D")
    }
    width, height = 960, 620
    chunks = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="sans-serif" fill="none" stroke="black">',
    ]
    for panel_index, (model_name, band, time, profile) in enumerate(panels):
        column = panel_index // 2
        row = panel_index % 2
        left = 55 + column * 470
        top = 45 + row * 290
        plot_width, plot_height = 390, 220
        ymin, ymax = band_limits[band]
        margin = max((ymax - ymin) * 0.05, 1e-12)
        ymin -= margin
        ymax += margin
        x = left + (time - time.min()) / np.ptp(time) * plot_width
        y = top + (ymax - profile) / (ymax - ymin) * plot_height
        points = " ".join(f"{px:.3f},{py:.3f}" for px, py in zip(x, y))
        zero_y = top + ymax / (ymax - ymin) * plot_height
        x_ticks = (
            float(time.min()),
            float(np.mean((time.min(), time.max()))),
            float(time.max()),
        )
        y_ticks = (ymin, 0.0, ymax)
        chunks.extend(
            [
                f'<rect x="{left}" y="{top}" width="{plot_width}" '
                f'height="{plot_height}" stroke-width="1"/>',
                f'<polyline points="{points}" stroke="#235789" stroke-width="1"/>',
                f'<line x1="{left}" x2="{left + plot_width}" y1="{zero_y:.3f}" '
                f'y2="{zero_y:.3f}" stroke="#777" stroke-width="0.7"/>',
                f'<text x="{left + plot_width / 2}" y="{top - 15}" '
                'text-anchor="middle" fill="black" stroke="none" font-size="16">'
                f"{model_name} {band} normalized residual profile</text>",
                f'<text x="{left + plot_width / 2}" y="{top + plot_height + 25}" '
                'text-anchor="middle" fill="black" stroke="none" font-size="13">'
                "Time (ms)</text>",
                f'<text x="{left - 43}" y="{top + plot_height / 2}" '
                f'transform="rotate(-90 {left - 43} {top + plot_height / 2})" '
                'text-anchor="middle" fill="black" stroke="none" font-size="12">'
                "Band-summed residual (noise standard deviations)</text>",
            ]
        )
        for tick in x_ticks:
            tick_x = left + (tick - time.min()) / np.ptp(time) * plot_width
            chunks.append(
                f'<text x="{tick_x:.3f}" y="{top + plot_height + 14}" '
                'text-anchor="middle" fill="black" stroke="none" font-size="10">'
                f"{tick:.2f}</text>"
            )
        for tick in y_ticks:
            tick_y = top + (ymax - tick) / (ymax - ymin) * plot_height
            chunks.append(
                f'<text x="{left - 5}" y="{tick_y + 3:.3f}" '
                'text-anchor="end" fill="black" stroke="none" font-size="10">'
                f"{tick:.1f}</text>"
            )
    chunks.extend(("</g>", "</svg>"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(chunks) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fit", type=Path, required=True)
    parser.add_argument("--samples", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--comparison-fit", type=Path, required=True)
    parser.add_argument("--comparison-model", type=Path, required=True)
    parser.add_argument("--stdout-log", type=Path, required=True)
    parser.add_argument("--stderr-log", type=Path, required=True)
    parser.add_argument("--review-manifest", type=Path)
    parser.add_argument("--residual-svg", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = audit(
        ArtifactBundle(
            fit=args.fit,
            samples=args.samples,
            model=args.model,
            comparison_fit=args.comparison_fit,
            comparison_model=args.comparison_model,
            stdout_log=args.stdout_log,
            stderr_log=args.stderr_log,
            review_manifest=args.review_manifest,
        )
    )
    if args.residual_svg is not None:
        render_residual_svg(
            load_model(args.model), load_model(args.comparison_model), args.residual_svg
        )
        result["diagnostic_outputs"] = {
            "residual_profile_svg": {
                "name": args.residual_svg.name,
                "sha256": sha256(args.residual_svg),
                "review_eligible": False,
            }
        }
    result["audit_generation"] = {
        "argv": [sys.executable, *sys.argv],
        "working_directory": os.getcwd(),
        "script_sha256": sha256(Path(__file__)),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
