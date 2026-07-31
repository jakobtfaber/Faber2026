"""Workflow tests for the permanent synthetic vertical slice."""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from collections.abc import Iterator
from pathlib import Path

import jsonschema
import numpy as np
import pytest

import workflows.dualband_burst_model as workflow
from workflows.dualband_burst_model import promote_result, run_event


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module", autouse=True)
def _clean_test_checkout() -> Iterator[None]:
    patch = pytest.MonkeyPatch()
    patch.setattr(
        workflow,
        "_git_identity",
        lambda _root: {"commit": "test", "dirty": False, "dirty_paths": []},
    )
    yield
    patch.undo()


@pytest.fixture(scope="module")
def published_result(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    output_root = tmp_path_factory.mktemp("published")
    result_dir = run_event(
        event="synthetic",
        stage="review",
        repository_root=Path(__file__).parents[1],
        output_root=output_root,
    )
    return output_root, result_dir


def test_synthetic_workflow_publishes_five_hash_bound_products(
    published_result: tuple[Path, Path],
) -> None:
    _, result_dir = published_result
    expected = {
        "params.json",
        "posterior.npz",
        "model-products.npz",
        "provenance.json",
        "review-packet.pdf",
    }
    assert {path.name for path in result_dir.iterdir()} == expected
    assert not result_dir.with_name("synthetic.publishing").exists()

    params = json.loads((result_dir / "params.json").read_text())
    provenance = json.loads((result_dir / "provenance.json").read_text())
    assert params["status"] == "provisional-owner-review"
    assert provenance["immutable_params_sha256"] == workflow._immutable_params_sha256(
        params
    )
    assert Path(provenance["environment"]["dynesty_origin"]).is_file()
    assert params["event"] == {
        "nickname": "synthetic",
        "tns_name": "SYNTHETIC",
        "instrument_burst_ids": {
            "chimefrb": "synthetic-chimefrb",
            "dsa110": "synthetic-dsa110",
        },
    }
    for name in expected - {"params.json"}:
        assert params["products"][name]["sha256"] == _sha256(result_dir / name)


def test_resume_reuses_identical_products_and_owner_promotion_changes_status_only(
    published_result: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    output_root, first = published_result
    repository_root = Path(__file__).parents[1]
    before = {path.name: _sha256(path) for path in first.iterdir()}
    second = run_event("synthetic", "review", repository_root, output_root)
    assert second == first
    assert {path.name: _sha256(path) for path in second.iterdir()} == before

    promoted = tmp_path / "dualband-burst-models" / "synthetic"
    promoted.parent.mkdir()
    shutil.copytree(first, promoted)
    pre_promotion = (promoted / "params.json").read_text()
    promote_result(promoted, owner="synthetic-test-owner")
    after = {path.name: _sha256(path) for path in promoted.iterdir()}
    assert after["posterior.npz"] == before["posterior.npz"]
    assert after["model-products.npz"] == before["model-products.npz"]
    params = json.loads((promoted / "params.json").read_text())
    assert params["status"] == "accepted"
    receipt = promoted.parent.parent / params["owner_acceptance"]["receipt_path"]
    assert receipt.exists()
    assert _sha256(receipt) == params["owner_acceptance"]["receipt_sha256"]
    accepted = json.loads(receipt.read_text())
    provenance_hash = json.loads(
        (promoted / "provenance.json").read_text()
    )["immutable_params_sha256"]
    assert accepted["immutable_params_sha256"] == provenance_hash
    assert accepted["pre_promotion_params_sha256"] == hashlib.sha256(
        pre_promotion.encode()
    ).hexdigest()
    workflow._validate_canonical(
        promoted,
        params["request_sha256"],
        repository_root,
    )

    (promoted / "params.json").write_text(pre_promotion)
    promote_result(promoted, owner="synthetic-test-owner")
    assert json.loads((promoted / "params.json").read_text())["status"] == "accepted"


def test_canonical_refuses_tampered_scientific_summary(
    published_result: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    _, source = published_result
    canonical = tmp_path / "dualband-burst-models" / "synthetic"
    canonical.parent.mkdir()
    shutil.copytree(source, canonical)
    params_path = canonical / "params.json"
    params = json.loads(params_path.read_text())
    params["shared_absolute_dm"]["median"] += 0.01
    workflow._write_json(params_path, params)
    with pytest.raises(
        workflow.WorkflowFailure,
        match="parameters differ from their provenance binding",
    ):
        workflow._validate_canonical(
            canonical,
            params["request_sha256"],
            Path(__file__).parents[1],
        )


def test_params_schema_rejects_accepted_result_without_owner_receipt(
    published_result: tuple[Path, Path],
) -> None:
    _, result_dir = published_result
    params = json.loads((result_dir / "params.json").read_text())
    params["status"] = "accepted"
    params.pop("owner_acceptance", None)
    schema = json.loads(
        (
            Path(__file__).parents[1]
            / "analysis-configs"
            / "dualband-burst-models"
            / "params.schema.json"
        ).read_text()
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(params, schema)


def test_resume_refuses_a_changed_stage_product(tmp_path: Path) -> None:
    repository_root = Path(__file__).parents[1]
    run_directory = run_event(
        "synthetic", "observations", repository_root, tmp_path
    )
    with (run_directory / "observations.npz").open("ab") as stream:
        stream.write(b"changed")
    with pytest.raises(RuntimeError, match="changed after receipt"):
        run_event("synthetic", "fit", repository_root, tmp_path)
    receipts = list(
        (tmp_path / ".failed" / "synthetic").glob("*/*/failure-receipt.json")
    )
    assert len(receipts) == 1
    failure = json.loads(receipts[0].read_text())
    assert failure["reason_codes"] == ["provenance-stage-hash-mismatch"]
    assert failure["last_valid_stage"] is None
    assert not (tmp_path / "dualband-burst-models" / "synthetic").exists()


def test_permanent_slice_has_no_flits_or_legacy_pipeline_imports() -> None:
    root = Path(__file__).parents[1]
    paths = [
        *sorted((root / "faber2026").rglob("*.py")),
        root / "studies" / "dualband_synthetic.py",
        root / "workflows" / "dualband_burst_model.py",
        root / "scripts" / "run_dualband_burst_model.py",
    ]
    source = "\n".join(path.read_text() for path in paths)
    assert "import flits" not in source.lower()
    assert "from flits" not in source.lower()
    assert "radio_pipeline" not in source


def test_verification_uses_declared_component_identifiers() -> None:
    source = (Path(__file__).parents[1] / "workflows" / "dualband_burst_model.py").read_text()
    assert '"width_400_s:component-1"' not in source


def test_unsupported_union_parameter_has_no_posterior_summary() -> None:
    summary = workflow._weighted_summary(
        np.array([float("nan"), 1.0]), np.array([0.0, 0.0])
    )
    assert math.isnan(summary.median)


def test_crop_tail_verification_handles_mixed_morphology_samples() -> None:
    from faber2026.burst_models import JointFitResult, PosteriorSummary
    from studies.dualband_synthetic import build_synthetic_event

    root = Path(__file__).parents[1]
    configuration = workflow._load_configuration("synthetic", root)
    event = build_synthetic_event(configuration)
    names = (
        "absolute_dm",
        "toa_400_s:matched-component",
        "width_400_s:matched-component",
        "width_index",
        "timing_error_s:chimefrb",
        "timing_error_s:dsa110",
        "tau_1ghz_s",
        "amplitude:chimefrb:chime-component-1",
        "amplitude:chimefrb:chime-component-2",
        "local_toa_s:chimefrb:chime-component-2",
        "local_width_s:chimefrb:chime-component-2",
        "amplitude:dsa110:dsa-component-1",
    )
    samples = np.array(
        [
            [491.25, 0.08, 0.002, 0.0, 0.0, 0.0, np.nan, 1.0, 0.6, 0.125, 0.002, 1.0],
            [491.25, 0.08, 0.002, 0.0, 0.0, 0.0, 0.0003, 1.0, 0.6, 0.125, 0.002, 1.0],
        ]
    )
    products = {
        observation.instrument: np.zeros_like(observation.intensity)
        for observation in event.request.observations
    }
    result = JointFitResult(
        status="provisional-owner-review",
        shared_dm=PosteriorSummary(491.25, 491.24, 491.26),
        component_toas=(PosteriorSummary(0.08, 0.079, 0.081),),
        parameter_names=names,
        parameter_units=tuple("s" for _ in names),
        samples=samples,
        weights=np.array([0.5, 0.5]),
        sample_morphologies=np.array(["gaussian", "emg"]),
        sample_associations=np.array(["one-to-one", "one-to-one"]),
        log_evidence=0.0,
        log_evidence_uncertainty=0.1,
        maximum_not_on_boundary=True,
        prior_edge_mass_by_parameter={name: 0.0 for name in names},
        morphology_weights={"gaussian": 0.5, "emg": 0.5},
        morphology_statuses={
            "gaussian": "provisional-owner-review",
            "emg": "provisional-owner-review",
        },
        morphology_log_evidences={"gaussian": 0.0, "emg": 0.0},
        morphology_log_evidence_uncertainties={"gaussian": 0.1, "emg": 0.1},
        morphology_maximum_prior_edge_mass={"gaussian": 0.0, "emg": 0.0},
        association_weights={"one-to-one": 1.0},
        model_by_instrument=products,
        residual_by_instrument=products,
    )
    with pytest.raises(workflow.WorkflowFailure) as raised:
        workflow._verification(event, result, configuration)
    checks = raised.value.diagnostics["checks"]
    assert np.isfinite(checks["crop-tail-support"]["measured"])
    assert checks["crop-tail-support"]["measured"] <= 1.0
    assert "verification-crop-tail-support" not in raised.value.reason_codes


def test_preflight_failure_writes_a_unique_failure_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_environment(_root: Path) -> dict[str, object]:
        raise RuntimeError("synthetic environment rejection")

    monkeypatch.setattr(workflow, "_environment_preflight", reject_environment)
    with pytest.raises(RuntimeError, match="synthetic environment rejection"):
        run_event("synthetic", "observations", Path(__file__).parents[1], tmp_path)
    receipts = list(
        (tmp_path / ".failed" / "synthetic").glob("*/*/failure-receipt.json")
    )
    assert len(receipts) == 1
    assert json.loads(receipts[0].read_text())["failed_stage"] == "preflight"


def test_resume_rejects_environment_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_environment = {"manifest_sha256": "1" * 64}
    second_environment = {"manifest_sha256": "2" * 64}
    monkeypatch.setattr(
        workflow,
        "_environment_preflight",
        lambda _root: first_environment,
    )
    run_event("synthetic", "observations", Path(__file__).parents[1], tmp_path)
    monkeypatch.setattr(
        workflow,
        "_environment_preflight",
        lambda _root: second_environment,
    )
    with pytest.raises(RuntimeError, match="environment differs"):
        run_event("synthetic", "fit", Path(__file__).parents[1], tmp_path)
    receipts = list(
        (tmp_path / ".failed" / "synthetic").glob("*/*/failure-receipt.json")
    )
    assert len(receipts) == 1
    assert json.loads(receipts[0].read_text())["reason_codes"] == [
        "provenance-environment-mismatch"
    ]
