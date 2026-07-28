from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_expanded_foreground_independent_release_gate.py"
GATE = ROOT / "docs/rse/specs/validation-expanded-foreground-independent-release-gate.json"
PIPELINE = Path(os.environ.get("FOREGROUND_PIPELINE_REPO", ROOT))
MANUSCRIPT = Path(os.environ.get("FABER2026_MANUSCRIPT_REPO", ROOT))


def _module():
    spec = importlib.util.spec_from_file_location("foreground_release_gate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_release_gate_is_fail_closed_until_source_and_owner_gates_pass():
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    assert gate["status"] == "failed"
    assert gate["disposition"] == "fail_closed"
    assert gate["scientific_trust_promoted"] is False
    assert gate["figure3_promoted"] is False
    blockers = {item["id"] for item in gate["blockers"]}
    # source-verification-incomplete was discharged by the 2026-07-26 pin bump
    # (52/52, zero discrepancies); figure3-registry-snapshot-stale was
    # discharged by the corrected candidate built at pipeline 2463289 from the
    # pinned registry snapshot (dsa110-FLITS #234).
    assert blockers == {
        "expanded-catalog-gate-not-passed",
        "figure3-owner-approval-missing",
    }
    assert all(item["status"] == "failed" for item in gate["blockers"])


def test_release_gate_preserves_its_frozen_source_commit_binding():
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    source = gate["pipeline_commit"]
    assert len(source) == 40
    assert gate["expected"]["source_verification_pipeline_commit"] == source
    assert gate["expected"]["registry_replay_pipeline_commit"] == source


def test_release_gate_accepts_only_a_figure_built_from_the_pinned_registry():
    module = _module()
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    build = json.loads(
        (ROOT / "figure_review/batches/2026-07-26-fig3-no-diamonds"
              "/provenance/expanded-catalog-build.json").read_text(encoding="utf-8")
    )
    # The corrected candidate is built from the pinned registry snapshot, so
    # the snapshot-staleness failure must be gone from the current gate...
    assert build["registry_sha256"] == gate["expected"]["figure3_build_registry_sha256"]
    assert build["registry_sha256"] == gate["expected"]["pinned_registry_sha256"]
    failures = module.gate_failures(module.load_gate(GATE))
    assert not any(
        item.startswith("Figure 3 was built from registry snapshot")
        for item in failures
    )
    # ...while a candidate recorded against any other snapshot still fails.
    tampered = json.loads(GATE.read_text(encoding="utf-8"))
    tampered["expected"]["pinned_registry_sha256"] = "0" * 64
    failures = module.gate_failures(tampered)
    assert any(
        item.startswith("Figure 3 was built from registry snapshot")
        for item in failures
    )


def test_source_verifier_accepts_an_explicit_commit_binding():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/verify_foreground_registry_sources.py"),
            "--help",
        ],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    assert "--pipeline-commit" in result.stdout
    assert "--analysis-commit" in result.stdout


def test_release_gate_validator_exits_nonzero_and_names_blockers():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--gate",
            str(GATE),
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 1
    assert "expanded foreground independent release gate failed" in result.stderr
    assert "expanded-catalog-gate-not-passed" in result.stderr
    assert "figure3-owner-approval-missing" in result.stderr


def test_release_gate_rejects_trust_promotion_when_failed(tmp_path: Path):
    module = _module()
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    gate["scientific_trust_promoted"] = True
    path = tmp_path / "gate.json"
    path.write_text(json.dumps(gate), encoding="utf-8")
    failures = module.gate_failures(module.load_gate(path))
    assert "failed gate cannot promote scientific trust" in failures


def test_recorded_blockers_do_not_allow_passed_status(tmp_path: Path):
    module = _module()
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    gate["status"] = "passed"
    gate["disposition"] = "release_ready"
    path = tmp_path / "gate.json"
    path.write_text(json.dumps(gate), encoding="utf-8")
    failures = module.gate_failures(module.load_gate(path))
    assert any("passed gate cannot retain blockers" in item for item in failures)
    assert "expanded catalog gate is not passed" in failures
    assert "Figure 3 owner approval is missing" in failures
    assert "Figure 3 approval receipt is missing" in failures


def test_emptying_the_blocker_list_does_not_pass_the_gate(tmp_path: Path):
    module = _module()
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    gate["status"] = "passed"
    gate["disposition"] = "release_ready"
    gate["blockers"] = []
    path = tmp_path / "gate.json"
    path.write_text(json.dumps(gate), encoding="utf-8")
    failures = module.gate_failures(module.load_gate(path))
    assert "expanded catalog gate is not passed" in failures
    assert "Figure 3 owner approval is missing" in failures
    assert "Figure 3 approval receipt is missing" in failures


def test_release_gate_pins_registry_and_figure3_evidence_hashes(tmp_path: Path):
    module = _module()
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    gate["expected"]["registry_replay_input_sha256"]["intervening_census_registry.csv"] = "0" * 64
    gate["expected"]["figure3_evidence_sha256"]["figure3-input"] = "0" * 64
    path = tmp_path / "gate.json"
    path.write_text(json.dumps(gate), encoding="utf-8")
    failures = module.gate_failures(module.load_gate(path))
    assert "registry replay input hash drift" in failures
    assert "Figure 3 evidence hash drift" in failures


def test_release_gate_hashes_every_pinned_artifact():
    module = _module()
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    assert module._artifact_failures(gate) == []


def test_release_gate_replays_sources_and_proves_no_promotion():
    if "FOREGROUND_PIPELINE_REPO" not in os.environ or "FABER2026_MANUSCRIPT_REPO" not in os.environ:
        pytest.skip("integration repositories not configured")
    module = _module()
    gate = json.loads(GATE.read_text(encoding="utf-8"))
    failures = module._independent_replay_failures(gate, PIPELINE)
    # At the 2026-07-26 pinned commit (2463289) the replay is 52/52 with
    # zero discrepancy rows, so a clean replay is the release requirement.
    assert failures == []
    assert module._promotion_failures(gate, MANUSCRIPT) == []
