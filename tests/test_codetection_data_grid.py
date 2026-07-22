"""Tests for the 12-panel observed-peak Figure 1 producer."""

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
        lambda data_root, nick, factors=None, pad_scale=1.0, pad_cap_ms=None,
        target_dm=None, extra_shift_ms=None, extra_dedisp_pc=None: calls.append(
            (
                data_root, nick, factors, pad_scale, pad_cap_ms,
                target_dm, extra_shift_ms, extra_dedisp_pc,
            )
        )
        or [],
    )
    grid.load_row_bands(
        {"nick": "zach", "npz": "fits/zach.npz"}, root=tmp_path,
        data_root=tmp_path, target_dm=262.361665,
    )
    grid.load_row_bands(
        {"nick": "chromatica", "npz": None}, root=tmp_path,
        data_root=tmp_path, target_dm=272.638699,
    )
    # audit-established stem-misstatement correction: applied only to the named
    # burst, passed straight through as extra dedispersion
    grid.load_row_bands(
        {"nick": "isha", "npz": None}, root=tmp_path,
        data_root=tmp_path, target_dm=411.435717,
        dm_corrections={"isha": {"chime": 0.234}},
    )
    grid.load_row_bands(
        {"nick": "zach", "npz": None}, root=tmp_path,
        data_root=tmp_path, target_dm=262.361665,
        dm_corrections={"isha": {"chime": 0.234}},
    )

    assert calls == [
        (
            tmp_path, "zach", grid.DISPLAY_FACTORS, grid.DISPLAY_PAD_SCALE,
            grid.DISPLAY_PAD_CAP_MS, 262.361665, None, None,
        ),
        (
            tmp_path,
            "chromatica",
            grid.DISPLAY_FACTORS,
            grid.DISPLAY_PAD_SCALE,
            grid.DISPLAY_PAD_CAP_MS,
            272.638699,
            None,
            None,
        ),
        (
            tmp_path, "isha", grid.DISPLAY_FACTORS, grid.DISPLAY_PAD_SCALE,
            grid.DISPLAY_PAD_CAP_MS, 411.435717, None, {"chime": 0.234},
        ),
        (
            tmp_path, "zach", grid.DISPLAY_FACTORS, grid.DISPLAY_PAD_SCALE,
            grid.DISPLAY_PAD_CAP_MS, 262.361665, None, None,
        ),
    ]


def test_adopted_dm_catalog_is_complete_and_chime_primary():
    rows = grid.load_manifest(grid.MANIFEST_DEFAULT)
    adopted = grid.load_adopted_dms(grid.DM_CATALOG_DEFAULT)
    assert set(adopted) == {row["nick"].lower() for row in rows}
    assert adopted["zach"] == 262.361665
    assert adopted["johndoeii"] == 696.518001


def test_adopted_dm_catalog_rejects_non_chime_adoption(tmp_path):
    source = grid.DM_CATALOG_DEFAULT.read_text()
    bad = tmp_path / "dm.csv"
    bad.write_text(source.replace("chime_primary", "random_effects", 1))
    try:
        grid.load_adopted_dms(bad)
    except ValueError as exc:
        assert "chime_primary" in str(exc)
    else:
        raise AssertionError("expected invalid adoption to be rejected")


def test_display_pad_scale_tightens_window():
    assert 0 < grid.DISPLAY_PAD_SCALE < 1.0
    from plot_codetection_triptych import PAD_FLOOR_MS

    assert PAD_FLOOR_MS <= grid.DISPLAY_PAD_CAP_MS <= 5.0


def test_pad_cap_bounds_window_for_scattered_bursts():
    from plot_codetection_triptych import chime_width_display_window

    def _wide_band(label, width):
        time = np.linspace(-40.0, 40.0, 801)  # 0.1 ms bins
        data = np.zeros((8, time.size))
        on = (time >= 0.0) & (time <= width)
        data[:, on] = 100.0
        from flits.batch.codetection_plots import BandSpectrum

        return BandSpectrum(
            freq_mhz=np.linspace(400.0, 800.0, 8) if "CHIME" in label else np.linspace(1310.0, 1500.0, 8),
            time_ms=time,
            data=data,
            model=np.zeros_like(data),
            sigma=np.ones(8),
            label=label,
            channel_valid=np.ones(8, dtype=bool),
        )

    bands = [_wide_band("CHIME/FRB", 20.0), _wide_band("DSA-110", 1.0)]
    t0, t1 = chime_width_display_window(bands, pad_scale=0.5, pad_cap_ms=3.0)
    assert t0 >= -3.5 and t1 <= 23.5  # pad capped at 3 ms (+ span resolution)
    assert t0 < 0.0 < 20.0 < t1  # on-pulse union never cropped
    uncapped_t0, uncapped_t1 = chime_width_display_window(bands, pad_scale=0.5)
    assert uncapped_t1 - uncapped_t0 > t1 - t0


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


def test_gap_display_map_compresses_only_the_gap():
    bands = [_band("CHIME/FRB", 400.0, 800.0), _band("DSA-110", 1310.0, 1500.0)]
    fmap = grid._gap_display_map(bands)
    # Bands keep true scale.
    assert float(fmap(400.0)) == 400.0
    assert float(fmap(800.0)) == 800.0
    assert float(fmap(1500.0)) - float(fmap(1310.0)) == 190.0
    # Gap shrinks to GAP_COMPRESS of its true bandwidth.
    gap_disp = float(fmap(1310.0)) - float(fmap(800.0))
    assert gap_disp == grid.GAP_COMPRESS * 510.0
    fig, ax = plt.subplots()
    grid.draw_joint_waterfall(ax, bands, title="")
    y0, y1 = ax.get_ylim()
    assert (y1 - y0) < 1100.0 - (1.0 - grid.GAP_COMPRESS) * 510.0 + 1.0
    plt.close(fig)
