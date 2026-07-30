"""Adversarial tests for the analysis-only foreground census validation.

A validator that passes is only evidence if it would have failed on a defect.
Every test here corrupts one committed input in one specific way and asserts
that the matching check rejects it. If a mutation stops failing, the check has
stopped asserting.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_foreground_census_analysis_only.py"


def _module():
    spec = importlib.util.spec_from_file_location("foreground_census_validation", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validation = _module()


@pytest.fixture(scope="module")
def data():
    return validation.Inputs.load()


def mutated(data, table: str, mutate):
    """Return a deep copy of the inputs with one table rewritten."""
    clone = validation.Inputs(
        tables=copy.deepcopy(data.tables), hashes=dict(data.hashes)
    )
    mutate(clone.tables[table])
    return clone


def first_matching(rows, predicate):
    for row in rows:
        if predicate(row):
            return row
    raise AssertionError("no row matched the mutation target")


# --------------------------------------------------------------------------
# the committed state passes
# --------------------------------------------------------------------------


def test_every_check_passes_on_the_committed_census(data):
    for name, check in validation.CHECKS.items():
        if name == "census_matches_figure3":
            result = check(data, figure=validation.STAGED_FIGURE, render=False)
        else:
            result = check(data)
        assert result.passed, f"{name} failed on committed inputs: {result.failures}"


def test_the_staged_figure_is_compared_when_rendering_is_enabled(data):
    """The Figure 3 comparison is the slow half of the gate; assert it is real."""
    result = validation.check_census_matches_figure3(
        data, figure=validation.STAGED_FIGURE, render=True
    )
    assert result.passed, result.failures
    assert result.facts["candidate_content_matches_fresh_render"] is True
    assert result.facts["review_candidate_figure3_sha256"]


# --------------------------------------------------------------------------
# check 1 - sourced redshifts
# --------------------------------------------------------------------------


def test_an_unsourced_candidate_redshift_is_rejected(data):
    def drop_provenance(rows):
        target = first_matching(rows, lambda r: r["source_disposition"] == "frozen_admitted")
        rows.remove(target)

    result = validation.check_sourced_redshifts(mutated(data, "provenance", drop_provenance))
    assert not result.passed
    assert any("no provenance record" in f for f in result.failures)


def test_a_provenance_record_without_a_response_hash_is_rejected(data):
    def blank_hash(rows):
        first_matching(rows, lambda r: r["source_disposition"] == "frozen_admitted")[
            "query_response_sha256"
        ] = ""

    result = validation.check_sourced_redshifts(mutated(data, "provenance", blank_hash))
    assert not result.passed
    assert any("missing query_response_sha256" in f for f in result.failures)


def test_a_registry_redshift_that_drifts_from_its_source_is_rejected(data):
    def drift(rows):
        target = first_matching(rows, lambda r: r["best_z_source"] == "DESI spec")
        target["best_z"] = str(float(target["best_z"]) + 0.01)

    result = validation.check_sourced_redshifts(mutated(data, "registry", drift))
    assert not result.passed
    assert any("disagrees with the provenance record" in f for f in result.failures)


def test_a_host_redshift_with_no_published_extract_is_rejected(data):
    def orphan(rows):
        rows[0]["z_spec"] = "0.1234"
        rows[0]["nickname"] = "notaburst"

    result = validation.check_sourced_redshifts(mutated(data, "bursts", orphan))
    assert not result.passed
    assert any("no source-bearing extract row" in f for f in result.failures)


def test_a_host_redshift_that_contradicts_its_extract_is_rejected(data):
    def contradict(rows):
        target = first_matching(rows, lambda r: r["nickname"] == "phineas")
        target["z_spec"] = "0.9999"

    result = validation.check_sourced_redshifts(mutated(data, "bursts", contradict))
    assert not result.passed
    assert any("does not match the Verdi extract" in f for f in result.failures)


# --------------------------------------------------------------------------
# check 2 - redshiftless systems fail closed
# --------------------------------------------------------------------------


def test_a_confirmed_system_without_a_redshift_is_rejected(data):
    def promote(rows):
        target = first_matching(rows, lambda r: r["best_z_source"] == "none")
        target["final_verdict"] = "confirmed"

    result = validation.check_hostless_fail_closed(mutated(data, "registry", promote))
    assert not result.passed
    assert any("confirmed without an adopted redshift" in f for f in result.failures)


def test_a_budget_eligible_system_without_a_redshift_is_rejected(data):
    def promote(rows):
        target = first_matching(rows, lambda r: r["best_z_source"] == "none")
        target["budget_eligible"] = "True"

    result = validation.check_hostless_fail_closed(mutated(data, "registry", promote))
    assert not result.passed
    assert any("budget-eligible without an adopted redshift" in f for f in result.failures)


def test_a_diagnostic_redshift_that_drifts_from_its_posterior_is_rejected(data):
    def invent(rows):
        target = first_matching(
            rows,
            lambda r: r["nickname"] == "wilhelm" and r["row_kind"] == "host",
        )
        target["frb_z"] = "0.55"

    result = validation.check_hostless_fail_closed(mutated(data, "halo_grid", invent))
    assert not result.passed
    assert any("differs from the posterior" in f for f in result.failures)


def test_a_foreground_system_on_a_redshiftless_sightline_is_rejected(data):
    def inject(rows):
        template = first_matching(rows, lambda r: r["row_kind"] == "system")
        clone = dict(template)
        clone["nickname"] = "freya"
        rows.append(clone)

    result = validation.check_hostless_fail_closed(mutated(data, "halo_grid", inject))
    assert not result.passed
    assert any("probabilistic candidate" in f for f in result.failures)


def test_a_hostless_panel_without_query_limitations_is_rejected(data):
    def blank(rows):
        target = first_matching(
            rows,
            lambda r: r["nickname"] == "mahi" and r["row_kind"] == "host",
        )
        target["query_limitations"] = ""

    result = validation.check_hostless_fail_closed(mutated(data, "halo_grid", blank))
    assert not result.passed
    assert any("omits coverage or query limitations" in f for f in result.failures)


def test_a_hostless_panel_with_posterior_hash_drift_is_rejected(data):
    def drift(rows):
        target = first_matching(
            rows,
            lambda r: r["nickname"] == "freya" and r["row_kind"] == "host",
        )
        target["frb_posterior_sha256"] = "0" * 64

    result = validation.check_hostless_fail_closed(mutated(data, "halo_grid", drift))
    assert not result.passed
    assert any("posterior hash" in f for f in result.failures)


def test_a_probabilistic_candidate_cannot_enter_the_budget(data):
    def promote(rows):
        target = first_matching(
            rows,
            lambda r: r.get("evidence_class") == "probabilistic_candidate",
        )
        target["budget_eligible"] = "True"

    result = validation.check_hostless_fail_closed(mutated(data, "halo_grid", promote))
    assert not result.passed
    assert any("was promoted" in f for f in result.failures)


def test_a_false_invalid_redshift_flag_is_rejected(data):
    """The fail-closed reason has to be true, not merely recorded."""

    def falsify(rows):
        target = first_matching(
            rows, lambda r: r.get("geometry_status") == "invalid_foreground_redshift"
        )
        target["system_z"] = "0.05"

    result = validation.check_hostless_fail_closed(mutated(data, "halo_grid", falsify))
    assert not result.passed
    assert any("is a valid foreground value" in f for f in result.failures)


def test_a_flagged_system_that_stays_budget_eligible_is_rejected(data):
    def promote(rows):
        target = first_matching(rows, lambda r: r.get("geometry_status") not in ("pass", "host_roster"))
        target["budget_eligible"] = "True"

    result = validation.check_hostless_fail_closed(mutated(data, "halo_grid", promote))
    assert not result.passed
    assert any("still budget-eligible" in f for f in result.failures)


# --------------------------------------------------------------------------
# check 3 - deterministic, auditable matching
# --------------------------------------------------------------------------


def test_a_leaked_cross_listing_duplicate_is_rejected(data):
    """A cross-listing that survives deduplication double-counts one galaxy."""

    duplicate = data["duplicates"][0]

    def leak(rows):
        clone = dict(
            first_matching(
                rows,
                lambda r: r["row_kind"] == "system"
                and r["nickname"] == duplicate["nickname"],
            )
        )
        clone["object_id"] = duplicate["duplicate_obj"]
        rows.append(clone)

    result = validation.check_deterministic_matching(mutated(data, "halo_grid", leak))
    assert not result.passed
    assert any("duplicates survive into Figure 3" in f for f in result.failures)


def test_the_figure_input_reproduction_reads_the_committed_files(data):
    """The reproduction half of this check is an on-disk rebuild, not a replay
    of the in-memory tables, so record that it actually ran."""
    result = validation.check_deterministic_matching(data)
    assert result.facts["figure3_input_rebuild_is_canonically_equivalent"] is True
    assert len(result.facts["figure3_input_sha256"]) == 64


def test_figure_input_receipt_hash_drift_is_rejected(data, monkeypatch, tmp_path):
    receipt = json.loads(validation.HALO_GRID_RECEIPT.read_text(encoding="utf-8"))
    output_key = next(iter(receipt["output"]))
    receipt["output"][output_key] = "0" * 64
    corrupted = tmp_path / "receipt.json"
    corrupted.write_text(json.dumps(receipt), encoding="utf-8")
    monkeypatch.setattr(validation, "HALO_GRID_RECEIPT", corrupted)
    result = validation.check_deterministic_matching(data)
    assert not result.passed
    assert any("differ from their reproduction receipt" in f for f in result.failures)


def test_a_fabricated_duplicate_separation_is_rejected(data):
    def fabricate(rows):
        rows[0]["sep_arcsec"] = "42.0"

    result = validation.check_deterministic_matching(mutated(data, "duplicates", fabricate))
    assert not result.passed
    assert any("but the coordinates give" in f for f in result.failures)


def test_a_deduplication_without_recorded_evidence_is_rejected(data):
    def blank(rows):
        rows[0]["evidence"] = ""

    result = validation.check_deterministic_matching(mutated(data, "duplicates", blank))
    assert not result.passed
    assert any("no recorded evidence" in f for f in result.failures)


def test_a_cross_match_with_an_unrecorded_runner_up_is_rejected(data):
    def hide(rows):
        target = first_matching(
            rows,
            lambda r: r.get("unwise_status") == "matched"
            and (validation.number(r.get("unwise_candidate_count")) or 0) > 1,
        )
        target["unwise_second_separation_arcsec"] = ""

    result = validation.check_deterministic_matching(
        mutated(data, "cross_references", hide)
    )
    assert not result.passed
    assert any("runner-up separation is not recorded" in f for f in result.failures)


def test_a_cross_match_that_did_not_adopt_the_nearest_source_is_rejected(data):
    def swap(rows):
        target = first_matching(
            rows,
            lambda r: r.get("unwise_status") == "matched"
            and validation.number(r.get("unwise_second_separation_arcsec")) is not None,
        )
        target["unwise_separation_arcsec"] = str(
            validation.number(target["unwise_second_separation_arcsec"]) + 1.0
        )

    result = validation.check_deterministic_matching(
        mutated(data, "cross_references", swap)
    )
    assert not result.passed
    assert any("the nearest match was not adopted" in f for f in result.failures)


def test_an_ambiguous_cross_match_that_hides_its_ambiguity_is_rejected(data):
    def hide(rows):
        target = first_matching(rows, lambda r: r.get("unwise_status") == "ambiguous")
        target["unwise_second_separation_arcsec"] = ""

    result = validation.check_deterministic_matching(
        mutated(data, "cross_references", hide)
    )
    assert not result.passed
    assert any("ambiguous but records no" in f for f in result.failures)


def test_a_cross_match_without_a_response_snapshot_is_rejected(data):
    def blank(rows):
        first_matching(rows, lambda r: r.get("gsc242_status") == "matched")[
            "gsc242_snapshot_sha256"
        ] = ""

    result = validation.check_deterministic_matching(
        mutated(data, "cross_references", blank)
    )
    assert not result.passed
    assert any("no response snapshot hash" in f for f in result.failures)


# --------------------------------------------------------------------------
# check 4 - survey coverage
# --------------------------------------------------------------------------


def test_a_missing_sightline_coverage_row_is_rejected(data):
    def drop(rows):
        target = first_matching(rows, lambda r: r["nickname"].lower() == "mahi")
        rows.remove(target)

    result = validation.check_survey_coverage(mutated(data, "survey_coverage", drop))
    assert not result.passed
    assert any("not the" in f and "required for" in f for f in result.failures)


def test_a_coverage_coordinate_that_drifts_from_the_roster_is_rejected(data):
    def drift(rows):
        rows[0]["dec"] = "+70d00m00.0s"

    result = validation.check_survey_coverage(mutated(data, "survey_coverage", drift))
    assert not result.passed
    assert any("declination" in f for f in result.failures)


def test_a_footprint_hash_that_does_not_match_the_file_is_rejected(data):
    def corrupt(rows):
        first_matching(rows, lambda r: r["footprint_sha256"])["footprint_sha256"] = "0" * 64

    result = validation.check_survey_coverage(mutated(data, "survey_coverage", corrupt))
    assert not result.passed
    assert any("hashes to" in f for f in result.failures)


def test_a_footprint_file_claim_with_no_hash_is_rejected(data):
    def strip(rows):
        target = first_matching(rows, lambda r: r["footprint_sha256"])
        target["footprint_sha256"] = ""

    result = validation.check_survey_coverage(mutated(data, "survey_coverage", strip))
    assert not result.passed
    assert any("names a file but records no hash" in f for f in result.failures)


def test_an_undeclared_footprint_status_is_rejected(data):
    def vague(rows):
        rows[0]["footprint_status"] = "probably"

    result = validation.check_survey_coverage(mutated(data, "survey_coverage", vague))
    assert not result.passed
    assert any("neither covered nor not_covered" in f for f in result.failures)


# --------------------------------------------------------------------------
# check 5 - mass and radius conventions
# --------------------------------------------------------------------------


def test_a_halo_radius_that_does_not_follow_the_declared_overdensity_is_rejected(data):
    def inflate(rows):
        target = first_matching(
            rows, lambda r: r["type"] == "halo" and validation.number(r.get("r200c_kpc"))
        )
        target["r200c_kpc"] = str(validation.number(target["r200c_kpc"]) * 1.05)

    result = validation.check_mass_radius_conventions(
        mutated(data, "cross_references", inflate)
    )
    assert not result.passed
    assert any("does not reproduce from M200c" in f for f in result.failures)


def test_a_cluster_carrying_halo_convention_geometry_is_rejected(data):
    def mix(rows):
        target = first_matching(rows, lambda r: r["type"] == "cluster")
        target["m200c_msun"] = "1e14"
        target["r200c_kpc"] = "800"

    result = validation.check_mass_radius_conventions(
        mutated(data, "cross_references", mix)
    )
    assert not result.passed
    assert any("mixing the two conventions" in f for f in result.failures)


def test_an_undeclared_mass_method_is_rejected(data):
    def relabel(rows):
        first_matching(rows, lambda r: r["type"] == "halo")[
            "m200c_method"
        ] = "hand_tuned"

    result = validation.check_mass_radius_conventions(
        mutated(data, "cross_references", relabel)
    )
    assert not result.passed
    assert any("not the declared" in f for f in result.failures)


def test_a_cluster_radius_drawn_in_the_wrong_units_is_rejected(data):
    def megaparsecs(rows):
        target = first_matching(
            rows,
            lambda r: r["row_kind"] == "system"
            and r["system_type"] == "cluster"
            and r["geometry_status"] == "pass",
        )
        target["radius_kpc"] = str(validation.number(target["radius_kpc"]) / 1000.0)

    result = validation.check_mass_radius_conventions(
        mutated(data, "halo_grid", megaparsecs)
    )
    assert not result.passed
    assert any("is not the catalog R500 in kiloparsecs" in f for f in result.failures)


def test_geometry_drawn_despite_a_failed_geometry_flag_is_rejected(data):
    def draw(rows):
        target = first_matching(
            rows, lambda r: r.get("geometry_status") == "missing_sourced_geometry"
        )
        target["mass_msun"] = "1e14"
        target["radius_kpc"] = "700"

    result = validation.check_mass_radius_conventions(mutated(data, "halo_grid", draw))
    assert not result.passed
    assert any("geometry did not pass" in f for f in result.failures)


# --------------------------------------------------------------------------
# check 6 - the census and Figure 3 agree
# --------------------------------------------------------------------------


def _figure3(data):
    return validation.check_census_matches_figure3(
        data, figure=validation.STAGED_FIGURE, render=False
    )


def test_a_dropped_sightline_panel_is_rejected(data):
    def drop(rows):
        target = first_matching(
            rows, lambda r: r["row_kind"] == "host" and r["nickname"] == "mahi"
        )
        rows.remove(target)

    assert any("not twelve" in f for f in _figure3(mutated(data, "halo_grid", drop)).failures)


def test_a_system_drawn_without_a_confirmed_census_row_is_rejected(data):
    def invent(rows):
        clone = dict(first_matching(rows, lambda r: r["row_kind"] == "system"))
        clone["object_id"] = "9999999999"
        rows.append(clone)

    assert any(
        "not confirmed in the census" in f
        for f in _figure3(mutated(data, "halo_grid", invent)).failures
    )


def test_a_confirmed_census_system_missing_from_the_figure_is_rejected(data):
    def drop(rows):
        target = first_matching(rows, lambda r: r["row_kind"] == "system")
        rows.remove(target)

    assert any(
        "absent from Figure 3" in f
        for f in _figure3(mutated(data, "halo_grid", drop)).failures
    )


def test_an_impact_parameter_that_drifts_from_the_census_is_rejected(data):
    def drift(rows):
        target = first_matching(rows, lambda r: r["row_kind"] == "system")
        target["impact_kpc"] = str(validation.number(target["impact_kpc"]) + 10.0)

    assert any(
        "impact parameter" in f
        for f in _figure3(mutated(data, "halo_grid", drift)).failures
    )


def test_a_relabelled_burst_is_rejected(data):
    def relabel(rows):
        target = first_matching(rows, lambda r: r["row_kind"] == "host")
        target["frb_name"] = "FRB 19990101A"

    assert any(
        "the roster says" in f
        for f in _figure3(mutated(data, "halo_grid", relabel)).failures
    )


def test_a_silently_dropped_panel_is_rejected(data):
    """Every sightline must retain a placed host marker."""

    def blank(rows):
        target = first_matching(
            rows, lambda r: r["row_kind"] == "host" and r["nickname"] == "zach"
        )
        target["frb_z"] = ""

    assert any(
        "panel roster is incomplete" in f
        for f in _figure3(mutated(data, "halo_grid", blank)).failures
    )


def test_the_panel_accounting_matches_the_installed_figure(data):
    result = _figure3(data)
    assert result.facts["figure3_host_rows"] == 12
    assert len(result.facts["figure3_panels_drawn"]) == 12
    assert result.facts["diagnostic_redshift_panels"] == [
        "freya",
        "mahi",
        "wilhelm",
    ]
    assert result.facts["confirmed_systems_drawn"] == 22
    assert result.facts["probabilistic_candidates_drawn"] == 2


def test_an_installed_figure_that_is_not_the_staged_render_is_rejected(data, tmp_path):
    if not validation.STAGED_FIGURE.is_file():
        pytest.skip("the staged Figure 3 render is not present in this checkout")
    impostor = tmp_path / "impostor.pdf"
    impostor.write_bytes(validation.STAGED_FIGURE.read_bytes() + b"\n% tampered\n")
    result = validation.check_census_matches_figure3(
        data, figure=impostor, render=False
    )
    assert not result.passed
    assert any("differs from the staged review artifact" in f for f in result.failures)


def test_a_missing_installed_figure_is_rejected(data, tmp_path):
    result = validation.check_census_matches_figure3(
        data, figure=tmp_path / "absent.pdf", render=True
    )
    assert not result.passed
    assert any("review candidate is missing" in f for f in result.failures)


# --------------------------------------------------------------------------
# the receipt
# --------------------------------------------------------------------------


def test_the_receipt_binds_every_input_and_the_installed_figure_bytes(tmp_path):
    output = tmp_path / "receipt.json"
    code = validation.main(
        [
            "--skip-render",
            "--figure",
            str(validation.STAGED_FIGURE),
            "--output",
            str(output),
        ]
    )
    assert code == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "passed"
    assert set(validation.INPUT_PATHS) <= {
        Path(p).name.split(".")[0] or p for p in ()
    } or len(report["input_sha256"]) == len(validation.INPUT_PATHS)
    for digest in report["input_sha256"].values():
        assert len(digest) == 64
    figure_check = next(
        c for c in report["checks"] if c["id"] == "census_matches_figure3"
    )
    assert len(figure_check["facts"]["review_candidate_figure3_sha256"]) == 64


def test_the_gate_reports_failure_through_its_exit_code(monkeypatch, tmp_path):
    def failing_run(**_kwargs):
        return {
            "schema_version": 1,
            "artifact": "foreground_census_analysis_only_validation",
            "scope": "test",
            "status": "failed",
            "input_sha256": {},
            "checks": [
                {
                    "id": "sourced_redshifts",
                    "title": "t",
                    "status": "failed",
                    "failures": ["synthetic"],
                    "facts": {},
                }
            ],
        }

    monkeypatch.setattr(validation, "run", failing_run)
    assert validation.main([]) == 1


def test_the_cli_default_fails_closed_without_the_review_candidate(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        validation,
        "STAGED_FIGURE",
        tmp_path / "missing-review-candidate.pdf",
    )
    assert validation.main([]) == 1
