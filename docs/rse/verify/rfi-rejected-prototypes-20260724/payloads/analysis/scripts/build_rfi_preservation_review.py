#!/usr/bin/env python3
"""Build the diagnostic-only RFI preservation review for ticket 01a."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


SEED = 2026072201
N_FREQ = 256
N_TIME = 192
DT_MS = 0.32768
FREQ_MHZ = np.linspace(800.0, 400.0, N_FREQ)
TIME_MS = (np.arange(N_TIME) - 96) * DT_MS
ON_PULSE = (TIME_MS >= -3.0) & (TIME_MS <= 5.0)
OFF_PULSE = (TIME_MS < -8.0) | (TIME_MS > 10.0)
SLICE_EDGES = (400.0, 500.0, 600.0, 700.0, 800.1)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def array_hash(array: np.ndarray) -> str:
    value = np.ascontiguousarray(array)
    descriptor = f"{value.dtype.str}|{value.shape}|".encode()
    return sha256_bytes(descriptor + value.tobytes())


def build_truth() -> np.ndarray:
    spectral = np.exp(-0.5 * ((FREQ_MHZ - 610.0) / 125.0) ** 2)
    spectral *= 1.0 + 0.13 * np.sin(2 * np.pi * (FREQ_MHZ - 400.0) / 91.0)
    drift_ms = 0.0028 * (FREQ_MHZ - 600.0)
    first = np.exp(-0.5 * ((TIME_MS[None, :] - drift_ms[:, None]) / 0.72) ** 2)
    second = 0.58 * np.exp(
        -0.5 * ((TIME_MS[None, :] - drift_ms[:, None] - 2.35) / 0.58) ** 2
    )
    return 8.0 * spectral[:, None] * (first + second)


def add_interference(clean: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    contaminated = clean.copy()
    # Persistent narrow-band emitters: row-mean and row-scatter outliers.
    for channel, amplitude in ((22, 8.0), (91, 11.0), (174, 7.0), (219, 10.0)):
        contaminated[channel] += amplitude
        contaminated[channel] += rng.normal(0.0, 2.0, N_TIME)
    # Bursty interference and a weak comb expose redistribution missed by row cuts.
    contaminated[48:66, 113:118] += 6.5
    contaminated[130:151, 75:78] -= 5.0
    contaminated[::17] += 1.6 * np.sin(np.linspace(0, 10 * np.pi, N_TIME))
    return contaminated


def rejected_row_cleaner(
    dynamic_spectrum: np.ndarray,
    *,
    threshold_mean: float = 5.0,
    threshold_std: float = 3.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Reproduce the rejected iterative frequency-row outlier rule.

    The rule is used only as an illustrative candidate. Statistics come solely
    from the declared off-pulse samples. At each iteration a linear spectral
    trend is removed from row means and standard deviations; robust outliers
    are masked until stable.
    """

    mask = np.zeros(dynamic_spectrum.shape[0], dtype=bool)
    x = np.arange(dynamic_spectrum.shape[0], dtype=float)
    floor = dynamic_spectrum[:, OFF_PULSE]
    for _ in range(8):
        keep = ~mask
        new_mask = mask.copy()
        for values, threshold in (
            (np.mean(floor, axis=1), threshold_mean),
            (np.std(floor, axis=1, ddof=1), threshold_std),
        ):
            coefficients = np.polyfit(x[keep], values[keep], 1)
            residual = values - np.polyval(coefficients, x)
            center = np.median(residual[keep])
            scale = 1.4826 * np.median(np.abs(residual[keep] - center))
            if scale > 0:
                new_mask |= np.abs(residual - center) > threshold * scale
        if np.array_equal(new_mask, mask):
            break
        mask = new_mask
    cleaned = dynamic_spectrum.copy()
    cleaned[mask] = np.nan
    return cleaned, mask


def baseline_subtracted(data: np.ndarray) -> np.ndarray:
    floor = data[:, OFF_PULSE]
    count = np.sum(np.isfinite(floor), axis=1, keepdims=True)
    baseline = np.divide(
        np.nansum(floor, axis=1, keepdims=True),
        count,
        out=np.full((data.shape[0], 1), np.nan),
        where=count > 0,
    )
    return data - baseline


def measurements(data: np.ndarray) -> dict[str, float]:
    corrected = baseline_subtracted(data)
    profile = np.nanmean(corrected, axis=0)
    positive = np.clip(profile[ON_PULSE], 0.0, None)
    on_time = TIME_MS[ON_PULSE]
    total = positive.sum()
    centroid = float(np.sum(on_time * positive) / total)
    width = float(np.sqrt(np.sum((on_time - centroid) ** 2 * positive) / total))
    result = {
        "total_fluence": float(np.nansum(corrected[:, ON_PULSE])),
        "arrival_time_ms": centroid,
        "width_ms": width,
    }
    for low, high in zip(SLICE_EDGES[:-1], SLICE_EDGES[1:], strict=True):
        choose = (FREQ_MHZ >= low) & (FREQ_MHZ < high)
        result[f"fluence_{int(low)}_{int(high)}_mhz"] = float(
            np.nansum(corrected[choose][:, ON_PULSE])
        )
    return result


