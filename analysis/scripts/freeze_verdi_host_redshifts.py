#!/usr/bin/env python3
"""Freeze a minimal, fail-closed host-redshift extract from a Verdi draft ZIP.

The source archive is not copied. The generated comparison records source row
identifiers and hashes, preserves local values, and makes missing authority
fields explicit. It never promotes a draft value into the census.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


SCHEMA = "faber2026-verdi-host-redshift-evidence/v1"
CURRENT_MEMBER = "verdi2025.tex"
PRIOR_MEMBER = "test.tex"
SOURCE_TITLE = (
    "Probing Host Galaxy Environments with a New Sample of Localized FRBs "
    "Detected with the DSA-110"
)
PAPER_UNCERTAINTY_NOTE = "<0.4% paper-wide bound; no row-level uncertainty"

# Local identifiers differ from the supplied draft while the frozen sky
# positions are identical. These are comparison aliases, not adjudications.
FRB_ALIASES = {
    "20230325A": ("20230325C", "same localization coordinates in current draft"),
    "20230913A": ("20230913G", "same localization coordinates in current draft"),
    "20240122A": ("20240122E", "same localization coordinates in current draft"),
    "20240203A": ("20240203D", "same localization coordinates in current draft"),
}

# The older draft uses internal names instead of final FRB identifiers.
OLDER_DRAFT_NAMES = {
    "Freya": "20230325C",
    "Hamilton": "20230913G",
    "Mahi": "20240122E",
    "Chromatica": "20240203D",
}

EXPLICIT_SPECTROSCOPY = {
    "20230913G": "spectroscopic; Keck-I/LRIS emission lines in appendix",
    "20240203D": "spectroscopic; Keck-I/LRIS emission lines in appendix",
}

CSV_FIELDS = [
    "nickname",
    "local_frb_id",
    "verdi_frb_id",
    "identifier_relation",
    "local_host_redshift",
    "current_draft_redshift",
    "prior_draft_redshift",
    "comparison_status",
    "host_identifier",
    "redshift_uncertainty",
    "paper_uncertainty_note",
    "measurement_kind",
    "current_source_rows",
    "prior_source_rows",
    "bibliographic_source",
    "source_release",
    "source_received_date",
    "archive_sha256",
    "current_member_sha256",
    "prior_member_sha256",
    "authority_status",
    "blocking_reasons",
]


@dataclass(frozen=True)
class SourceRow:
    member: str
    table: str
    frb_id: str
    redshift: float | None
    redshift_text: str
    line: int

    @property
    def row_id(self) -> str:
        return f"{self.member}:{self.line}:table:{self.table}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize_first_cell(cell: str) -> str | None:
    match = re.search(r"20\d{6}[A-Z]", cell)
    if match:
        return match.group(0)
    for name, frb_id in OLDER_DRAFT_NAMES.items():
        if name in cell:
            return frb_id
    return None


def _parse_redshift(cell: str) -> tuple[float | None, str] | None:
    value = cell.strip().rstrip("\\").strip().strip("$").strip()
    if value == "--":
        return None, ""
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value):
        return None
    return float(value), value


def parse_tex_rows(member: str, text: str) -> list[SourceRow]:
    """Parse first-column FRB identifiers and second-column redshifts in tables."""
    rows: list[SourceRow] = []
    table = "unlabeled"
    in_data = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        if "\\tablecaption" in line:
            label = re.search(r"\\label\{(?:table|tab):([^}]+)\}", line)
            table = label.group(1) if label else "unlabeled"
        if "\\startdata" in line:
            in_data = True
            continue
        if "\\enddata" in line:
            in_data = False
            continue
        if not in_data or "&" not in line:
            continue
        cells = line.split("&", maxsplit=2)
        if len(cells) < 2:
            continue
        frb_id = _normalize_first_cell(cells[0])
        parsed_redshift = _parse_redshift(cells[1])
        if frb_id is None or parsed_redshift is None:
            continue
        redshift, redshift_text = parsed_redshift
        rows.append(
            SourceRow(
                member=member,
                table=table,
                frb_id=frb_id,
                redshift=redshift,
                redshift_text=redshift_text,
                line=line_number,
            )
        )
    return rows


def _selected_row(rows: list[SourceRow], frb_id: str) -> SourceRow | None:
    matches = [row for row in rows if row.frb_id == frb_id]
    if not matches:
        return None
    priority = {"burst_props": 0, "scatter_props": 1}
    return sorted(matches, key=lambda row: (priority.get(row.table, 9), row.line))[0]


def _source_rows(rows: list[SourceRow], frb_id: str) -> str:
    return ";".join(row.row_id for row in rows if row.frb_id == frb_id)


def _float_equal(left: float | None, right: float | None) -> bool:
    return left is not None and right is not None and abs(left - right) < 5e-7


def _comparison_status(
    local: float | None,
    current: SourceRow | None,
    prior: SourceRow | None,
) -> str:
    if local is not None:
        if current is not None and current.redshift is not None:
            return (
                "matches_current_draft"
                if _float_equal(local, current.redshift)
                else "conflicts_with_current_draft"
            )
        if current is not None and prior is not None and prior.redshift is not None:
            return (
                "current_draft_missing_prior_draft_matches"
                if _float_equal(local, prior.redshift)
                else "current_draft_missing_prior_draft_conflicts"
            )
        if current is not None:
            return "current_draft_explicitly_missing"
        if prior is not None and prior.redshift is not None:
            return (
                "prior_draft_only_matches"
                if _float_equal(local, prior.redshift)
                else "prior_draft_only_conflicts"
            )
        return "absent_from_archive"

    if current is not None and current.redshift is not None:
        return "local_missing_current_draft_has_value"
    if prior is not None and prior.redshift is not None:
        return "local_missing_prior_draft_has_value"
    if current is not None or prior is not None:
        return "no_redshift_in_local_or_drafts"
    return "absent_from_archive"


def _blocking_reasons(
    *,
    local_frb_id: str,
    verdi_frb_id: str,
    local: float | None,
    current: SourceRow | None,
    prior: SourceRow | None,
) -> str:
    reasons = [
        "missing_host_identifier",
        "missing_row_redshift_uncertainty",
        "unpublished_source_without_release_identifier",
    ]
    if verdi_frb_id not in EXPLICIT_SPECTROSCOPY:
        reasons.append("measurement_kind_not_row_specific")
    if local_frb_id != verdi_frb_id:
        reasons.append("frb_identifier_alias_not_adjudicated")
    if current is None:
        reasons.append("absent_from_current_draft")
    elif current.redshift is None:
        reasons.append("current_draft_redshift_missing")
    if local is None and current is not None and current.redshift is not None:
        reasons.append("local_redshift_missing")
    if current is not None and prior is not None and current.redshift != prior.redshift:
        reasons.append("current_prior_draft_conflict")
    return ";".join(reasons)


def _read_bursts(path: Path, expected_rows: int) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"nickname", "tns", "z_spec"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"bursts CSV must contain {sorted(required)}")
    if len(rows) != expected_rows:
        raise ValueError(f"expected {expected_rows} burst rows, found {len(rows)}")
    keys = [(row["nickname"], row["tns"]) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("bursts CSV contains duplicate nickname/FRB keys")
    return rows


def _csv_bytes(rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def freeze_evidence(
    *,
    archive_path: Path,
    bursts_path: Path,
    output_dir: Path,
    source_received_date: str,
    expected_archive_sha256: str,
    expected_rows: int = 12,
) -> dict:
    """Write deterministic comparison CSV and manifest; return the manifest."""
    archive_bytes = archive_path.read_bytes()
    archive_hash = sha256_bytes(archive_bytes)
    if archive_hash != expected_archive_sha256:
        raise ValueError(
            "archive SHA-256 mismatch: "
            f"expected {expected_archive_sha256}, found {archive_hash}"
        )

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        names = set(archive.namelist())
        missing = {CURRENT_MEMBER, PRIOR_MEMBER} - names
        if missing:
            raise ValueError(f"archive missing required members: {sorted(missing)}")
        member_bytes = {
            member: archive.read(member) for member in (CURRENT_MEMBER, PRIOR_MEMBER)
        }

    parsed = {
        member: parse_tex_rows(member, data.decode("utf-8"))
        for member, data in member_bytes.items()
    }
    bursts = _read_bursts(bursts_path, expected_rows)
    member_hashes = {
        member: sha256_bytes(data) for member, data in member_bytes.items()
    }
    bibliography = (
        f"Verdi et al., {SOURCE_TITLE} "
        f"(unpublished draft archive received {source_received_date})"
    )

    output_rows: list[dict[str, str]] = []
    source_conflicts: list[str] = []
    for burst in bursts:
        local_frb_id = burst["tns"].removeprefix("FRB ").strip()
        verdi_frb_id, alias_basis = FRB_ALIASES.get(
            local_frb_id, (local_frb_id, "exact identifier")
        )
        local_text = burst["z_spec"].strip()
        local = float(local_text) if local_text else None
        current = _selected_row(parsed[CURRENT_MEMBER], verdi_frb_id)
        prior = _selected_row(parsed[PRIOR_MEMBER], verdi_frb_id)
        if (
            current is not None
            and prior is not None
            and current.redshift != prior.redshift
        ):
            source_conflicts.append(burst["nickname"])

        measurement_kind = EXPLICIT_SPECTROSCOPY.get(
            verdi_frb_id,
            (
                "not stated at row level; host spectroscopy described at sample level"
                if current is not None and current.redshift is not None
                else "not stated at row level"
            ),
        )
        output_rows.append(
            {
                "nickname": burst["nickname"],
                "local_frb_id": local_frb_id,
                "verdi_frb_id": verdi_frb_id,
                "identifier_relation": alias_basis,
                "local_host_redshift": local_text,
                "current_draft_redshift": current.redshift_text if current else "",
                "prior_draft_redshift": prior.redshift_text if prior else "",
                "comparison_status": _comparison_status(local, current, prior),
                "host_identifier": "",
                "redshift_uncertainty": "",
                "paper_uncertainty_note": PAPER_UNCERTAINTY_NOTE,
                "measurement_kind": measurement_kind,
                "current_source_rows": _source_rows(
                    parsed[CURRENT_MEMBER], verdi_frb_id
                ),
                "prior_source_rows": _source_rows(parsed[PRIOR_MEMBER], verdi_frb_id),
                "bibliographic_source": bibliography,
                "source_release": "unpublished draft; no version identifier",
                "source_received_date": source_received_date,
                "archive_sha256": archive_hash,
                "current_member_sha256": member_hashes[CURRENT_MEMBER],
                "prior_member_sha256": member_hashes[PRIOR_MEMBER],
                "authority_status": "insufficient",
                "blocking_reasons": _blocking_reasons(
                    local_frb_id=local_frb_id,
                    verdi_frb_id=verdi_frb_id,
                    local=local,
                    current=current,
                    prior=prior,
                ),
            }
        )

    csv_data = _csv_bytes(output_rows)
    statuses = Counter(row["comparison_status"] for row in output_rows)
    script_hash = sha256_bytes(Path(__file__).read_bytes())
    manifest = {
        "schema": SCHEMA,
        "status": "fail_closed",
        "disposition": (
            "Minimal comparison frozen; archive is insufficient for authoritative "
            "row-complete host-redshift provenance."
        ),
        "source": {
            "title": SOURCE_TITLE,
            "archive_filename": archive_path.name,
            "archive_sha256": archive_hash,
            "archive_size_bytes": len(archive_bytes),
            "source_received_date": source_received_date,
            "release": "unpublished draft; no version identifier",
            "members": {
                member: {
                    "sha256": member_hashes[member],
                    "size_bytes": len(member_bytes[member]),
                    "role": "current_named_draft"
                    if member == CURRENT_MEMBER
                    else "older_internal_draft",
                }
                for member in (CURRENT_MEMBER, PRIOR_MEMBER)
            },
        },
        "input": {
            "bursts_filename": bursts_path.name,
            "bursts_sha256": sha256_bytes(bursts_path.read_bytes()),
            "row_count": len(bursts),
        },
        "generator": {
            "path": "scripts/freeze_verdi_host_redshifts.py",
            "sha256": script_hash,
        },
        "output": {
            "comparison_csv": "verdi_host_redshift_comparison.csv",
            "comparison_csv_sha256": sha256_bytes(csv_data),
        },
        "summary": {
            "rows": len(output_rows),
            "comparison_status_counts": dict(sorted(statuses.items())),
            "source_conflict_rows": len(source_conflicts),
            "source_conflict_nicknames": sorted(source_conflicts),
            "rows_with_current_draft_source": sum(
                bool(row["current_source_rows"]) for row in output_rows
            ),
            "rows_with_row_level_host_identifier": 0,
            "rows_with_row_level_redshift_uncertainty": 0,
            "rows_with_explicit_row_level_measurement_kind": sum(
                row["verdi_frb_id"] in EXPLICIT_SPECTROSCOPY for row in output_rows
            ),
        },
        "authority_contract": {
            "satisfied": False,
            "required": [
                "FRB identifier",
                "host identifier",
                "redshift and uncertainty",
                "measurement kind",
                "bibliographic source",
                "upstream row identifier",
                "release or retrieval date",
                "content hash",
            ],
            "blocking_findings": [
                "No row-level host-galaxy identifiers are present.",
                "No row-level redshift uncertainties are present.",
                "Four local and source FRB identifiers have different suffixes.",
                "The current and older drafts disagree for at least one sightline.",
                "At least one local host redshift is absent from the current draft.",
                "The archive has no release or version identifier.",
            ],
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "verdi_host_redshift_comparison.csv").write_bytes(csv_data)
    manifest_data = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    (output_dir / "source_manifest.json").write_bytes(manifest_data)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--bursts", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-received-date", required=True)
    parser.add_argument("--expect-archive-sha256", required=True)
    parser.add_argument("--expected-rows", type=int, default=12)
    parser.add_argument(
        "--require-authoritative",
        action="store_true",
        help="exit nonzero when the authority contract is not satisfied",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = freeze_evidence(
        archive_path=args.archive,
        bursts_path=args.bursts,
        output_dir=args.output_dir,
        source_received_date=args.source_received_date,
        expected_archive_sha256=args.expect_archive_sha256,
        expected_rows=args.expected_rows,
    )
    if args.require_authoritative and not manifest["authority_contract"]["satisfied"]:
        print("host-redshift authority contract is not satisfied")
        return 2
    print(json.dumps(manifest["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
