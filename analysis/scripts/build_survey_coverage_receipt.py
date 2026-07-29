#!/usr/bin/env python3
"""Build the frozen all-sightline discovery-survey footprint receipt."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys

from astropy.coordinates import SkyCoord

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from foregrounds.census.config import SURVEY_CONTRACT, TARGETS
from foregrounds.paths import CENSUS_ROOT
from foregrounds.census.survey_coverage import survey_in_footprint
from foregrounds.census.survey_footprint_mocs import CDS_MOC_IDS, moc_cache_path

DISCOVERY_SURVEYS = ("NED", "GLADE+", "DESI_DR8_NORTH", "SDSS_DR12", "CLUSTERS")
OUTPUT_DIR = CENSUS_ROOT / "data" / "survey_coverage"
CSV_PATH = OUTPUT_DIR / "all_12_sightlines.csv"
JSON_PATH = OUTPUT_DIR / "all_12_sightlines.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for nickname, ra, dec, redshift in TARGETS:
        coord = SkyCoord(ra, dec, unit=("hourangle", "deg"))
        for survey in DISCOVERY_SURVEYS:
            contained = survey_in_footprint(survey, coord)
            moc_path = moc_cache_path(survey) if survey in CDS_MOC_IDS else None
            rows.append(
                {
                    "nickname": nickname,
                    "ra": ra,
                    "dec": dec,
                    "host_redshift_status": (
                        "established" if redshift is not None else "dm_z_diagnostic"
                    ),
                    "survey": survey,
                    "release": SURVEY_CONTRACT[survey]["release"],
                    "depth": SURVEY_CONTRACT[survey]["depth"],
                    "footprint_status": (
                        "covered"
                        if contained is True
                        else "not_covered"
                        if contained is False
                        else "unknown"
                    ),
                    "footprint_source": (
                        str(moc_path.relative_to(CENSUS_ROOT))
                        if moc_path is not None and moc_path.is_file()
                        else "all_sky_contract"
                        if contained is True and survey not in CDS_MOC_IDS
                        else "unavailable"
                    ),
                    "footprint_sha256": (
                        _sha256(moc_path)
                        if moc_path is not None and moc_path.is_file()
                        else ""
                    ),
                }
            )
    return rows


def render() -> tuple[str, str]:
    rows = build_rows()
    fieldnames = list(rows[0])
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    payload = {
        "schema_version": 1,
        "scope": "12 FRB sightlines x 5 discovery-survey footprints",
        "semantics": (
            "Footprint coverage only. A covered footprint is not a catalog "
            "non-detection; query results and failures must be recorded separately."
        ),
        "rows": rows,
    }
    return buffer.getvalue(), json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main() -> int:
    csv_text, json_text = render()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CSV_PATH.write_text(csv_text, encoding="utf-8")
    JSON_PATH.write_text(json_text, encoding="utf-8")
    print(f"wrote {CSV_PATH}")
    print(f"wrote {JSON_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
