#!/usr/bin/env python3
"""Build the pre-fit geocentric timing constraint for one event."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

import astropy.constants as const
import astropy.units as u
from astropy.coordinates import GCRS, ITRS, EarthLocation, SkyCoord
from astropy.time import Time
from astropy.utils import iers
from one_event_workflow import load_config, validate_timing_uncertainties

from radio_pipeline.fitting.products import mjd_crop_time0_unix_ns

CHIME_LOCATION = EarthLocation(
    lat=49.3206 * u.deg,
    lon=-119.6236 * u.deg,
    height=545 * u.m,
)
DSA_LOCATION = EarthLocation(
    lat=37.2333 * u.deg,
    lon=-118.2834 * u.deg,
    height=1222 * u.m,
)


def _earth_orientation_provenance(epoch: Time) -> dict:
    table = iers.earth_orientation_table.get()
    data_path_value = table.meta.get("data_path")
    if not data_path_value:
        raise RuntimeError("active Earth-orientation table lacks a data path")
    data_path = Path(data_path_value).resolve()
    if not data_path.is_file():
        raise RuntimeError("active Earth-orientation data file is unavailable")
    mjd = table["MJD"].to_value(u.day)
    mjd_start = float(mjd[0])
    mjd_end = float(mjd[-1])
    epoch_mjd = float(epoch.mjd)
    if not mjd_start <= epoch_mjd <= mjd_end:
        raise RuntimeError("geometry epoch lies outside the Earth-orientation table")
    return {
        "astropy_version": importlib.metadata.version("astropy"),
        "astropy_iers_data_version": importlib.metadata.version("astropy-iers-data"),
        "table_class": f"{type(table).__module__}.{type(table).__name__}",
        "data_path": str(data_path),
        "data_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
        "mjd_start": mjd_start,
        "mjd_end": mjd_end,
        "predictive_mjd": (
            float(table.meta["predictive_mjd"])
            if table.meta.get("predictive_mjd") is not None
            else None
        ),
        "auto_download": bool(iers.conf.auto_download),
    }


def _site_delay_gcrs_s(
    location: EarthLocation,
    epoch: Time,
    source: SkyCoord,
) -> float:
    position = location.get_gcrs(epoch).cartesian.xyz
    direction = source.transform_to(GCRS(obstime=epoch)).cartesian.xyz
    return float((-(position.dot(direction)) / const.c).to_value(u.s))


def _site_delay_itrs_s(
    location: EarthLocation,
    epoch: Time,
    source: SkyCoord,
) -> float:
    position = location.get_itrs(epoch).cartesian.xyz
    direction = source.transform_to(ITRS(obstime=epoch)).cartesian.xyz
    return float((-(position.dot(direction)) / const.c).to_value(u.s))


def build(config: dict) -> dict:
    """Calculate both projections and bind reviewed uncertainty inputs."""

    settings = config.get("joint_fit")
    if not isinstance(settings, dict):
        raise ValueError("joint_fit configuration is required")
    geometry = settings.get("geometry")
    if not isinstance(geometry, dict):
        raise ValueError("joint_fit.geometry configuration is required")
    required = (
        "source_icrs",
        "epoch_mjd_utc",
        "site_delay_sigma_s",
        "clock_sigma_s",
        "timing_uncertainty_provenance",
    )
    missing = [key for key in required if key not in geometry]
    if missing:
        raise ValueError(f"joint_fit.geometry lacks reviewed fields: {missing}")
    validate_timing_uncertainties(geometry)
    if float(config["geometry"]["reference_frequency_mhz"]) != 400.0:
        raise ValueError("joint fit requires the 400 MHz reference")
    source = SkyCoord(
        geometry["source_icrs"],
        unit=(u.hourangle, u.deg),
        frame="icrs",
    )
    epoch = Time(str(geometry["epoch_mjd_utc"]), format="mjd", scale="utc")
    iers.conf.auto_download = False
    locations = {"chime": CHIME_LOCATION, "dsa": DSA_LOCATION}
    gcrs = {
        name: _site_delay_gcrs_s(location, epoch, source) for name, location in locations.items()
    }
    itrs = {
        name: _site_delay_itrs_s(location, epoch, source) for name, location in locations.items()
    }
    # Only the station-to-station projection is observable here. Comparing
    # absolute site terms mixes small frame-origin conventions into the oracle.
    disagreement = abs((gcrs["chime"] - gcrs["dsa"]) - (itrs["chime"] - itrs["dsa"]))
    maximum = float(geometry.get("maximum_projection_disagreement_s", 5.0e-7))
    if disagreement > maximum:
        raise RuntimeError("independent GCRS and ITRS projections disagree")
    uncertainty_provenance = geometry["timing_uncertainty_provenance"]
    earth_orientation_provenance = _earth_orientation_provenance(epoch)
    return {
        "schema_version": 1,
        "status": "provisional_pending_owner_approval",
        "event": config["event"],
        "event_binding_sha256": config["event_binding_sha256"],
        "reference_frequency_mhz": 400.0,
        "epoch_unix_ns": mjd_crop_time0_unix_ns(geometry["epoch_mjd_utc"], 0.0, 0.0),
        "epoch_mjd_utc": str(geometry["epoch_mjd_utc"]),
        "source_icrs": geometry["source_icrs"],
        "site_delay_s": gcrs,
        "site_delay_itrs_oracle_s": itrs,
        "site_delay_sigma_s": {
            name: float(geometry["site_delay_sigma_s"][name]) for name in locations
        },
        "clock_sigma_s": {name: float(geometry["clock_sigma_s"][name]) for name in locations},
        "timing_uncertainty_provenance": uncertainty_provenance,
        "earth_orientation_provenance": earth_orientation_provenance,
        "projection_disagreement_s": disagreement,
        "sign_convention": (
            "topocentric ToA equals geocentric ToA plus site delay; "
            "site delay is minus station position dotted with source direction "
            "divided by the speed of light"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(load_config(args.config))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
