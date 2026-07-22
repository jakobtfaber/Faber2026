#!/usr/bin/env python3
"""Validate and apply owner-reviewed event-specific bad-channel maps."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

SCHEMA_VERSION = 1
APPROVED_STATUS = "owner_approved"
EFFECTIVE_STATUS = "owner_approved_effective_mask"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_map(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError("bad-channel map must be a JSON object")
    return payload


def frequency_values_sha256(frequency_mhz: np.ndarray) -> str:
    """Hash frequency values independently of their container file path."""
    frequency = np.ascontiguousarray(frequency_mhz, dtype=np.float64)
    return hashlib.sha256(frequency.tobytes()).hexdigest()


def bad_row_mask(
    payload: dict[str, Any],
    frequency_mhz: np.ndarray,
    *,
    frequency_sha256: str,
    source_sha256: str,
    require_approved: bool = True,
) -> np.ndarray:
    """Return the exact reviewed bad-row mask or fail closed."""
    frequency = np.asarray(frequency_mhz, dtype=float)
    if frequency.ndim != 1 or not np.isfinite(frequency).all():
        raise ValueError("frequency axis must be finite and one-dimensional")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported bad-channel map schema")
    if require_approved and payload.get("status") != APPROVED_STATUS:
        raise ValueError("bad-channel map is not owner-approved")
    binding = payload.get("frequency_axis")
    if not isinstance(binding, dict):
        raise ValueError("frequency_axis binding is required")
    if binding.get("sha256") != frequency_sha256:
        raise ValueError("frequency-axis SHA-256 mismatch")
    if binding.get("row_count") != frequency.size:
        raise ValueError("frequency-axis row count mismatch")
    source = payload.get("source_product")
    if not isinstance(source, dict) or source.get("sha256") != source_sha256:
        raise ValueError("source-product SHA-256 mismatch")
    if require_approved:
        review = payload.get("review")
        if not isinstance(review, dict) or not review.get("reviewer") or not review.get(
            "reviewed_at"
        ):
            raise ValueError("approved map requires reviewer and review time")

    ranges = payload.get("bad_row_ranges")
    if not isinstance(ranges, list):
        raise ValueError("bad_row_ranges must be a list")
    mask = np.zeros(frequency.size, dtype=bool)
    previous_stop = 0
    for index, item in enumerate(ranges):
        if not isinstance(item, dict):
            raise ValueError("each bad-row range must be an object")
        start, stop = item.get("start"), item.get("stop")
        if not isinstance(start, int) or not isinstance(stop, int):
            raise ValueError("bad-row bounds must be integers")
        if not 0 <= start < stop <= frequency.size:
            raise ValueError("bad-row range is outside the frequency axis")
        if index and start < previous_stop:
            raise ValueError("bad-row ranges must be sorted and non-overlapping")
        if not item.get("reason") or not item.get("evidence"):
            raise ValueError("each bad-row range requires reason and evidence")
        selected = frequency[start:stop]
        expected_low = float(np.min(selected))
        expected_high = float(np.max(selected))
        if not np.isclose(item.get("frequency_min_mhz"), expected_low, atol=1e-9):
            raise ValueError("bad-row minimum frequency does not match the bound axis")
        if not np.isclose(item.get("frequency_max_mhz"), expected_high, atol=1e-9):
            raise ValueError("bad-row maximum frequency does not match the bound axis")
        mask[start:stop] = True
        previous_stop = stop
    return mask


def apply_bad_rows(values: np.ndarray, bad_rows: np.ndarray) -> np.ndarray:
    """Return a copy with reviewed bad rows represented only by NaN."""
    data = np.asarray(values)
    rows = np.asarray(bad_rows, dtype=bool)
    if data.ndim < 1 or rows.shape != (data.shape[0],):
        raise ValueError("bad-row mask must match the first data dimension")
    output = np.array(data, copy=True, dtype=np.result_type(data.dtype, np.float32))
    output[rows] = np.nan
    return output


def effective_bad_row_mask(
    payload: dict[str, Any],
    frequency_mhz: np.ndarray,
    source_valid: np.ndarray,
    *,
    frequency_sha256: str,
    source_sha256: str,
    source_valid_sha256: str,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Return exactly ``source unavailable OR owner manual``.

    Correctness criterion: exact Boolean set equality. The source-valid array is
    an input authority, not a display convenience, and is hash-bound by the map.
    """
    frequency = np.asarray(frequency_mhz, dtype=float)
    valid = np.asarray(source_valid)
    if valid.dtype != np.bool_ or valid.shape != frequency.shape:
        raise ValueError("source-valid mask must be Boolean and match the frequency axis")
    binding = payload.get("frequency_axis")
    if not isinstance(binding, dict) or binding.get("source_valid_sha256") != source_valid_sha256:
        raise ValueError("source-valid SHA-256 mismatch")
    manual = bad_row_mask(
        payload,
        frequency,
        frequency_sha256=frequency_sha256,
        source_sha256=source_sha256,
        require_approved=True,
    )
    source_unavailable = ~valid
    effective = source_unavailable | manual
    if not np.array_equal(effective, np.logical_or(source_unavailable, manual)):
        raise RuntimeError("effective bad-channel union invariant failed")
    return effective, {
        "source_unavailable": source_unavailable,
        "manual": manual,
    }


