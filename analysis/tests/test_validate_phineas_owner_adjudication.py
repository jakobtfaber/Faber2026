"""Independent criteria for the Phineas owner-adjudication validator."""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_phineas_owner_adjudication.py"
SPEC = importlib.util.spec_from_file_location("phineas_validation", SCRIPT)
assert SPEC and SPEC.loader
validation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validation)


def test_identical_coordinates_have_zero_separation():
    assert validation.angular_separation_rad(177.0, 71.0, 177.0, 71.0) == 0.0


def test_moster_inversion_round_trip_at_both_parameterizations():
    for z in (0.1096, 0.1925, 0.2146):
        for evolve in (False, True):
            expected = 10.2
            halo = validation.invert_moster(expected, z, evolve)
            recovered = validation.moster_log_mstar(halo, z, evolve)
            assert math.isclose(recovered, expected, rel_tol=0.0, abs_tol=1e-12)


def test_r200c_returns_mass_definition():
    log_mass = 12.0
    z = 0.2
    radius = validation.r200c_kpc(log_mass, z)
    enclosed = (
        4.0
        * math.pi
        / 3.0
        * radius**3
        * 200.0
        * validation._critical_density_msun_kpc3(z)
    )
    assert math.isclose(enclosed, 10.0**log_mass, rel_tol=1e-12)


def test_distance_duality_identity():
    z = 0.2
    assert validation.luminosity_distance_kpc(z) == (
        validation.angular_diameter_distance_kpc(z) * (1.0 + z) ** 2
    )


def test_modified_nfw_column_is_positive_inside_and_zero_outside():
    mass = 1e12
    z = 0.2
    radius = validation._bryan_norman_rvir_kpc(mass, z)
    assert validation.modified_nfw_dm(mass, z, 0.5 * radius) > 0.0
    assert validation.modified_nfw_dm(mass, z, radius) == 0.0
