from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import dm_redshift_inference as dri
import numpy as np
import pytest

from foregrounds.propagation.dm_distributions import GridPosterior
from foregrounds.propagation.dm_redshift import CandidateMixture, infer_coupled


def _conditional_mean_dm(candidate) -> float:
    return sum(
        weight * (0.0 if median is None else median)
        for weight, median in zip(
            candidate.conditional_weights,
            candidate.dm_medians,
            strict=True,
        )
    )


def test_hostless_roster_has_no_established_redshifts():
    rows = dri.load_hostless()
    assert {row.name for row in rows} == dri.HOSTLESS


def test_installed_hostless_census_receipt_matches_authoritative_builder():
    installed = json.loads(dri.HOSTLESS_CENSUS_RECEIPT.read_text(encoding="utf-8"))
    assert dri.load_hostless_census_receipt() == installed


def test_redshift_prior_is_positive_and_finite():
    for z in (0.01, 0.1, 0.5, 1.0, 2.5):
        assert math.isfinite(dri.redshift_prior(z))
        assert dri.redshift_prior(z) > 0.0


@pytest.fixture(scope="module")
def baseline_results():
    return {row.name: dri.infer_one(row, 100.0) for row in dri.load_hostless()}


def test_zero_halo_oracle_preserves_prior_diagnostic_quantiles(baseline_results):
    """Known diagnostic values from the pre-coupling zero-halo implementation."""
    expected = {
        "FRB 20221203A": (0.4101509, 0.5492019, 0.7047773),
        "FRB 20230325C": (0.7255791, 0.9172988, 1.1441181),
        "FRB 20240122A": (0.7364598, 0.9317269, 1.1630560),
    }
    for name, quantiles in expected.items():
        result = baseline_results[name]
        assert (result["z16"], result["z50"], result["z84"]) == pytest.approx(quantiles, abs=2e-6)


def test_complete_grids_are_normalized_and_tail_controlled(baseline_results):
    for result in baseline_results.values():
        grid = np.asarray(result["grid"])
        density = np.asarray(result["density"])
        assert grid.shape == density.shape == (250,)
        assert np.trapezoid(density, grid) == pytest.approx(1.0, abs=1e-12)
        assert result["normalization"] == pytest.approx(1.0, abs=1e-12)
        assert result["edge_mass_low_5pct"] < 0.02
        assert result["edge_mass_high_5pct"] < 0.02
        assert result["grid_coarsening_max_quantile_shift"] < 0.005
        joint = np.asarray(result["joint_density"])
        assert joint.shape == (1, 250)
        assert np.trapezoid(joint.sum(axis=0), grid) == pytest.approx(1.0, abs=1e-12)


def test_dm_redshift_order_tracks_excess_dm(baseline_results):
    assert baseline_results["FRB 20240122A"]["z50"] > baseline_results["FRB 20221203A"]["z50"]
    assert baseline_results["FRB 20230325C"]["z50"] > baseline_results["FRB 20221203A"]["z50"]


def test_positive_foreground_dm_lowers_inferred_redshift():
    """Analytic synthetic oracle: fixed excess DM is shared between IGM and halo."""
    grid = np.linspace(0.01, 1.5, 600)
    observed_excess = 800.0
    sigma = 25.0

    def likelihood(z, active):
        prediction = 1000.0 * z + sum(_conditional_mean_dm(candidate) for candidate in active)
        return math.exp(-0.5 * ((observed_excess - prediction) / sigma) ** 2)

    baseline = infer_coupled(
        grid, candidates=(), likelihood=likelihood, redshift_prior=lambda _z: 1.0
    )
    candidate = CandidateMixture(
        identifier="synthetic",
        z_mean=0.05,
        z_sigma=0.005,
        dm_sigma_ln=0.4,
        dm_at_redshift=lambda _z: 200.0,
    )
    coupled = infer_coupled(
        grid,
        candidates=(candidate,),
        likelihood=likelihood,
        redshift_prior=lambda _z: 1.0,
    )
    assert baseline.posterior.quantiles()[1] == pytest.approx(0.8, abs=0.005)
    assert coupled.posterior.quantiles()[1] == pytest.approx(0.6, abs=0.005)
    assert coupled.candidate_foreground_probability["synthetic"] > 0.999