def write_effective_mask_artifact(
    payload: dict[str, Any],
    frequency_mhz: np.ndarray,
    source_valid: np.ndarray,
    *,
    frequency_sha256: str,
    source_sha256: str,
    source_valid_sha256: str,
    map_sha256: str,
    output_mask: Path,
    output_provenance: Path,
) -> dict[str, Any]:
    """Write a hash-bound ACF mask and its independently inspectable record."""
    effective, components = effective_bad_row_mask(
        payload,
        frequency_mhz,
        source_valid,
        frequency_sha256=frequency_sha256,
        source_sha256=source_sha256,
        source_valid_sha256=source_valid_sha256,
    )
    output_mask.parent.mkdir(parents=True, exist_ok=True)
    output_provenance.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_mask, effective, allow_pickle=False)
    manual = components["manual"]
    source_unavailable = components["source_unavailable"]
    overlap = source_unavailable & manual
    binding = payload["frequency_axis"]
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": EFFECTIVE_STATUS,
        "event": payload.get("event"),
        "instrument": payload.get("instrument"),
        "frequency_axis": {
            "path": binding.get("path"),
            "sha256": frequency_sha256,
            "values_sha256": frequency_values_sha256(frequency_mhz),
            "row_count": int(np.asarray(frequency_mhz).size),
        },
        "source_product": payload.get("source_product"),
        "effective_mask": {
            "path": str(output_mask),
            "sha256": sha256(output_mask),
            "rows": int(effective.sum()),
        },
        "components": {
            "source_unavailable": {
                "source_valid_path": binding.get("source_valid_path"),
                "source_valid_sha256": source_valid_sha256,
                "rows": int(source_unavailable.sum()),
            },
            "owner_manual": {
                "map_sha256": map_sha256,
                "rows": int(manual.sum()),
            },
            "overlap": {"rows": int(overlap.sum())},
        },
        "union_rule": "source_unavailable OR owner_manual",
        "review": payload.get("review"),
    }
    output_provenance.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return record


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--frequency", type=Path, required=True)
    parser.add_argument("--source-product", type=Path, required=True)
    parser.add_argument("--source-valid", type=Path)
    parser.add_argument("--output-mask", type=Path)
    parser.add_argument("--output-provenance", type=Path)
    parser.add_argument("--allow-draft", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    frequency = np.load(args.frequency)
    payload = load_map(args.map)
    if args.source_valid is not None:
        if args.allow_draft:
            raise ValueError("effective science masks cannot be materialized from drafts")
        if args.output_mask is None or args.output_provenance is None:
            raise ValueError("effective mask requires --output-mask and --output-provenance")
        record = write_effective_mask_artifact(
            payload,
            frequency,
            np.load(args.source_valid),
            frequency_sha256=sha256(args.frequency),
            source_sha256=sha256(args.source_product),
            source_valid_sha256=sha256(args.source_valid),
            map_sha256=sha256(args.map),
            output_mask=args.output_mask,
            output_provenance=args.output_provenance,
        )
        mask = np.load(args.output_mask)
    else:
        if args.output_provenance is not None:
            raise ValueError("--output-provenance requires --source-valid")
        mask = bad_row_mask(
            payload,
            frequency,
            frequency_sha256=sha256(args.frequency),
            source_sha256=sha256(args.source_product),
            require_approved=not args.allow_draft,
        )
        if args.output_mask is not None:
            np.save(args.output_mask, mask)
        record = None
    print(
        json.dumps(
            {
                "map": str(args.map),
                "frequency": str(args.frequency),
                "frequency_sha256": sha256(args.frequency),
                "source_product": str(args.source_product),
                "source_sha256": sha256(args.source_product),
                "bad_rows": int(mask.sum()),
                "effective_provenance": (
                    str(args.output_provenance) if record is not None else None
                ),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
