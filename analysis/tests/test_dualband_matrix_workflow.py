"""Four-cell dual-band workflow orchestration tests."""

from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path

import jsonschema
import numpy as np
import pytest
from pypdf import PdfReader

import workflows.dualband_burst_model as workflow
from faber2026.burst_models import JointFitResult, PosteriorSummary
from studies.dualband_synthetic import build_synthetic_event

REPOSITORY_ROOT = Path(__file__).parents[1]
REQUEST_HASH = "1" * 64
ENVIRONMENT_HASH = "2" * 64
SOURCE = {"commit": "test", "dirty": False, "dirty_paths": []}


def _fixed_environment() -> dict[str, object]:
    return {"manifest_sha256": ENVIRONMENT_HASH, "code": SOURCE}


def _write_fake_matrix(root: Path) -> Path:
    configuration = json.loads(
        (
            REPOSITORY_ROOT
            / "analysis-configs"
            / "dualband-burst-models"
            / "synthetic.json"
        ).read_text()
    )
    event = build_synthetic_event(configuration)
    input_hashes = {
        observation.instrument: dict(observation.input_hashes)
        for observation in event.request.observations
    }
    matrix = root / "synthetic" / REQUEST_HASH
    for association in configuration["fit"]["associations"]:
        association_id = association["association_id"]
        for morphology in configuration["fit"]["morphologies"]:
            cell = matrix / association_id / morphology
            checkpoints = cell / "checkpoints"
            checkpoints.mkdir(parents=True)
            for name in (
                "posterior.npz",
                "model-products.npz",
                f"checkpoints/{association_id}-{morphology}.pkl",
            ):
                path = cell / name
                path.write_bytes(name.encode())
            run_context = {
                "request_sha256": REQUEST_HASH,
                "environment_sha256": ENVIRONMENT_HASH,
                "schema_version": configuration["schema_version"],
                "model_version": "joint-burst-v1",
                "input_hashes": input_hashes,
            }
            binding = {
                "run_identity": workflow.hashlib.sha256(
                    workflow._canonical_json(run_context)
                ).hexdigest(),
                "run_context": run_context,
                "model_version": "joint-burst-v1",
                "association": association_id,
                "morphology": morphology,
                "parameters": ["absolute_dm"],
                "prior_specs": [["uniform", 491.1, 491.4]],
                "nlive": configuration["fit"]["nlive"],
                "dlogz": configuration["fit"]["dlogz"],
            }
            workflow._write_json(
                checkpoints / f"{association_id}-{morphology}.json",
                {
                    "schema_version": "1.0.0",
                    "binding": binding,
                    "binding_sha256": workflow.hashlib.sha256(
                        workflow._canonical_json(binding)
                    ).hexdigest(),
                },
            )
            receipt = {
                "schema_version": "1.0.0",
                "request_sha256": REQUEST_HASH,
                "environment_sha256": ENVIRONMENT_HASH,
                "source": SOURCE,
                "cell": {
                    "association_id": association_id,
                    "morphology": morphology,
                },
                "binding": {
                    "configuration_schema_version": configuration["schema_version"],
                    "model_version": "joint-burst-v1",
                    "input_hashes": input_hashes,
                },
                "sampler": {
                    "seed": configuration["fit"]["seed"],
                    "nlive": configuration["fit"]["nlive"],
                    "dlogz": configuration["fit"]["dlogz"],
                },
                "timing": {
                    "started_unix_ns": 1,
                    "finished_unix_ns": 2,
                    "elapsed_seconds": 1.0,
                },
                "files": workflow._cell_files(cell),
            }
            workflow._write_json(cell / "cell-receipt.json", receipt)
    return matrix


@pytest.mark.integration
def test_fit_cell_writes_closed_hash_bound_receipt(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        workflow,
        "_git_identity",
        lambda _root: {"commit": "test", "dirty": False, "dirty_paths": []},
    )
    cell = workflow.run_fit_cell(
        event="synthetic",
        association_id="one-to-one",
        morphology="gaussian",
        repository_root=REPOSITORY_ROOT,
        cells_root=tmp_path,
    )

    receipt = json.loads((cell / "cell-receipt.json").read_text())
    schema = json.loads(
        (
            REPOSITORY_ROOT
            / "analysis-configs"
            / "dualband-burst-models"
            / "cell-receipt.schema.json"
        ).read_text()
    )
    jsonschema.validate(receipt, schema)
    assert receipt["cell"] == {
        "association_id": "one-to-one",
        "morphology": "gaussian",
    }
    assert receipt["source"] == {
        "commit": "test",
        "dirty": False,
        "dirty_paths": [],
    }
    assert set(receipt["files"]) == {
        "posterior.npz",
        "model-products.npz",
        "checkpoints/one-to-one-gaussian.json",
        "checkpoints/one-to-one-gaussian.pkl",
    }
    assert {path.name for path in cell.iterdir()} == {
        "cell-receipt.json",
        "checkpoints",
        "model-products.npz",
        "posterior.npz",
    }


