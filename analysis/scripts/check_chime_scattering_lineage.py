#!/usr/bin/env python3
"""Read-only checksum and wrap-defect checks for CHIME scattering cubes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

DEFAULT_ROOTS = (
    Path("/data/Faber2026/runs/flits-runs/data"),
    Path(
        "/data/research/astrophysics/frbs/chime-dsa-codetections/manifest_cubes"
    ),
)
PATTERN = "*_32000b_cntr_bpc.npy"


def sha256(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def profile_metrics(profile: np.ndarray) -> dict[str, Any]:
    values = np.asarray(profile, dtype=float)
    baseline = float(np.nanmedian(values))
    noise = float(1.4826 * np.nanmedian(np.abs(values - baseline)))
    snr = (values - baseline) / max(noise, 1e-12)
    hot = np.isfinite(snr) & (snr > 5.0)
    edge_width = values.size // 50
    edge_hot_count = int(hot[:edge_width].sum() + hot[-edge_width:].sum())
    indices = np.flatnonzero(hot)
    centroid = None
    if indices.size:
        weights = snr[indices]
        centroid = float(np.sum(weights * indices) / np.sum(weights))
    centered = centroid is not None and 0.4 * values.size < centroid < 0.6 * values.size
    reasons = []
    if not indices.size:
        reasons.append("no-burst-above-5sigma")
    if edge_hot_count:
        reasons.append("edge-significance")
    if centroid is not None and not centered:
        reasons.append("off-center")
    return {
        "baseline": baseline,
        "noise_mad_sigma": noise,
        "max_snr": float(np.nanmax(snr)),
        "hot_count": int(indices.size),
        "edge_width": edge_width,
        "edge_hot_count": edge_hot_count,
        "centroid_bin": centroid,
        "centroid_fraction": None if centroid is None else centroid / values.size,
        "verdict": "pass" if not reasons else "fail",
        "reasons": reasons,
    }


def inspect_cube(path: Path, root: Path) -> dict[str, Any]:
    cube = np.load(path, mmap_mode="r")
    if cube.ndim != 2:
        raise ValueError(f"{path}: expected two dimensions, got {cube.shape}")
    with np.errstate(invalid="ignore"):
        profile = np.nanmean(cube, axis=0, dtype=np.float64)
    result = {
        "path": str(path),
        "root": str(root.resolve()),
        "filename": path.name,
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "shape": list(cube.shape),
        "dtype": str(cube.dtype),
        "nan_fraction": float(np.isnan(cube).sum() / cube.size),
    }
    result.update(profile_metrics(profile))
    return result


def group_by_filename(
    cubes: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    by_name: dict[str, list[dict[str, Any]]] = {}
    for cube in cubes:
        by_name.setdefault(cube["filename"], []).append(cube)
    return by_name


def pair_records(
    by_name: dict[str, list[dict[str, Any]]], expected_roots: list[str]
) -> tuple[list[dict[str, Any]], list[str]]:
    pairs: list[dict[str, Any]] = []
    for filename, matches in sorted(by_name.items()):
        hashes = {match["sha256"] for match in matches}
        copy_roots = [match["root"] for match in matches]
        roots_match = (
            sorted(copy_roots) == sorted(expected_roots)
            and len(set(copy_roots)) == len(copy_roots)
        )
        pairs.append(
            {
                "filename": filename,
                "copies": len(matches),
                "hashes_match": len(hashes) == 1,
                "roots_match": roots_match,
                "sha256": matches[0]["sha256"],
            }
        )
    malformed_pairs = [
        pair["filename"]
        for pair in pairs
        if pair["copies"] != 2
        or not pair["hashes_match"]
        or not pair["roots_match"]
    ]
    return pairs, malformed_pairs


def run(roots: tuple[Path, ...]) -> dict[str, Any]:
    resolved_roots = [str(root.resolve()) for root in roots]
    paths = [
        (root, path) for root in roots for path in sorted(root.glob(PATTERN))
    ]
    cubes = [inspect_cube(path, root) for root, path in paths]
    by_name = group_by_filename(cubes)
    pairs, malformed_pairs = pair_records(by_name, resolved_roots)
    failed = [cube["path"] for cube in cubes if cube["verdict"] != "pass"]
    topology_errors = []
    if len(roots) != 2:
        topology_errors.append("expected-exactly-two-roots")
    if len(set(resolved_roots)) != len(resolved_roots):
        topology_errors.append("roots-not-distinct")
    if len(by_name) != 12:
        topology_errors.append("expected-exactly-twelve-filenames")
    return {
        "schema": "faber2026-chime-scattering-lineage-check/v1",
        "read_only": True,
        "criteria": {
            "profile": "NaN-aware frequency mean",
            "noise": "1.4826 times median absolute deviation",
            "signal_threshold_sigma": 5.0,
            "edge_fraction_each_side": 0.02,
            "centroid_fraction_open_interval": [0.4, 0.6],
        },
        "roots": [str(root) for root in roots],
        "summary": {
            "cube_count": len(cubes),
            "unique_filename_count": len(by_name),
            "direct_pass_count": len(cubes) - len(failed),
            "direct_fail_count": len(failed),
            "pair_count": len(pairs),
            "malformed_pair_count": len(malformed_pairs),
            "topology_error_count": len(topology_errors),
            "all_24_pass": (
                len(cubes) == 24
                and not failed
                and not malformed_pairs
                and not topology_errors
            ),
        },
        "failed_paths": failed,
        "malformed_pairs": malformed_pairs,
        "topology_errors": topology_errors,
        "pairs": pairs,
        "cubes": cubes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", action="append", type=Path)
    args = parser.parse_args()
    roots = tuple(args.root) if args.root else DEFAULT_ROOTS
    print(json.dumps(run(roots), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
