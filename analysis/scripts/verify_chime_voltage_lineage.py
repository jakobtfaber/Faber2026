"""Reconstruct native-resolution CHIME references; align on held-out noise only."""

import hashlib
import json
import platform
from pathlib import Path

import h5py
import numpy as np
from scipy.signal import correlate

NAMES = ("casey", "freya", "isha", "mahi", "oran", "phineas", "whitney")
K_DM = 1 / 2.41e-4
TRAIN = slice(4096, 8192)
HOLD = slice(8192, 12288)
PULSE = slice(12800, 19200)
IDENTITY_TOLERANCE = 64 * np.finfo(np.float32).eps


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dechirp(voltage, dm, frequency_mhz, dt_s):
    frequency = np.fft.fftfreq(voltage.shape[-1], d=dt_s * 1e6)
    phase = (
        2j
        * np.pi
        * 1e6
        * K_DM
        * dm
        * frequency**2
        / ((frequency + frequency_mhz) * frequency_mhz**2)
    )
    return np.fft.ifft(np.fft.fft(voltage, axis=-1) * np.exp(phase), axis=-1)


def correlation(left, right):
    a = np.asarray(left, dtype=float) - np.mean(left)
    b = np.asarray(right, dtype=float) - np.mean(right)
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denominator) if denominator > 0 else 0.0


def match_noise(reference, native):
    template = native[TRAIN] - native[TRAIN].mean()
    length = template.size
    score = correlate(reference, template, mode="valid", method="fft")
    total = np.r_[0.0, np.cumsum(reference)]
    squares = np.r_[0.0, np.cumsum(reference**2)]
    variance = (
        squares[length:] - squares[:-length] - (total[length:] - total[:-length]) ** 2 / length
    )
    denominator = np.sqrt(np.maximum(variance, 0) * np.dot(template, template))
    score = np.divide(score, denominator, out=np.full(score.shape, -np.inf), where=denominator > 0)
    peak = int(np.argmax(score))
    origin = peak - TRAIN.start
    train_score = float(score[peak])
    score[max(0, peak - 2) : peak + 3] = -np.inf
    alternate = float(np.max(score))
    if origin + HOLD.start < 0 or origin + HOLD.stop > reference.size:
        return None
    held = correlation(native[HOLD], reference[origin + HOLD.start : origin + HOLD.stop])
    if train_score < 0.95 or held < 0.95 or alternate > 0.5:
        return None
    return {
        "origin_sample": origin,
        "train_correlation": train_score,
        "holdout_correlation": held,
        "alternate_correlation": alternate,
    }


def pulse_lag(native, reference):
    a, b = native[PULSE], reference[PULSE]
    scores = []
    for lag in range(-32, 33):
        left, right = (
            (a[lag:], b[:-lag]) if lag > 0 else ((a[:lag], b[-lag:]) if lag < 0 else (a, b))
        )
        scores.append(correlation(left, right))
    index = int(np.argmax(scores))
    return {
        "lag_native_bins": index - 32,
        "correlation": scores[index],
        "search_boundary": index in (0, 64),
    }


def waveform_error(native, reference):
    if not np.isfinite(native).all() or not np.isfinite(reference).all():
        return float("inf")
    return float(np.max(np.abs(native - reference) / (1 + np.abs(reference))))


def reconstruct_row(h5, row, native, dm):
    voltage = h5["tiedbeam_baseband"][row]
    valid = np.isfinite(voltage).all(axis=0)
    missing = np.flatnonzero(~valid)
    length = int(missing[0]) if missing.size else valid.size
    if length < HOLD.stop or not np.isfinite(native).all() or np.std(native[TRAIN]) == 0:
        return "invalid-voltage-or-native-support"
    frequency = float(h5["index_map/freq"][row]["centre"])
    input_dm = float(h5["tiedbeam_baseband"].attrs.get("DM", 0))
    field = dechirp(voltage[:, :length], dm - input_dm, frequency, float(h5.attrs["delta_time"]))
    reference = np.sum(np.abs(field) ** 2, axis=0)
    match = match_noise(reference, native)
    if match is None:
        return "noise-identity-rejected"
    start = match["origin_sample"]
    if start + PULSE.start < 0 or start + PULSE.stop > reference.size:
        return "pulse-outside-reference"
    aligned = np.full(native.size, np.nan)
    lo, hi = max(0, -start), min(native.size, reference.size - start)
    aligned[lo:hi] = reference[start + lo : start + hi]
    reference = aligned
    match["frequency_mhz"] = frequency
    match["reference_coverage_native_samples"] = [lo, hi]
    match["first_4096_correlation"] = (
        correlation(native[:4096], reference[:4096]) if lo == 0 else None
    )
    match["last_4096_correlation"] = (
        correlation(native[-4096:], reference[-4096:]) if hi == native.size else None
    )
    native = (native - native[TRAIN].mean()) / native[TRAIN].std()
    reference = (reference - reference[TRAIN].mean()) / reference[TRAIN].std()
    match["holdout_waveform_error"] = waveform_error(native[HOLD], reference[HOLD])
    match["pulse_waveform_error"] = waveform_error(native[PULSE], reference[PULSE])
    return match, native, reference


