#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GATE = ROOT / "docs/rse/specs/validation-expanded-foreground-independent-release-gate.json"
DEFAULT_RECEIPTS_DIR = ROOT / "figure_review/approval_receipts"


def load_gate(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _load_json_relative(path: str) -> dict[str, Any]:
    with (ROOT / path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _blocker_ids(gate: dict[str, Any]) -> set[str]:
    return {
        item.get("id", "")
        for item in gate.get("blockers", [])
        if isinstance(item, dict) and item.get("id")
    }


def _string(value: Any) -> str:
    return value if isinstance(value, str) else ""

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_failures(gate: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for relative, expected in gate["expected"]["artifact_sha256"].items():
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"pinned artifact missing: {relative}")
        elif _sha256(path) != expected:
            failures.append(f"pinned artifact SHA-256 drift: {relative}")
    return failures


def _independent_replay_failures(gate: dict[str, Any], pipeline_repo: Path) -> list[str]:
    failures: list[str] = []
    expected = gate["expected"]
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=pipeline_repo, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if head != gate["pipeline_commit"]:
        failures.append(f"pipeline checkout drift: {head}")
        return failures
    with tempfile.TemporaryDirectory(prefix="foreground-gate05-") as tmp:
        tmpdir = Path(tmp)
        source_path = tmpdir / "source.json"
        # Replay at the commits this gate declares, never at the verifier's own
        # historical defaults: a receipt produced from a different pipeline
        # lineage must not be able to satisfy a gate bound to the current pin.
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/verify_foreground_registry_sources.py"),
                "--pipeline-dir", str(pipeline_repo),
                "--pipeline-commit", gate["pipeline_commit"],
                "--analysis-commit", gate["analysis_base_commit"],
                "--output", str(source_path),
            ],
            cwd=ROOT, check=False, capture_output=True, text=True,
        )
        if not source_path.is_file():
            failures.append("independent source replay produced no report")
        else:
            replayed = load_gate(source_path)
            if replayed != _load_json_relative(
                gate["inputs"]["source_verification_replay"]
            ):
                failures.append("independent source replay differs from pinned receipt")
            if replayed.get("source_verified_rows") != expected["source_verified_rows"]:
                failures.append(
                    "independent source replay verified "
                    f"{replayed.get('source_verified_rows')} of "
                    f"{replayed.get('rows')} rows at the pinned pipeline commit"
                )
            if replayed.get("rows_with_discrepancies") != expected["source_discrepancy_rows"]:
                failures.append(
                    "independent source replay reports "
                    f"{replayed.get('rows_with_discrepancies')} discrepancy rows"
                )

    registry = subprocess.run(
        ["git", "show", f"{gate['pipeline_commit']}:{expected['pinned_registry_path']}"],
        cwd=pipeline_repo, check=False, capture_output=True,
    )
    if registry.returncode:
        failures.append("pinned registry is unreadable at the pinned pipeline commit")
    elif hashlib.sha256(registry.stdout).hexdigest() != expected["pinned_registry_sha256"]:
        failures.append("pinned registry SHA-256 drift at the pinned pipeline commit")

    return failures


def _promotion_failures(gate: dict[str, Any], manuscript_repo: Path) -> list[str]:
    failures: list[str] = []
    expected = gate["expected"]
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=manuscript_repo, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if head != gate["parent_commit"]:
        failures.append(f"manuscript parent checkout drift: {head}")
    pin = subprocess.run(
        ["git", "rev-parse", "HEAD:pipeline"], cwd=manuscript_repo, check=False,
        capture_output=True, text=True,
    ).stdout.strip()
    if pin != gate["pipeline_commit"]:
        failures.append(f"manuscript pipeline gitlink drift: {pin}")
    candidate = ROOT / expected["figure3_candidate"]
    target = manuscript_repo / expected["figure3_target"]
    if not target.is_file():
        failures.append("installed Figure 3 is missing")
    else:
        installed_hash = _sha256(target)
        if installed_hash != expected["installed_figure3_sha256"]:
            failures.append("installed Figure 3 SHA-256 drift")
        if installed_hash == _sha256(candidate):
            failures.append("unapproved Figure 3 candidate was promoted")
    receipt = DEFAULT_RECEIPTS_DIR / f"{expected['figure3_candidate_id']}.json"
    if receipt.exists():
        failures.append("approval receipt exists before owner approval")
    return failures


