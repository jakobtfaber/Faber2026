#!/usr/bin/env python3
"""Reconstruct the deprecated Zach C2D4 failure from producing artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import numpy as np


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
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
    return 0.5 * (
        float(summary["err_minus"]) + float(summary["err_plus"])
    )


def sigma_separation(
    left: dict[str, Any], right: dict[str, Any]
) -> float:
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


def audit(
    *,
    fit_path: Path,
    samples_path: Path,
    model_path: Path,
    comparison_fit_path: Path,
    comparison_model_path: Path,
    stdout_log_path: Path,
    stderr_log_path: Path,
    broad_width_ratio: float = 5.0,
    low_fluence_fraction: float = 0.05,
    mode_sigma_limit: float = 3.0,
) -> dict[str, Any]:
    fit = json.loads(fit_path.read_text(encoding="utf-8"))
    comparison_fit = json.loads(
        comparison_fit_path.read_text(encoding="utf-8")
    )

    if (fit.get("components_C"), fit.get("components_D")) != (2, 4):
        raise ValueError("deprecated fit is not C2D4")
    if (
        comparison_fit.get("components_C"),
        comparison_fit.get("components_D"),
    ) != (2, 3):
        raise ValueError("comparison fit is not C2D3")

    with np.load(samples_path, allow_pickle=True) as samples_file:
        names = [str(name) for name in samples_file["param_names"]]
        samples = np.asarray(samples_file["samples"], dtype=float)
        weights = np.asarray(samples_file["weights"], dtype=float)
    if samples.shape != (weights.size, len(names)):
        raise ValueError("posterior sample dimensions do not match names/weights")
    if not np.isclose(weights.sum(), 1.0, rtol=0.0, atol=1e-12):
        raise ValueError("posterior weights do not sum to one")

    required = [
        "t0_D1",
        "t0_D2",
        "t0_D3",
        "t0_D4",
        "zeta_D4",
    ]
    missing = sorted(set(required) - set(names))
    if missing:
        raise ValueError(f"posterior samples lack parameters: {missing}")

    posterior_quantiles = {
        name: weighted_quantiles(
            samples[:, names.index(name)], weights, (0.16, 0.50, 0.84)
        )
        for name in required
    }
    for name, quantiles in posterior_quantiles.items():
        recorded = fit["percentiles"][name]
        expected = [recorded["lower"], recorded["median"], recorded["upper"]]
        if not np.array_equal(np.asarray(quantiles), np.asarray(expected)):
            raise ValueError(f"sample-derived {name} quantiles disagree with fit")

    with np.load(model_path, allow_pickle=True) as model_file:
        if (int(model_file["nC"]), int(model_file["nD"])) != (2, 4):
            raise ValueError("model grid component count disagrees with fit")
        time_d = np.asarray(model_file["timeD"], dtype=float)
        fluence_d = np.asarray(model_file["fluenceD"], dtype=float)
        chi2_c = float(model_file["chi2C"])
        chi2_d = float(model_file["chi2D"])
    with np.load(comparison_model_path, allow_pickle=True) as comparison_model:
        comparison_chi2_c = float(comparison_model["chi2C"])
        comparison_chi2_d = float(comparison_model["chi2D"])

    if time_d.size < 2 or fluence_d.shape != (4,):
        raise ValueError("unexpected DSA model-grid dimensions")
    window = [float(time_d.min()), float(time_d.max())]
    window_span = float(np.ptp(time_d))
    arrivals = {
        name: posterior_quantiles[name][1] for name in required if name.startswith("t0_")
    }
    arrivals_in_window = {
        name: bool(window[0] <= value <= window[1])
        for name, value in arrivals.items()
    }

    width_ms = posterior_quantiles["zeta_D4"][1]
    width_ratio = float(width_ms / window_span)
    fluence_fractions = fluence_d / fluence_d.sum()
    fourth_fraction = float(fluence_fractions[3])
    pedestal = bool(
        width_ratio >= broad_width_ratio
        and fourth_fraction <= low_fluence_fraction
    )

    beta_separation = sigma_separation(fit["beta"], comparison_fit["beta"])
    tau_separation = sigma_separation(
        fit["tau_1ghz"], comparison_fit["tau_1ghz"]
    )
    configuration_matched = bool(
        fit.get("gain_s2") == comparison_fit.get("gain_s2")
        and fit.get("beta_bounds") == comparison_fit.get("beta_bounds")
        and fit.get("components_C") == comparison_fit.get("components_C")
        and fit.get("components_D") == comparison_fit.get("components_D") + 1
    )
    mode_continuous = bool(
        configuration_matched
        and beta_separation <= mode_sigma_limit
        and tau_separation <= mode_sigma_limit
    )

    return {
        "schema": "faber2026-deprecated-joint-fit-audit/v1",
        "subject": {
            "burst": "zach",
            "tns": "FRB 20220207C",
            "model": "C2D4",
            "disposition": "deprecated_reject",
        },
        "artifacts": {
            name: {"name": path.name, "sha256": sha256(path)}
            for name, path in {
                "fit": fit_path,
                "samples": samples_path,
                "model_grid": model_path,
                "comparison_fit": comparison_fit_path,
                "comparison_model_grid": comparison_model_path,
                "stdout_log": stdout_log_path,
                "stderr_log": stderr_log_path,
            }.items()
        },
        "execution": parse_log_header(stdout_log_path),
        "posterior_reconstruction": {
            "sample_count": int(samples.shape[0]),
            "weight_sum": float(weights.sum()),
            "quantiles_16_50_84": posterior_quantiles,
            "matches_fit_summary_exactly": True,
        },
        "failure": {
            "dsa_fitted_window_ms": window,
            "dsa_fitted_window_span_ms": window_span,
            "arrival_medians_ms": arrivals,
            "all_arrival_medians_in_window": bool(all(arrivals_in_window.values())),
            "arrival_medians_in_window": arrivals_in_window,
            "fourth_component_width_ms": width_ms,
            "fourth_component_width_to_window_ratio": width_ratio,
            "dsa_component_fluence": [float(value) for value in fluence_d],
            "dsa_component_fluence_fractions": [
                float(value) for value in fluence_fractions
            ],
            "fourth_component_fluence_fraction": fourth_fraction,
            "broad_low_fluence_pedestal": pedestal,
            "thresholds": {
                "minimum_width_to_window_ratio": broad_width_ratio,
                "maximum_low_fluence_fraction": low_fluence_fraction,
            },
            "reduced_residual_statistic": {"CHIME": chi2_c, "DSA": chi2_d},
        },
        "comparison_to_c2d3": {
            "configuration_matched": configuration_matched,
            "common_parameter_sigma_separation": {
                "beta": beta_separation,
                "tau_1ghz": tau_separation,
            },
            "mode_continuous": mode_continuous,
            "log_evidence_C2D4_minus_C2D3": float(
                fit["log_evidence"] - comparison_fit["log_evidence"]
            ),
            "reduced_residual_statistic_C2D3": {
                "CHIME": comparison_chi2_c,
                "DSA": comparison_chi2_d,
            },
        },
        "guard_contract": {
            "require_arrival_medians_inside_fitted_window": True,
            "flag_broad_low_fluence_components": True,
            "require_component_count_identity_across_artifacts": True,
            "require_mode_and_configuration_match_for_evidence_comparison": True,
            "require_residual_morphology_review": True,
        },
        "verdict": {
            "guard_triggered": pedestal,
            "deprecated_panel_review_eligible": False,
            "deprecated_fit_value_trusted": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fit", type=Path, required=True)
    parser.add_argument("--samples", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--comparison-fit", type=Path, required=True)
    parser.add_argument("--comparison-model", type=Path, required=True)
    parser.add_argument("--stdout-log", type=Path, required=True)
    parser.add_argument("--stderr-log", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = audit(
        fit_path=args.fit,
        samples_path=args.samples,
        model_path=args.model,
        comparison_fit_path=args.comparison_fit,
        comparison_model_path=args.comparison_model,
        stdout_log_path=args.stdout_log,
        stderr_log_path=args.stderr_log,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
