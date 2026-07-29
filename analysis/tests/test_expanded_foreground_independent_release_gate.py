"""The retired expanded-foreground release gate.

This gate bound every replay it declared to the `dsa110-FLITS` pipeline
repository through a `pipeline/` submodule the manuscript no longer carries. It
was retired on 2026-07-29 and superseded by an analysis-only validation.

These tests assert the retirement contract rather than the gate's old
behaviour: the record still refuses promotion, the validator reports the
supersession instead of raising, the successor exists, and no tampering can
turn a retired or failed gate into a passing one.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_expanded_foreground_independent_release_gate.py"
GATE = ROOT / "docs/rse/specs/validation-expanded-foreground-independent-release-gate.json"
SUCCESSOR = ROOT / "scripts/validate_foreground_census_analysis_only.py"


def _module():
    spec = importlib.util.spec_from_file_location("foreground_release_gate", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _gate() -> dict:
    return json.loads(GATE.read_text(encoding="utf-8"))


def test_the_gate_is_recorded_as_retired_and_names_its_successor():
    gate = _gate()
    assert gate["status"] == "retired"
    assert gate["disposition"] == "superseded"
    assert gate["retired_at"]
    assert gate["superseded_by"] == "scripts/validate_foreground_census_analysis_only.py"
    assert SUCCESSOR.is_file(), "the retired gate names a successor that does not exist"
    assert "pipeline" in gate["retirement_reason"]


def test_retirement_did_not_promote_anything():
    """Retiring a fail-closed gate must not quietly release what it withheld."""
    gate = _gate()
    assert gate["scientific_trust_promoted"] is False
    assert gate["figure3_promoted"] is False
    assert gate["release_rule"]["may_say_verified"] is False
    assert gate["release_rule"]["may_promote_figure3"] is False
    assert gate["release_rule"]["may_promote_scientific_trust"] is False


def test_the_retired_state_is_preserved_for_the_record():
    gate = _gate()
    assert gate["retired_state"]["status"] == "failed"
    assert gate["retired_state"]["disposition"] == "fail_closed"
    blockers = {item["id"] for item in gate["blockers"]}
    assert blockers == {
        "expanded-catalog-gate-not-passed",
        "figure3-owner-approval-missing",
    }
    assert all(item["status"] == "failed" for item in gate["blockers"])


def test_the_validator_reports_the_supersession_instead_of_raising():
    module = _module()
    failures = module.gate_failures(module.load_gate(GATE))
    assert len(failures) == 1
    assert "gate retired" in failures[0]
    assert "validate_foreground_census_analysis_only.py" in failures[0]


def test_the_validator_still_exits_nonzero():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--gate", str(GATE)],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 1
    assert "expanded foreground independent release gate failed" in result.stderr
    assert "gate retired" in result.stderr


def test_a_missing_declared_input_fails_closed_rather_than_raising(tmp_path: Path):
    """The failure that retired this gate was a traceback, not a refusal."""
    module = _module()
    gate = _gate()
    gate["disposition"] = "fail_closed"
    gate["inputs"]["figure3_review_manifest"] = "docs/rse/specs/does-not-exist.json"
    gate["inputs"]["figure_approval_inventory"] = "docs/rse/specs/also-missing.md"
    path = tmp_path / "gate.json"
    path.write_text(json.dumps(gate), encoding="utf-8")
    failures = module.gate_failures(module.load_gate(path))
    assert any("declared gate input is missing" in item for item in failures)


def test_a_retired_gate_cannot_be_flipped_to_passed(tmp_path: Path):
    module = _module()
    for disposition in ("superseded", "release_ready"):
        gate = _gate()
        gate["status"] = "passed"
        gate["disposition"] = disposition
        path = tmp_path / f"gate-{disposition}.json"
        path.write_text(json.dumps(gate), encoding="utf-8")
        assert module.gate_failures(module.load_gate(path)), (
            f"a retired gate passed when its disposition was set to {disposition}"
        )


def test_a_failed_gate_cannot_promote_scientific_trust(tmp_path: Path):
    module = _module()
    gate = _gate()
    gate["status"] = "failed"
    gate["disposition"] = "fail_closed"
    gate["scientific_trust_promoted"] = True
    path = tmp_path / "gate.json"
    path.write_text(json.dumps(gate), encoding="utf-8")
    failures = module.gate_failures(module.load_gate(path))
    assert "failed gate cannot promote scientific trust" in failures


def test_emptying_the_blocker_list_does_not_pass_the_gate(tmp_path: Path):
    module = _module()
    gate = _gate()
    gate["status"] = "passed"
    gate["disposition"] = "release_ready"
    gate["blockers"] = []
    path = tmp_path / "gate.json"
    path.write_text(json.dumps(gate), encoding="utf-8")
    assert module.gate_failures(module.load_gate(path))


def test_the_successor_covers_the_science_the_retired_gate_withheld():
    """Retirement is only honest if the successor asserts the same content."""
    spec = importlib.util.spec_from_file_location("successor", SUCCESSOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert set(module.CHECKS) == {
        "sourced_redshifts",
        "hostless_fail_closed",
        "deterministic_matching",
        "survey_coverage",
        "mass_radius_conventions",
        "census_matches_figure3",
    }
    # The registry-replay inputs the retired gate pinned must still be readable
    # from analysis/ alone, with the same bytes.
    pinned = _gate()["expected"]["registry_replay_input_sha256"]
    data = module.Inputs.load()
    for name, digest in pinned.items():
        matches = [
            value
            for path, value in data.hashes.items()
            if Path(path).name == name
        ]
        assert matches, f"the retired gate pinned {name}, which analysis/ no longer holds"
        assert matches[0] == digest, (
            f"{name} differs from the byte content the retired gate pinned"
        )
