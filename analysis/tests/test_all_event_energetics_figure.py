from __future__ import annotations

import csv
import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest
import yaml
from astropy import units as u
from astropy.cosmology import Planck18

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "energetics" / "studies" / "burst-energies"
SPEC = importlib.util.spec_from_file_location(
    "plot_all_event_energetics",
    STUDY / "plot_all_event_energetics.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
CANDIDATE = STUDY / "data_fluences.candidate.csv"


def test_candidate_roster_and_gate_counts() -> None:
    points = MODULE.load_fluence_points(CANDIDATE, candidate=True)
    rows, roster = MODULE.build_plot_rows(points, candidate=True)

    assert len(points) == 24
    assert len(rows) == 24
    assert sum(row["window_stable"] for row in rows) == 17
    assert sum(row["display_status"] == "failed window gate" for row in rows) == 4
    assert sum(row["display_status"] == "unavailable" for row in rows) == 3
    assert sum(meta["eligible"] for meta in roster.values()) == 8


def test_candidate_energy_uses_core_equation() -> None:
    points = MODULE.load_fluence_points(CANDIDATE, candidate=True)
    rows, _ = MODULE.build_plot_rows(points, candidate=True)
    zach_chime = next(
        row for row in rows if row["nickname"] == "zach" and row["band"] == "CHIME"
    )

    distance_m = Planck18.luminosity_distance(0.043).to_value(u.m)
    expected = (
        4
        * math.pi
        * distance_m**2
        * zach_chime["fluence_jy_ms_hz"]
        * 1e-22
        / 1.043
    )
    assert zach_chime["energy_erg"] == pytest.approx(expected, rel=1e-13)


def test_accepted_point_includes_calibration_systematic() -> None:
    point = MODULE.FluencePoint(
        nickname="zach",
        band="CHIME",
        fluence=100.0,
        stat_err=1.0,
        window_sensitivity=0.01,
        window_status="accepted",
        calibration_status="accepted",
        calibration_systematic_dex=0.1,
        noise_status="accepted",
        review_status="accepted",
        input_path="/input",
        input_sha256="a" * 64,
        calibration_paths="/calibration",
        calibration_sha256="b" * 64,
    )

    assert point.accepted
    assert point.window_stable
    assert point.combined_err > math.hypot(1.0, 1.0)


def test_manuscript_mode_rejects_candidate_receipts() -> None:
    with pytest.raises(ValueError, match="requires accepted measurements"):
        MODULE.load_fluence_points(CANDIDATE, candidate=False)


def test_manuscript_mode_rejects_forged_accepted_statuses(tmp_path: Path) -> None:
    forged = tmp_path / "forged.csv"
    with CANDIDATE.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0])
    fieldnames.append("calibration_systematic_dex")
    for row in rows:
        row.update(
            fluence_jy_ms_hz="1",
            stat_err_jy_ms_hz="0.1",
            window_status="accepted",
            window_sensitivity_frac="0.01",
            calibration_status="accepted",
            calibration_systematic_dex="0.1",
            noise_status="accepted",
            review_status="accepted",
            input_path="",
            input_sha256="",
            calibration_paths="",
            calibration_sha256="",
        )
    with forged.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match="SHA-256|missing"):
        MODULE.load_fluence_points(forged, candidate=False)


def test_candidate_rejects_non_positive_uncertainty(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.csv"
    with CANDIDATE.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0])
    finite = next(row for row in rows if row["stat_err_jy_ms_hz"])
    finite["stat_err_jy_ms_hz"] = "-1"
    with malformed.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with pytest.raises(ValueError, match="non-positive statistical error"):
        MODULE.load_fluence_points(malformed, candidate=True)


def test_candidate_render_writes_pdf_and_provenance(tmp_path: Path) -> None:
    output = tmp_path / "energetics.pdf"
    provenance = MODULE.make_figure(CANDIDATE, output, candidate=True)

    assert output.stat().st_size > 10_000
    assert output.with_suffix(".provenance.json").is_file()
    assert provenance["status"] == "candidate_not_manuscript_admitted"
    assert provenance["counts"] == {
        "bands_total": 24,
        "window_stable": 17,
        "accepted": 0,
        "failed_window_gate": 4,
        "unavailable": 3,
        "redshift_eligible_events": 8,
    }
    finite = next(row for row in provenance["rows"] if row["fluence_jy_ms_hz"] is not None)
    assert finite["input_path"]
    assert len(finite["input_sha256"]) == 64


def test_candidate_pdf_is_byte_reproducible(tmp_path: Path) -> None:
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.pdf"
    MODULE.make_figure(CANDIDATE, first, candidate=True)
    MODULE.make_figure(CANDIDATE, second, candidate=True)

    assert first.read_bytes() == second.read_bytes()


def test_figure_catalog_stages_candidate_behind_review_slot() -> None:
    catalog = yaml.safe_load((ROOT / "figures" / "catalog.yaml").read_text())
    figure = next(item for item in catalog["figures"] if item["id"] == "energetics_all_events")

    assert figure["manuscript"] is True
    assert figure["approval_slot"] == "fig-energetics-summary"
    assert figure["candidate_root"].startswith("analysis/figure_review/staging/")
    assert "--candidate" in figure["producer"]["argv"]

    slots = json.loads((ROOT / "figure_review" / "definitions" / "slots.json").read_text())
    slot = next(
        item for item in slots["groups"] if item["id"] == "fig-energetics-summary"
    )
    assert slot["protect_in_manuscript"] is True


def test_display_labels_come_from_canonical_event_roster() -> None:
    with MODULE.EVENT_ROSTER.open(newline="", encoding="utf-8") as handle:
        expected = {
            row["nick"].lower(): row["tns"].removeprefix("FRB ").strip()
            for row in csv.DictReader(handle)
        }
    assert MODULE.DISPLAY_LABELS == expected
    assert MODULE.DISPLAY_LABELS["freya"] == "20230325C"
    assert MODULE.DISPLAY_LABELS["hamilton"] == "20230913G"
    assert MODULE.DISPLAY_LABELS["chromatica"] == "20240203D"