def event(name):
    cube_paths = list(
        Path("/data/research/astrophysics/frbs/chime-dsa-codetections/manifest_cubes").glob(
            name + "_chime_I_*_32000b_cntr_bpc.npy"
        )
    )
    raw_paths = list(Path("/data/Faber2026/data/chime-frb", name).glob("*.h5"))
    if len(cube_paths) != 1 or len(raw_paths) != 1:
        raise ValueError("ambiguous input paths for " + name)
    cube_path, raw_path = cube_paths[0], raw_paths[0]
    cube = np.load(cube_path, mmap_mode="r", allow_pickle=False)
    if cube.shape != (1024, 32000):
        raise ValueError("unexpected native cube shape")
    dm = float(".".join(cube_path.stem.split("_")[3:5]))
    matches, rejected = [], []
    native_sum = np.zeros(32000)
    reference_sum = np.zeros(32000)
    groups = {label: [np.zeros(32000), np.zeros(32000), 0] for label in ("low", "high")}
    native_finite = set(np.flatnonzero(np.isfinite(cube).any(axis=1)).tolist())
    constant_channels = {i for i in native_finite if np.nanstd(cube[i]) == 0}
    native_live = native_finite - constant_channels
    with h5py.File(raw_path, "r") as h5:
        frequency_map = h5["index_map/freq"][:]
        ids = frequency_map["id"].astype(int)
        if len(set(ids)) != len(ids) or np.any(ids < 0) or np.any(ids >= 1024):
            raise ValueError("invalid frequency identities")
        if float(h5.attrs["delta_time"]) != 2.56e-6:
            raise ValueError("unexpected native cadence")
        counters = h5["time0"]["fpga_count"]
        present = 0
        for row, channel in enumerate(ids):
            native = np.asarray(cube[channel], dtype=float)
            if channel not in native_live:
                continue
            if not np.isfinite(native).all():
                rejected.append({"channel_id": int(channel), "reason": "nonfinite-native-support"})
                continue
            if np.std(native[TRAIN]) == 0:
                rejected.append({"channel_id": int(channel), "reason": "constant-training-window"})
                continue
            present += 1
            result = reconstruct_row(h5, row, native, dm)
            if isinstance(result, str):
                rejected.append({"channel_id": int(channel), "reason": result})
                continue
            match, normal_native, normal_reference = result
            frequency = match["frequency_mhz"]
            ctime = (int(counters[row]) - int(counters[-1])) * 2.56e-6
            match["channel_id"] = int(channel)
            match["origin_at_400_s"] = (
                match["origin_sample"] * 2.56e-6 + ctime - K_DM * dm * (frequency**-2 - 400**-2)
            )
            matches.append(match)
            native_sum += normal_native
            reference_sum += normal_reference
            group = groups["low" if frequency < 600 else "high"]
            group[0] += normal_native
            group[1] += normal_reference
            group[2] += 1
    report = {
        "burst": name,
        "native_path": str(cube_path),
        "raw_path": str(raw_path),
        "native_sha256": sha256(cube_path),
        "raw_sha256": sha256(raw_path),
        "dm_filename_package_coordinate": dm,
        "matched_channels": matches,
        "native_present_channels": present,
        "native_live_channels": len(native_live),
        "native_constant_channels": sorted(constant_channels),
        "native_channels_missing_from_h5": sorted(native_live - set(ids.tolist())),
        "rejected_channels": rejected,
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "h5py": h5py.__version__,
            "platform": platform.platform(),
        },
    }
    if not matches:
        report["verdict"] = "inconclusive-no-noise-alignment"
        return report
    origin = np.array([m["origin_at_400_s"] for m in matches])
    spread = float(np.ptp(origin) / 2.56e-6)
    report.update(
        origin_at_400_s=float(np.median(origin)),
        origin_spread_bins=spread,
        pulse=pulse_lag(native_sum, reference_sum),
        subbands={
            label: {"channels": g[2], **pulse_lag(g[0], g[1])}
            for label, g in groups.items()
            if g[2]
        },
    )
    lag_ok = all(
        abs(x["lag_native_bins"]) < 5 and not x["search_boundary"]
        for x in [report["pulse"], *report["subbands"].values()]
    )
    identity_ok = all(
        max(m["holdout_waveform_error"], m["pulse_waveform_error"]) <= IDENTITY_TOLERANCE
        for m in matches
    )
    report["waveform_identity_tolerance"] = float(IDENTITY_TOLERANCE)
    report["waveform_identity_pass"] = identity_ok
    support_ok = (
        len(matches) >= 16 and len(matches) == len(native_live) and len(report["subbands"]) == 2
    )
    report["verdict"] = (
        "heldout-waveform-identity-pass"
        if lag_ok and identity_ok and support_ok and spread <= 1.1
        else "inconclusive-alignment-or-support"
    )
    report["plot_profiles"] = {
        "native": (native_sum / len(matches)).reshape(-1, 128).mean(1).tolist(),
        "reference": [
            float(x) if np.isfinite(x) else None
            for x in (reference_sum / len(matches)).reshape(-1, 128).mean(1)
        ],
    }
    return report


if __name__ == "__main__":
    import sys

    for name in sys.argv[1:] or NAMES:
        print(json.dumps(event(name), allow_nan=False), flush=True)
