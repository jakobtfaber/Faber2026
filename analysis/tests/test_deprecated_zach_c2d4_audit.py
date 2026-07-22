from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scripts.audit_deprecated_zach_c2d4 import audit


def _summary(components_d: int) -> dict:
    percentiles = {
        "t0_D1": {"lower": 0.9, "median": 1.0, "upper": 1.1},
        "t0_D2": {"lower": 1.9, "median": 2.0, "upper": 2.1},
        "t0_D3": {"lower": 2.9, "median": 3.0, "upper": 3.1},
    }
    if components_d == 4:
        percentiles.update(
            {
                "t0_D4": {"lower": 3.9, "median": 4.0, "upper": 4.1},
                "zeta_D4": {"lower": 29.0, "median": 30.0, "upper": 31.0},
            }
        )
    return {
        "components_C": 2,
        "components_D": components_d,
        "gain_s2": 100.0,
        "beta_bounds": [3.0, 4.0],
        "beta": {"median": 3.2, "err_minus": 0.1, "err_plus": 0.1},
        "tau_1ghz": {"median": 0.2, "err_minus": 0.01, "err_plus": 0.01},
        "log_evidence": 90.0 if components_d == 4 else 100.0,
        "percentiles": percentiles,
    }


def _write_fixture(tmp_path: Path) -> dict[str, Path]:
    fit = tmp_path / "fit.json"
    comparison_fit = tmp_path / "comparison-fit.json"
    fit.write_text(json.dumps(_summary(4)), encoding="utf-8")
    comparison_fit.write_text(json.dumps(_summary(3)), encoding="utf-8")

    names = np.array(
        ["t0_D1", "t0_D2", "t0_D3", "t0_D4", "zeta_D4"], dtype=object
    )
    samples = np.array(
        [
            [0.9, 1.9, 2.9, 3.9, 29.0],
            [1.0, 2.0, 3.0, 4.0, 30.0],
            [1.1, 2.1, 3.1, 4.1, 31.0],
        ]
    )
    samples_path = tmp_path / "samples.npz"
    np.savez(samples_path, samples=samples, weights=[0.16, 0.34, 0.50], param_names=names)

    model = tmp_path / "model.npz"
    np.savez(
        model,
        nC=2,
        nD=4,
        timeD=np.linspace(0.0, 5.0, 6),
        fluenceD=[50.0, 30.0, 18.0, 2.0],
        chi2C=1.1,
        chi2D=1.2,
    )
    comparison_model = tmp_path / "comparison-model.npz"
    np.savez(comparison_model, chi2C=1.1, chi2D=1.3)

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
    return {
        "fit_path": fit,
        "samples_path": samples_path,
        "model_path": model,
        "comparison_fit_path": comparison_fit,
        "comparison_model_path": comparison_model,
        "stdout_log_path": stdout,
        "stderr_log_path": stderr,
    }


def test_audit_flags_broad_low_fluence_pedestal(tmp_path: Path) -> None:
    result = audit(**_write_fixture(tmp_path))

    failure = result["failure"]
    assert failure["fourth_component_width_to_window_ratio"] == 6.0
    assert failure["fourth_component_fluence_fraction"] == 0.02
    assert failure["broad_low_fluence_pedestal"] is True
    assert failure["all_arrival_medians_in_window"] is True
    assert result["comparison_to_c2d3"]["mode_continuous"] is True
    assert result["comparison_to_c2d3"]["log_evidence_C2D4_minus_C2D3"] == -10.0
    assert result["verdict"] == {
        "guard_triggered": True,
        "deprecated_panel_review_eligible": False,
        "deprecated_fit_value_trusted": False,
    }


def test_audit_rejects_component_count_mismatch(tmp_path: Path) -> None:
    paths = _write_fixture(tmp_path)
    fit = json.loads(paths["fit_path"].read_text(encoding="utf-8"))
    fit["components_D"] = 3
    paths["fit_path"].write_text(json.dumps(fit), encoding="utf-8")

    try:
        audit(**paths)
    except ValueError as error:
        assert str(error) == "deprecated fit is not C2D4"
    else:
        raise AssertionError("component-count mismatch did not fail closed")
