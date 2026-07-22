from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from scripts.audit_deprecated_zach_c2d4 import (
    ArtifactBundle,
    audit,
    load_model,
    render_residual_svg,
    sha256,
)


def _component_names(components_d: int) -> list[str]:
    return [
        parameter
        for band, count in (("C", 2), ("D", components_d))
        for index in range(1, count + 1)
        for parameter in (f"t0_{band}{index}", f"zeta_{band}{index}")
    ]


def _summary(components_d: int) -> dict:
    percentiles = {}
    for name in _component_names(components_d):
        index = int(name[-1])
        median = float(index) if name.startswith("t0") else float(index + 1)
        if name == "zeta_D4":
            median = 30.0
        percentiles[name] = {
            "lower": median - 0.1,
            "median": median,
            "upper": median + 0.1,
        }
    return {
        "burst": "zach",
        "components_C": 2,
        "components_D": components_d,
        "gain_s2": 100.0,
        "beta_bounds": [3.0, 4.0],
        "beta": {"median": 3.2, "err_minus": 0.1, "err_plus": 0.1},
        "tau_1ghz": {"median": 0.2, "err_minus": 0.01, "err_plus": 0.01},
        "log_evidence": 90.0 if components_d == 4 else 100.0,
        "percentiles": percentiles,
    }


def _model(path: Path, components_d: int, prediction_offset: float) -> None:
    time_c = np.linspace(0.0, 5.0, 6)
    time_d = np.linspace(0.0, 5.0, 6)
    data_c = np.arange(18, dtype=float).reshape(3, 6) / 10.0
    data_d = np.arange(24, dtype=float).reshape(4, 6) / 10.0
    np.savez(
        path,
        nC=2,
        nD=components_d,
        timeC=time_c,
        freqC=np.arange(3),
        dataC=data_c,
        modelC=data_c + prediction_offset,
        noiseC=np.ones(3),
        validC=np.ones(3, dtype=bool),
        fluenceC=[60.0, 40.0],
        chi2C=1.1,
        timeD=time_d,
        freqD=np.arange(4),
        dataD=data_d,
        modelD=data_d + prediction_offset,
        noiseD=np.ones(4),
        validD=np.ones(4, dtype=bool),
        chi2D=1.2,
        fluenceD=([50.0, 30.0, 18.0, 2.0] if components_d == 4 else [50.0, 30.0, 20.0]),
        burst="zach",
    )


def _write_fixture(tmp_path: Path, *, review_manifest: bool = True) -> ArtifactBundle:
    fit = tmp_path / "fit.json"
    comparison_fit = tmp_path / "comparison-fit.json"
    fit.write_text(json.dumps(_summary(4)), encoding="utf-8")
    comparison_fit.write_text(json.dumps(_summary(3)), encoding="utf-8")

    names = _component_names(4)
    medians = np.array([_summary(4)["percentiles"][name]["median"] for name in names])
    samples = np.vstack((medians - 0.1, medians, medians + 0.1))
    samples_path = tmp_path / "samples.npz"
    np.savez(
        samples_path,
        samples=samples,
        weights=[0.16, 0.34, 0.50],
        param_names=np.array(names, dtype=object),
    )

    model = tmp_path / "model.npz"
    comparison_model = tmp_path / "comparison-model.npz"
    _model(model, 4, 0.25)
    _model(comparison_model, 3, 0.50)

    stdout = tmp_path / "job.out"
    stdout.write_text(
        "HOST=h17 JOB=180 START=2026-07-19T14:55:43-07:00 "
        "BURST=zach NLIVE=400 NPROC=4 "
        "EARGS=[--components-C 2 --components-D 4 --gain-s2 100] "
        "MAXCH=def SNRT=def\n",
        encoding="utf-8",
    )
    stderr = tmp_path / "job.err"
    stderr.write_text("progress\n", encoding="utf-8")

    manifest_path = None
    if review_manifest:
        manifest_path = tmp_path / "review.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "components_C": 2,
                    "components_D": 4,
                    "fit_sha256": sha256(fit),
                    "samples_sha256": sha256(samples_path),
                    "model_grid_sha256": sha256(model),
                }
            ),
            encoding="utf-8",
        )
    return ArtifactBundle(
        fit=fit,
        samples=samples_path,
        model=model,
        comparison_fit=comparison_fit,
        comparison_model=comparison_model,
        stdout_log=stdout,
        stderr_log=stderr,
        review_manifest=manifest_path,
    )


def test_audit_reconstructs_all_components_and_flags_pedestal(
    tmp_path: Path,
) -> None:
    result = audit(_write_fixture(tmp_path))

    assert len(result["component_diagnostics"]["C"]["components"]) == 2
    assert len(result["component_diagnostics"]["D"]["components"]) == 4
    failure = result["failure"]
    assert failure["fourth_DSA_component_width_to_window_ratio"] == 6.0
    assert failure["fourth_DSA_component_fluence_fraction"] == 0.02
    assert failure["broad_low_fluence_pedestal"] is True
    assert failure["all_flagged_component_degeneracies"] == [
        {
            "band": "D",
            "component": 4,
            "broad_vs_window": True,
            "low_fluence": True,
        }
    ]
    assert result["guard_contract"]["component_arrival_intervals_inside_fitted_window"]
    assert result["guard_contract"]["any_low_fluence_component_flag_triggered"]
    assert result["component_identity"][
        "content_identity_complete_across_review_manifest"
    ]
    assert result["verdict"]["deprecated_panel_review_eligible"] is False


