from __future__ import annotations

import csv
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from freeze_verdi_host_redshifts import freeze_evidence, parse_tex_rows  # noqa: E402


def _write_archive(path: Path) -> None:
    current = r"""
\title{Probing Host Galaxy Environments with a New Sample of Localized FRBs Detected with the DSA-110}
\begin{deluxetable}{cc}
\tablecaption{Host redshifts\label{table:burst_props}}
\startdata
20221113A & 0.2505 \\
20221203A & -- \\
20230913G & 0.3024 \\
\enddata
\end{deluxetable}
"""
    prior = r"""
\begin{deluxetable}{cc}
\tablecaption{Host redshifts\label{table:burst_props}}
\startdata
20221113A & 0.2505 \\
20221203A & 0.5100 \\
\enddata
\end{deluxetable}
"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("verdi2025.tex", current)
        archive.writestr("test.tex", prior)


def _write_bursts(path: Path) -> None:
    path.write_text(
        "nickname,tns,z_spec,localization\n"
        "isha,FRB 20221113A,0.2505,04 45 38.64 +70 18 26.6\n"
        "wilhelm,FRB 20221203A,0.51,21 00 31.09 +72 02 15.22\n"
        "hamilton,FRB 20230913A,0.3024,20 20 08.92 +70 47 33.96\n",
        encoding="utf-8",
    )


def test_parse_tex_rows_records_table_and_line() -> None:
    text = "\n".join(
        [
            r"\tablecaption{Host redshifts\label{table:burst_props}}",
            r"\startdata",
            r"20221113A & 0.2505 \\",
            r"\textcolor{red}{Hamilton} & -- \\",
            r"\enddata",
        ]
    )
    rows = parse_tex_rows("draft.tex", text)
    assert [(row.frb_id, row.redshift, row.line) for row in rows] == [
        ("20221113A", 0.2505, 3),
        ("20230913G", None, 4),
    ]
    assert {row.table for row in rows} == {"burst_props"}


def test_freeze_detects_superseded_value_and_identifier_alias(tmp_path: Path) -> None:
    archive = tmp_path / "verdi.zip"
    bursts = tmp_path / "bursts.csv"
    output = tmp_path / "out"
    _write_archive(archive)
    _write_bursts(bursts)

    manifest = freeze_evidence(
        archive_path=archive,
        bursts_path=bursts,
        output_dir=output,
        source_received_date="2026-07-22",
        expected_archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        expected_rows=3,
    )

    with (output / "verdi_host_redshift_comparison.csv").open(newline="") as handle:
        rows = {row["nickname"]: row for row in csv.DictReader(handle)}

    assert rows["isha"]["comparison_status"] == "matches_current_draft"
    assert rows["wilhelm"]["comparison_status"] == (
        "current_draft_missing_prior_draft_matches"
    )
    assert rows["wilhelm"]["prior_draft_redshift"] == "0.5100"
    assert rows["hamilton"]["verdi_frb_id"] == "20230913G"
    assert rows["hamilton"]["comparison_status"] == "matches_current_draft"
    assert all(row["authority_status"] == "insufficient" for row in rows.values())
    assert manifest["status"] == "fail_closed"
    assert manifest["summary"]["source_conflict_rows"] == 1
    assert manifest["authority_contract"]["satisfied"] is False


def test_freeze_is_byte_deterministic_and_rejects_wrong_hash(tmp_path: Path) -> None:
    archive = tmp_path / "verdi.zip"
    bursts = tmp_path / "bursts.csv"
    _write_archive(archive)
    _write_bursts(bursts)
    archive_hash = hashlib.sha256(archive.read_bytes()).hexdigest()

    hashes = []
    for name in ("first", "second"):
        output = tmp_path / name
        freeze_evidence(
            archive_path=archive,
            bursts_path=bursts,
            output_dir=output,
            source_received_date="2026-07-22",
            expected_archive_sha256=archive_hash,
            expected_rows=3,
        )
        hashes.append(
            [
                hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(output.iterdir())
            ]
        )
    assert hashes[0] == hashes[1]

    with pytest.raises(ValueError, match="archive SHA-256 mismatch"):
        freeze_evidence(
            archive_path=archive,
            bursts_path=bursts,
            output_dir=tmp_path / "bad",
            source_received_date="2026-07-22",
            expected_archive_sha256="0" * 64,
            expected_rows=3,
        )


def test_committed_extract_remains_fail_closed() -> None:
    evidence = ROOT / "docs/rse/specs/evidence/verdi-host-redshifts-2026-07-22"
    manifest = json.loads((evidence / "source_manifest.json").read_text())
    with (evidence / "verdi_host_redshift_comparison.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 12
    assert manifest["status"] == "fail_closed"
    assert manifest["authority_contract"]["satisfied"] is False
    assert manifest["summary"]["source_conflict_rows"] >= 1
    assert all(row["authority_status"] == "insufficient" for row in rows)
    assert all(row["host_identifier"] == "" for row in rows)
    assert all(row["redshift_uncertainty"] == "" for row in rows)
