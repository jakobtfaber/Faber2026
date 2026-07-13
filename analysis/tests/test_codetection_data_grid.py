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


def test_load_row_bands_uses_archival_products_for_every_row(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(
        grid,
        "bands_archival",
        lambda data_root, nick, factors=None, pad_scale=1.0: calls.append(
            (data_root, nick, factors, pad_scale)
        )
        or [],
    )

    grid.load_row_bands(
        {"nick": "zach", "npz": "fits/zach.npz"}, root=tmp_path, data_root=tmp_path
    )
    grid.load_row_bands({"nick": "chromatica", "npz": None}, root=tmp_path, data_root=tmp_path)

    assert calls == [
        (tmp_path, "zach", grid.DISPLAY_FACTORS, grid.DISPLAY_PAD_SCALE),
        (tmp_path, "chromatica", grid.DISPLAY_FACTORS, grid.DISPLAY_PAD_SCALE),
    ]


def test_display_pad_scale_tightens_window():
    assert 0 < grid.DISPLAY_PAD_SCALE < 1.0


def test_display_factors_are_near_native():
    from plot_codetection_gallery import BANDS

    for tel, (f_factor, t_factor) in grid.DISPLAY_FACTORS.items():
        n_native = {"dsa": 6144, "chime": 1024}[tel]
        n_display = {"dsa": 512, "chime": 1024}[tel]
        assert n_native // f_factor == n_display
        dt = BANDS[tel]["dt_ms"] * t_factor
        assert abs(dt - 32.768e-3) / 32.768e-3 < 0.05


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
