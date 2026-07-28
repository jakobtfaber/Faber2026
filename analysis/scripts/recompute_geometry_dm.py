#!/usr/bin/env python3
"""Independently recompute corrected-trigger geometric-alignment DMs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import astropy.constants as const
import astropy.units as u
from astropy.coordinates import EarthLocation, ITRS, SkyCoord
from astropy.time import Time
from astropy.utils import iers

K_DM_S_MHZ2 = 4148.808
REFERENCE_FREQUENCY_MHZ = 400.0
DSA_NATIVE_FREQUENCY_MHZ = 1530.0
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def referral_slope_ms_per_dm(
    native_frequency_mhz: float = DSA_NATIVE_FREQUENCY_MHZ,
    reference_frequency_mhz: float = REFERENCE_FREQUENCY_MHZ,
) -> float:
    return -1000.0 * K_DM_S_MHZ2 * (
        reference_frequency_mhz**-2 - native_frequency_mhz**-2
    )


def geometric_delay_ms(
    arrival_time: Time,
    source: SkyCoord,
    first: EarthLocation = CHIME_LOCATION,
    second: EarthLocation = DSA_LOCATION,
) -> float:
    first_position = first.get_gcrs(arrival_time).cartesian.xyz
    second_position = second.get_gcrs(arrival_time).cartesian.xyz
    projected_baseline = (second_position - first_position).dot(source.cartesian.xyz)
    return float((projected_baseline / const.c).to_value(u.ms))


def geometric_delay_itrs_ms(
    arrival_time: Time,
    source: SkyCoord,
    first: EarthLocation = CHIME_LOCATION,
    second: EarthLocation = DSA_LOCATION,
) -> float:
    """Independent Earth-fixed projection used as a sign/value oracle."""

    first_position = first.get_itrs(arrival_time).cartesian.xyz
    second_position = second.get_itrs(arrival_time).cartesian.xyz
    direction = source.transform_to(ITRS(obstime=arrival_time)).cartesian.xyz
    projected_baseline = (second_position - first_position).dot(direction)
    return float((projected_baseline / const.c).to_value(u.ms))


def dsa_toa_at_reference(
    trigger_mjd: float,
    dm: float,
    *,
    native_frequency_mhz: float = DSA_NATIVE_FREQUENCY_MHZ,
    reference_frequency_mhz: float = REFERENCE_FREQUENCY_MHZ,
) -> Time:
    shift_s = K_DM_S_MHZ2 * float(dm) * (
        reference_frequency_mhz**-2 - native_frequency_mhz**-2
    )
    return Time(float(trigger_mjd), format="mjd", scale="utc") + shift_s * u.s


def alignment_dm(
    baseline_dm: float,
    measured_offset_ms: float,
    delay_ms: float,
) -> float:
    slope = referral_slope_ms_per_dm()
    return float(baseline_dm + (delay_ms - measured_offset_ms) / slope)


def recompute(
    timing_results_path: Path,
    trigger_recovery_path: Path,
    reproduction_fixture_path: Path,
    *,
    event: str | None = None,
    event_binding_sha256: str | None = None,
) -> dict[str, Any]:
    iers.conf.auto_download = False
    timing = json.loads(timing_results_path.read_text())
    triggers = json.loads(trigger_recovery_path.read_text())
    fixture = json.loads(reproduction_fixture_path.read_text())
    source_by_burst = {
        str(row["name"]).lower(): str(row["source_coord"]).strip()
        for row in fixture["bursts"]
    }
    results = []
    for burst, archived in timing.items():
        key = burst.lower()
        if event is not None and key != event.lower():
            continue
        if key not in triggers or key not in source_by_burst:
            raise ValueError(f"{burst}: missing trigger or source localization")
        trigger = triggers[key]
        if trigger["status"] != "VERIFIED":
            raise ValueError(f"{burst}: corrected trigger is not VERIFIED")
        baseline_dm = float(archived["dm"])
        chime_toa = Time(
            float(archived["toa_chime_unix_400"]),
            format="unix",
            scale="utc",
        )
        dsa_toa = dsa_toa_at_reference(
            float(trigger["mjd_trigger_exact"]),
            baseline_dm,
        )
        measured_offset_ms = float((chime_toa - dsa_toa).to_value(u.ms))
        source = SkyCoord(
            source_by_burst[key],
            unit=(u.hourangle, u.deg),
            frame="icrs",
        )
        delay_ms = geometric_delay_ms(chime_toa, source)
        delay_itrs_ms = geometric_delay_itrs_ms(chime_toa, source)
        if abs(delay_ms - delay_itrs_ms) > 5.0e-4:
            raise ValueError(f"{burst}: independent geometric projections disagree")
        geometry_dm = alignment_dm(baseline_dm, measured_offset_ms, delay_ms)
        check_offset_ms = measured_offset_ms + referral_slope_ms_per_dm() * (
            geometry_dm - baseline_dm
        )
        results.append(
            {
                "burst": burst,
                "baseline_dm_pc_cm3": baseline_dm,
                "baseline_dm_role": "timing referral coordinate only",
                "chime_toa_unix_400": float(chime_toa.to_value("unix")),
                "corrected_dsa_trigger_mjd": float(trigger["mjd_trigger_exact"]),
                "corrected_dsa_trigger_status": trigger["status"],
                "source_icrs": source_by_burst[key],
                "corrected_measured_offset_ms": measured_offset_ms,
                "geometric_delay_ms": delay_ms,
                "geometric_delay_itrs_oracle_ms": delay_itrs_ms,
                "geometry_projection_difference_ns": float(
                    1.0e6 * (delay_ms - delay_itrs_ms)
                ),
                "geometry_aligning_dm_pc_cm3": geometry_dm,
                "alignment_check_residual_ms": float(check_offset_ms - delay_ms),
                "archived_geometric_delay_ms": float(archived["geometric_delay_ms"]),
                "independent_minus_archived_geometric_delay_us": float(
                    1000.0 * (delay_ms - float(archived["geometric_delay_ms"]))
                ),
            }
        )
    if event is not None and not results:
        raise ValueError(f"{event}: event not found in all geometry inputs")
    return {
        "schema_version": 2,
        "status": "diagnostic_only",
        "event_binding_sha256": event_binding_sha256,
        "method": {
            "description": (
                "direct recomputation from corrected DSA trigger, archived CHIME "
                "400-MHz arrival, explicit observatory coordinates, source "
                "localization, and a shared 400-MHz reference"
            ),
            "dispersion_constant_s_mhz2": K_DM_S_MHZ2,
            "reference_frequency_mhz": REFERENCE_FREQUENCY_MHZ,
            "dsa_native_frequency_mhz": DSA_NATIVE_FREQUENCY_MHZ,
            "timing_slope_ms_per_pc_cm3": referral_slope_ms_per_dm(),
            "chime_location": {
                "latitude_deg": 49.3206,
                "longitude_deg": -119.6236,
                "height_m": 545.0,
            },
            "dsa_location": {
                "latitude_deg": 37.2333,
                "longitude_deg": -118.2834,
                "height_m": 1222.0,
            },
            "dm_uncertainty_used": False,
            "reason_no_geometry_uncertainty": (
                "independent station-clock and fitted-arrival uncertainties are absent"
            ),
        },
        "provenance": {
            "timing_results": str(timing_results_path),
            "timing_results_sha256": sha256(timing_results_path),
            "corrected_trigger_recovery": str(trigger_recovery_path),
            "corrected_trigger_recovery_sha256": sha256(trigger_recovery_path),
            "current_reproduction_fixture": str(reproduction_fixture_path),
            "current_reproduction_fixture_sha256": sha256(
                reproduction_fixture_path
            ),
        },
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timing-results", type=Path, required=True)
    parser.add_argument("--trigger-recovery", type=Path, required=True)
    parser.add_argument("--reproduction-fixture", type=Path, required=True)
    parser.add_argument("--event")
    parser.add_argument("--event-binding-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = recompute(
        args.timing_results,
        args.trigger_recovery,
        args.reproduction_fixture,
        event=args.event,
        event_binding_sha256=args.event_binding_sha256,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
