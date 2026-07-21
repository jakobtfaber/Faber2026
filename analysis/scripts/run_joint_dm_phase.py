#!/usr/bin/env python3
"""Current reference-parity independent and joint CHIME/DSA DM fits.

The provenance-pinned v2 source snapshot remains immutable under
analysis/dm-joint-phase-v2/code. This current producer requires separate
full-resolution roots for CHIME/FRB and DSA-110.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT / "analysis/dm-joint-phase-v2/code"))

from dispersion.dm_joint_phase import (
    block_average,
    crop_on_pulse,
    fit_surface,
    gaussian_joint_fit,
    phase_surface,
    product_dm_from_filename,
)
from dispersion.dm_power_analysis import (
    CHIME_DT_S,
    DSA_DT_S,
    _freq_grid_mhz,
    _orient_waterfall_to_ascending_frequency,
)

RESOLUTIONS = ((1, 1), (2, 1), (1, 2), (2, 2))
CUTOFFS = (500.0, 1000.0, 1500.0, 2500.0, 5000.0)
CHIME_FULL_ROOT_DEFAULT = Path.home() / "Data/Faber2026/chimefrb/CHIME_bursts"
DSA_FULL_ROOT_DEFAULT = Path.home() / "Data/Faber2026/dsa110/DSA_bursts"


def root_for_telescope(
    telescope: str,
    chime_full_root: Path,
    dsa_full_root: Path,
) -> Path:
    roots = {"chime": Path(chime_full_root), "dsa": Path(dsa_full_root)}
    try:
        return roots[telescope]
    except KeyError as exc:
        raise ValueError(f"unknown telescope: {telescope!r}") from exc



def _serialise(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    raise TypeError(type(value).__name__)


def _resolution_result(
    waterfall: np.ndarray,
    frequency: np.ndarray,
    dt_s: float,
    product_dm: float,
    absolute_grid: np.ndarray,
    frequency_factor: int,
    time_factor: int,
) -> dict:
    reduced, reduced_frequency = block_average(
        waterfall, frequency, frequency_factor, time_factor
    )
    residual_grid = absolute_grid - product_dm
    surface = phase_surface(
        reduced,
        reduced_frequency,
        dt_s * time_factor,
        residual_grid,
        high_hz=5000.0,
    )
    fit = fit_surface(surface, cutoff_candidates_hz=CUTOFFS)
    return {
        "frequency_factor": frequency_factor,
        "time_factor": time_factor,
        "nchan": int(reduced.shape[0]),
        "ntime": int(reduced.shape[1]),
        "dt_s": float(dt_s * time_factor),
        "dm": float(product_dm + fit.dm),
        "residual_dm": float(fit.dm),
        "sigma_jackknife": float(fit.sigma_jackknife),
        "cutoff_hz": float(fit.cutoff_hz),
        "cutoff_peaks_absolute": {
            str(cutoff): float(product_dm + peak)
            for cutoff, peak in fit.cutoff_peaks.items()
        },
        "cutoff_contrast": {str(k): float(v) for k, v in fit.cutoff_contrast.items()},
        "dm_grid": absolute_grid,
        "score": fit.score,
        "jackknife_peaks_absolute": product_dm + fit.jackknife_peaks,
    }


def _select_resolution(results: list[dict]) -> tuple[dict, list[dict]]:
    values = np.asarray([row["dm"] for row in results])
    best_group: list[dict] = []
    for row in results:
        group = [other for other in results if abs(other["dm"] - row["dm"]) <= 0.10]
        if len(group) > len(best_group):
            best_group = group
    if len(best_group) < 2:
        best_group = results
    selected = min(
        best_group,
        key=lambda row: (
            np.log2(row["frequency_factor"]) + np.log2(row["time_factor"]),
            row["time_factor"],
            row["frequency_factor"],
            -max(row["cutoff_contrast"].values()),
        ),
    )
    selected_values = np.asarray([row["dm"] for row in best_group])
    selected["sigma_resolution"] = (
        float(np.std(selected_values, ddof=1)) if selected_values.size > 1 else 0.0
    )
    selected["resolution_cluster_size"] = len(best_group)
    selected["all_resolution_spread"] = float(np.ptp(values))
    return selected, best_group


def fit_band(
    row: dict,
    chime_full_root: Path,
    dsa_full_root: Path,
    absolute_grid: np.ndarray,
) -> dict:
    telescope = row["telescope"]
    path = root_for_telescope(telescope, chime_full_root, dsa_full_root) / row["filename"]
    raw = np.load(path, mmap_mode="r")
    oriented = _orient_waterfall_to_ascending_frequency(raw, telescope)
    frequency = _freq_grid_mhz(telescope, oriented.shape[0])
    dt_s = CHIME_DT_S if telescope == "chime" else DSA_DT_S
    cropped, crop, valid = crop_on_pulse(oriented, dt_s)
    selected_frequency = frequency[valid]
    product_dm = product_dm_from_filename(row["filename"])
    resolutions = [
        _resolution_result(
            cropped,
            selected_frequency,
            dt_s,
            product_dm,
            absolute_grid,
            frequency_factor,
            time_factor,
        )
        for frequency_factor, time_factor in RESOLUTIONS
    ]
    selected_coarse, cluster = _select_resolution(resolutions)
    fine_half_width = max(
        0.08,
        2.0 * float(selected_coarse["sigma_jackknife"]),
        2.0 * float(selected_coarse["sigma_resolution"]),
    )
    fine_centre = float(selected_coarse["dm"])
    selected = None
    expansions = 0
    initial_fine_half_width = fine_half_width
    for expansions in range(4):
        fine_half_width = initial_fine_half_width * 2.0**expansions
        fine_grid = np.arange(
            fine_centre - fine_half_width,
            fine_centre + fine_half_width + 0.001,
            0.002,
        )
        selected = _resolution_result(
            cropped,
            selected_frequency,
            dt_s,
            product_dm,
            fine_grid,
            int(selected_coarse["frequency_factor"]),
            int(selected_coarse["time_factor"]),
        )
        peak_index = int(np.nanargmax(selected["score"]))
        if 3 <= peak_index <= fine_grid.size - 4:
            break
        fine_centre = float(selected["dm"])
    assert selected is not None
    selected["sigma_resolution"] = selected_coarse["sigma_resolution"]
    selected["resolution_cluster_size"] = selected_coarse["resolution_cluster_size"]
    selected["all_resolution_spread"] = selected_coarse["all_resolution_spread"]
    cutoff_values = np.asarray(list(selected["cutoff_peaks_absolute"].values()))
    sigma_cutoff = float(np.std(cutoff_values, ddof=1))
    sigma = max(
        0.005,
        float(selected["sigma_jackknife"]),
        float(selected["sigma_resolution"]),
        sigma_cutoff,
    )
    return {
        "burst": row["burst"],
        "telescope": telescope,
        "input_path": str(path),
        "product_dm": product_dm,
        "raw_shape": list(raw.shape),
        "valid_channels": int(valid.sum()),
        "crop": list(crop),
        "frequency_mhz": [float(selected_frequency.min()), float(selected_frequency.max())],
        "native_dt_s": dt_s,
        "dm": float(selected["dm"]),
        "sigma": sigma,
        "sigma_components": {
            "jackknife": float(selected["sigma_jackknife"]),
            "resolution": float(selected["sigma_resolution"]),
            "cutoff": sigma_cutoff,
            "floor": 0.005,
        },
        "selected_resolution": {
            "frequency_factor": selected["frequency_factor"],
            "time_factor": selected["time_factor"],
            "nchan": selected["nchan"],
            "ntime": selected["ntime"],
            "dt_s": selected["dt_s"],
            "cutoff_hz": selected["cutoff_hz"],
            "cluster_size": len(cluster),
            "fine_grid_expansions": expansions,
        },
        "selected_curve": {
            "dm_grid": selected["dm_grid"],
            "score": selected["score"],
            "cutoff_peaks_absolute": selected["cutoff_peaks_absolute"],
            "cutoff_contrast": selected["cutoff_contrast"],
            "jackknife_peaks_absolute": selected["jackknife_peaks_absolute"],
        },
        "resolutions": resolutions,
    }


def run(
    manifest: Path,
    chime_full_root: Path,
    dsa_full_root: Path,
    output: Path,
) -> list[dict]:
    rows = list(csv.DictReader(manifest.open()))
    by_event: dict[str, dict[str, dict]] = {}
    for row in rows:
        by_event.setdefault(row["burst"], {})[row["telescope"]] = row
    output.parent.mkdir(parents=True, exist_ok=True)
    results = []
    for burst in sorted(by_event):
        pair = by_event[burst]
        refs = [product_dm_from_filename(pair[band]["filename"]) for band in ("chime", "dsa")]
        centre = float(np.mean(refs))
        grid = np.arange(centre - 1.0, centre + 1.0001, 0.01)
        chime = fit_band(pair["chime"], chime_full_root, dsa_full_root, grid)
        dsa = fit_band(pair["dsa"], chime_full_root, dsa_full_root, grid)
        joint = gaussian_joint_fit(chime["dm"], chime["sigma"], dsa["dm"], dsa["sigma"])
        result = {"burst": burst, "chime": chime, "dsa": dsa, "joint": joint}
        results.append(result)
        output.write_text(json.dumps(results, indent=2, default=_serialise) + "\n")
        print(
            f"{burst}: CHIME {chime['dm']:.4f}+/-{chime['sigma']:.4f}; "
            f"DSA {dsa['dm']:.4f}+/-{dsa['sigma']:.4f}; "
            f"joint {joint['dm']:.4f}+/-{joint['sigma']:.4f}; "
            f"tension {joint['tension_sigma']:.2f}",
            flush=True,
        )
    return results


def recompute_joint(output: Path) -> list[dict]:
    """Refresh joint estimates without repeating the expensive band fits."""
    results = json.loads(output.read_text())
    for result in results:
        chime = result["chime"]
        dsa = result["dsa"]
        result["joint"] = gaussian_joint_fit(
            chime["dm"], chime["sigma"], dsa["dm"], dsa["sigma"]
        )
    output.write_text(json.dumps(results, indent=2, default=_serialise) + "\n")
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("data-manifest.csv"))
    path_arg = lambda value: Path(value).expanduser()  # noqa: E731
    parser.add_argument(
        "--chime-full-root", type=path_arg, default=CHIME_FULL_ROOT_DEFAULT
    )
    parser.add_argument(
        "--dsa-full-root", type=path_arg, default=DSA_FULL_ROOT_DEFAULT
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/dm_joint_phase_v2/fits.json"),
    )
    parser.add_argument(
        "--recompute-joint-only",
        action="store_true",
        help="reuse stored band fits and only refresh their joint estimates",
    )
    args = parser.parse_args()
    if args.recompute_joint_only:
        recompute_joint(args.output)
    else:
        run(
            args.manifest,
            args.chime_full_root,
            args.dsa_full_root,
            args.output,
        )


if __name__ == "__main__":
    main()
