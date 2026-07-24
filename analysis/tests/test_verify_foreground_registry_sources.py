import importlib.util
import json
import csv
import io
import os
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_foreground_registry_sources.py"
REPLAY = ROOT / "docs/rse/specs/evidence/foreground-source-verification-2026-07-22/replay.json"
ADVERSARIAL_REVIEW = (
    ROOT
    / "docs/rse/specs/evidence/foreground-source-verification-2026-07-22"
    / "adversarial-review.json"
)
PIPELINE_SOURCE = Path(os.environ.get(
    "FOREGROUND_PIPELINE_REPO",
    str(Path.home() / "Developer/repos/github.com/jakobtfaber/Faber2026/pipeline"),
))


def _module():
    spec = importlib.util.spec_from_file_location("foreground_source_verifier", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_frozen_replay_is_row_complete_and_passes():
    result = json.loads(REPLAY.read_text())
    assert result["pipeline_commit"] == "c913175e567db70980e5f2745dcdf8f7f3ad9fb4"
    assert result["rows"] == 52
    assert len(result["row_results"]) == 52
    assert len({row["key"] for row in result["row_results"]}) == 52
    assert result["disposition"] == "pass"
    assert result["gate_pass"] is True
    assert result["source_verified_rows"] == 52
    assert result["rows_with_discrepancies"] == 0
    assert result["verdict_mismatches"] == []
    assert result["budget_mismatches"] == []
    assert result["errors"] == []
    assert all(item["ok"] for item in result["duplicate_checks"])


def test_replay_names_every_source_discrepancy_class():
    result = json.loads(REPLAY.read_text())
    assert result["host_status_counts"] == {
        "verified": 51,
        "verified_rounded_to_registry_precision": 1,
    }
    assert result["candidate_status_counts"] == {
        "verified": 46,
        "verified_identity_only_no_redshift": 6,
    }


def test_adversarial_review_passes_identity_only_and_keeps_figure_blocked():
    review = json.loads(ADVERSARIAL_REVIEW.read_text())
    assert review["verdict"] == "pass"
    assert len(review["rows"]) == 6
    assert all(row["redshift_state"] == "blank" for row in review["rows"])
    assert all(row["verdict"] == "inconclusive" for row in review["rows"])
    assert all(row["budget_eligible"] is False for row in review["rows"])
    assert review["figure_3"]["unchanged_from_pipeline_base"] is True
    assert review["figure_3"]["identity_rows_in_confirmed_only_grid"] == 0
    assert review["figure_3"]["promoted"] is False


def test_host_precision_comparison_distinguishes_zach_and_whitney():
    module = _module()
    assert module.rounded_source_match("0.043", "0.043040")
    assert not module.rounded_source_match("0.479", "0.477958")


def test_spherical_separation_handles_high_declination():
    module = _module()
    value = module.separation_arcsec(310.0912903, 72.81041703, 310.0912903, 72.81041703)
    assert value == 0.0


PIPELINE_PATHS = [
    "galaxies/foreground/data/intervening_census_registry.csv",
    "galaxies/foreground/data/candidate_redshift_provenance.csv",
    "galaxies/foreground/data/candidate_redshift_source_payloads_2026-07-22.json",
    "galaxies/foreground/data/frozen_census/strm_catalog_rows.csv",
    "galaxies/foreground/data/census_masses/census_duplicates.csv",
    "galaxies/foreground/data/census_extensions/v4_extension.csv",
]
ANALYSIS_PATHS = [
    "docs/rse/specs/evidence/verdi-host-redshifts-2026-07-22/verdi_host_redshift_comparison.csv",
    "docs/rse/specs/evidence/law2024-zach-whitney-host-redshifts-2026-07-22/host_redshift_rows.csv",
    "docs/rse/specs/evidence/connor2025-whitney-host-redshift-2026-07-22/host_redshift_row.csv",
]


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def _make_repo(path, source, commit, files):
    path.mkdir()
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "fixture@example.invalid")
    _git(path, "config", "user.name", "Fixture")
    for relpath in files:
        target = path / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_git(source, "show", f"{commit}:{relpath}"))
    _git(path, "add", ".")
    _git(path, "commit", "-qm", "fixture")
    return _git(path, "rev-parse", "HEAD").strip()


@pytest.fixture
def mutable_repos(tmp_path):
    analysis = tmp_path / "analysis"
    pipeline = tmp_path / "pipeline"
    analysis_commit = _make_repo(
        analysis, ROOT, "fe73689cad723db5d68427c61e301157a39cc101", ANALYSIS_PATHS
    )
    pipeline_commit = _make_repo(pipeline, PIPELINE_SOURCE, "c913175", PIPELINE_PATHS)
    return analysis, pipeline, analysis_commit, pipeline_commit


def _rewrite_csv(path, mutate):
    rows = list(csv.DictReader(path.open()))
    fields = list(rows[0])
    mutate(rows)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _commit(repo, message):
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", message)
    return _git(repo, "rev-parse", "HEAD").strip()


def test_verifier_rejects_dirty_tracked_input(mutable_repos):
    module = _module()
    analysis, pipeline, ac, pc = mutable_repos
    path = pipeline / PIPELINE_PATHS[0]
    path.write_text(path.read_text() + "\n")
    result = module.verify(analysis, pipeline, analysis_commit=ac, pipeline_commit=pc)
    assert "tracked input differs from pinned blob: registry" in result["errors"]
    assert result["gate_pass"] is False


