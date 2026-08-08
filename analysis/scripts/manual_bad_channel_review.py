#!/usr/bin/env python3
"""Interactively select exact bad-channel rows and save a draft map."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, NamedTuple

import numpy as np


BUNDLE_SCHEMA_VERSION = 1
MAP_SCHEMA_VERSION = 1
APPROVED_STATUS = "owner_approved"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class ReviewBundle(NamedTuple):
    dynamic_spectrum: np.ndarray
    frequency_mhz: np.ndarray
    row_valid: np.ndarray
    time_ms: np.ndarray
    off_mean: np.ndarray
    off_standard_deviation: np.ndarray
    on_spectrum: np.ndarray
    metadata: dict[str, Any]


def validate_review_bundle(bundle: ReviewBundle) -> None:
    dynamic = np.asarray(bundle.dynamic_spectrum)
    frequency = np.asarray(bundle.frequency_mhz, dtype=float)
    valid = np.asarray(bundle.row_valid, dtype=bool)
    time = np.asarray(bundle.time_ms, dtype=float)
    row_arrays = (
        np.asarray(bundle.off_mean),
        np.asarray(bundle.off_standard_deviation),
        np.asarray(bundle.on_spectrum),
    )
    if dynamic.ndim != 2:
        raise ValueError("dynamic spectrum must be two-dimensional")
    if frequency.shape != (dynamic.shape[0],) or valid.shape != frequency.shape:
        raise ValueError("frequency and row-valid arrays must match dynamic rows")
    if time.shape != (dynamic.shape[1],):
        raise ValueError("time axis must match dynamic columns")
    if any(values.shape != frequency.shape for values in row_arrays):
        raise ValueError("row measures must match the frequency axis")
    if not np.isfinite(frequency).all() or not np.isfinite(time).all():
        raise ValueError("frequency and time axes must be finite")
    metadata = bundle.metadata
    if not isinstance(metadata, dict) or metadata.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        raise ValueError("unsupported review-bundle schema")
    for key in ("event", "instrument", "frequency_axis_sha256", "source_product_sha256"):
        if not metadata.get(key):
            raise ValueError(f"review bundle requires {key}")


def load_review_bundle(path: Path) -> ReviewBundle:
    with np.load(path, allow_pickle=False) as values:
        required = {
            "dynamic_spectrum",
            "frequency_mhz",
            "row_valid",
            "time_ms",
            "off_mean",
            "off_standard_deviation",
            "on_spectrum",
            "metadata_json",
        }
        missing = sorted(required - set(values.files))
        if missing:
            raise ValueError(f"review bundle missing: {', '.join(missing)}")
        metadata = json.loads(str(values["metadata_json"].item()))
        bundle = ReviewBundle(
            dynamic_spectrum=np.array(values["dynamic_spectrum"], copy=True),
            frequency_mhz=np.array(values["frequency_mhz"], copy=True),
            row_valid=np.array(values["row_valid"], dtype=bool, copy=True),
            time_ms=np.array(values["time_ms"], copy=True),
            off_mean=np.array(values["off_mean"], copy=True),
            off_standard_deviation=np.array(
                values["off_standard_deviation"], copy=True
            ),
            on_spectrum=np.array(values["on_spectrum"], copy=True),
            metadata=metadata,
        )
    validate_review_bundle(bundle)
    return bundle


def verify_map_binding(payload: dict[str, Any], bundle: ReviewBundle) -> None:
    validate_review_bundle(bundle)
    if payload.get("schema_version") != MAP_SCHEMA_VERSION:
        raise ValueError("unsupported bad-channel map schema")
    if payload.get("event") != bundle.metadata["event"]:
        raise ValueError("event mismatch between map and review bundle")
    if payload.get("instrument") != bundle.metadata["instrument"]:
        raise ValueError("instrument mismatch between map and review bundle")
    frequency = payload.get("frequency_axis")
    if not isinstance(frequency, dict):
        raise ValueError("frequency-axis binding is required")
    if frequency.get("sha256") != bundle.metadata["frequency_axis_sha256"]:
        raise ValueError("frequency-axis SHA-256 mismatch")
    if frequency.get("row_count") != bundle.frequency_mhz.size:
        raise ValueError("frequency-axis row count mismatch")
    source = payload.get("source_product")
    if not isinstance(source, dict):
        raise ValueError("source-product binding is required")
    if source.get("sha256") != bundle.metadata["source_product_sha256"]:
        raise ValueError("source-product SHA-256 mismatch")


def rows_for_frequency_span(
    frequency_mhz: np.ndarray,
    row_valid: np.ndarray,
    minimum_mhz: float,
    maximum_mhz: float,
) -> np.ndarray:
    frequency = np.asarray(frequency_mhz, dtype=float)
    valid = np.asarray(row_valid, dtype=bool)
    if frequency.ndim != 1 or valid.shape != frequency.shape:
        raise ValueError("frequency and row-valid arrays must be one-dimensional matches")
    if not np.isfinite([minimum_mhz, maximum_mhz]).all():
        raise ValueError("selection bounds must be finite")
    low, high = sorted((float(minimum_mhz), float(maximum_mhz)))
    selected = valid & (frequency >= low) & (frequency <= high)
    if not selected.any():
        available = np.flatnonzero(valid)
        if not available.size:
            raise ValueError("review bundle has no selectable rows")
        midpoint = 0.5 * (low + high)
        selected[available[np.argmin(np.abs(frequency[available] - midpoint))]] = True
    return selected


def mask_to_range_records(
    selected_rows: np.ndarray,
    frequency_mhz: np.ndarray,
    *,
    reason: str,
    evidence: str,
) -> list[dict[str, Any]]:
    selected = np.asarray(selected_rows, dtype=bool)
    frequency = np.asarray(frequency_mhz, dtype=float)
    if selected.ndim != 1 or frequency.shape != selected.shape:
        raise ValueError("selected rows must match the frequency axis")
    if not reason.strip() or not evidence.strip():
        raise ValueError("reason and evidence are required")
    padded = np.pad(selected, (1, 1))
    edges = np.diff(padded.astype(np.int8))
    starts = np.flatnonzero(edges == 1)
    stops = np.flatnonzero(edges == -1)
    records: list[dict[str, Any]] = []
    for start, stop in zip(starts, stops, strict=True):
        frequencies = frequency[start:stop]
        records.append(
            {
                "start": int(start),
                "stop": int(stop),
                "frequency_min_mhz": float(np.min(frequencies)),
                "frequency_max_mhz": float(np.max(frequencies)),
                "reason": reason.strip(),
                "evidence": evidence.strip(),
            }
        )
    return records


def range_records_to_mask(
    records: list[dict[str, Any]], frequency_mhz: np.ndarray
) -> np.ndarray:
    frequency = np.asarray(frequency_mhz, dtype=float)
    selected = np.zeros(frequency.size, dtype=bool)
    previous_stop = 0
    for index, item in enumerate(records):
        start, stop = item.get("start"), item.get("stop")
        if not isinstance(start, int) or not isinstance(stop, int):
            raise ValueError("bad-row bounds must be integers")
        if not 0 <= start < stop <= frequency.size:
            raise ValueError("bad-row range is outside the frequency axis")
        if index and start < previous_stop:
            raise ValueError("bad-row ranges must be sorted and non-overlapping")
        selected_frequency = frequency[start:stop]
        if not np.isclose(
            item.get("frequency_min_mhz"), np.min(selected_frequency), atol=1e-9
        ):
            raise ValueError("bad-row minimum frequency does not match bundle")
        if not np.isclose(
            item.get("frequency_max_mhz"), np.max(selected_frequency), atol=1e-9
        ):
            raise ValueError("bad-row maximum frequency does not match bundle")
        selected[start:stop] = True
        previous_stop = stop
    return selected


def mask_preview(values: np.ndarray, selected_rows: np.ndarray) -> np.ndarray:
    data = np.asarray(values)
    selected = np.asarray(selected_rows, dtype=bool)
    if data.ndim != 2 or selected.shape != (data.shape[0],):
        raise ValueError("selected rows must match dynamic-spectrum rows")
    output = np.array(data, copy=True, dtype=np.result_type(data.dtype, np.float32))
    output[selected] = np.nan
    return output


class ManualFlaggingSession:
    def __init__(self, payload: dict[str, Any], bundle: ReviewBundle):
        if payload.get("status") == APPROVED_STATUS:
            raise ValueError("approved map is immutable; create a new draft revision")
        verify_map_binding(payload, bundle)
        self.payload = copy.deepcopy(payload)
        self.bundle = bundle
        records = payload.get("bad_row_ranges", [])
        if not isinstance(records, list):
            raise ValueError("bad_row_ranges must be a list")
        self.selected_rows = range_records_to_mask(records, bundle.frequency_mhz)
        self._history: list[np.ndarray] = []

    def add_span(self, minimum_mhz: float, maximum_mhz: float) -> None:
        added = rows_for_frequency_span(
            self.bundle.frequency_mhz,
            self.bundle.row_valid,
            minimum_mhz,
            maximum_mhz,
        )
        changed = self.selected_rows | added
        if not np.array_equal(changed, self.selected_rows):
            self._history.append(self.selected_rows.copy())
            self.selected_rows = changed

    def remove_span(self, minimum_mhz: float, maximum_mhz: float) -> None:
        removed = rows_for_frequency_span(
            self.bundle.frequency_mhz,
            self.bundle.row_valid,
            minimum_mhz,
            maximum_mhz,
        )
        changed = self.selected_rows & ~removed
        if not np.array_equal(changed, self.selected_rows):
            self._history.append(self.selected_rows.copy())
            self.selected_rows = changed

    def undo(self) -> None:
        if self._history:
            self.selected_rows = self._history.pop()

    def clear(self) -> None:
        if self.selected_rows.any():
            self._history.append(self.selected_rows.copy())
            self.selected_rows = np.zeros_like(self.selected_rows)

    def save_draft(self, path: Path, *, reason: str, evidence: str) -> None:
        output = copy.deepcopy(self.payload)
        output["status"] = "draft"
        output["bad_row_ranges"] = mask_to_range_records(
            self.selected_rows,
            self.bundle.frequency_mhz,
            reason=reason,
            evidence=evidence,
        )
        review = output.setdefault("review", {})
        review["reviewer"] = None
        review["reviewed_at"] = None
        review["editor_sha256"] = sha256(Path(__file__))
        listed_evidence = review.get("evidence")
        if not isinstance(listed_evidence, list):
            listed_evidence = []
        if evidence not in listed_evidence:
            listed_evidence.append(evidence)
        review["evidence"] = listed_evidence
        review["notes"] = "Draft manual selections; owner approval remains pending."
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
        self.payload = output


def _display_rows(
    bundle: ReviewBundle, frequency_low_mhz: float, frequency_high_mhz: float
) -> np.ndarray:
    low, high = sorted((frequency_low_mhz, frequency_high_mhz))
    rows = np.flatnonzero(
        (bundle.frequency_mhz >= low) & (bundle.frequency_mhz <= high)
    )
    if not rows.size:
        raise ValueError("review interval contains no frequency rows")
    return rows[np.argsort(bundle.frequency_mhz[rows])]


def build_review_figure(
    session: ManualFlaggingSession,
    frequency_low_mhz: float,
    frequency_high_mhz: float,
):
    import matplotlib.pyplot as plt

    bundle = session.bundle
    rows = _display_rows(bundle, frequency_low_mhz, frequency_high_mhz)
    frequency = bundle.frequency_mhz[rows]
    before = np.where(
        bundle.row_valid[rows, None], bundle.dynamic_spectrum[rows], np.nan
    )
    after = mask_preview(before, session.selected_rows[rows])
    finite = before[np.isfinite(before)]
    limit = max(0.5, float(np.percentile(np.abs(finite), 99.5)))
    extent = (
        float(bundle.time_ms[0]),
        float(bundle.time_ms[-1]),
        float(frequency[0]),
        float(frequency[-1]),
    )
    figure, axes = plt.subplots(3, 1, figsize=(13, 9), constrained_layout=True)
    cmap = plt.colormaps["RdBu_r"].copy()
    cmap.set_bad("0.76")
    before_image = axes[0].imshow(
        np.ma.masked_invalid(before),
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap=cmap,
        vmin=-limit,
        vmax=limit,
        interpolation="nearest",
    )
    after_image = axes[1].imshow(
        np.ma.masked_invalid(after),
        origin="lower",
        aspect="auto",
        extent=extent,
        cmap=cmap,
        vmin=-limit,
        vmax=limit,
        interpolation="nearest",
    )
    axes[0].set_title("Before proposed manual flags")
    axes[1].set_title("After proposed manual flags — draft only")
    for axis in axes[:2]:
        axis.set_ylabel("Frequency (MHz)")
        axis.set_xlabel("Aligned relative time (ms)")
    valid = bundle.row_valid[rows]
    axes[2].plot(bundle.on_spectrum[rows][valid], frequency[valid], color="black", lw=0.6, label="before")
    retained = valid & ~session.selected_rows[rows]
    axes[2].plot(
        bundle.on_spectrum[rows][retained],
        frequency[retained],
        color="#d62728",
        lw=0.8,
        label="retained after draft",
    )
    axes[2].set_xlabel("Time-integrated burst spectrum")
    axes[2].set_ylabel("Frequency (MHz)")
    axes[2].legend(frameon=False)
    figure.colorbar(before_image, ax=axes[:2], label="Standardized intensity", shrink=0.7)
    selected_count = int(session.selected_rows.sum())
    valid_count = int(bundle.row_valid.sum())
    figure.suptitle(
        f"{bundle.metadata['event']} {bundle.metadata['instrument']} manual flags — "
        f"{selected_count} rows; retained {1.0 - selected_count / max(valid_count, 1):.3%}"
    )
    return figure, {
        "before": axes[0],
        "after": axes[1],
        "spectrum": axes[2],
        "before_image": before_image,
        "after_image": after_image,
        "rows": rows,
    }