def test_candidate_state_posterior_is_normalized():
    grid = np.linspace(0.01, 1.0, 200)
    candidates = (
        CandidateMixture("a", 0.2, 0.05, 0.4, lambda _z: 20.0),
        CandidateMixture("b", 0.5, 0.10, 0.4, lambda _z: 30.0),
    )
    result = infer_coupled(
        grid,
        candidates=candidates,
        likelihood=lambda z, active: (
            math.exp(-(((z - 0.6) / 0.2) ** 2))
            * math.exp(-0.01 * sum(_conditional_mean_dm(candidate) for candidate in active))
        ),
        redshift_prior=lambda _z: 1.0,
    )
    assert len(result.state_labels) == 4
    assert result.state_probability.sum() == pytest.approx(1.0, abs=1e-12)
    assert np.trapezoid(result.joint_density.sum(axis=0), grid) == pytest.approx(1.0, abs=1e-12)
    assert set(result.candidate_foreground_probability) == {"a", "b"}


def test_candidate_dm_is_marginalized_over_photo_z_not_evaluated_at_mean():
    narrow = CandidateMixture("narrow", 0.3, 0.01, 0.4, lambda z: 100.0 + 500.0 * z)
    broad = CandidateMixture("broad", 0.3, 0.12, 0.4, lambda z: 100.0 + 500.0 * z)
    narrow_distribution = narrow.foreground_distribution(0.8, quadrature_order=24)
    broad_distribution = broad.foreground_distribution(0.8, quadrature_order=24)

    assert np.ptp(narrow_distribution.dm_medians) > 0.0
    assert not np.allclose(
        narrow_distribution.redshift_nodes,
        broad_distribution.redshift_nodes,
    )
    narrow_variance = np.average(
        (np.asarray(narrow_distribution.dm_medians) - _conditional_mean_dm(narrow_distribution))
        ** 2,
        weights=narrow_distribution.conditional_weights,
    )
    broad_variance = np.average(
        (np.asarray(broad_distribution.dm_medians) - _conditional_mean_dm(broad_distribution)) ** 2,
        weights=broad_distribution.conditional_weights,
    )
    assert broad_variance > 50.0 * narrow_variance
    assert len(set(broad_distribution.dm_medians)) > 1


def test_grid_posterior_rejects_invalid_and_reports_edge_mass():
    posterior = GridPosterior(
        np.linspace(0.0, 1.0, 101),
        np.exp(-0.5 * ((np.linspace(0.0, 1.0, 101) - 0.5) / 0.1) ** 2),
    )
    low, high = posterior.edge_mass()
    assert low == pytest.approx(high, rel=1e-12)
    with pytest.raises(ValueError):
        GridPosterior(np.array([0.0, 0.5, 0.4]), np.ones(3))


def test_real_candidate_inputs_are_fail_closed():
    by_name = {row.name: row for row in dri.load_hostless()}
    freya, flags = dri.load_candidate_mixtures(by_name["FRB 20230325C"])
    assert len(freya) == 2
    assert freya[0].identifier == "197030881733398302"
    assert freya[0].dm_at_photo_z_mean > 0.0
    assert freya[1].dm_at_photo_z_mean == 0.0
    assert freya[0].angular_separation_arcsec == pytest.approx(17.50958845, abs=1e-7)
    assert freya[1].angular_separation_arcsec == pytest.approx(32.92401936, abs=1e-7)
    assert all(flag["photo_z_catastrophic_failures"] == "unmodeled" for flag in flags)
    first_flag = next(flag for flag in flags if flag["identifier"] == freya[0].identifier)
    assert first_flag["legacy_impact_kpc"] == 60.1
    assert first_flag["coordinate_impact_at_photo_z_mean_kpc"] == pytest.approx(
        81.35971589, abs=1e-7
    )
    for name in ("FRB 20221203A", "FRB 20240122A"):
        candidates, candidate_flags = dri.load_candidate_mixtures(by_name[name])
        assert candidates == ()
        assert candidate_flags or name == "FRB 20240122A"


def test_candidate_b_crossing_changes_with_redshift_dependent_geometry():
    sightline = next(row for row in dri.load_hostless() if row.name == "FRB 20230325C")
    candidates, _ = dri.load_candidate_mixtures(sightline)
    candidate_b = next(
        candidate for candidate in candidates if candidate.identifier == "197040882212782495"
    )
    assert candidate_b.dm_at_redshift(0.5) > 0.0
    assert candidate_b.dm_at_redshift(0.8) == 0.0
    distribution = candidate_b.foreground_distribution(1.0, quadrature_order=24)
    assert any(value is not None and value > 0.0 for value in distribution.dm_medians)
    assert any(value == 0.0 for value in distribution.dm_medians)


