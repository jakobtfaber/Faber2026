#!/usr/bin/env python3
"""Measure residual frequency-time drift in all adopted-DM Figure 1 products."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "pipeline"
sys.path.insert(0, str(PIPELINE))

from dispersion.chime_dm import K_DM, measure_dm  # noqa: E402
from dispersion.dm_campaign.render_dm_zoom_comparison import (  # noqa: E402
    _subband_arrival_times,
)
from dispersion.dm_power_analysis import (  # noqa: E402
    CHIME_DT_S,
    DSA_DT_S,
    _freq_grid_mhz,
    _orient_waterfall_to_ascending_frequency,
    shift_waterfall_residual_dm,
)

DATA_DEFAULT = Path.home() / "Data/Faber2026/dsa110/DSA_bursts"
CATALOG_DEFAULT = ROOT / "analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv"
ROSTER_DEFAULT = ROOT / "scripts/jointmodel_triptych_manifest.yaml"


def roster_nicks(manifest_path: Path) -> set[str]:
    """The twelve-burst Figure 1 roster from the shared render manifest."""
    import yaml

    bursts = yaml.safe_load(manifest_path.read_text())["bursts"]
    nicks = [burst["nick"].lower() for burst in bursts]
    if len(nicks) != 12 or len(set(nicks)) != 12:
        raise ValueError(f"render manifest roster is not 12 unique bursts: {nicks}")
    return set(nicks)


def product_dm(path: Path) -> float:
    """Parse the DM encoded as integer and fractional filename fields."""
    fields = path.stem.split("_")
    index = fields.index("I")
    return float(f"{fields[index + 1]}.{fields[index + 2]}")


def zero_consistency(measurement: dict, *, max_sigma: float = 2.0) -> str:
    """Classify a residual-DM measurement without treating missing fits as zero."""
    residual = measurement.get("residual_dm")
    sigma = measurement.get("sigma")
    if measurement.get("n", 0) < 3 or residual is None or sigma in (None, 0):
        return "unconstrained"
    return "consistent_zero" if abs(residual) <= max_sigma * sigma else "nonzero"


def products(data_root: Path, nick: str) -> dict[str, Path]:
    file_nick = "johndoeII" if nick == "johndoeii" else nick
    result = {}
    for telescope in ("chime", "dsa"):
        matches = list(data_root.glob(f"{file_nick}_{telescope}_I_*_cntr_bpc.npy"))
        if len(matches) != 1:
            raise RuntimeError(f"{nick}/{telescope}: expected one product, found {matches}")
        result[telescope] = matches[0]
    return result


def peak_slope(path: Path, telescope: str, target_dm: float) -> dict:
    band = {
        "telescope": telescope,
        "input_path": str(path),
        "product_dm": product_dm(path),
    }
    frequency, arrival_ms, reference_frequency, _ = _subband_arrival_times(
        band, target_dm, window_s=0.030, n_sub=8
    )
    good = np.isfinite(arrival_ms)
    if good.sum() < 3:
        return {"n": int(good.sum()), "residual_dm": None, "sigma": None}
    x_seconds = K_DM * (
        1.0 / frequency[good] ** 2 - 1.0 / reference_frequency**2
    )
    y_seconds = arrival_ms[good] / 1e3
    design = np.column_stack([x_seconds, np.ones_like(x_seconds)])
    beta, _, _, _ = np.linalg.lstsq(design, y_seconds, rcond=None)
    residual = y_seconds - design @ beta
    dof = max(len(y_seconds) - 2, 1)
    covariance = np.linalg.inv(design.T @ design) * (residual @ residual / dof)
    return {
        "n": int(good.sum()),
        "residual_dm": float(beta[0]),
        "sigma": float(np.sqrt(covariance[0, 0])),
    }


def emg_slope(path: Path, telescope: str, target_dm: float) -> dict:
    raw = np.load(path, mmap_mode="r")
    waterfall = _orient_waterfall_to_ascending_frequency(raw, telescope)
    frequency = _freq_grid_mhz(telescope, waterfall.shape[0])
    dt_seconds = CHIME_DT_S if telescope == "chime" else DSA_DT_S
    shifted = shift_waterfall_residual_dm(
        waterfall,
        frequency,
        dt_seconds,
        target_dm - product_dm(path),
        mode="zero_fill",
    )
    profile = np.nansum(np.nan_to_num(shifted), axis=0)
    peak = int(np.argmax(profile))
    half_window = min(shifted.shape[1] // 2, int(round(0.020 / dt_seconds)))
    cropped = shifted[:, max(0, peak - half_window) : min(shifted.shape[1], peak + half_window)]
    result = measure_dm(
        cropped,
        frequency,
        dt_seconds,
        target_dm,
        n_subband=8,
        dm_window=0.5 if telescope == "chime" else 2.0,
        dm_step=0.02 if telescope == "chime" else 0.1,
        min_snr=3.0,
        min_good_subbands=3,
        dm_err_max=20.0,
    )
    return {
        "n": int(result["n_good_subbands"]),
        "residual_dm": None if result["dm"] is None else float(result["dm"] - target_dm),
        "sigma": result["dm_err"],
        "reason": result["reason"],
    }


def audit(data_root: Path, catalog: Path, roster_manifest: Path = ROSTER_DEFAULT) -> dict:
    measurements = []
    with catalog.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    catalog_nicks = [row["nick"].lower() for row in rows]
    expected = roster_nicks(roster_manifest)
    if len(catalog_nicks) != len(set(catalog_nicks)) or set(catalog_nicks) != expected:
        raise ValueError(
            "catalog does not cover the twelve-burst Figure 1 roster exactly: "
            f"catalog={sorted(catalog_nicks)} roster={sorted(expected)}"
        )
    for row in rows:
        nick = row["nick"].lower()
        target_dm = float(row["adopted_dm"])
        for telescope, path in products(data_root, nick).items():
            peak = peak_slope(path, telescope, target_dm)
            emg = emg_slope(path, telescope, target_dm)
            peak["zero_consistency"] = zero_consistency(peak)
            emg["zero_consistency"] = zero_consistency(emg)
            measurements.append(
                {
                    "nick": nick,
                    "telescope": telescope,
                    "input_path": str(path),
                    "target_dm": target_dm,
                    "product_dm": product_dm(path),
                    "profile_peak_estimator": peak,
                    "emg_estimator": emg,
                }
            )
    if len(measurements) != 24:
        raise ValueError(f"expected 24 panel measurements (12 bursts x 2 bands), got {len(measurements)}")
    all_zero = all(
        item["emg_estimator"]["zero_consistency"] == "consistent_zero"
        for item in measurements
    )
    return {
        "schema_version": 1,
        "pipeline_revision": subprocess.check_output(
            ["git", "-C", str(PIPELINE), "rev-parse", "HEAD"], text=True
        ).strip(),
        "gate": "EMG residual DM is consistent with zero within 2 sigma in every panel",
        "gate_passed": all_zero,
        "measurements": measurements,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=DATA_DEFAULT)
    parser.add_argument("--catalog", type=Path, default=CATALOG_DEFAULT)
    parser.add_argument("--roster-manifest", type=Path, default=ROSTER_DEFAULT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.dumps(
        audit(args.data_root, args.catalog, args.roster_manifest), indent=2, sort_keys=True
    ) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
