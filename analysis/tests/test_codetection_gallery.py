import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from plot_codetection_gallery import (
    NICK_TNS,
    block_mean,
    dead_channel_mask,
    discover_products,
    peak_window,
)


def test_block_mean_reduces_and_averages():
    arr = np.arange(24, dtype=float).reshape(4, 6)
    out = block_mean(arr, f_factor=2, t_factor=3)
    assert out.shape == (2, 2)
    assert out[0, 0] == np.mean([0, 1, 2, 6, 7, 8])


def test_block_mean_trims_ragged_edge():
    arr = np.ones((5, 7))
    assert block_mean(arr, 2, 3).shape == (2, 2)


def test_dead_channel_mask_flags_zero_variance():
    rng = np.random.default_rng(0)
    arr = rng.normal(size=(8, 100))
    arr[3] = 0.0
    arr[5] = 2.5
    mask = dead_channel_mask(arr)
    assert mask[3] and mask[5] and mask.sum() == 2


def test_peak_window_centers_on_peak():
    prof = np.zeros(1000)
    prof[400] = 10.0
    i0, i1 = peak_window(prof, dt_ms=0.16384, window_ms=25.0)
    assert i0 == 400 - 153 and i1 == 400 + 154  # round(25/0.16384) = 153


def test_peak_window_clips_at_edges():
    prof = np.zeros(100)
    prof[2] = 1.0
    i0, i1 = peak_window(prof, dt_ms=1.0, window_ms=25.0)
    assert i0 == 0 and i1 == 28


def test_discover_products_parses_dm_stems(tmp_path):
    (tmp_path / "zach_dsa_I_262_368_2500b_cntr_bpc.npy").touch()
    (tmp_path / "zach_chime_I_262_3621_32000b_cntr_bpc.npy").touch()
    prods = discover_products(tmp_path, "zach")
    assert prods["dsa"].dm == 262.368 and prods["chime"].dm == 262.3621


def test_discover_products_raises_on_missing(tmp_path):
    (tmp_path / "zach_dsa_I_262_368_2500b_cntr_bpc.npy").touch()
    try:
        discover_products(tmp_path, "zach")
    except FileNotFoundError as e:
        assert "chime" in str(e)
    else:
        raise AssertionError("expected FileNotFoundError")


def test_nick_tns_matches_pipeline():
    sys.path.insert(0, str(ROOT / "pipeline" / "scattering"))
    from scat_analysis.burst_metadata import _FALLBACK_TNS

    canon = {k.lower(): v for k, v in _FALLBACK_TNS.items()}
    assert {k.lower(): v for k, v in NICK_TNS.items()} == canon
