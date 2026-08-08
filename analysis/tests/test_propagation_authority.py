"""Independent invariants for the foreground propagation authority."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import dm_budget_uncertainty as dbu  # noqa: E402

from foregrounds.propagation import intervening_authority as authority  # noqa: E402
from foregrounds.propagation import scattering_predict  # noqa: E402


def test_registry_roster_is_unique_and_deduplicated():
    systems, dispositions = authority.build_systems()
    identities = [(system.tns, system.object) for system in systems]
    assert len(systems) == 8
    assert len(identities) == len(set(identities))
    assert {item["object"] for item in dispositions if item["status"] == "deduplicated"} == {
        "824",
        "827",
        "832",
        "1153",
        "1190",
    }
    assert {
        (item["object"], item["status"])
        for item in dispositions
        if item["status"].startswith("omitted")
    } == {("953", "omitted_no_central_mnfw_crossing")}


def test_coordinate_geometry_and_mnfw_columns_reproduce_independently():
    systems, _ = authority.build_systems()
    for system in systems:
        theta = math.radians(system.theta_arcsec / 3600.0)
        impact = theta * authority.COSMO.angular_diameter_distance(system.z).to_value("kpc")
        assert system.impact_kpc == pytest.approx(impact, rel=1e-12)
        if system.kind == "cluster":
            expected = scattering_predict.dm_cluster_mnfw_model(system.mass_msun, system.z, impact)
        else:
            expected = scattering_predict.dm_halo_mnfw(system.mass_msun, system.z, impact)
        assert system.dm_point == pytest.approx(expected or 0.0, rel=1e-12, abs=1e-12)


def test_intervening_receipt_hash_binds_every_input_and_output():
    receipt = json.loads(authority.RECEIPT_JSON.read_text())
    for relative, expected in receipt["inputs"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
    for relative, expected in receipt["outputs"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
    assert hashlib.sha256(Path(authority.__file__).read_bytes()).hexdigest() == receipt["producer"]
    assert authority.render()[authority.RECEIPT_JSON] == authority.RECEIPT_JSON.read_text()


def test_host_authority_is_deterministic_and_hash_bound():
    rendered = dbu.render_authority_outputs()
    assert rendered == dbu.render_authority_outputs()
    for path, text in rendered.items():
        assert path.read_text() == text
    receipt = json.loads(rendered[dbu.HOST_RECEIPT_JSON])
    for relative, expected in receipt["inputs"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
    for relative, expected in receipt["outputs"].items():
        assert hashlib.sha256(rendered[ROOT / relative].encode()).hexdigest() == expected


def test_cluster_profiles_and_host_priors_remain_conditional():
    payload = json.loads(dbu.HOST_RESULTS_JSON.read_text())
    phineas = payload["sightlines"]["FRB 20230307A"]
    assert set(phineas) == {"mnfw", "beta"}
    assert phineas["mnfw"]["dm_host_p50"] != phineas["beta"]["dm_host_p50"]
    assert "averaging" in payload["cluster_profiles"]
    assert set(phineas["mnfw"]["host_prior_conditionals"]) == {"50", "100", "200"}


def test_shared_figm_covariance_has_expected_rank_one_structure():
    modeled = tuple(
        row
        for row in dbu.load_sightlines()
        if not (row.dm_int > 0.0 and not row.intervening_systems)
    )
    covariance = dbu.shared_figm_covariance(modeled)
    assert np.allclose(covariance, covariance.T)
    assert np.linalg.eigvalsh(covariance).min() >= -1e-10
    assert np.count_nonzero(np.linalg.eigvalsh(covariance) > 1e-8) == 1
    assert np.all(covariance > 0.0)


def test_observed_dm_likelihood_broadens_host_result():
    row = next(row for row in dbu.load_sightlines() if row.name == "FRB 20220207C")
    precise = dbu.host_distribution(dataclasses.replace(row, dm_obs_sigma=0.01))
    noisy = dbu.host_distribution(dataclasses.replace(row, dm_obs_sigma=20.0))
    precise_width = precise["dm_host_p84"] - precise["dm_host_p16"]
    noisy_width = noisy["dm_host_p84"] - noisy["dm_host_p16"]
    assert noisy_width > precise_width


def test_photo_z_probability_behind_source_is_zero_dm(monkeypatch):
    row = next(row for row in dbu.load_sightlines() if row.name == "FRB 20220310F")
    system = row.intervening_systems[0]
    monkeypatch.setattr(
        dbu.scattering_predict,
        "dm_halo_mnfw",
        lambda mass, redshift, impact: 10.0,
    )
    pdf = dbu.system_pdf(system, source_z=row.z, dx=0.1)
    expected = stats.norm.sf(row.z, loc=system.z, scale=system.z_sigma)
    assert pdf.density[0] * pdf.dx == pytest.approx(expected, abs=3e-2)


def test_chromatica_mismatch_is_fail_closed():
    payload = json.loads(dbu.HOST_RESULTS_JSON.read_text())
    assert "FRB 20240203D" not in payload["sightlines"]
    assert "FRB 20240203D" in payload["blocked_sightlines"]
    row = next(
        row
        for row in json.loads(dbu.BUDGET_DATA.read_text())["rows"]
        if row["burst"] == "FRB 20240203D"
    )
    assert row["dm_host"] == [102, 31, 37]
    receipt = json.loads(dbu.HOST_RECEIPT_JSON.read_text())
    assert receipt["manuscript_budget_mutated"] is False
    assert receipt["manuscript_budget_sha256"] == hashlib.sha256(
        dbu.BUDGET_DATA.read_bytes()
    ).hexdigest()


def test_missing_tng_source_and_mass_uncertainties_are_explicit():
    payload = json.loads(dbu.HOST_RESULTS_JSON.read_text())
    assert payload["tng_calibration_status"] == (
        "provisional_transcribed_grid_source_artifact_missing"
    )
    assert not list(ROOT.rglob("tng_params_new.npy"))
    systems, _ = authority.build_systems()
    galaxies = [system for system in systems if system.model == "redshift_marginalized_lognormal"]
    assert galaxies
    assert all(
        system.mass_sigma_dex is None and "mass uncertainty unavailable" in system.uncertainty_flags
        for system in galaxies
    )
    cluster = next(system for system in systems if system.kind == "cluster")
    assert cluster.mass_sigma_dex == pytest.approx(0.2)


def test_cluster_mnfw_respects_owner_adjudicated_xray_mass_cap(monkeypatch):
    row = next(row for row in dbu.load_sightlines() if row.name == "FRB 20230307A")
    cluster = next(system for system in row.intervening_systems if system.kind == "cluster")
    sampled_masses = []

    def record_mass(mass, redshift, impact):
        sampled_masses.append(mass)
        return 10.0

    monkeypatch.setattr(
        dbu.scattering_predict,
        "dm_cluster_mnfw_model",
        record_mass,
    )
    dbu._cluster_mnfw_pdf(cluster, dx=0.1)
    assert sampled_masses
    assert max(sampled_masses) <= dbu.CL_M500_XRAY_UL


def test_hostless_statement_is_diagnostic_only():
    payload = json.loads(dbu.HOST_RESULTS_JSON.read_text())
    assert payload["hostless"] == "diagnostic DM-redshift only; no host-DM promotion"