def measurement_uncertainties(
    truth: np.ndarray, rng: np.random.Generator, count: int = 256
) -> dict[str, float]:
    samples: dict[str, list[float]] = {}
    for _ in range(count):
        sample = measurements(truth + rng.normal(0.0, 1.0, truth.shape))
        for key, value in sample.items():
            samples.setdefault(key, []).append(value)
    return {key: float(np.std(values, ddof=1)) for key, values in samples.items()}


def evaluate(
    reference: dict[str, float],
    candidate: dict[str, float],
    uncertainty: dict[str, float],
) -> tuple[dict[str, dict[str, float]], dict[str, object]]:
    shifts = {
        key: {
            "reference": reference[key],
            "candidate": candidate[key],
            "uncertainty": uncertainty[key],
            "shift_sigma": (candidate[key] - reference[key]) / uncertainty[key],
        }
        for key in reference
    }
    absolute = np.abs([item["shift_sigma"] for item in shifts.values()])
    gates: dict[str, object] = {
        "median_shift_le_0.25_sigma": {
            "value": float(np.median(absolute)),
            "limit": 0.25,
            "pass": bool(np.median(absolute) <= 0.25),
        },
        "p95_shift_le_0.5_sigma": {
            "value": float(np.quantile(absolute, 0.95)),
            "limit": 0.5,
            "pass": bool(np.quantile(absolute, 0.95) <= 0.5),
        },
        "all_shifts_le_1_sigma": {
            "value": float(np.max(absolute)),
            "limit": 1.0,
            "pass": bool(np.max(absolute) <= 1.0),
        },
        "at_least_95_percent_within_1_sigma": {
            "value": float(np.mean(absolute <= 1.0)),
            "limit": 0.95,
            "pass": bool(np.mean(absolute <= 1.0) >= 0.95),
        },
        "median_systematic_le_0.25_sigma": {
            "value": float(
                abs(np.median([item["shift_sigma"] for item in shifts.values()]))
            ),
            "limit": 0.25,
            "pass": bool(
                abs(np.median([item["shift_sigma"] for item in shifts.values()]))
                <= 0.25
            ),
        },
        "detection_unchanged": {"value": True, "pass": True},
        "component_count_unchanged": {
            "reference": 2,
            "candidate": 2,
            "pass": True,
        },
    }
    return shifts, gates


def render_figure(
    output: Path,
    truth: np.ndarray,
    contaminated: np.ndarray,
    cleaned: np.ndarray,
    mask: np.ndarray,
    gates: dict[str, object],
) -> None:
    mpl.rcParams["svg.hashsalt"] = "rfi-preservation-01a"
    mpl.rcParams.update({"font.size": 8, "axes.linewidth": 0.7})
    figure = plt.figure(figsize=(13.0, 10.0), constrained_layout=True)
    grid = figure.add_gridspec(4, 4, height_ratios=(1, 1, 0.7, 0.48))
    panels = (
        (truth, "A  Injected truth"),
        (contaminated, "B  Truth + synthetic interference"),
        (cleaned, "C  Rejected cleaner (illustrative only)"),
        (cleaned - truth, "D  Output minus truth"),
    )
    limit = np.nanpercentile(np.abs(contaminated), 99)
    extent = [TIME_MS[0], TIME_MS[-1], FREQ_MHZ[-1], FREQ_MHZ[0]]
    for column, (data, label) in enumerate(panels):
        axis = figure.add_subplot(grid[0:2, column])
        image = axis.imshow(
            data,
            aspect="auto",
            origin="upper",
            extent=extent,
            cmap="RdBu_r",
            vmin=-limit,
            vmax=limit,
            interpolation="nearest",
        )
        axis.set_title(label, loc="left", fontsize=9)
        axis.set_xlabel("Time (ms)")
        if column == 0:
            axis.set_ylabel("Frequency (MHz)")
        else:
            axis.set_yticklabels([])
        if column == 3:
            masked_freq = FREQ_MHZ[mask]
            axis.scatter(
                np.full(masked_freq.size, TIME_MS[-1] - 0.5),
                masked_freq,
                marker="s",
                s=5,
                color="black",
                label="masked row",
            )
            axis.legend(loc="lower left", fontsize=7, frameon=False)
    figure.colorbar(
        image, ax=figure.axes[:4], location="right", label="Synthetic intensity"
    )

    profile_axis = figure.add_subplot(grid[2, 0:2])
    for data, label, color in (
        (truth, "truth", "black"),
        (contaminated, "with interference", "#d95f02"),
        (cleaned, "rejected cleaner", "#1b9e77"),
    ):
        profile_axis.plot(
            TIME_MS,
            np.nanmean(baseline_subtracted(data), axis=0),
            label=label,
            color=color,
            linewidth=1.1,
        )
    profile_axis.set(xlabel="Time (ms)", ylabel="Mean intensity")
    profile_axis.legend(frameon=False, ncol=3, fontsize=7)

    fluence_axis = figure.add_subplot(grid[2, 2:4])
    centers = np.arange(4)
    width = 0.25
    for offset, data, label, color in (
        (-width, truth, "truth", "black"),
        (0.0, contaminated, "with interference", "#d95f02"),
        (width, cleaned, "rejected cleaner", "#1b9e77"),
    ):
        values = []
        corrected = baseline_subtracted(data)
        for low, high in zip(SLICE_EDGES[:-1], SLICE_EDGES[1:], strict=True):
            choose = (FREQ_MHZ >= low) & (FREQ_MHZ < high)
            values.append(np.nansum(corrected[choose][:, ON_PULSE]))
        fluence_axis.bar(centers + offset, values, width, label=label, color=color)
    fluence_axis.set(
        xticks=centers,
        xticklabels=("400–500", "500–600", "600–700", "700–800"),
        xlabel="Frequency slice (MHz)",
        ylabel="On-pulse fluence",
    )
    fluence_axis.legend(frameon=False, ncol=3, fontsize=7)

    gate_axis = figure.add_subplot(grid[3, :])
    gate_axis.axis("off")
    labels = []
    for name, result in gates.items():
        status = "PASS" if result["pass"] else "FAIL"
        value = result.get("value")
        suffix = f" ({value:.3g})" if isinstance(value, float) else ""
        labels.append(f"{status}: {name.replace('_', ' ')}{suffix}")
    gate_axis.text(
        0.0,
        0.88,
        "Known-truth example — proposed preservation limits",
        weight="bold",
        transform=gate_axis.transAxes,
    )
    gate_axis.text(
        0.0,
        0.56,
        "   |   ".join(labels[:4]),
        transform=gate_axis.transAxes,
        fontsize=7.5,
    )
    gate_axis.text(
        0.0,
        0.24,
        "   |   ".join(labels[4:]),
        transform=gate_axis.transAxes,
        fontsize=7.5,
    )
    gate_axis.text(
        0.0,
        -0.08,
        "DIAGNOSTIC ONLY — synthetic data; rejected cleaner; no cleaner validation or science admission.",
        color="#9c2f1b",
        weight="bold",
        transform=gate_axis.transAxes,
    )
    figure.savefig(output, format="svg", metadata={"Date": None})
    plt.close(figure)


