"""Regression tests for the manuscript-facing ToA convention."""

import importlib.util
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "plot_toa_offset_decomposition",
        ROOT / "scripts/plot_toa_offset_decomposition.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


plotter = _load_module()


def test_committed_decomposition_uses_canonical_peak_offsets():
    source = json.loads(plotter.TOA_RESULTS.read_text())
    rows = plotter.load_rows()
    assert len(rows) == 12
    assert {row["convention"] for row in rows} == {"peak"}
    for row in rows:
        expected = source[row["burst"]]
        assert row["offset"] == expected["measured_offset_ms"]
        assert row["offset"] == expected["peak_measured_offset_ms"]
        assert row["offset"] != expected["model_corrected_offset_ms"]


def test_decomposition_axes_contain_every_offset_and_geometry_marker():
    rows = plotter.load_rows()
    fig = plotter.make_figure(rows)
    xmin, xmax = fig.axes[0].get_xlim()
    plotted = [value for row in rows for value in (row["offset"], row["geo"])]
    assert xmin < min(plotted)
    assert max(plotted) < xmax
    plt.close(fig)


def test_unvalidated_model_row_must_fail_closed_to_peak(monkeypatch, tmp_path):
    source = json.loads(plotter.TOA_RESULTS.read_text())
    row = next(iter(source.values()))
    row["measured_offset_ms"] = row["model_corrected_offset_ms"]
    bad = tmp_path / "toa.json"
    bad.write_text(json.dumps(source))
    monkeypatch.setattr(plotter, "TOA_RESULTS", bad)
    with pytest.raises(ValueError, match="does not preserve the observed-peak offset"):
        plotter.load_rows()


def test_validated_model_row_may_become_canonical(monkeypatch, tmp_path):
    source = json.loads(plotter.TOA_RESULTS.read_text())
    for row in source.values():
        row["model_correction_status"] = "validated"
        row["measured_offset_ms"] = row["model_corrected_offset_ms"]
    validated = tmp_path / "toa.json"
    validated.write_text(json.dumps(source))
    monkeypatch.setattr(plotter, "TOA_RESULTS", validated)
    rows = plotter.load_rows()
    assert {row["convention"] for row in rows} == {"model"}