def test_three_host_priors_are_conditional_not_averaged():
    result = dri.build_result()
    assert result["model"]["host_prior_combination"].startswith("none")
    assert result["model"]["impact_geometry_authority"].startswith("coordinate-derived")
    assert "not used" in result["model"]["legacy_impact_disposition"]
    for row in result["rows"]:
        assert [item["host_rest_median"] for item in row["baseline"]] == [50.0, 100.0, 200.0]
        assert [item["host_rest_median"] for item in row["coupled"]] == [50.0, 100.0, 200.0]


def test_render_and_receipt_are_deterministic_and_hash_bound():
    first = dri.render_outputs()
    second = dri.render_outputs()
    assert first == second
    receipt = json.loads(first[dri.RECEIPT_JSON])
    for relative, expected in receipt["outputs"].items():
        path = dri.ANALYSIS_ROOT / relative
        assert hashlib.sha256(first[path].encode()).hexdigest() == expected


def test_serialized_quantiles_stay_within_one_micro_redshift():
    raw = dri.build_result()
    serialized = dri._canonicalize(raw)
    deltas = []
    for raw_row, serialized_row in zip(raw["rows"], serialized["rows"], strict=True):
        for mode in ("baseline", "coupled"):
            for raw_posterior, serialized_posterior in zip(
                raw_row[mode],
                serialized_row[mode],
                strict=True,
            ):
                deltas.extend(
                    abs(raw_posterior[field] - serialized_posterior[field])
                    for field in ("z16", "z50", "z84")
                )
    assert max(deltas) <= 1e-6


def test_cli_check_is_cross_process_byte_stable():
    completed = subprocess.run(
        [
            sys.executable,
            str(dri.ANALYSIS_ROOT / "scripts" / "dm_redshift_inference.py"),
            "--check",
        ],
        cwd=dri.ANALYSIS_ROOT.parent,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "OK: 6 DM-redshift artifacts" in completed.stdout


def _available_analysis_pythons() -> tuple[Path, ...]:
    candidates = (
        Path(sys.executable),
        Path.home() / ".conda" / "envs" / "py312" / "bin" / "python",
        Path("/opt/anaconda3/bin/python3"),
        Path("/opt/homebrew/bin/python3"),
        Path("/usr/bin/python3"),
    )
    available = []
    resolved_available = set()
    for candidate in candidates:
        if not candidate.is_file():
            continue
        probe = subprocess.run(
            [
                str(candidate),
                "-c",
                "import numpy, scipy, astropy, yaml",
            ],
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )
        resolved = candidate.resolve()
        if probe.returncode == 0 and resolved not in resolved_available:
            available.append(candidate)
            resolved_available.add(resolved)
    return tuple(available)


def test_independent_interpreters_generate_semantically_and_byte_identical_outputs(tmp_path):
    script = dri.ANALYSIS_ROOT / "scripts" / "dm_redshift_inference.py"
    interpreters = _available_analysis_pythons()
    assert Path(sys.executable) in interpreters
    roots = tuple(tmp_path / f"process-{index}" for index in range(len(interpreters)))
    processes = []
    for index, (interpreter, root) in enumerate(zip(interpreters, roots, strict=True)):
        environment = os.environ.copy()
        environment["PYTHONHASHSEED"] = str(1 + 8675308 * index)
        processes.append(
            subprocess.Popen(
                [str(interpreter), str(script), "--output-dir", str(root)],
                cwd=dri.ANALYSIS_ROOT.parent,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=environment,
            )
        )
    for process in processes:
        stdout, stderr = process.communicate(timeout=180)
        assert process.returncode == 0, f"{stdout}\n{stderr}"

    reference_root = roots[0]
    relative_files = sorted(
        path.relative_to(reference_root) for path in reference_root.rglob("*") if path.is_file()
    )
    assert relative_files
    for root in roots[1:]:
        assert relative_files == sorted(
            path.relative_to(root) for path in root.rglob("*") if path.is_file()
        )
        for relative in relative_files:
            assert (reference_root / relative).read_bytes() == (root / relative).read_bytes()

    relative_json = dri.RESULT_JSON.relative_to(dri.ANALYSIS_ROOT)
    reference = json.loads((reference_root / relative_json).read_text(encoding="utf-8"))
    for root in roots[1:]:
        comparison = json.loads((root / relative_json).read_text(encoding="utf-8"))
        assert reference == comparison
        for first_row, second_row in zip(reference["rows"], comparison["rows"], strict=True):
            for mode in ("baseline", "coupled"):
                for first_posterior, second_posterior in zip(
                    first_row[mode],
                    second_row[mode],
                    strict=True,
                ):
                    np.testing.assert_array_equal(
                        first_posterior["density"],
                        second_posterior["density"],
                    )
                    np.testing.assert_array_equal(
                        first_posterior["joint_density"],
                        second_posterior["joint_density"],
                    )
