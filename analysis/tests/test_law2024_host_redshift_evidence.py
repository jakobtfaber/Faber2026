from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    ROOT
    / "docs/rse/specs/evidence/law2024-zach-whitney-host-redshifts-2026-07-22"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict:
    return json.loads((EVIDENCE / "source_manifest.json").read_text())


def _rows() -> dict[str, dict[str, str]]:
    with (EVIDENCE / "host_redshift_rows.csv").open(newline="") as handle:
        return {row["nickname"]: row for row in csv.DictReader(handle)}


def test_frozen_law_source_extract_hashes_match_manifest() -> None:
    manifest = _manifest()

    assert manifest["status"] == "verified_authoritative_publication"
    assert manifest["scope"]["changes_census"] is False
    assert manifest["scope"]["changes_verdicts_or_budgets"] is False
    assert manifest["retrieval"]["publisher_pdf"]["sha256"] == (
        "f484b7dd23acd2f36cb3de65865d2d4f01c1d29e11978dcdaf3467f928d01478"
    )
    assert manifest["retrieval"]["arxiv_source"]["sha256"] == (
        "03d941deaa0bc98326a4c3c11466d18efb5a648d9c04acad2ed81743e5b3ee99"
    )

    for artifact in manifest["frozen_source_bytes"]:
        path = EVIDENCE / artifact["path"]
        assert path.stat().st_size == artifact["size_bytes"]
        assert _sha256(path) == artifact["sha256"]

    output = manifest["normalized_output"]
    assert output["row_count"] == 2
    assert _sha256(EVIDENCE / output["path"]) == output["sha256"]


def test_law_table2_table3_row_linkage_is_exact() -> None:
    rows = _rows()

    assert rows.keys() == {"zach", "whitney"}
    expected = {
        "zach": (
            "FRB 20220207C",
            "PSO J310.1977+72.8826",
            "0.043040",
        ),
        "whitney": (
            "FRB 20220310F",
            "PSO J134.7211+73.4910",
            "0.477958",
        ),
    }
    for nickname, (frb, host, redshift) in expected.items():
        row = rows[nickname]
        assert (row["frb_identifier"], row["host_identifier"]) == (frb, host)
        assert row["published_redshift"] == redshift
        assert row["measurement_kind"] == "spectroscopic"
        assert row["redshift_uncertainty_available"] == "false"
        assert row["redshift_uncertainty"] == ""
        assert row["host_identity_row"].endswith(f"Table 2|{frb}")
        assert row["redshift_row"].endswith(f"Table 3|{frb}")
        assert row["doi"] == "10.3847/1538-4357/ad3736"


def test_frozen_author_source_contains_identity_redshift_and_method_rows() -> None:
    macros = (EVIDENCE / "identifier_macros.tex").read_text()
    table2 = (EVIDENCE / "table2_host_identity.tex").read_text()
    table3 = (EVIDENCE / "table3_host_redshift.tex").read_text()
    method = (EVIDENCE / "spectroscopy_method.tex").read_text()

    assert r"\newcommand{\frbzach}{20220207C}" in macros
    assert r"\newcommand{\frbwhitney}{20220310F}" in macros
    assert r"\frbzach & PSO J310.1977$+$72.8826" in table2
    assert r"\frbwhitney & PSO J134.7211$+$73.4910" in table2
    assert r"\frbzach & 0.043040" in table3
    assert r"\frbwhitney & 0.477958" in table3
    assert "We measure the spectroscopic redshift" in method
    assert "at least 3 emission lines" in method


def test_manifest_does_not_invent_row_level_uncertainties() -> None:
    manifest = _manifest()

    assert manifest["verification"]["row_level_redshift_uncertainty_reported"] is False
    for row in manifest["row_linkage"]:
        assert row["redshift_uncertainty_available"] is False
        assert row["redshift_uncertainty"] is None
