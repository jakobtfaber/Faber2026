"""Read-only prerequisites and low-signal diagnostics; never certifies alignment."""

import ast
import hashlib
import json
import platform
from pathlib import Path

import numpy as np

ROOT = Path("/data/research/astrophysics/frbs/chime-dsa-codetections")
NAMES = ("casey", "freya", "isha", "mahi", "oran", "phineas", "whitney")
LOW_SIGNAL = ("isha", "mahi", "oran", "phineas")
WIDTHS = (1, 4, 16, 64, 256, 1024)
NATIVE_DT_S = 2.56e-6


def identity(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path), "sha256": digest.hexdigest(), "bytes": path.stat().st_size}


def block_diagnostic(profile, width):
    values = np.asarray(profile, dtype=np.float64)
    if width < 1 or width > values.size or not np.isfinite(values).all():
        raise ValueError("finite profile and positive supported width required")
    size = values.size // width
    reduced = values[: size * width].reshape(size, width).mean(axis=1)
    baseline = np.median(reduced)
    noise = 1.4826 * np.median(np.abs(reduced - baseline))
    if not np.isfinite(noise) or noise <= 0:
        raise ValueError("positive finite noise scale required")
    snr = (reduced - baseline) / noise
    centers = (np.arange(size) * width + (width - 1) / 2) / values.size
    middle = (centers > 0.4) & (centers < 0.6)
    edges = (centers < 0.02) | (centers > 0.98)
    return {
        "width_native_samples": width,
        "width_us": width * NATIVE_DT_S * 1e6,
        "discarded_tail_samples": int(values.size - size * width),
        "central_max_snr": float(snr[middle].max()),
        "edge_max_snr": float(snr[edges].max()) if edges.any() else None,
        "noise_mad": float(noise),
    }


def target_config(path):
    tree = ast.parse(path.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "TARGETS" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise ValueError("TARGETS literal missing")


def array_identity(path):
    result = identity(path)
    array = np.load(path, mmap_mode="r", allow_pickle=False)
    result.update(shape=list(array.shape), dtype=str(array.dtype))
    return result


def audit_event(name, config):
    matches = sorted((ROOT / "manifest_cubes").glob(name + "_chime_I_*_32000b_cntr_bpc.npy"))
    if len(matches) != 1:
        raise ValueError("expected exactly one native cube for " + name)
    native = matches[0]
    array = np.load(native, mmap_mode="r", allow_pickle=False)
    if array.shape != (1024, 32000):
        raise ValueError("unexpected native shape")
    # Sum/count avoids all-NaN channel warnings and preserves missing samples.
    counts = np.isfinite(array).sum(axis=0)
    profile = np.divide(
        np.nansum(array, axis=0, dtype=np.float64),
        counts,
        out=np.full(array.shape[1], np.nan),
        where=counts > 0,
    )
    up = ROOT / "upchan_codetections"
    metadata_path = up / (name + "_time0_metadata.json")
    metadata = json.loads(metadata_path.read_text())
    reference = array_identity(up / (name + "_chime_upchan.npy"))
    reference["frequency_file"] = array_identity(up / (name + "_chime_freq.npy"))
    reference["time0_file"] = identity(metadata_path)
    reference["generation_log"] = identity(
        up
        / (
            "upchannelize_"
            + name
            + "_noshift_"
            + ("20260704" if name == "freya" else "20260707" if name == "oran" else "20260706")
            + ".log"
        )
    )
    reference["dt_s"] = float(metadata["delta_time"] * 2 * config["upchan"])
    reference["dm"] = config["dm"]
    parts = native.stem.split("_")
    return {
        "burst": name,
        "native": array_identity(native),
        "native_dt_s_config": NATIVE_DT_S,
        "native_dm_filename": float(parts[3] + "." + parts[4]),
        "reference": reference,
        "reference_sample_in_native_bins": reference["dt_s"] / NATIVE_DT_S,
        "native_origin_evidence": None,
        "aligned_lag_native_bins": None,
        "cross_verdict": "blocked-missing-native-crop-origin",
        "diagnostics": [
            block_diagnostic(profile, w) for w in (WIDTHS if name in LOW_SIGNAL else (1,))
        ],
    }


def main():
    source = ROOT / "scripts/upchannelize_chime.py"
    config = target_config(source)
    report = {
        "schema": "chime-alignment-prerequisites-v1",
        "status": "aligned-verification-blocked",
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "platform": platform.platform(),
            "host": platform.node(),
        },
        "reference_builder": identity(source),
        "events": [audit_event(name, config[name]) for name in NAMES],
    }
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
