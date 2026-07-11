"""Tests for the 12-panel fit-grid data-only Figure 1 producer."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "pipeline"))

import plot_codetection_data_grid as grid  # noqa: E402
from flits.batch.codetection_plots import BandSpectrum  # noqa: E402


def _band(label: str, f0: float, f1: float) -> BandSpectrum:
    time = np.linspace(-2.0, 2.0, 16)
    data = np.arange(8 * 16, dtype=float).reshape(8, 16)
    return BandSpectrum(
        freq_mhz=np.linspace(f0, f1, 8),
        time_ms=time,
        data=data,
        model=np.zeros_like(data),
        sigma=np.ones(8),
        label=label,
        channel_valid=np.ones(8, dtype=bool),
    )


def test_manifest_defines_twelve_grid_panels_in_epoch_order():
    rows = grid.load_manifest(grid.MANIFEST_DEFAULT)
    assert len(rows) == 12
    assert rows[0]["nick"] == "zach"
    assert rows[-1]["nick"] == "casey"


def test_load_row_bands_uses_fit_delivery_data_when_npz_exists(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(grid, "bands_from_npz", lambda path, nick: calls.append((path, nick)) or [])
    monkeypatch.setattr(grid, "bands_data_only", lambda *args: (_ for _ in ()).throw(AssertionError))

    grid.load_row_bands(
        {"nick": "zach", "npz": "fits/zach.npz"}, root=tmp_path, data_root=tmp_path
    )

    assert calls == [(tmp_path / "fits/zach.npz", "zach")]


def test_draw_joint_waterfall_draws_two_bands_and_hatched_gap():
    fig, ax = plt.subplots()
    grid.draw_joint_waterfall(
        ax,
        [_band("CHIME/FRB", 400.0, 800.0), _band("DSA-110", 1310.0, 1500.0)],
        title="FRB test",
    )
    assert len(ax.images) == 2
    assert len(ax.patches) == 1
    assert ax.get_title() == "FRB test"
    plt.close(fig)
