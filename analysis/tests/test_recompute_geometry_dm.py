from __future__ import annotations

import importlib.util
from pathlib import Path

import astropy.units as u
import pytest
from astropy.coordinates import SkyCoord
from astropy.time import Time

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/recompute_geometry_dm.py"
SPEC = importlib.util.spec_from_file_location("recompute_geometry_dm", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_referral_slope_matches_shared_400_mhz_convention() -> None:
    assert MODULE.referral_slope_ms_per_dm() == pytest.approx(
        -24.157736787133153,
        abs=1.0e-12,
    )


def test_alignment_dm_closes_geometry_residual() -> None:
    baseline = 272.664
    measured = -1.45294996583556
    delay = -2.284541885429817
    dm = MODULE.alignment_dm(baseline, measured, delay)
    check = measured + MODULE.referral_slope_ms_per_dm() * (dm - baseline)
    assert check == pytest.approx(delay, abs=1.0e-12)


def test_geometric_delay_is_millisecond_scale_for_chromatica() -> None:
    source = SkyCoord(
        "20h50m28.59s +73d54m00.0s",
        unit=(u.hourangle, u.deg),
    )
    arrival = Time(1706990275.9983277, format="unix", scale="utc")
    delay = MODULE.geometric_delay_ms(arrival, source)
    itrs_oracle = MODULE.geometric_delay_itrs_ms(arrival, source)
    assert delay == pytest.approx(-2.284541885429817, abs=2.0e-9)
    assert itrs_oracle == pytest.approx(-2.2845614245, abs=2.0e-9)
    assert delay < 0
    assert abs(delay - itrs_oracle) < 5.0e-5