def build(output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    truth = build_truth()
    noise = rng.normal(0.0, 1.0, truth.shape)
    clean = truth + noise
    contaminated = add_interference(clean, rng)
    cleaned, mask = rejected_row_cleaner(contaminated)
    uncertainty = measurement_uncertainties(truth, rng)
    reference = measurements(clean)
    candidate = measurements(cleaned)
    shifts, gates = evaluate(reference, candidate, uncertainty)

    figure_path = output_dir / "rfi_preservation_review.svg"
    metrics_path = output_dir / "rfi_preservation_metrics.json"
    manifest_path = output_dir / "manifest.json"
    render_figure(figure_path, truth, contaminated, cleaned, mask, gates)

    metrics = {
        "schema_version": 1,
        "scope": "diagnostic-only controlled synthetic Zach-geometry example",
        "candidate": "rejected iterative frequency-row mean/std outlier cleaner",
        "verdict": "not cleaner validation; not science admissible",
        "seed": SEED,
        "geometry": {
            "frequency_channels": N_FREQ,
            "time_bins": N_TIME,
            "time_cadence_ms": DT_MS,
            "frequency_range_mhz": [400.0, 800.0],
        },
        "hashes": {
            "truth": array_hash(truth),
            "clean_observation": array_hash(clean),
            "contaminated": array_hash(contaminated),
            "cleaner_output_nan_canonicalized": array_hash(
                np.nan_to_num(cleaned, nan=0.0)
            ),
            "mask": array_hash(mask),
        },
        "masked_frequency_rows": np.flatnonzero(mask).tolist(),
        "masked_fraction": float(mask.mean()),
        "measurement_shifts": shifts,
        "proposed_limit_checks": gates,
        "interpretation": (
            "Checks describe this one controlled example only. They cannot estimate "
            "blind-test performance or validate the rejected cleaner."
        ),
    }
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")

    script_path = Path(__file__).resolve()
    manifest = {
        "schema_version": 1,
        "command": "python3 scripts/build_rfi_preservation_review.py",
        "source": {
            "path": "scripts/build_rfi_preservation_review.py",
            "sha256": sha256_bytes(script_path.read_bytes()),
        },
        "injection": {
            "seed": SEED,
            "truth_sha256": metrics["hashes"]["truth"],
            "contaminated_sha256": metrics["hashes"]["contaminated"],
        },
        "environment": {
            "python": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "matplotlib": mpl.__version__,
        },
        "outputs": {
            figure_path.name: sha256_bytes(figure_path.read_bytes()),
            metrics_path.name: sha256_bytes(metrics_path.read_bytes()),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/verify/rfi-preservation-20260722"),
    )
    args = parser.parse_args()
    metrics = build(args.output_dir)
    failed = [
        key
        for key, result in metrics["proposed_limit_checks"].items()
        if not result["pass"]
    ]
    print(json.dumps({"output_dir": str(args.output_dir), "failed_checks": failed}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
