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
        lambda data_root, nick, factors=None, pad_scale=1.0, pad_cap_ms=None, extra_shift_ms=None: calls.append(
            (data_root, nick, factors, pad_scale, pad_cap_ms, extra_shift_ms)
        )
        or [],
    )
    fake_shift = {"CHIME/FRB": 0.1, "DSA-110": -0.05}
    monkeypatch.setattr(
        grid,
        "fit_toa_shift_ms",
        lambda row, root, data_root: fake_shift if row.get("npz") else {},
    )

    grid.load_row_bands(
        {"nick": "zach", "npz": "fits/zach.npz"}, root=tmp_path, data_root=tmp_path
    )
    grid.load_row_bands({"nick": "chromatica", "npz": None}, root=tmp_path, data_root=tmp_path)

    assert calls == [
        (
            tmp_path,
            "zach",
            grid.DISPLAY_FACTORS,
            grid.DISPLAY_PAD_SCALE,
            grid.DISPLAY_PAD_CAP_MS,
            fake_shift,
        ),
        (
            tmp_path,
            "chromatica",
            grid.DISPLAY_FACTORS,
            grid.DISPLAY_PAD_SCALE,
            grid.DISPLAY_PAD_CAP_MS,
            {},
        ),
    ]


def test_register_fit_grid_recovers_crop_offset():
    rng = np.random.default_rng(7)
    dt = 0.032768
    native = rng.normal(size=4000)
    native[1200:1230] += 30.0  # burst
    start, r = 900, 2
    fit_prof = native[start : start + 1200].reshape(-1, r).mean(axis=1)
    fit_t = np.arange(fit_prof.size) * (r * dt)
    got = grid._register_fit_grid_ms(fit_t, fit_prof, native, dt)
    assert abs(got - start * dt) < r * dt + 1e-9


def test_fit_toa_shift_uses_dominant_component(monkeypatch, tmp_path):
    # Synthetic NPZ + JSON: two components, model peak on the later/brighter
    # one; the anchor must pick t0 nearest the model peak, not the earliest.
    dt_native = 0.032768
    r_fit = 2
    n_native = 4000
    burst_native = 2000
    native = np.zeros(n_native)
    native[burst_native : burst_native + 20] = 50.0

    start = 1500
    n_fit = 900
    fit_data = native[start : start + n_fit * r_fit].reshape(1, n_fit, r_fit).mean(axis=2)
    fit_t = np.arange(n_fit) * (r_fit * dt_native)
    model = np.zeros_like(fit_data)
    peak_fit_idx = (burst_native - start) // r_fit
    model[0, peak_fit_idx] = 1.0

    npz = tmp_path / "syn_jointmodel_X.npz"
    np.savez(
        npz,
        timeC=fit_t, dataC=fit_data, modelC=model,
        timeD=fit_t, dataD=fit_data, modelD=model,
    )
    t_peak_fit = float(fit_t[peak_fit_idx])
    fit_json = tmp_path / "syn_joint_fit_X.json"
    import json as _json

    fit_json.write_text(_json.dumps({
        "percentiles": {
            "t0_C1": {"median": t_peak_fit - 5.0},   # early spurious component
            "t0_C2": {"median": t_peak_fit - 0.2},   # dominant (near model peak)
            "t0_D1": {"median": t_peak_fit - 0.2},
        }
    }))

    class _Prod:
        path = "unused"

    monkeypatch.setattr(grid, "DISPLAY_FACTORS", {"dsa": (1, 2), "chime": (1, 2)})
    import plot_codetection_gallery as gal

    monkeypatch.setattr(gal, "discover_products", lambda root, nick: {"chime": _Prod, "dsa": _Prod})

    def _fake_load(path, band):
        r = band["t_factor"]
        prof = native[: (native.size // r) * r].reshape(-1, r).mean(axis=1)
        return prof[None, :], prof

    monkeypatch.setattr(gal, "load_band", _fake_load)
    monkeypatch.setattr(gal, "BANDS", {
        "dsa": dict(dt_ms=dt_native, f_factor=1, t_factor=2),
        "chime": dict(dt_ms=dt_native, f_factor=1, t_factor=2),
    })

    shifts = grid.fit_toa_shift_ms(
        {"nick": "syn", "npz": npz.name}, root=tmp_path, data_root=tmp_path
    )
    # Anchor = dominant component 0.2 ms before the peak -> shift +0.2 (within
    # one display bin of registration tolerance); the -5 ms component ignored.
    for label in ("CHIME/FRB", "DSA-110"):
        assert abs(shifts[label] - 0.2) < 2 * r_fit * dt_native


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
