from __future__ import annotations

import hashlib
import importlib.metadata
from pathlib import Path

import astropy.units as u
import pytest
from astropy.coordinates import SkyCoord
from astropy.time import Time

from scripts.build_geometry_constraint import build
from scripts.recompute_geometry_dm import geometric_delay_ms


def _config() -> dict:
    return {
        "event": "injected",
        "event_binding_sha256": "a" * 64,
        "geometry": {"reference_frequency_mhz": 400.0},
        "joint_fit": {
            "geometry": {
                "source_icrs": "12:00:00 +30:00:00",
                "epoch_mjd_utc": "60369.5",
                "site_delay_sigma_s": {"chime": 1.0e-8, "dsa": 1.0e-8},
                "clock_sigma_s": {"chime": 1.0e-6, "dsa": 1.0e-6},
                "timing_uncertainty_provenance": {
                    "status": "owner_adopted_provisional_bounds",
                    "inter_site_clock_sigma_s": 2.0**0.5 * 1.0e-6,
                    "clock_allocation": "equal_independent_station_terms",
                    "clock_basis": "injected",
                    "site_delay_basis": "injected",
                    "absolute_utc_calibration_status": "not_independently_measured",
                    "owner_adoption_date": "2026-07-29",
                },
                "maximum_projection_disagreement_s": 5.0e-7,
            }
        },
    }


def test_independent_geometry_projections_agree() -> None:
    result = build(_config())
    assert result["reference_frequency_mhz"] == 400.0
    earth_orientation = result["earth_orientation_provenance"]
    assert earth_orientation["astropy_version"] == importlib.metadata.version("astropy")
    assert earth_orientation["astropy_iers_data_version"] == importlib.metadata.version(
        "astropy-iers-data"
    )
    assert earth_orientation["table_class"].endswith(".IERS_Auto")
    assert earth_orientation["auto_download"] is False
    assert earth_orientation["data_sha256"] == hashlib.sha256(
        Path(earth_orientation["data_path"]).read_bytes()
    ).hexdigest()
    assert earth_orientation["mjd_start"] <= 60369.5 <= earth_orientation["mjd_end"]
    assert result["timing_uncertainty_provenance"][
        "absolute_utc_calibration_status"
    ] == "not_independently_measured"
    assert result["projection_disagreement_s"] < 5.0e-7
    chime_minus_dsa = (
        result["site_delay_s"]["chime"] - result["site_delay_s"]["dsa"]
    )
    oracle = (
        result["site_delay_itrs_oracle_s"]["chime"]
        - result["site_delay_itrs_oracle_s"]["dsa"]
    )
    assert chime_minus_dsa == pytest.approx(oracle, abs=5.0e-7)
    independently_signed = (
        geometric_delay_ms(
            Time("60369.5", format="mjd", scale="utc"),
            SkyCoord(
                "12:00:00 +30:00:00",
                unit=(u.hourangle, u.deg),
                frame="icrs",
            ),
        )
        / 1000.0
    )
    assert chime_minus_dsa == pytest.approx(
        independently_signed, abs=5.0e-7
    )
    assert chime_minus_dsa != pytest.approx(
        -independently_signed, abs=5.0e-7
    )


def test_geometry_requires_clock_uncertainty() -> None:
    config = _config()
    del config["joint_fit"]["geometry"]["clock_sigma_s"]
    with pytest.raises(ValueError, match="reviewed fields"):
        build(config)


def test_geometry_rejects_inconsistent_inter_site_clock_budget() -> None:
    config = _config()
    config["joint_fit"]["geometry"]["timing_uncertainty_provenance"][
        "inter_site_clock_sigma_s"
    ] = 1.0e-3
    with pytest.raises(ValueError, match="do not reproduce"):
        build(config)


def test_geometry_rejects_unequal_clock_allocation_with_same_quadrature() -> None:
    config = _config()
    config["joint_fit"]["geometry"]["clock_sigma_s"] = {
        "chime": 0.6e-6,
        "dsa": 0.8e-6,
    }
    config["joint_fit"]["geometry"]["timing_uncertainty_provenance"][
        "inter_site_clock_sigma_s"
    ] = 1.0e-6
    with pytest.raises(ValueError, match="must be equal"):
        build(config)
