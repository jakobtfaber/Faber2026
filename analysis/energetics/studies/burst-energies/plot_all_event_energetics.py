#!/usr/bin/env python3
"""Render the all-event burst-fluence and energy manuscript candidate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ANALYSIS_ROOT = Path(__file__).resolve().parents[3]
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from plotting.style import use_manuscript_style  # noqa: E402

HERE = Path(__file__).resolve().parent
SAMPLE = (
    "zach",
    "whitney",
    "oran",
    "isha",
    "wilhelm",
    "phineas",
    "freya",
    "johndoeii",
    "hamilton",
    "mahi",
    "chromatica",
    "casey",
)
EVENT_ROSTER = ANALYSIS_ROOT / "dispersion/results/joint-phase/manuscript_dm_catalog.csv"


def _display_labels() -> dict[str, str]:
    with EVENT_ROSTER.open(newline="", encoding="utf-8") as handle:
        labels = {
            row["nick"].lower(): row["tns"].removeprefix("FRB ").strip()
            for row in csv.DictReader(handle)
        }
    missing = set(SAMPLE) - set(labels)
    if missing:
        raise ValueError(f"event roster is missing: {sorted(missing)}")
    return labels


DISPLAY_LABELS = _display_labels()
BANDS = ("CHIME", "DSA")
BAND_LABELS = {"CHIME": "CHIME/FRB", "DSA": "DSA-110"}
BAND_COLORS = {"CHIME": "#0072B2", "DSA": "#D55E00"}
STABLE_WINDOW_LIMIT = 0.10


def _load_core():
    spec = importlib.util.spec_from_file_location("energetics_core", HERE / "energetics_core.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load energetics_core.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CORE = _load_core()


@dataclass(frozen=True)
class FluencePoint:
    nickname: str
    band: str
    fluence: float | None
    stat_err: float | None
    window_sensitivity: float | None
    window_status: str
    calibration_status: str
    calibration_systematic_dex: float | None
    noise_status: str
    review_status: str
    input_path: str
    input_sha256: str
    calibration_paths: str
    calibration_sha256: str

    @property
    def has_value(self) -> bool:
        return self.fluence is not None and math.isfinite(self.fluence) and self.fluence > 0

    @property
    def window_stable(self) -> bool:
        return (
            self.has_value
            and self.window_status in {"candidate", "accepted"}
            and self.window_sensitivity is not None
            and 0 <= self.window_sensitivity <= STABLE_WINDOW_LIMIT
        )

    @property
    def accepted(self) -> bool:
        return (
            self.has_value
            and self.window_status == "accepted"
            and self.window_sensitivity is not None
            and 0 <= self.window_sensitivity <= STABLE_WINDOW_LIMIT
            and self.calibration_status == "accepted"
            and self.calibration_systematic_dex is not None
            and 0 < self.calibration_systematic_dex <= 1
            and self.noise_status == "accepted"
            and self.review_status == "accepted"
        )

    @property
    def stat_window_err(self) -> float | None:
        if not self.has_value or self.stat_err is None or self.window_sensitivity is None:
            return None
        return math.hypot(self.stat_err, self.fluence * self.window_sensitivity)

    @property
    def combined_err(self) -> float | None:
        if self.stat_window_err is None:
            return None
        terms = [self.stat_window_err]
        if self.calibration_systematic_dex is not None:
            terms.append(self.fluence * (10**self.calibration_systematic_dex - 1))
        return math.sqrt(sum(term**2 for term in terms))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _optional_float(value: str) -> float | None:
    if value.strip() == "":
        return None
    parsed = float(value)
    return parsed if math.isfinite(parsed) else None


def load_fluence_points(path: Path, *, candidate: bool) -> dict[tuple[str, str], FluencePoint]:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    points: dict[tuple[str, str], FluencePoint] = {}
    for row in rows:
        key = (row["nickname"].lower(), row["band"])
        if key in points:
            raise ValueError(f"duplicate fluence row: {key}")
        point = FluencePoint(
            nickname=key[0],
            band=key[1],
            fluence=_optional_float(row["fluence_jy_ms_hz"]),
            stat_err=_optional_float(row["stat_err_jy_ms_hz"]),
            window_sensitivity=_optional_float(row["window_sensitivity_frac"]),
            window_status=row["window_status"],
            calibration_status=row["calibration_status"],
            calibration_systematic_dex=_optional_float(
                row.get("calibration_systematic_dex", "")
            ),
            noise_status=row["noise_status"],
            review_status=row["review_status"],
            input_path=row["input_path"],
            input_sha256=row["input_sha256"],
            calibration_paths=row["calibration_paths"],
            calibration_sha256=row["calibration_sha256"],
        )
        if point.fluence is not None and point.fluence <= 0:
            raise ValueError(f"non-positive fluence: {key}")
        if point.stat_err is not None and point.stat_err <= 0:
            raise ValueError(f"non-positive statistical error: {key}")
        if point.window_sensitivity is not None and point.window_sensitivity < 0:
            raise ValueError(f"negative window sensitivity: {key}")
        points[key] = point

    expected = {(nickname, band) for nickname in SAMPLE for band in BANDS}
    if set(points) != expected:
        missing = sorted(expected - set(points))
        extra = sorted(set(points) - expected)
        raise ValueError(f"fluence roster mismatch: missing={missing}, extra={extra}")

    if not candidate:
        rejected = [key for key, point in points.items() if not point.accepted]
        if rejected:
            raise ValueError(
                "manuscript rendering requires accepted measurements; "
                f"{len(rejected)} of {len(points)} bands are not accepted"
            )
        # Status strings alone are not evidence. Reuse the strict validator so
        # accepted rendering checks source files and calibration hashes.
        CORE.load_accepted_fluences(path)
    return points


def build_plot_rows(
    points: dict[tuple[str, str], FluencePoint],
    *,
    candidate: bool,
) -> tuple[list[dict], dict[str, dict]]:
    roster = CORE.load_energy_roster(ANALYSIS_ROOT)
    rows: list[dict] = []
    for nickname in SAMPLE:
        redshift = roster[nickname]["redshift"]
        eligible = bool(roster[nickname]["eligible"])
        for band in BANDS:
            point = points[(nickname, band)]
            plotted_err = point.stat_window_err if candidate else point.combined_err
            energy = (
                CORE.energy_erg(point.fluence, float(redshift))
                if point.has_value and eligible
                else None
            )
            energy_err = (
                CORE.energy_erg(plotted_err, float(redshift))
                if plotted_err is not None and eligible
                else None
            )
            rows.append(
                {
                    "nickname": nickname,
                    "band": band,
                    "fluence_jy_ms_hz": point.fluence,
                    "combined_err_jy_ms_hz": plotted_err,
                    "window_status": point.window_status,
                    "window_stable": point.window_stable,
                    "accepted": point.accepted,
                    "redshift": redshift,
                    "redshift_eligible": eligible,
                    "redshift_kind": roster[nickname]["measurement_kind"],
                    "input_path": point.input_path,
                    "input_sha256": point.input_sha256,
                    "calibration_paths": point.calibration_paths,
                    "calibration_sha256": point.calibration_sha256,
                    "calibration_systematic_dex": point.calibration_systematic_dex,
                    "energy_erg": energy,
                    "energy_err_erg": energy_err,
                    "display_status": (
                        "accepted"
                        if point.accepted
                        else "window-stable candidate"
                        if candidate and point.window_stable
                        else "failed window gate"
                        if point.has_value
                        else "unavailable"
                    ),
                }
            )
    return rows, roster


def _plot_band_points(
    ax: plt.Axes,
    rows: list[dict],
    value_key: str,
    error_key: str,
    *,
    eligible_only: bool,
) -> None:
    x = np.arange(len(SAMPLE), dtype=float)
    offsets = {"CHIME": -0.14, "DSA": 0.14}
    for band in BANDS:
        band_rows = [row for row in rows if row["band"] == band]
        for index, row in enumerate(band_rows):
            value = row[value_key]
            if eligible_only and not row["redshift_eligible"]:
                continue
            xpos = x[index] + offsets[band]
            if value is None:
                ax.plot(
                    xpos,
                    0.06,
                    marker="_",
                    color="0.65",
                    markersize=7,
                    transform=ax.get_xaxis_transform(),
                    clip_on=False,
                )
                continue
            color = BAND_COLORS[band]
            if row["display_status"] in {"accepted", "window-stable candidate"}:
                ax.errorbar(
                    xpos,
                    value,
                    yerr=row[error_key],
                    fmt="o",
                    mfc="white",
                    mec=color,
                    ecolor=color,
                    ms=4.6,
                    mew=1.0,
                    elinewidth=0.7,
                    capsize=1.5,
                    zorder=3,
                )
            else:
                ax.plot(xpos, value, marker="x", color=color, ms=5.0, mew=1.0, zorder=3)


def make_figure(
    fluence_path: Path,
    output: Path,
    *,
    candidate: bool,
) -> dict:
    points = load_fluence_points(fluence_path, candidate=candidate)
    rows, roster = build_plot_rows(points, candidate=candidate)

    use_manuscript_style()
    plt.rcParams.update(
        {
            "font.size": 7.5,
            "axes.labelsize": 8.0,
            "legend.fontsize": 7.0,
            "axes.linewidth": 0.7,
        }
    )
    fig, axes = plt.subplots(2, 1, figsize=(7.3, 5.0), sharex=True, constrained_layout=True)
    fluence_ax, energy_ax = axes

    _plot_band_points(
        fluence_ax,
        rows,
        "fluence_jy_ms_hz",
        "combined_err_jy_ms_hz",
        eligible_only=False,
    )
    _plot_band_points(
        energy_ax,
        rows,
        "energy_erg",
        "energy_err_erg",
        eligible_only=True,
    )

    fluence_ax.set_yscale("log")
    energy_ax.set_yscale("log")
    fluence_ax.set_ylabel(r"$\int\!\!\int S_\nu\,dt\,d\nu$ (Jy ms Hz)")
    energy_ax.set_ylabel(r"$E_{\rm iso,band}$ (erg)")
    energy_ax.set_xticks(np.arange(len(SAMPLE)))
    energy_ax.set_xticklabels(
        [DISPLAY_LABELS[nickname] for nickname in SAMPLE],
        rotation=35,
        ha="right",
    )
    for ax in axes:
        ax.grid(axis="y", which="major", color="0.88", linewidth=0.5)
        ax.tick_params(which="both", top=True, right=True)

    legend_handles = [
        plt.Line2D(
            [],
            [],
            marker="o",
            mfc="white",
            mec=BAND_COLORS[band],
            color=BAND_COLORS[band],
            linestyle="none",
            label=BAND_LABELS[band],
        )
        for band in BANDS
    ]
    legend_handles.extend(
        [
            plt.Line2D(
                [],
                [],
                marker="o",
                mfc="white",
                mec="0.25",
                color="0.25",
                linestyle="none",
                label="window-stable candidate" if candidate else "accepted measurement",
            ),
            plt.Line2D(
                [],
                [],
                marker="x",
                color="0.35",
                linestyle="none",
                label="failed window gate",
            ),
            plt.Line2D(
                [],
                [],
                marker="_",
                color="0.65",
                linestyle="none",
                label="unavailable",
            ),
        ]
    )
    fluence_ax.legend(
        handles=legend_handles,
        ncol=5,
        frameon=False,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.0),
        handletextpad=0.35,
        columnspacing=0.9,
    )
    fluence_ax.text(0.01, 0.84, "a", transform=fluence_ax.transAxes, weight="bold")
    energy_ax.text(0.01, 0.92, "b", transform=energy_ax.transAxes, weight="bold")

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)

    stable_count = sum(row["window_stable"] for row in rows)
    accepted_count = sum(row["accepted"] for row in rows)
    failed_count = sum(row["display_status"] == "failed window gate" for row in rows)
    unavailable_count = sum(row["display_status"] == "unavailable" for row in rows)
    law_source = (
        ANALYSIS_ROOT
        / "foregrounds/census/data/frozen_census/law2024_host_redshift_extract.csv"
    )
    verdi_source = (
        ANALYSIS_ROOT
        / "foregrounds/census/data/frozen_census/verdi2025_host_redshift_extract.csv"
    )
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ANALYSIS_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    worktree_status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=no"],
        cwd=ANALYSIS_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    provenance = {
        "schema_version": 1,
        "status": (
            "candidate_not_manuscript_admitted" if candidate else "accepted_pending_owner_review"
        ),
        "figure": str(output),
        "figure_sha256": sha256(output),
        "producer": str(Path(__file__).resolve()),
        "producer_sha256": sha256(Path(__file__).resolve()),
        "analysis_revision": revision,
        "clean_tracked_worktree": worktree_status == "",
        "command": sys.argv,
        "cwd": os.getcwd(),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "matplotlib": importlib.metadata.version("matplotlib"),
            "scienceplots": importlib.metadata.version("SciencePlots"),
            "astropy": importlib.metadata.version("astropy"),
        },
        "fluence_receipt": str(fluence_path),
        "fluence_receipt_sha256": sha256(fluence_path),
        "event_roster": str(EVENT_ROSTER),
        "event_roster_sha256": sha256(EVENT_ROSTER),
        "redshift_sources": [
            {"path": str(law_source), "sha256": sha256(law_source)},
            {"path": str(verdi_source), "sha256": sha256(verdi_source)},
        ],
        "uncertainty": (
            "quadrature of statistical error and window-sensitivity spread; "
            + (
                "reviewed calibration systematic included as the conservative "
                "upper multiplicative excursion"
                if not candidate
                else "calibration systematics absent"
            )
        ),
        "counts": {
            "bands_total": len(rows),
            "window_stable": stable_count,
            "accepted": accepted_count,
            "failed_window_gate": failed_count,
            "unavailable": unavailable_count,
            "redshift_eligible_events": sum(meta["eligible"] for meta in roster.values()),
        },
        "rows": rows,
    }
    provenance_path = output.with_suffix(".provenance.json")
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n")
    return provenance


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fluences", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--candidate",
        action="store_true",
        help="render non-accepted receipts for review; never manuscript-admitted",
    )
    args = parser.parse_args()
    provenance = make_figure(
        args.fluences.resolve(),
        args.output.resolve(),
        candidate=args.candidate,
    )
    print(json.dumps(provenance["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
