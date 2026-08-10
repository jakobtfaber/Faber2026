#!/usr/bin/env python3
"""Measure fit-independent two-band fluences and emit a review candidate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scattering"))

from energetics.methods import dsa_beam  # noqa: E402
from energetics.methods.chime_beam import chime_sigma_jy, load_chime_sefd  # noqa: E402
from energetics.methods.flux_cal import (  # noqa: E402
    burst_epoch_position,
    calibrated_band_integral_jy_ms_hz,
    dsa_beam_offset,
    dsa_pointing_dec,
    dsa_sigma_jy,
    load_dsa_sefd_beam,
)
from scattering.scat_analysis.config_utils import load_telescope_block  # noqa: E402
from scattering.scat_analysis.pipeline.io import BurstDataset  # noqa: E402

NICKNAMES = (
    "casey", "chromatica", "freya", "hamilton", "isha", "johndoeii",
    "mahi", "oran", "phineas", "whitney", "wilhelm", "zach",
)
FIELDS = (
    "nickname", "band", "fluence_jy_ms_hz", "stat_err_jy_ms_hz",
    "window_status", "window_sensitivity_frac", "calibration_status",
    "calibration_systematic_dex", "noise_status", "review_status",
    "input_path", "input_sha256",
    "calibration_paths", "calibration_sha256", "thresholds_sigma", "pad_factors",
)
DSA_BEAM_CUBE = dsa_beam.DEFAULT_BEAM


def digest(path: Path) -> str:
    block = 1024 * 1024
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(block):
            hasher.update(chunk)
    return hasher.hexdigest()


def calibration_paths(band: str) -> list[Path]:
    return (
        [REPO / "energetics" / "studies" / "burst-energies" / "chime_sefd.csv"]
        if band == "CHIME"
        else [
            DSA_BEAM_CUBE,
            REPO / "energetics" / "studies" / "burst-energies" / "dsa_sefd.csv",
            REPO / "energetics" / "studies" / "burst-energies" / "dsa_pointing.csv",
        ]
    )


def calibration_digest(band: str) -> str:
    hasher = hashlib.sha256()
    for path in calibration_paths(band):
        hasher.update(path.name.encode())
        hasher.update(bytes.fromhex(digest(path)))
    return hasher.hexdigest()


def burst_config(nick: str, telescope: str) -> dict:
    filename = "johndoeII" if nick == "johndoeii" else nick
    path = REPO / "scattering" / "configs" / "bursts" / telescope / f"{filename}_{telescope}.yaml"
    return yaml.safe_load(path.read_text())


def one_measurement(
    nick: str, band: str, data_dir: Path, threshold: float, pad_factor: float
) -> dict:
    telescope = "chime" if band == "CHIME" else "dsa"
    config = burst_config(nick, telescope)
    source = data_dir / Path(config["path"]).name
    tel = load_telescope_block(
        str(REPO / "scattering" / "configs" / "telescopes.yaml"), telescope
    )
    dataset = BurstDataset(
        source,
        source,
        telescope=tel,
        f_factor=int(config.get("f_factor", 1)),
        t_factor=int(config.get("t_factor", 1)),
        onpulse_crop=True,
        onpulse_thresh=threshold,
        onpulse_pad_factor=pad_factor,
    )
    if dataset.onpulse_crop_status != "applied":
        raise ValueError(dataset.onpulse_crop_status)
    model = dataset.model
    noise = np.clip(model.noise_std, 1e-9, None)
    sn_integrated = np.nansum(model.data / noise[:, None], axis=1)
    freq_hz = model.freq * 1e9
    dnu_hz = dataset.df_MHz * 1e6
    dt_ms = dataset.dt_ms
    if band == "CHIME":
        sigma_jy = chime_sigma_jy(
            freq_hz, dnu_hz, load_chime_sefd(), dt_ms / 1e3, g=1.0
        )
    else:
        _mjd, _ra, dec = burst_epoch_position(nick)
        theta, phi = dsa_beam_offset(dec, dsa_pointing_dec(nick))
        sigma_jy = dsa_sigma_jy(
            freq_hz,
            dnu_hz,
            load_dsa_sefd_beam(nick),
            dt_ms / 1e3,
            theta,
            phi,
            lambda th, ph, freq: dsa_beam.beam_gain(
                th, ph, freq, path=DSA_BEAM_CUBE
            ),
        )
    fluence = calibrated_band_integral_jy_ms_hz(
        sn_integrated, sigma_jy, freq_hz, dt_ms
    )
    # Independent-channel radiometer approximation. Correlated-noise validation
    # remains a measurement gate and is not hidden in this statistical term.
    channel_width = float(np.median(np.diff(freq_hz)))
    weights = np.full(freq_hz.size, channel_width)
    weights[[0, -1]] *= 0.5
    channel_error = sigma_jy * dt_ms * np.sqrt(model.data.shape[1]) * weights
    stat_err = float(np.sqrt(np.sum(channel_error**2)))
    return {"fluence": fluence, "stat_err": stat_err, "source": source}


def measure(nick: str, band: str, data_dir: Path) -> dict:
    values, failures = [], []
    for threshold in (2.5, 3.0, 3.5):
        for pad_factor in (0.25, 0.5, 1.0):
            try:
                row = one_measurement(nick, band, data_dir, threshold, pad_factor)
                row.update(threshold=threshold, pad_factor=pad_factor)
                values.append(row)
            except (FileNotFoundError, ValueError, IndexError) as exc:
                failures.append(f"{threshold}/{pad_factor}:{exc}")
    if failures or len(values) != 9:
        return {
            "nickname": nick,
            "band": band,
            "fluence_jy_ms_hz": "",
            "stat_err_jy_ms_hz": "",
            "window_status": "failed:" + ";".join(failures),
            "window_sensitivity_frac": "",
            "calibration_status": "pending_review",
            "calibration_systematic_dex": "",
            "noise_status": "pending_validation",
            "review_status": "pending",
            "input_path": "",
            "input_sha256": "",
            "calibration_paths": "",
            "calibration_sha256": "",
            "thresholds_sigma": "2.5,3.0,3.5",
            "pad_factors": "0.25,0.5,1.0",
        }
    central = next(
        row for row in values if row["threshold"] == 3.0 and row["pad_factor"] == 0.5
    )
    spread = (max(v["fluence"] for v in values) - min(v["fluence"] for v in values)) / abs(
        central["fluence"]
    )
    return {
        "nickname": nick,
        "band": band,
        "fluence_jy_ms_hz": f"{central['fluence']:.17g}",
        "stat_err_jy_ms_hz": f"{central['stat_err']:.17g}",
        "window_status": "candidate" if spread <= 0.10 else "failed_unstable",
        "window_sensitivity_frac": f"{spread:.8g}",
        "calibration_status": "pending_review",
        "calibration_systematic_dex": "",
        "noise_status": "pending_validation",
        "review_status": "pending",
        "input_path": str(central["source"]),
        "input_sha256": digest(central["source"]),
        "calibration_paths": ";".join(str(path.resolve()) for path in calibration_paths(band)),
        "calibration_sha256": calibration_digest(band),
        "thresholds_sigma": "2.5,3.0,3.5",
        "pad_factors": "0.25,0.5,1.0",
    }


def main() -> int:
    global DSA_BEAM_CUBE
    parser = argparse.ArgumentParser()
    parser.add_argument("--chime-data-dir", required=True, type=Path)
    parser.add_argument("--dsa-data-dir", required=True, type=Path)
    parser.add_argument("--dsa-beam-cube", type=Path, default=DSA_BEAM_CUBE)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    DSA_BEAM_CUBE = args.dsa_beam_cube.resolve()
    rows = []
    for nick in NICKNAMES:
        rows.append(measure(nick, "CHIME", args.chime_data_dir))
        rows.append(measure(nick, "DSA", args.dsa_data_dir))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    failures = sum(row["window_status"].startswith("failed") for row in rows)
    print(f"wrote {args.output}: {len(rows)} band receipts, {failures} failed windows")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