def gate_failures(
    gate: dict[str, Any],
    *,
    pipeline_repo: Path | None = None,
    manuscript_repo: Path | None = None,
) -> list[str]:
    failures: list[str] = []
    blockers = _blocker_ids(gate)
    expected = gate["expected"]
    failures.extend(_artifact_failures(gate))
    if pipeline_repo is not None:
        failures.extend(_independent_replay_failures(gate, pipeline_repo))
    if manuscript_repo is not None:
        failures.extend(_promotion_failures(gate, manuscript_repo))

    if gate.get("status") != "passed":
        failures.append(f"status={gate.get('status')!r}")
    elif blockers:
        failures.append(f"passed gate cannot retain blockers: {sorted(blockers)}")
    if gate.get("status") != "passed" and gate.get("scientific_trust_promoted"):
        failures.append("failed gate cannot promote scientific trust")
    if gate.get("status") != "passed" and gate.get("figure3_promoted"):
        failures.append("failed gate cannot promote Figure 3")
    if gate.get("status") == "passed" and gate.get("disposition") != "release_ready":
        failures.append(f"passed gate disposition={gate.get('disposition')!r}")
    if gate.get("status") != "passed" and gate.get("disposition") != "fail_closed":
        failures.append(f"disposition={gate.get('disposition')!r}")

    catalog_gate = _load_json_relative(gate["inputs"]["expanded_catalog_gate"])
    if catalog_gate.get("status") != "passed":
        failures.append("expanded catalog gate is not passed")
        if "expanded-catalog-gate-not-passed" not in blockers and gate.get("status") != "passed":
            failures.append("missing recorded blocker: expanded-catalog-gate-not-passed")

    source_replay = _load_json_relative(gate["inputs"]["source_verification_replay"])
    if source_replay.get("gate_pass") is not True:
        failures.append("source verification replay did not pass")
        if "source-verification-incomplete" not in blockers and gate.get("status") != "passed":
            failures.append("missing recorded blocker: source-verification-incomplete")
    if source_replay.get("pipeline_commit") != expected["source_verification_pipeline_commit"]:
        failures.append("source verification pipeline commit drift")
    if source_replay.get("source_verified_rows") != expected["source_verified_rows"]:
        failures.append("source verification count drift")
    if source_replay.get("rows_with_discrepancies") != expected["source_discrepancy_rows"]:
        failures.append("source discrepancy count drift")

    registry_replay = _load_json_relative(gate["inputs"]["registry_replay"])
    if registry_replay.get("status") != "validated":
        failures.append(f"registry replay status={registry_replay.get('status')!r}")
    if registry_replay.get("pipeline_commit") != expected["registry_replay_pipeline_commit"]:
        failures.append("registry replay pipeline commit drift")
    if registry_replay.get("rows") != expected["registry_rows"]:
        failures.append("registry replay row count drift")
    if registry_replay.get("finite_host_rows") != expected["finite_host_rows"]:
        failures.append("registry replay finite-host count drift")
    if registry_replay.get("duplicate_checks_passed") != expected["duplicate_checks_passed"]:
        failures.append("registry replay duplicate-check count drift")
    if registry_replay.get("input_sha256") != expected["registry_replay_input_sha256"]:
        failures.append("registry replay input hash drift")
    if registry_replay.get("verdict_mismatches") != []:
        failures.append("registry replay verdict mismatches are nonempty")
    if registry_replay.get("budget_mismatches") != []:
        failures.append("registry replay budget mismatches are nonempty")

    fig3_manifest = _load_json_relative(gate["inputs"]["figure3_review_manifest"])
    approval_inventory = (ROOT / gate["inputs"]["figure_approval_inventory"]).read_text(
        encoding="utf-8"
    )
    if "none of the figures" not in approval_inventory or "It remains available, unapproved, and unpromoted." not in approval_inventory:
        failures.append("owner approve-none decision is missing or changed")
    candidate = next(
        (
            item
            for item in fig3_manifest.get("candidates", [])
            if item.get("id") == gate["expected"]["figure3_candidate_id"]
        ),
        None,
    )
    if candidate is None:
        failures.append("Figure 3 candidate missing from review manifest")
    else:
        decision = candidate.get("decision", {})
        if decision.get("status") != "approved":
            failures.append("Figure 3 owner approval is missing")
            if "figure3-owner-approval-missing" not in blockers and gate.get("status") != "passed":
                failures.append("missing recorded blocker: figure3-owner-approval-missing")
        else:
            if decision.get("reviewer_role") != "manuscript_owner":
                failures.append("Figure 3 approval reviewer role is not manuscript_owner")
            for key in ("reviewer", "reviewed_at", "notes"):
                if not _string(decision.get(key)).strip():
                    failures.append(f"Figure 3 approval missing {key}")
        if candidate.get("artifact_sha256") != gate["expected"]["figure3_candidate_sha256"]:
            failures.append("Figure 3 candidate SHA-256 drift")
        artifact = ROOT / Path(gate["inputs"]["figure3_review_manifest"]).parent / candidate["artifact"]
        if not artifact.is_file() or _sha256(artifact) != expected["figure3_candidate_sha256"]:
            failures.append("Figure 3 candidate bytes do not match pinned SHA-256")
        if candidate.get("protect_in_manuscript") is not False:
            failures.append("unapproved Figure 3 must remain unprotected")
        if fig3_manifest.get("source_revision") != expected["figure3_candidate_parent_commit"]:
            failures.append("Figure 3 manifest source revision drift")
        if fig3_manifest.get("pipeline_revision") != expected["figure3_candidate_pipeline_commit"]:
            failures.append("Figure 3 manifest pipeline revision drift")
        evidence_hashes = {
            item.get("id"): item.get("sha256")
            for item in fig3_manifest.get("evidence", [])
            if isinstance(item, dict)
        }
        if evidence_hashes != expected["figure3_evidence_sha256"]:
            failures.append("Figure 3 evidence hash drift")

    # The candidate is only admissible if it was built from the registry
    # snapshot this gate pins. A candidate built from an earlier snapshot can
    # carry superseded identifiers even when every hash it records is intact.
    build = _load_json_relative(
        str(Path(gate["inputs"]["figure3_review_manifest"]).parent
            / "provenance/expanded-catalog-build.json")
    )
    if build.get("registry_sha256") != expected["pinned_registry_sha256"]:
        failures.append(
            "Figure 3 was built from registry snapshot "
            f"{build.get('registry_sha256')}, not the pinned "
            f"{expected['pinned_registry_sha256']}"
        )

    receipt_path = DEFAULT_RECEIPTS_DIR / f"{expected['figure3_candidate_id']}.json"
    if gate.get("status") == "passed" and not receipt_path.is_file():
        failures.append("Figure 3 approval receipt is missing")
    elif receipt_path.is_file():
        receipt = load_gate(receipt_path)
        if receipt.get("candidate_id") != expected["figure3_candidate_id"]:
            failures.append("Figure 3 approval receipt candidate mismatch")
        if receipt.get("candidate_sha256") != expected["figure3_candidate_sha256"]:
            failures.append("Figure 3 approval receipt candidate hash drift")
        if receipt.get("promoted_sha256") != expected["figure3_candidate_sha256"]:
            failures.append("Figure 3 promoted bytes do not match approved candidate")
        if receipt.get("promoted_target") != expected["figure3_target"]:
            failures.append("Figure 3 approval receipt target drift")
        receipt_decision = receipt.get("decision", {})
        if receipt_decision.get("status") != "approved":
            failures.append("Figure 3 approval receipt is not approved")
        if receipt_decision.get("reviewer_role") != "manuscript_owner":
            failures.append("Figure 3 approval receipt reviewer role is not manuscript_owner")

    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed independent release gate for expanded foreground catalog and Figure 3."
    )
    parser.add_argument("--gate", type=Path, default=DEFAULT_GATE)
    parser.add_argument(
        "--pipeline-repo",
        type=Path,
        help="optional retired-repository replay; omitted for self-contained validation",
    )
    parser.add_argument("--manuscript-repo", type=Path)
    args = parser.parse_args(argv)

    failures = gate_failures(
        load_gate(args.gate),
        pipeline_repo=args.pipeline_repo.resolve() if args.pipeline_repo else None,
        manuscript_repo=args.manuscript_repo.resolve() if args.manuscript_repo else None,
    )
    if failures:
        print("expanded foreground independent release gate failed:", file=sys.stderr)
        for blocker in _blocker_ids(load_gate(args.gate)):
            print(f"- blocker: {blocker}", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