def test_verifier_rejects_measurement_kind_mutation(mutable_repos):
    module = _module()
    analysis, pipeline, ac, _ = mutable_repos
    path = pipeline / PIPELINE_PATHS[1]
    def mutate(rows):
        row = next(r for r in rows if r["nickname"] == "whitney" and r["obj"] == "1473")
        row["measurement_kind"] = "spectroscopic"
    _rewrite_csv(path, mutate)
    pc = _commit(pipeline, "mutate kind")
    result = module.verify(analysis, pipeline, analysis_commit=ac, pipeline_commit=pc)
    target = next(r for r in result["row_results"] if r["key"] == "whitney/halo/1473")
    assert "measurement kind differs from frozen source semantics" in target["discrepancies"]


def test_verifier_rejects_adopted_error_mutation(mutable_repos):
    module = _module()
    analysis, pipeline, ac, _ = mutable_repos
    path = pipeline / PIPELINE_PATHS[1]
    def mutate(rows):
        row = next(r for r in rows if r["nickname"] == "whitney" and r["obj"] == "1473")
        row["adopted_z_err"] = "0.999"
    _rewrite_csv(path, mutate)
    pc = _commit(pipeline, "mutate error")
    result = module.verify(analysis, pipeline, analysis_commit=ac, pipeline_commit=pc)
    target = next(r for r in result["row_results"] if r["key"] == "whitney/halo/1473")
    assert "candidate ledger and registry uncertainties differ" in target["discrepancies"]


def test_verifier_rejects_identity_only_ledger_mutation(mutable_repos):
    module = _module()
    analysis, pipeline, ac, _ = mutable_repos
    path = pipeline / PIPELINE_PATHS[1]
    def mutate(rows):
        row = next(r for r in rows if r["nickname"] == "isha")
        row["stable_source_id"] = "AllWISE:wrong"
    _rewrite_csv(path, mutate)
    pc = _commit(pipeline, "mutate identity")
    result = module.verify(analysis, pipeline, analysis_commit=ac, pipeline_commit=pc)
    target = next(r for r in result["row_results"] if r["key"].startswith("isha/"))
    assert "manual extension identity-ledger semantics mismatch" in target["discrepancies"]


def test_verifier_rejects_paired_registry_and_ledger_error_mutation(mutable_repos):
    module = _module()
    analysis, pipeline, ac, _ = mutable_repos
    nickname, obj = "casey", "192821700026167542"
    registry_path = pipeline / PIPELINE_PATHS[0]
    provenance_path = pipeline / PIPELINE_PATHS[1]
    def mutate_registry(rows):
        next(r for r in rows if r["nickname"] == nickname and r["obj"] == obj)["best_z_err"] = "0.0005"
    def mutate_provenance(rows):
        next(r for r in rows if r["nickname"] == nickname and r["obj"] == obj)["adopted_z_err"] = "0.0005"
    _rewrite_csv(registry_path, mutate_registry)
    _rewrite_csv(provenance_path, mutate_provenance)
    pc = _commit(pipeline, "mutate paired uncertainty")
    result = module.verify(analysis, pipeline, analysis_commit=ac, pipeline_commit=pc)
    target = next(r for r in result["row_results"] if r["key"] == f"{nickname}/halo/{obj}")
    assert "candidate uncertainty differs from frozen source" in target["discrepancies"]


@pytest.mark.parametrize("nickname,obj,expected", [
    ("whitney", "1473", "source-reported uncertainty metadata violates family contract"),
    ("whitney", "J085546.0+732230, 1160094", "source-reported uncertainty metadata violates family contract"),
    ("zach", "195373100910393540", "source-reported uncertainty metadata violates family contract"),
    ("phineas", "WHL J115048.0+714428", "source-reported uncertainty metadata violates family contract"),
    ("chromatica", "196733128040225775", "NED uncertainty-unavailable semantics mismatch"),
])
def test_verifier_rejects_source_reported_error_metadata_mutation(
    mutable_repos, nickname, obj, expected
):
    module = _module()
    analysis, pipeline, ac, _ = mutable_repos
    path = pipeline / PIPELINE_PATHS[1]
    def mutate(rows):
        row = next(r for r in rows if r["nickname"] == nickname and r["obj"] == obj)
        row["source_reported_z_err"] = "0.999"
    _rewrite_csv(path, mutate)
    pc = _commit(pipeline, "mutate source-reported error")
    result = module.verify(analysis, pipeline, analysis_commit=ac, pipeline_commit=pc)
    target = next(r for r in result["row_results"] if r["key"].split("/", 2)[0] == nickname and r["key"].split("/", 2)[2] == obj)
    assert expected in target["discrepancies"]


def test_verifier_rejects_duplicate_mapping_mutation(mutable_repos):
    module = _module()
    analysis, pipeline, ac, _ = mutable_repos
    path = pipeline / PIPELINE_PATHS[4]
    _rewrite_csv(path, lambda rows: rows.pop())
    pc = _commit(pipeline, "remove duplicate")
    result = module.verify(analysis, pipeline, analysis_commit=ac, pipeline_commit=pc)
    assert "duplicate mapping set differs from the exact seven-row contract" in result["errors"]
