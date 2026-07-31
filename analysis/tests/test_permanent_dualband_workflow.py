"""Workflow tests for the permanent synthetic vertical slice."""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Iterator
from pathlib import Path

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
    assert params["status"] == "provisional-owner-review"
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

    promoted = tmp_path / "synthetic"
    shutil.copytree(first, promoted)
    promote_result(promoted, owner="synthetic-test-owner")
    after = {path.name: _sha256(path) for path in promoted.iterdir()}
    assert after["posterior.npz"] == before["posterior.npz"]
    assert after["model-products.npz"] == before["model-products.npz"]
    params = json.loads((promoted / "params.json").read_text())
    assert params["status"] == "accepted"
    receipt = promoted.parent.parent / params["owner_acceptance"]["receipt_path"]
    assert receipt.exists()
    assert _sha256(receipt) == params["owner_acceptance"]["receipt_sha256"]


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
