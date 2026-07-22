"""Independent physical and numerical checks for the Phineas halo mixture."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import phineas_halo_crossing_probability as crossing  # noqa: E402

VALIDATOR = (
    Path(__file__).resolve().parent.parent
    / "analysis"
    / "scripts"
    / "validate_phineas_owner_adjudication.py"
)
SPEC = importlib.util.spec_from_file_location("clean_room", VALIDATOR)
assert SPEC and SPEC.loader
clean_room = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(clean_room)


def test_frozen_photometry_reproduces_adjudicated_stellar_masses():
    inputs = crossing.load_inputs()
    assert crossing.central_log_mstar(inputs["194021777634832653"]) == pytest.approx(
        10.2105328, abs=2e-6
    )
    assert crossing.central_log_mstar(inputs["983"]) == pytest.approx(
        8.94412396, abs=2e-6
    )


def test_redshift_dependent_moster_inversion_round_trips():
    z = np.array([0.1096, 0.1649, 0.1925, 0.2146])
    expected = np.array([9.0, 10.0, 10.5, 11.0])
    halo_mass = crossing.invert_moster(expected, z)
    assert crossing.moster_log_mstar(halo_mass, z) == pytest.approx(expected, abs=2e-14)


def test_non_crossing_draws_have_exactly_zero_dm():
    for object_id in crossing.load_inputs():
        draws = crossing.cached_draws(object_id, 14)
        assert np.all(draws.dm[~draws.crossing] == 0.0)
        assert np.all(draws.dm[draws.crossing] > 0.0)


def test_vectorized_hot_column_matches_clean_room_scalar_formula():
    log_mhalo = np.array([11.647, 12.246, 11.492])
    z = np.array([0.1925, 0.2146, 0.1096])
    impact = np.array([144.437, 129.623, 105.160])
    vectorized = crossing.modified_nfw_dm(log_mhalo, z, impact, np.ones(len(log_mhalo)))
    scalar = np.array(
        [
            clean_room.modified_nfw_dm(10.0**mass, redshift, separation)
            for mass, redshift, separation in zip(log_mhalo, z, impact)
        ]
    )
    assert vectorized == pytest.approx(scalar, rel=2e-13)


def test_crossing_probabilities_converge_with_fourfold_more_draws():
    for object_id in crossing.load_inputs():
        coarse = crossing.cached_draws(object_id, 14).crossing.mean()
        fine = crossing.cached_draws(object_id, 16).crossing.mean()
        assert coarse == pytest.approx(fine, abs=0.002)


def test_histogram_is_normalized_and_preserves_non_crossing_atom():
    for object_id in crossing.load_inputs():
        draws = crossing.cached_draws(object_id, 14)
        x0, density = crossing.halo_dm_histogram(object_id, dx=0.1, power=14)
        assert x0 == 0.0
        assert density.sum() * 0.1 == pytest.approx(1.0, abs=1e-14)
        assert density[0] * 0.1 == pytest.approx(
            1.0 - draws.crossing.mean(), abs=1.0 / len(draws.dm)
        )


def test_out_of_domain_redshift_tail_is_fail_closed():
    draws = crossing.cached_draws("983", 14)
    assert np.all(~draws.crossing[~draws.model_domain])
    assert np.all(draws.dm[~draws.model_domain] == 0.0)
    assert draws.model_domain.mean() > 0.99