def test_aggregate_refuses_a_missing_cell(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        workflow,
        "_git_identity",
        lambda _root: {"commit": "test", "dirty": False, "dirty_paths": []},
    )
    with pytest.raises(workflow.WorkflowFailure, match="missing matrix cell"):
        workflow.aggregate_fit_cells(
            event="synthetic",
            repository_root=REPOSITORY_ROOT,
            cells_root=tmp_path / "cells",
            output_root=tmp_path / "results",
        )


def test_fit_cell_refuses_unsafe_event_path(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="safe path components"):
        workflow.run_fit_cell(
            event="../synthetic",
            association_id="one-to-one",
            morphology="gaussian",
            repository_root=REPOSITORY_ROOT,
            cells_root=tmp_path,
        )


def test_fit_cell_reuse_refuses_changed_identity(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(workflow, "_request_hash", lambda *_args: REQUEST_HASH)
    monkeypatch.setattr(
        workflow,
        "_environment_preflight",
        lambda *_args: _fixed_environment(),
    )
    matrix = _write_fake_matrix(tmp_path)
    receipt_path = matrix / "one-to-one" / "gaussian" / "cell-receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["source"]["commit"] = "another"
    workflow._write_json(receipt_path, receipt)
    with pytest.raises(workflow.WorkflowFailure, match="identity differs"):
        workflow.run_fit_cell(
            event="synthetic",
            association_id="one-to-one",
            morphology="gaussian",
            repository_root=REPOSITORY_ROOT,
            cells_root=tmp_path,
        )


def test_aggregate_refuses_semantic_cell_substitution(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(workflow, "_request_hash", lambda *_args: REQUEST_HASH)
    monkeypatch.setattr(
        workflow,
        "_environment_preflight",
        lambda *_args: _fixed_environment(),
    )
    _write_fake_matrix(tmp_path / "cells")
    configuration = workflow._load_configuration("synthetic", REPOSITORY_ROOT)
    event = build_synthetic_event(configuration)
    models = {
        observation.instrument: np.zeros_like(observation.intensity)
        for observation in event.request.observations
    }
    substituted = JointFitResult(
        status="provisional-owner-review",
        shared_dm=PosteriorSummary(491.25, 491.24, 491.26),
        component_toas=(PosteriorSummary(0.08, 0.07, 0.09),),
        parameter_names=("absolute_dm",),
        parameter_units=("pc cm^-3",),
        samples=np.array([[491.25]]),
        weights=np.array([1.0]),
        sample_morphologies=np.array(["gaussian"]),
        sample_associations=np.array(["wrong-chime-component"]),
        log_evidence=0.0,
        log_evidence_uncertainty=0.1,
        maximum_not_on_boundary=True,
        prior_edge_mass_by_parameter={"absolute_dm": 0.0},
        morphology_weights={"gaussian": 1.0},
        morphology_statuses={"gaussian": "provisional-owner-review"},
        morphology_log_evidences={"gaussian": 0.0},
        morphology_log_evidence_uncertainties={"gaussian": 0.1},
        morphology_maximum_prior_edge_mass={"gaussian": 0.0},
        association_weights={"wrong-chime-component": 1.0},
        model_by_instrument=models,
        residual_by_instrument=models,
    )
    monkeypatch.setattr(workflow, "_load_fit", lambda *_args: substituted)
    with pytest.raises(workflow.WorkflowFailure, match="posterior semantics"):
        workflow.aggregate_fit_cells(
            "synthetic",
            REPOSITORY_ROOT,
            tmp_path / "cells",
            tmp_path / "results",
        )


@pytest.mark.parametrize(
    "mutation",
    (
        "file-bytes",
        "request",
        "environment",
        "source",
        "cell",
        "sampler",
        "extra-file",
        "filename-substitution",
        "symlink",
    ),
)
def test_aggregate_refuses_untrusted_cell_artifacts(
    tmp_path: Path,
    monkeypatch,
    mutation: str,
) -> None:
    monkeypatch.setattr(workflow, "_request_hash", lambda *_args: REQUEST_HASH)
    monkeypatch.setattr(workflow, "_environment_preflight", lambda *_args: _fixed_environment())
    matrix = _write_fake_matrix(tmp_path / "cells")
    cell = matrix / "one-to-one" / "gaussian"
    receipt_path = cell / "cell-receipt.json"
    receipt = json.loads(receipt_path.read_text())
    if mutation == "file-bytes":
        (cell / "posterior.npz").write_bytes(b"tampered")
    elif mutation == "request":
        receipt["request_sha256"] = "3" * 64
    elif mutation == "environment":
        receipt["environment_sha256"] = "3" * 64
    elif mutation == "source":
        receipt["source"]["commit"] = "another"
    elif mutation == "cell":
        receipt["cell"]["association_id"] = "another"
    elif mutation == "sampler":
        receipt["sampler"]["seed"] += 1
    elif mutation == "extra-file":
        (cell / "unexpected.bin").write_bytes(b"unexpected")
    elif mutation == "filename-substitution":
        original = cell / "posterior.npz"
        original.rename(cell / "substitute.npz")
    elif mutation == "symlink":
        os.symlink(cell / "posterior.npz", cell / "unexpected-link")
    if mutation in {"request", "environment", "source", "cell", "sampler"}:
        workflow._write_json(receipt_path, receipt)
    with pytest.raises(workflow.WorkflowFailure):
        workflow.aggregate_fit_cells(
            event="synthetic",
            repository_root=REPOSITORY_ROOT,
            cells_root=tmp_path / "cells",
            output_root=tmp_path / "results",
        )
    assert not (tmp_path / "results" / "dualband-burst-models").exists()


def test_fit_serialization_preserves_authoritative_summaries_exactly(
    tmp_path: Path,
) -> None:
    configuration = workflow._load_configuration("synthetic", REPOSITORY_ROOT)
    event = build_synthetic_event(configuration)
    event = replace(
        event,
        request=replace(event.request, component_ids=("first", "second")),
    )
    models = {
        observation.instrument: np.zeros_like(observation.intensity)
        for observation in event.request.observations
    }
    summary = PosteriorSummary(491.234567890123, 491.123456789012, 491.345678901234)
    first_toa = PosteriorSummary(0.081234567890, 0.071234567890, 0.091234567890)
    second_toa = PosteriorSummary(0.181234567890, 0.171234567890, 0.191234567890)
    names = (
        "absolute_dm",
        "toa_400_s:first",
        "toa_400_s:second",
        "timing_error_s:chimefrb",
        "timing_error_s:dsa110",
    )
    result = JointFitResult(
        status="provisional-owner-review",
        shared_dm=summary,
        component_toas=(first_toa, second_toa),
        parameter_names=names,
        parameter_units=("pc cm^-3", "s", "s", "s", "s"),
        samples=np.array(
            [
                [491.2, 0.08, 0.18, -0.0001, 0.0001],
                [491.3, 0.09, 0.19, 0.0001, -0.0001],
            ]
        ),
        weights=np.array([0.5, 0.5]),
        sample_morphologies=np.array(["gaussian", "emg"]),
        sample_associations=np.array(["one-to-one", "wrong-chime-component"]),
        log_evidence=1.0,
        log_evidence_uncertainty=0.1,
        maximum_not_on_boundary=True,
        prior_edge_mass_by_parameter={name: 0.0 for name in names},
        morphology_weights={"gaussian": 0.6, "emg": 0.4},
        morphology_statuses={
            "gaussian": "provisional-owner-review",
            "emg": "provisional-owner-review",
        },
        morphology_log_evidences={"gaussian": 1.0, "emg": 0.5},
        morphology_log_evidence_uncertainties={"gaussian": 0.1, "emg": 0.2},
        morphology_maximum_prior_edge_mass={"gaussian": 0.0, "emg": 0.0},
        association_weights={"one-to-one": 0.7, "wrong-chime-component": 0.3},
        model_by_instrument=models,
        residual_by_instrument=models,
    )
    posterior = tmp_path / "posterior.npz"
    products = tmp_path / "model-products.npz"
    workflow._save_fit(posterior, result)
    workflow._save_model_products(products, event, result)
    loaded = workflow._load_fit(posterior, products, event)
    assert loaded.shared_dm == summary
    assert loaded.component_toas == (first_toa, second_toa)
    assert loaded.status == result.status
    assert tuple(loaded.morphology_weights) == ("gaussian", "emg")
    assert tuple(loaded.association_weights) == (
        "one-to-one",
        "wrong-chime-component",
    )
    published = workflow._published_summary_fields(
        event,
        loaded,
        configuration["uncertainty_budget"],
    )
    params_path = tmp_path / "params.json"
    workflow._write_json(params_path, published)
    params = json.loads(params_path.read_text())
    assert {
        key: params["shared_absolute_dm"][key]
        for key in ("median", "lower", "upper")
    } == {
        "median": summary.median,
        "lower": summary.lower,
        "upper": summary.upper,
    }
    assert [component["id"] for component in params["components"]] == [
        "first",
        "second",
    ]
    assert [component["geocentric_toa_400_s"] for component in params["components"]] == [
        {"median": first_toa.median, "lower": first_toa.lower, "upper": first_toa.upper},
        {
            "median": second_toa.median,
            "lower": second_toa.lower,
            "upper": second_toa.upper,
        },
    ]


@pytest.mark.slow
def test_four_cell_aggregate_matches_full_serial_workflow(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(workflow, "_git_identity", lambda _root: SOURCE)
    configuration = json.loads(
        (
            REPOSITORY_ROOT
            / "analysis-configs"
            / "dualband-burst-models"
            / "synthetic.json"
        ).read_text()
    )
    cells_root = tmp_path / "cells"
    for association in configuration["fit"]["associations"]:
        for morphology in configuration["fit"]["morphologies"]:
            workflow.run_fit_cell(
                event="synthetic",
                association_id=association["association_id"],
                morphology=morphology,
                repository_root=REPOSITORY_ROOT,
                cells_root=cells_root,
            )
    aggregate = workflow.aggregate_fit_cells(
        "synthetic", REPOSITORY_ROOT, cells_root, tmp_path / "aggregate"
    )
    serial = workflow.run_event(
        "synthetic", "review", REPOSITORY_ROOT, tmp_path / "serial"
    )
    expected_products = {
        "params.json",
        "posterior.npz",
        "model-products.npz",
        "provenance.json",
        "review-packet.pdf",
    }
    assert {path.name for path in aggregate.iterdir()} == expected_products
    assert {path.name for path in serial.iterdir()} == expected_products
    for name in ("posterior.npz", "model-products.npz"):
        with np.load(aggregate / name, allow_pickle=False) as left, np.load(
            serial / name, allow_pickle=False
        ) as right:
            assert left.files == right.files
            for key in left.files:
                np.testing.assert_array_equal(left[key], right[key])
    aggregate_params = json.loads((aggregate / "params.json").read_text())
    serial_params = json.loads((serial / "params.json").read_text())
    for key in (
        "shared_absolute_dm",
        "components",
        "morphology_weights",
        "morphology_statuses",
        "morphology_log_evidences",
        "morphology_log_evidence_uncertainties",
        "association_weights",
        "verification",
    ):
        assert aggregate_params[key] == serial_params[key]
    aggregate_provenance = json.loads((aggregate / "provenance.json").read_text())
    serial_provenance = json.loads((serial / "provenance.json").read_text())
    assert aggregate_provenance["aggregation"]["method"] == (
        "configured-serial-cell-evidence-mixture"
    )
    assert aggregate_provenance["aggregation"]["ordered_cells"] == [
        "one-to-one/gaussian",
        "one-to-one/emg",
        "wrong-chime-component/gaussian",
        "wrong-chime-component/emg",
    ]
    assert set(aggregate_provenance["aggregation"]["cells"]) == set(
        aggregate_provenance["aggregation"]["ordered_cells"]
    )
    assert "aggregation" not in serial_provenance
    for key in (
        "request_sha256",
        "configuration_sha256",
        "observation_product_sha256",
        "source_kind",
        "environment",
        "code",
        "lock_sha256",
        "inputs",
    ):
        assert aggregate_provenance[key] == serial_provenance[key]
    aggregate_pdf = PdfReader(aggregate / "review-packet.pdf")
    serial_pdf = PdfReader(serial / "review-packet.pdf")
    assert len(aggregate_pdf.pages) == len(serial_pdf.pages)
    assert [page.extract_text() for page in aggregate_pdf.pages] == [
        page.extract_text() for page in serial_pdf.pages
    ]
    for directory, params in (
        (aggregate, aggregate_params),
        (serial, serial_params),
    ):
        for name in expected_products - {"params.json"}:
            assert params["products"][name]["sha256"] == workflow._sha256(
                directory / name
            )
