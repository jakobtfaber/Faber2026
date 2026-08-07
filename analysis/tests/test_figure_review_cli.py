"""CLI selection tests for the fail-closed figure-review workflow."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import figure_review  # noqa: E402


def test_new_batch_accepts_a_single_candidate_selection():
    args = figure_review.parser().parse_args(
        [
            "new-batch",
            "test-batch",
            "--title",
            "test",
            "--pipeline-revision",
            "deadbeef",
            "--candidate",
            "fig1-gallery",
        ]
    )
    assert args.candidate == ["fig1-gallery"]


def reproduction_receipt(manifest: dict, candidate: dict) -> dict:
    return {
        "candidate_id": candidate["id"],
        "clean_worktree": True,
        "command": ["python", "produce.py"],
        "cwd": ".",
        "environment": {"identity": "pipeline/uv.lock", "sha256": "d" * 64},
        "inputs": [{"path": "input.dat", "sha256": "a" * 64}],
        "output_sha256": candidate["artifact_sha256"],
        "pipeline_revision": manifest["pipeline_revision"],
        "source_revision": manifest["source_revision"],
        "status": "verified",
        "verified_at": "2026-07-22T00:00:00+00:00",
        "verifier": "test",
    }


def test_reproduction_gate_rejects_missing_receipt():
    manifest = {"source_revision": "1" * 40, "pipeline_revision": "2" * 40}
    candidate = {"id": "candidate", "artifact_sha256": "b" * 64}
    assert figure_review.reproduction_errors(manifest, candidate) == [
        "candidate: reproduction has not been certified"
    ]


def test_reproduction_gate_accepts_complete_matching_receipt():
    manifest = {"source_revision": "1" * 40, "pipeline_revision": "2" * 40}
    candidate = {"id": "candidate", "artifact_sha256": "b" * 64}
    candidate["reproduction"] = reproduction_receipt(manifest, candidate)
    assert figure_review.reproduction_errors(manifest, candidate) == []


def test_reproduction_gate_rejects_output_or_dirty_worktree():
    manifest = {"source_revision": "1" * 40, "pipeline_revision": "2" * 40}
    candidate = {"id": "candidate", "artifact_sha256": "b" * 64}
    receipt = reproduction_receipt(manifest, candidate)
    receipt["output_sha256"] = "c" * 64
    receipt["clean_worktree"] = False
    candidate["reproduction"] = receipt
    errors = figure_review.reproduction_errors(manifest, candidate)
    assert "candidate: reproduced output SHA-256 mismatch" in errors
    assert "candidate: reproduction was not run from a clean worktree" in errors


def test_next_command_supports_json_flag():
    args = figure_review.parser().parse_args(["next", "--json"])
    assert args.json is True


def test_status_command_supports_json_flag():
    args = figure_review.parser().parse_args(["status", "--json"])
    assert args.json is True


def test_triptych_slots_require_fit_and_residual_provenance():
    slot = next(item for item in figure_review.slots() if item["id"] == "triptych-zach")
    requirements = " ".join(slot["required_provenance"])
    assert "fit summary" in requirements
    assert "fit-generation reproducibility" in requirements
    assert "residual diagnostics" in requirements


def test_registry_artifact_matching_handles_hashes_globs_and_directories():
    assert figure_review.registry_artifact_matches(
        "figures/dm_host_posteriors.pdf",
        "figures/dm_host_posteriors.pdf md5:deadbeef",
    )
    assert figure_review.registry_artifact_matches(
        "figures/association_cards/association_card_*.pdf",
        "figures/association_cards/ dirhash:deadbeef",
    )