def test_audit_keeps_evidence_comparison_diagnostic_only(tmp_path: Path) -> None:
    result = audit(_write_fixture(tmp_path))

    evidence = result["evidence_comparison"]
    assert evidence["fitted_support_and_data_match"] == {
        "timeC": True,
        "freqC": True,
        "timeD": True,
        "freqD": True,
        "dataC": True,
        "dataD": True,
        "noiseC": True,
        "noiseD": True,
        "validC": True,
        "validD": True,
    }
    assert evidence["likelihood_identity"] == "unproven"
    assert evidence["posterior_mode_identity"] == "unproven"
    assert evidence["comparison_admissible"] is False
    assert evidence["raw_log_evidence_C2D4_minus_C2D3_diagnostic_only"] == -10.0


def test_audit_reconstructs_residual_maps_and_profiles(tmp_path: Path) -> None:
    result = audit(_write_fixture(tmp_path))

    for model in ("C2D4", "C2D3_comparison"):
        for band in ("C", "D"):
            residual = result["residual_morphology"][model][band]
            assert residual["normalized_map_shape"][1] == 6
            assert len(residual["normalized_map_sha256"]) == 64
            assert len(residual["band_summed_profile_sha256"]) == 64
            assert residual["band_summed_profile_max_abs"] > 0
            assert residual["recorded_reduced_residual_statistic"] > 0


def test_audit_records_missing_review_manifest_as_incomplete(tmp_path: Path) -> None:
    result = audit(_write_fixture(tmp_path, review_manifest=False))

    assert result["component_identity"]["component_structure_matches"] is True
    assert (
        result["component_identity"]["content_identity_complete_across_review_manifest"]
        is False
    )
    assert (
        result["guard_contract"]["content_identity_complete_across_review_manifest"]
        is False
    )


def test_audit_rejects_component_count_mismatch(tmp_path: Path) -> None:
    artifacts = _write_fixture(tmp_path)
    fit = json.loads(artifacts.fit.read_text(encoding="utf-8"))
    fit["components_D"] = 3
    artifacts.fit.write_text(json.dumps(fit), encoding="utf-8")

    with pytest.raises(ValueError, match="deprecated fit is not C2D4"):
        audit(artifacts)


@pytest.mark.parametrize("field", ["samples", "model"])
def test_audit_rejects_scientific_artifact_identity_mismatch(
    tmp_path: Path, field: str
) -> None:
    artifacts = _write_fixture(tmp_path)
    if field == "samples":
        with np.load(artifacts.samples, allow_pickle=True) as source:
            np.savez(
                artifacts.samples,
                samples=source["samples"][:, :-1],
                weights=source["weights"],
                param_names=source["param_names"][:-1],
            )
    else:
        model = dict(np.load(artifacts.model, allow_pickle=True))
        model["nD"] = np.array(3)
        np.savez(artifacts.model, **model)

    with pytest.raises(ValueError, match="component identity mismatch"):
        audit(artifacts)


def test_audit_records_review_manifest_hash_mismatch(tmp_path: Path) -> None:
    artifacts = _write_fixture(tmp_path)
    review = json.loads(artifacts.review_manifest.read_text(encoding="utf-8"))
    review["model_grid_sha256"] = "0" * 64
    artifacts.review_manifest.write_text(json.dumps(review), encoding="utf-8")

    result = audit(artifacts)
    assert result["component_identity"]["component_structure_matches"] is True
    assert result["component_identity"]["review_manifest_hashes_match"] is False
    assert (
        result["component_identity"]["content_identity_complete_across_review_manifest"]
        is False
    )


def test_audit_rejects_model_burst_label_mismatch(tmp_path: Path) -> None:
    artifacts = _write_fixture(tmp_path)
    model = dict(np.load(artifacts.model, allow_pickle=True))
    model["burst"] = np.array("other")
    np.savez(artifacts.model, **model)

    with pytest.raises(ValueError, match="component identity mismatch"):
        audit(artifacts)


def test_audit_rejects_duplicate_posterior_parameter(tmp_path: Path) -> None:
    artifacts = _write_fixture(tmp_path)
    with np.load(artifacts.samples, allow_pickle=True) as source:
        np.savez(
            artifacts.samples,
            samples=np.column_stack((source["samples"], source["samples"][:, 0])),
            weights=source["weights"],
            param_names=np.append(source["param_names"], source["param_names"][0]),
        )

    with pytest.raises(ValueError, match="component identity mismatch"):
        audit(artifacts)


@pytest.mark.parametrize("field", ["validD", "noiseD"])
def test_support_comparison_includes_mask_and_noise(tmp_path: Path, field: str) -> None:
    artifacts = _write_fixture(tmp_path)
    comparison = dict(np.load(artifacts.comparison_model, allow_pickle=True))
    if field == "validD":
        comparison[field] = comparison[field].copy()
        comparison[field][0] = False
    else:
        comparison[field] = comparison[field] * 2
    np.savez(artifacts.comparison_model, **comparison)

    result = audit(artifacts)
    assert (
        result["evidence_comparison"]["fitted_support_and_data_match"][field] is False
    )
    assert result["evidence_comparison"]["comparison_admissible"] is False


def test_residual_svg_is_byte_reproducible(tmp_path: Path) -> None:
    artifacts = _write_fixture(tmp_path)
    first = tmp_path / "first.svg"
    second = tmp_path / "second.svg"
    render_residual_svg(
        load_model(artifacts.model), load_model(artifacts.comparison_model), first
    )
    render_residual_svg(
        load_model(artifacts.model), load_model(artifacts.comparison_model), second
    )

    assert first.read_bytes() == second.read_bytes()
    assert b"normalized residual profile" in first.read_bytes()
