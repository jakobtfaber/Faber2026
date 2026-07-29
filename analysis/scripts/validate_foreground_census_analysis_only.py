#!/usr/bin/env python3
"""Independent, analysis-only validation of the foreground census and Figure 3.

This replaces the retired release gate that bound its evidence to the
`dsa110-FLITS` pipeline repository and a `pipeline/` submodule the manuscript no
longer carries.  Every input read here lives under `analysis/`.

The validator recomputes rather than reads.  Where a stored table records a
derived quantity, the quantity is recalculated from the committed source
columns and compared, so a corrupted or hand-edited product fails rather than
being echoed back.

Six assertions, one per subcommand of the science question:

1. ``sourced_redshifts``  - every adopted redshift carries a source-bearing
   record: host redshifts trace to the Verdi or Law extracts, candidate
   redshifts trace to a frozen catalog row with response and row hashes.
2. ``hostless_fail_closed`` - sightlines and candidates without a trustworthy
   redshift are explicitly labelled, are excluded from the budget, and never
   reach a ``confirmed`` verdict.
3. ``deterministic_matching`` - the Figure 3 input values reproduce
   canonically from committed inputs, the approved input bytes remain pinned,
   cross-listing duplicates are removed by an auditable rule, and every
   recorded separation reproduces from the coordinates.
4. ``survey_coverage`` - all twelve sightlines carry a coverage row per survey,
   coordinates agree with the burst roster, and every footprint claim is backed
   by a hashed footprint file or an explicit contract.
5. ``mass_radius_conventions`` - halo and cluster rows use distinct, declared
   mass and radius definitions that are never mixed, and the halo radius
   reproduces from the halo mass under the declared overdensity and cosmology.
6. ``census_matches_figure3`` - the twelve-sightline census and the installed
   manuscript Figure 3 describe the same systems.

Exit status is 0 only when every assertion passes.  A JSON receipt binding all
input hashes and the installed Figure 3 bytes is written with ``--output``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CENSUS = ROOT / "foregrounds/census/data"
MANUSCRIPT_FIGURE = ROOT.parent / "figures/sightline_halo_grid.pdf"
# The producing render, kept beside the review artifacts. When it is present it
# gives a byte-level identity between what the figure workflow produced and what
# the manuscript installs, which a re-render on a different renderer version
# cannot provide.
STAGED_FIGURE = ROOT / "figure_review/artifacts/staging/fig3_halo_grid/figures/sightline_halo_grid.pdf"
APPROVED_HALO_GRID_SHA256 = (
    "2a59fb28bfe196fde63f2335548030ff911dfbeda9e07e133823ca511fdf79e9"
)

# Sightlines with no established host redshift.  These must stay diagnostic-only
# everywhere: no point-estimate redshift, no confirmed foreground system, no
# budget contribution.
DIAGNOSTIC_ONLY_SIGHTLINES = frozenset({"wilhelm", "freya", "mahi"})

# Redshift dispositions that are allowed to carry no adopted redshift.  Any
# other disposition without a redshift is a silent failure and is rejected.
REDSHIFTLESS_DISPOSITIONS = frozenset(
    {
        "identity_verified_no_catalog_redshift",
        "identity_verified_catalog_has_no_redshift",
    }
)

# The declared conventions.  A row that departs from these is a convention
# violation even when its numbers are individually plausible.
HALO_MASS_METHOD = "Moster13_Table1_redshift_dependent"
HALO_RADIUS_METHOD = "200_times_critical_density_Planck18"
CLUSTER_NOT_APPLICABLE = "not_applicable_cluster"
HALO_RADIUS_DEFINITION = "R200c"
CLUSTER_RADIUS_DEFINITION = "R500c_catalog"
HALO_OVERDENSITY = 200.0

# Tolerances.  The radius tolerance is a fractional agreement between the stored
# R200c and the value recomputed from the stored M200c; 0.1 per cent is far
# tighter than any physical uncertainty and only admits rounding.
RADIUS_RELATIVE_TOLERANCE = 1.0e-3
SEPARATION_ABSOLUTE_TOLERANCE_ARCSEC = 0.05
COORDINATE_TOLERANCE_DEG = 1.0e-6
RATIO_RELATIVE_TOLERANCE = 1.0e-6
REDSHIFT_ABSOLUTE_TOLERANCE = 1.0e-9


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def number(value: Any) -> float | None:
    """Parse a CSV cell as a finite float, or return None."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def angular_separation_arcsec(
    ra1_deg: float, dec1_deg: float, ra2_deg: float, dec2_deg: float
) -> float:
    """Great-circle separation via the Vincenty formula (stable at small angles)."""
    ra1, dec1, ra2, dec2 = (math.radians(v) for v in (ra1_deg, dec1_deg, ra2_deg, dec2_deg))
    dra = ra2 - ra1
    num = math.hypot(
        math.cos(dec2) * math.sin(dra),
        math.cos(dec1) * math.sin(dec2) - math.sin(dec1) * math.cos(dec2) * math.cos(dra),
    )
    den = math.sin(dec1) * math.sin(dec2) + math.cos(dec1) * math.cos(dec2) * math.cos(dra)
    return math.degrees(math.atan2(num, den)) * 3600.0


def sexagesimal_to_degrees(ra_text: str, dec_text: str) -> tuple[float, float]:
    """Parse ``20h40m47.886s`` / ``+72d52m56.378s`` without a catalog dependency."""

    def split(text: str, units: str) -> list[float]:
        parts: list[float] = []
        current = ""
        for char in text.strip():
            if char in units:
                parts.append(float(current))
                current = ""
            else:
                current += char
        if current.strip():
            parts.append(float(current))
        return parts

    hours, minutes, seconds = split(ra_text, "hms")
    ra_deg = 15.0 * (abs(hours) + minutes / 60.0 + seconds / 3600.0)

    dec_parts = split(dec_text, "dms")
    degrees, arcmin, arcsec = dec_parts
    sign = -1.0 if dec_text.strip().startswith("-") else 1.0
    dec_deg = sign * (abs(degrees) + arcmin / 60.0 + arcsec / 3600.0)
    return ra_deg, dec_deg


# --------------------------------------------------------------------------
# result plumbing
# --------------------------------------------------------------------------


@dataclass
class CheckResult:
    name: str
    title: str
    failures: list[str] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.failures

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.failures.append(message)


# --------------------------------------------------------------------------
# input bundle
# --------------------------------------------------------------------------


INPUT_PATHS: dict[str, str] = {
    "registry": "intervening_census_registry.csv",
    "cross_references": "expanded_catalog_cross_references.csv",
    "provenance": "candidate_redshift_provenance.csv",
    "duplicates": "census_masses/census_duplicates.csv",
    "halo_grid": "sightline_halo_grid.csv",
    "bursts": "frozen_census/bursts.csv",
    "verdi_hosts": "frozen_census/verdi2025_host_redshift_extract.csv",
    "law_hosts": "frozen_census/law2024_host_redshift_extract.csv",
    "survey_coverage": "survey_coverage/all_12_sightlines.csv",
    "ps1_strm_resolution": "frozen_census/ps1_strm_resolution.csv",
}


@dataclass
class Inputs:
    tables: dict[str, list[dict[str, str]]]
    hashes: dict[str, str]

    @classmethod
    def load(cls) -> Inputs:
        tables: dict[str, list[dict[str, str]]] = {}
        hashes: dict[str, str] = {}
        for key, relative in INPUT_PATHS.items():
            path = CENSUS / relative
            if not path.is_file():
                raise SystemExit(f"required census input is missing: {path}")
            tables[key] = read_csv(path)
            hashes[str(path.relative_to(ROOT))] = sha256_file(path)
        return cls(tables=tables, hashes=hashes)

    def __getitem__(self, key: str) -> list[dict[str, str]]:
        return self.tables[key]


def candidate_key(row: dict[str, str], object_field: str) -> tuple[str, str, str]:
    return (
        row["nickname"].strip().lower(),
        row["type"].strip(),
        str(row[object_field]).strip(),
    )


# --------------------------------------------------------------------------
# check 1 - sourced redshifts
# --------------------------------------------------------------------------


def check_sourced_redshifts(data: Inputs) -> CheckResult:
    result = CheckResult(
        "sourced_redshifts",
        "Every adopted redshift carries a source-bearing record",
    )

    # --- host redshifts -------------------------------------------------
    # The frozen extracts are keyed on the source event designation, not on the
    # TNS name: three events were renamed after publication, so the extracts'
    # `mapped_tns` column preserves the as-published label and must not be used
    # as the join key.
    verdi = {row["mapped_nickname"].strip().lower(): row for row in data["verdi_hosts"]}
    law = {row["mapped_nickname"].strip().lower(): row for row in data["law_hosts"]}

    hosts_with_redshift = 0
    for burst in data["bursts"]:
        nickname = burst["nickname"].strip().lower()
        host_z = number(burst.get("z_spec"))
        if host_z is None:
            continue
        hosts_with_redshift += 1
        verdi_row = verdi.get(nickname)
        law_row = law.get(nickname)
        if verdi_row is not None and number(verdi_row.get("redshift")) is not None:
            reported = number(verdi_row["redshift"])
            result.require(
                abs(reported - host_z) <= REDSHIFT_ABSOLUTE_TOLERANCE,
                f"{nickname}: roster host redshift {host_z} does not match the "
                f"Verdi extract value {reported}",
            )
            result.require(
                bool(verdi_row.get("source_event", "").strip()),
                f"{nickname}: Verdi host record has no source event designation",
            )
        elif law_row is not None and number(law_row.get("adopted_redshift")) is not None:
            adopted = number(law_row["adopted_redshift"])
            result.require(
                abs(adopted - host_z) <= REDSHIFT_ABSOLUTE_TOLERANCE,
                f"{nickname}: roster host redshift {host_z} does not match the "
                f"Law extract adopted value {adopted}",
            )
            for column in ("published_redshift", "measurement_kind", "source_table"):
                result.require(
                    bool(law_row.get(column, "").strip()),
                    f"{nickname}: Law host record is missing {column}",
                )
        else:
            result.failures.append(
                f"{nickname}: host redshift {host_z} has no source-bearing extract row"
            )

    # --- candidate redshifts --------------------------------------------
    provenance = {candidate_key(row, "obj"): row for row in data["provenance"]}
    required_columns = (
        "source_family",
        "source_release",
        "retrieved_at_utc",
        "stable_source_id",
        "source_row_sha256",
        "query_response_sha256",
    )
    sourced = 0
    for row in data["registry"]:
        key = candidate_key(row, "obj")
        best_z = number(row.get("best_z"))
        declared_source = row.get("best_z_source", "").strip()
        if best_z is None or declared_source in {"", "none"}:
            continue
        sourced += 1
        record = provenance.get(key)
        if record is None:
            result.failures.append(
                f"{key[0]}/{key[1]}/{key[2]}: adopted redshift {best_z} has no "
                "provenance record"
            )
            continue
        adopted = number(record.get("adopted_z"))
        result.require(
            adopted is not None and abs(adopted - best_z) <= REDSHIFT_ABSOLUTE_TOLERANCE,
            f"{key[0]}/{key[1]}/{key[2]}: registry redshift {best_z} disagrees "
            f"with the provenance record's {adopted}",
        )
        for column in required_columns:
            result.require(
                bool(record.get(column, "").strip()),
                f"{key[0]}/{key[1]}/{key[2]}: provenance record is missing {column}",
            )
        result.require(
            record.get("measurement_kind", "").strip()
            in {"spectroscopic", "photometric", "catalog_cluster"},
            f"{key[0]}/{key[1]}/{key[2]}: measurement kind "
            f"{record.get('measurement_kind')!r} is not a redshift measurement",
        )
        result.require(
            record.get("source_disposition", "").strip()
            not in REDSHIFTLESS_DISPOSITIONS,
            f"{key[0]}/{key[1]}/{key[2]}: adopted a redshift while its provenance "
            "disposition records that no catalog redshift exists",
        )

    result.facts = {
        "host_rows": len(data["bursts"]),
        "hosts_with_established_redshift": hosts_with_redshift,
        "verdi_extract_rows": len(data["verdi_hosts"]),
        "law_extract_rows": len(data["law_hosts"]),
        "candidate_rows_with_adopted_redshift": sourced,
        "provenance_rows": len(data["provenance"]),
    }
    return result


# --------------------------------------------------------------------------
# check 2 - redshiftless systems fail closed
# --------------------------------------------------------------------------


def check_hostless_fail_closed(data: Inputs) -> CheckResult:
    result = CheckResult(
        "hostless_fail_closed",
        "Systems and sightlines without a trustworthy redshift fail closed",
    )

    provenance = {candidate_key(row, "obj"): row for row in data["provenance"]}

    redshiftless = 0
    for row in data["registry"]:
        key = candidate_key(row, "obj")
        best_z = number(row.get("best_z"))
        declared_source = row.get("best_z_source", "").strip()
        if best_z is not None and declared_source not in {"", "none"}:
            continue
        redshiftless += 1
        result.require(
            row.get("final_verdict", "").strip() != "confirmed",
            f"{key[0]}/{key[1]}/{key[2]}: confirmed without an adopted redshift",
        )
        result.require(
            not truthy(row.get("budget_eligible")),
            f"{key[0]}/{key[1]}/{key[2]}: budget-eligible without an adopted redshift",
        )
        result.require(
            not truthy(row.get("registry_tier")),
            f"{key[0]}/{key[1]}/{key[2]}: promoted to the census tier without an "
            "adopted redshift",
        )
        record = provenance.get(key)
        result.require(
            record is not None,
            f"{key[0]}/{key[1]}/{key[2]}: redshiftless row has no provenance record "
            "stating why",
        )
        if record is not None:
            result.require(
                record.get("source_disposition", "").strip() in REDSHIFTLESS_DISPOSITIONS,
                f"{key[0]}/{key[1]}/{key[2]}: redshiftless row records disposition "
                f"{record.get('source_disposition')!r}, which asserts a usable redshift",
            )
            result.require(
                bool(record.get("stable_source_id", "").strip()),
                f"{key[0]}/{key[1]}/{key[2]}: redshiftless row has no verified identity",
            )

    # --- sightlines without an established host redshift ------------------
    coverage_status = {
        row["nickname"].strip().lower(): row["host_redshift_status"].strip()
        for row in data["survey_coverage"]
    }
    grid = data["halo_grid"]
    roster_without_redshift = set()
    for burst in data["bursts"]:
        nickname = burst["nickname"].strip().lower()
        if number(burst.get("z_spec")) is None:
            roster_without_redshift.add(nickname)

    result.require(
        roster_without_redshift == set(DIAGNOSTIC_ONLY_SIGHTLINES),
        "the set of sightlines without an established host redshift is "
        f"{sorted(roster_without_redshift)}, not the declared "
        f"{sorted(DIAGNOSTIC_ONLY_SIGHTLINES)}",
    )

    for nickname in sorted(roster_without_redshift):
        result.require(
            coverage_status.get(nickname) == "dm_z_diagnostic",
            f"{nickname}: host redshift status is {coverage_status.get(nickname)!r}, "
            "not the diagnostic-only label",
        )
        host_rows = [
            row
            for row in grid
            if row["nickname"].strip().lower() == nickname and row["row_kind"] == "host"
        ]
        result.require(
            len(host_rows) == 1,
            f"{nickname}: expected exactly one Figure 3 host row, found {len(host_rows)}",
        )
        for row in host_rows:
            result.require(
                number(row.get("frb_z")) is None,
                f"{nickname}: Figure 3 host row carries a point-estimate redshift "
                "for a sightline with no established host redshift",
            )
        systems = [
            row
            for row in grid
            if row["nickname"].strip().lower() == nickname and row["row_kind"] == "system"
        ]
        result.require(
            not systems,
            f"{nickname}: {len(systems)} foreground systems are drawn on a sightline "
            "whose host redshift is diagnostic only",
        )

    for burst in data["bursts"]:
        nickname = burst["nickname"].strip().lower()
        if nickname in roster_without_redshift:
            continue
        result.require(
            coverage_status.get(nickname) == "established",
            f"{nickname}: host redshift status is {coverage_status.get(nickname)!r}, "
            "not established",
        )

    # --- a fail-closed geometry flag must state a reason that is actually true
    host_redshifts = {
        burst["nickname"].strip().lower(): number(burst.get("z_spec"))
        for burst in data["bursts"]
    }
    flagged: list[dict[str, Any]] = []
    for row in grid:
        if row["row_kind"] != "system":
            continue
        status = row.get("geometry_status", "").strip()
        if status == "pass":
            continue
        nickname = row["nickname"].strip().lower()
        object_id = str(row["object_id"]).strip()
        system_z = number(row.get("system_z"))
        host_z = host_redshifts.get(nickname)
        flagged.append(
            {"nickname": nickname, "object_id": object_id, "reason": status}
        )
        if status == "invalid_foreground_redshift":
            result.require(
                system_z is None
                or system_z <= 0.0
                or host_z is None
                or system_z >= host_z,
                f"{nickname}/{object_id}: flagged as an invalid foreground redshift "
                f"but z={system_z} is a valid foreground value against host "
                f"z={host_z}",
            )
        elif status == "missing_sourced_geometry":
            result.require(
                number(row.get("mass_msun")) is None
                or number(row.get("radius_kpc")) is None,
                f"{nickname}/{object_id}: flagged as missing sourced geometry but "
                "carries both a mass and a radius",
            )
        else:
            result.failures.append(
                f"{nickname}/{object_id}: undeclared geometry status {status!r}"
            )
        result.require(
            not truthy(row.get("budget_eligible")),
            f"{nickname}/{object_id}: geometry flagged {status!r} but the system is "
            "still budget-eligible",
        )

    result.facts = {
        "redshiftless_candidate_rows": redshiftless,
        "diagnostic_only_sightlines": sorted(roster_without_redshift),
        "geometry_flagged_systems": flagged,
    }
    return result


# --------------------------------------------------------------------------
# check 3 - deterministic, auditable matching
# --------------------------------------------------------------------------


def check_deterministic_matching(data: Inputs) -> CheckResult:
    result = CheckResult(
        "deterministic_matching",
        "Matching and deduplication are deterministic and auditable",
    )

    # --- Figure 3 values reproduce canonically; approved bytes stay pinned -
    try:
        import pandas as pd

        from foregrounds.census.build_sightline_halo_grid_input import build_frame
    except Exception as error:  # pragma: no cover - import failure is a real failure
        result.failures.append(f"cannot import the Figure 3 input builder: {error}")
        return result

    def serialise(frame: Any) -> str:
        buffer = io.StringIO()
        frame.to_csv(
            buffer,
            index=False,
            lineterminator="\n",
            float_format=lambda value: format(value, ".15g"),
        )
        return buffer.getvalue()

    first = serialise(build_frame())
    second = serialise(build_frame())
    checked_frame = pd.read_csv(
        CENSUS / INPUT_PATHS["halo_grid"],
        dtype={"object_id": str},
    )
    checked_in = serialise(checked_frame)
    checked_path = CENSUS / INPUT_PATHS["halo_grid"]
    result.require(first == second, "two consecutive Figure 3 input builds differ")
    result.require(
        first == checked_in,
        "the committed Figure 3 input values do not reproduce from committed sources",
    )
    result.require(
        sha256_file(checked_path) == APPROVED_HALO_GRID_SHA256,
        "the approved Figure 3 input bytes have drifted",
    )

    # --- the deduplication rule is auditable ------------------------------
    coordinates = {
        candidate_key(row, "object_id"): (
            number(row.get("ra_deg")),
            number(row.get("dec_deg")),
        )
        for row in data["cross_references"]
    }
    by_object: dict[tuple[str, str], tuple[float | None, float | None]] = {}
    for (nickname, _type, obj), position in coordinates.items():
        by_object[(nickname, obj)] = position

    duplicate_pairs = 0
    for row in data["duplicates"]:
        nickname = row["nickname"].strip().lower()
        duplicate = str(row["duplicate_obj"]).strip()
        canonical = str(row["canonical_obj"]).strip()
        recorded = number(row.get("sep_arcsec"))
        result.require(
            bool(row.get("evidence", "").strip()),
            f"{nickname}/{duplicate}: deduplication has no recorded evidence",
        )
        left = by_object.get((nickname, duplicate))
        right = by_object.get((nickname, canonical))
        if left is None or right is None or None in left or None in right:
            result.failures.append(
                f"{nickname}: duplicate pair {duplicate}->{canonical} has no "
                "coordinates in the expanded catalog, so its separation cannot be "
                "reproduced"
            )
            continue
        duplicate_pairs += 1
        recomputed = angular_separation_arcsec(left[0], left[1], right[0], right[1])
        result.require(
            recorded is not None
            and abs(recomputed - recorded) <= SEPARATION_ABSOLUTE_TOLERANCE_ARCSEC,
            f"{nickname}: duplicate pair {duplicate}->{canonical} records "
            f"{recorded} arcsec but the coordinates give {recomputed:.4f} arcsec",
        )

    # --- every duplicate is actually removed, every canonical retained ----
    grid_keys = {
        (row["nickname"].strip().lower(), str(row["object_id"]).strip())
        for row in data["halo_grid"]
        if row["row_kind"] == "system"
    }
    confirmed = {
        (row["nickname"].strip().lower(), str(row["obj"]).strip())
        for row in data["registry"]
        if row.get("final_verdict", "").strip() == "confirmed"
    }
    duplicates = {
        (row["nickname"].strip().lower(), str(row["duplicate_obj"]).strip())
        for row in data["duplicates"]
    }
    canonicals = {
        (row["nickname"].strip().lower(), str(row["canonical_obj"]).strip())
        for row in data["duplicates"]
    }
    leaked = sorted(grid_keys & duplicates)
    result.require(
        not leaked,
        f"cross-listed duplicates survive into Figure 3: {leaked}",
    )
    dropped = sorted((confirmed - duplicates) - grid_keys)
    result.require(
        not dropped,
        f"confirmed non-duplicate systems are missing from Figure 3: {dropped}",
    )
    lost_canonicals = sorted((canonicals & confirmed) - grid_keys)
    result.require(
        not lost_canonicals,
        f"canonical members of a duplicate pair were dropped instead of kept: "
        f"{lost_canonicals}",
    )

    # --- cross-match results are paginated and ambiguity is visible -------
    surveys = ("gsc242", "allwise", "catwise2020", "unwise")
    audited = 0
    for row in data["cross_references"]:
        key = candidate_key(row, "object_id")
        for survey in surveys:
            status = row.get(f"{survey}_status", "").strip()
            if status == "ambiguous":
                # An ambiguous cross-match must show its ambiguity: at least two
                # candidates and the runner-up separation, so a reader can see
                # what was not adopted.
                audited += 1
                count = number(row.get(f"{survey}_candidate_count"))
                result.require(
                    count is not None and count >= 2,
                    f"{key[0]}/{key[2]}: {survey} is marked ambiguous but records "
                    f"{count} candidates",
                )
                result.require(
                    number(row.get(f"{survey}_second_separation_arcsec")) is not None,
                    f"{key[0]}/{key[2]}: {survey} is marked ambiguous but records no "
                    "runner-up separation",
                )
                continue
            if status != "matched":
                result.require(
                    status in {"unmatched", ""},
                    f"{key[0]}/{key[2]}: {survey} records undeclared match status "
                    f"{status!r}",
                )
                continue
            audited += 1
            separation = number(row.get(f"{survey}_separation_arcsec"))
            count = number(row.get(f"{survey}_candidate_count"))
            result.require(
                separation is not None,
                f"{key[0]}/{key[2]}: {survey} match records no separation",
            )
            result.require(
                count is not None and count >= 1,
                f"{key[0]}/{key[2]}: {survey} match records no candidate count, so "
                "the match cannot be audited for ambiguity",
            )
            result.require(
                bool(row.get(f"{survey}_snapshot_sha256", "").strip()),
                f"{key[0]}/{key[2]}: {survey} match has no response snapshot hash",
            )
            result.require(
                bool(row.get(f"{survey}_retrieved_at_utc", "").strip()),
                f"{key[0]}/{key[2]}: {survey} match has no retrieval timestamp",
            )
            second = number(row.get(f"{survey}_second_separation_arcsec"))
            if count is not None and count > 1:
                result.require(
                    second is not None,
                    f"{key[0]}/{key[2]}: {survey} returned {int(count)} candidates "
                    "but the runner-up separation is not recorded",
                )
                if second is not None and separation is not None:
                    result.require(
                        second >= separation,
                        f"{key[0]}/{key[2]}: {survey} runner-up separation "
                        f"{second} is closer than the adopted {separation}, so the "
                        "nearest match was not adopted",
                    )

    result.facts = {
        "figure3_input_rebuild_is_canonically_equivalent": first == checked_in,
        "figure3_input_comparison": (
            "canonical CSV values; approved checked-in bytes remain unchanged"
        ),
        "approved_figure3_input_sha256": APPROVED_HALO_GRID_SHA256,
        "duplicate_pairs_reproduced": duplicate_pairs,
        "cross_match_rows_audited": audited,
        "grid_system_rows": len(grid_keys),
        "confirmed_registry_rows": len(confirmed),
    }
    return result


# --------------------------------------------------------------------------
# check 4 - survey coverage
# --------------------------------------------------------------------------


def check_survey_coverage(data: Inputs) -> CheckResult:
    result = CheckResult(
        "survey_coverage",
        "Survey coverage is stated for every sightline and backed by a footprint",
    )

    coverage = data["survey_coverage"]
    roster = {row["nickname"].strip().lower(): row for row in data["bursts"]}
    surveys = sorted({row["survey"].strip() for row in coverage})
    nicknames = sorted({row["nickname"].strip().lower() for row in coverage})

    result.require(
        set(nicknames) == set(roster),
        f"coverage sightlines {nicknames} do not match the twelve-burst roster "
        f"{sorted(roster)}",
    )
    result.require(len(nicknames) == 12, f"expected 12 sightlines, found {len(nicknames)}")

    seen: set[tuple[str, str]] = set()
    footprint_hashes: dict[str, str] = {}
    for row in coverage:
        nickname = row["nickname"].strip().lower()
        survey = row["survey"].strip()
        pair = (nickname, survey)
        result.require(pair not in seen, f"{nickname}/{survey}: duplicate coverage row")
        seen.add(pair)

        burst = roster.get(nickname)
        if burst is not None:
            ra_deg, dec_deg = sexagesimal_to_degrees(row["ra"], row["dec"])
            roster_ra = number(burst.get("ra_deg"))
            roster_dec = number(burst.get("dec_deg"))
            result.require(
                roster_ra is not None
                and abs(ra_deg - roster_ra) <= COORDINATE_TOLERANCE_DEG,
                f"{nickname}/{survey}: coverage right ascension {ra_deg:.9f} deg "
                f"disagrees with the roster {roster_ra}",
            )
            result.require(
                roster_dec is not None
                and abs(dec_deg - roster_dec) <= COORDINATE_TOLERANCE_DEG,
                f"{nickname}/{survey}: coverage declination {dec_deg:.9f} deg "
                f"disagrees with the roster {roster_dec}",
            )

        status = row["footprint_status"].strip()
        result.require(
            status in {"covered", "not_covered"},
            f"{nickname}/{survey}: footprint status {status!r} is neither covered "
            "nor not_covered",
        )
        result.require(
            bool(row.get("release", "").strip()),
            f"{nickname}/{survey}: no survey release is recorded",
        )
        source = row.get("footprint_source", "").strip()
        recorded_hash = row.get("footprint_sha256", "").strip()
        result.require(
            bool(source),
            f"{nickname}/{survey}: coverage claim has no footprint source",
        )
        if recorded_hash:
            footprint = CENSUS.parent / source
            if not footprint.is_file():
                result.failures.append(
                    f"{nickname}/{survey}: footprint file {source} is missing"
                )
            else:
                actual = sha256_file(footprint)
                footprint_hashes[source] = actual
                result.require(
                    actual == recorded_hash,
                    f"{nickname}/{survey}: footprint {source} hashes to {actual[:16]}, "
                    f"not the recorded {recorded_hash[:16]}",
                )
        else:
            result.require(
                source in {"all_sky_contract", "unavailable"},
                f"{nickname}/{survey}: footprint source {source!r} names a file but "
                "records no hash",
            )

    expected_pairs = len(nicknames) * len(surveys)
    result.require(
        len(coverage) == expected_pairs,
        f"coverage table has {len(coverage)} rows, not the {expected_pairs} required "
        f"for {len(nicknames)} sightlines across {len(surveys)} surveys",
    )

    # A sightline that yields no candidate must be explained: either no survey
    # with a real footprint covers it, or it is covered and genuinely empty.
    with_candidates = {row["nickname"].strip().lower() for row in data["registry"]}
    unsearched: list[str] = []
    for nickname in nicknames:
        if nickname in with_candidates:
            continue
        covered = [
            row["survey"].strip()
            for row in coverage
            if row["nickname"].strip().lower() == nickname
            and row["footprint_status"].strip() == "covered"
        ]
        result.require(
            bool(covered),
            f"{nickname}: no candidates and no covered survey - the sightline was "
            "never searched",
        )
        unsearched.append(nickname)

    result.facts = {
        "surveys": surveys,
        "sightlines": len(nicknames),
        "coverage_rows": len(coverage),
        "footprint_files_verified": sorted(footprint_hashes),
        "sightlines_without_candidates": unsearched,
    }
    return result


# --------------------------------------------------------------------------
# check 5 - mass and radius conventions
# --------------------------------------------------------------------------


def check_mass_radius_conventions(data: Inputs) -> CheckResult:
    result = CheckResult(
        "mass_radius_conventions",
        "Halo and cluster mass and radius definitions are explicit and never mixed",
    )

    try:
        import astropy.units as u
        from astropy.cosmology import Planck18
    except Exception as error:  # pragma: no cover
        result.failures.append(f"cannot load the declared cosmology: {error}")
        return result

    halo_radii_reproduced = 0
    cluster_rows = 0
    for row in data["cross_references"]:
        key = candidate_key(row, "object_id")
        kind = row["type"].strip()
        if kind == "halo":
            result.require(
                row.get("m200c_units", "").strip() == "Msun",
                f"{key[0]}/{key[2]}: halo mass units are "
                f"{row.get('m200c_units')!r}, not solar masses",
            )
            result.require(
                row.get("r200c_units", "").strip() == "proper_kpc",
                f"{key[0]}/{key[2]}: halo radius units are "
                f"{row.get('r200c_units')!r}, not proper kiloparsecs",
            )
            result.require(
                row.get("m200c_method", "").strip() == HALO_MASS_METHOD,
                f"{key[0]}/{key[2]}: halo mass method is "
                f"{row.get('m200c_method')!r}, not the declared {HALO_MASS_METHOD!r}",
            )
            result.require(
                row.get("r200c_method", "").strip() == HALO_RADIUS_METHOD,
                f"{key[0]}/{key[2]}: halo radius method is "
                f"{row.get('r200c_method')!r}, not the declared {HALO_RADIUS_METHOD!r}",
            )
            mass = number(row.get("m200c_msun"))
            radius = number(row.get("r200c_kpc"))
            redshift = number(row.get("best_z"))
            status = row.get("m200c_status", "").strip()
            if mass is None or radius is None:
                result.require(
                    status == "unavailable",
                    f"{key[0]}/{key[2]}: halo has no mass or radius but its status "
                    f"is {status!r} rather than unavailable",
                )
                continue
            result.require(
                redshift is not None,
                f"{key[0]}/{key[2]}: halo carries a mass and radius but no redshift",
            )
            if redshift is None:
                continue
            critical = Planck18.critical_density(redshift).to(u.Msun / u.kpc**3).value
            expected = (3.0 * mass / (4.0 * math.pi * HALO_OVERDENSITY * critical)) ** (
                1.0 / 3.0
            )
            relative = abs(expected - radius) / radius
            result.require(
                relative <= RADIUS_RELATIVE_TOLERANCE,
                f"{key[0]}/{key[2]}: stored R200c {radius:.3f} kpc does not "
                f"reproduce from M200c under 200 times the critical density "
                f"(recomputed {expected:.3f} kpc, {relative:.2%} apart)",
            )
            halo_radii_reproduced += 1
            impact = number(row.get("impact_kpc"))
            ratio = number(row.get("b_over_r200c"))
            if impact is not None and ratio is not None:
                expected_ratio = impact / radius
                result.require(
                    abs(expected_ratio - ratio) <= RATIO_RELATIVE_TOLERANCE
                    * max(1.0, abs(ratio)),
                    f"{key[0]}/{key[2]}: recorded impact-to-radius ratio {ratio} "
                    f"does not equal impact/R200c ({expected_ratio})",
                )
        elif kind == "cluster":
            cluster_rows += 1
            for column in ("m200c_status", "r200c_status", "adopted_mass_status"):
                result.require(
                    row.get(column, "").strip() == CLUSTER_NOT_APPLICABLE,
                    f"{key[0]}/{key[2]}: cluster row records {column}="
                    f"{row.get(column)!r} instead of declaring the halo convention "
                    "inapplicable",
                )
            result.require(
                row.get("adopted_mass_authority", "").strip()
                == "cluster_catalog_M500_R500",
                f"{key[0]}/{key[2]}: cluster mass authority is "
                f"{row.get('adopted_mass_authority')!r}, not the catalog M500/R500",
            )
            result.require(
                number(row.get("m200c_msun")) is None
                and number(row.get("r200c_kpc")) is None,
                f"{key[0]}/{key[2]}: cluster row carries halo-convention mass or "
                "radius values, mixing the two conventions",
            )
        else:
            result.failures.append(f"{key[0]}/{key[2]}: unknown system type {kind!r}")

    # --- the Figure 3 rows carry the same conventions ---------------------
    cross_reference = {
        candidate_key(row, "object_id"): row for row in data["cross_references"]
    }
    grid_halo = grid_cluster = 0
    for row in data["halo_grid"]:
        if row["row_kind"] != "system":
            result.require(
                not row.get("radius_definition", "").strip(),
                f"{row['nickname']}: a non-system Figure 3 row declares a radius "
                "definition",
            )
            continue
        key = (
            row["nickname"].strip().lower(),
            row["system_type"].strip(),
            str(row["object_id"]).strip(),
        )
        source = cross_reference.get(key)
        if source is None:
            result.failures.append(
                f"{key[0]}/{key[2]}: Figure 3 row has no expanded-catalog source row"
            )
            continue
        definition = row.get("radius_definition", "").strip()
        mass = number(row.get("mass_msun"))
        radius = number(row.get("radius_kpc"))
        # A row whose geometry did not pass carries no mass or radius by design;
        # check 6 asserts that it is blank and that the reason is recorded. The
        # convention assertions below apply to drawn geometry only.
        if row.get("geometry_status", "").strip() != "pass":
            result.require(
                mass is None and radius is None,
                f"{key[0]}/{key[2]}: geometry did not pass but a mass or radius is "
                "still declared",
            )
            continue
        if key[1] == "halo":
            grid_halo += 1
            result.require(
                definition == HALO_RADIUS_DEFINITION,
                f"{key[0]}/{key[2]}: halo drawn with radius definition "
                f"{definition!r}",
            )
            result.require(
                mass is not None
                and abs(mass - (number(source.get("m200c_msun")) or math.nan)) <= 1.0,
                f"{key[0]}/{key[2]}: Figure 3 halo mass does not match the catalog "
                "M200c",
            )
            result.require(
                radius is not None
                and abs(radius - (number(source.get("r200c_kpc")) or math.nan)) <= 1e-6,
                f"{key[0]}/{key[2]}: Figure 3 halo radius does not match the catalog "
                "R200c",
            )
        else:
            grid_cluster += 1
            result.require(
                definition == CLUSTER_RADIUS_DEFINITION,
                f"{key[0]}/{key[2]}: cluster drawn with radius definition "
                f"{definition!r}",
            )
            catalog_mass = number(source.get("m500_1e14msun"))
            catalog_radius = number(source.get("r500_mpc"))
            if catalog_mass is not None:
                expected = catalog_mass * 1.0e14
                result.require(
                    mass is not None and abs(mass - expected) <= 1.0,
                    f"{key[0]}/{key[2]}: Figure 3 cluster mass {mass} is not the "
                    f"catalog M500 in solar masses ({expected})",
                )
            if catalog_radius is not None:
                expected = catalog_radius * 1.0e3
                result.require(
                    radius is not None and abs(radius - expected) <= 1e-6,
                    f"{key[0]}/{key[2]}: Figure 3 cluster radius {radius} kpc is not "
                    f"the catalog R500 in kiloparsecs ({expected})",
                )

    definitions = {
        row["radius_definition"].strip()
        for row in data["halo_grid"]
        if row["row_kind"] == "system" and row.get("geometry_status", "").strip() == "pass"
    }
    result.require(
        definitions <= {HALO_RADIUS_DEFINITION, CLUSTER_RADIUS_DEFINITION},
        f"Figure 3 uses undeclared radius definitions: {sorted(definitions)}",
    )

    result.facts = {
        "halo_radii_reproduced_from_mass": halo_radii_reproduced,
        "cluster_rows_checked": cluster_rows,
        "figure3_halo_rows": grid_halo,
        "figure3_cluster_rows": grid_cluster,
        "radius_definitions_used": sorted(definitions),
        "halo_overdensity": HALO_OVERDENSITY,
        "cosmology": "Planck18",
    }
    return result


# --------------------------------------------------------------------------
# check 6 - the census and the installed Figure 3 agree
# --------------------------------------------------------------------------


def _pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:  # pragma: no cover
        from PyPDF2 import PdfReader  # type: ignore[no-redef]
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() for page in reader.pages)


def check_census_matches_figure3(
    data: Inputs, *, figure: Path, render: bool = True
) -> CheckResult:
    result = CheckResult(
        "census_matches_figure3",
        "The twelve-sightline census and the installed Figure 3 describe the same "
        "systems",
    )

    grid = data["halo_grid"]
    roster = {row["nickname"].strip().lower(): row for row in data["bursts"]}
    hosts = [row for row in grid if row["row_kind"] == "host"]
    systems = [row for row in grid if row["row_kind"] == "system"]

    result.require(
        len(hosts) == 12,
        f"Figure 3 draws {len(hosts)} sightline panels, not twelve",
    )
    result.require(
        {row["nickname"].strip().lower() for row in hosts} == set(roster),
        "the Figure 3 sightline roster does not match the twelve-burst roster",
    )

    for row in hosts:
        nickname = row["nickname"].strip().lower()
        burst = roster.get(nickname)
        if burst is None:
            continue
        result.require(
            row["frb_name"].strip() == burst["tns"].strip(),
            f"{nickname}: Figure 3 labels the burst {row['frb_name']!r}, the roster "
            f"says {burst['tns']!r}",
        )
        for column, roster_column in (
            ("frb_ra_deg", "ra_deg"),
            ("frb_dec_deg", "dec_deg"),
        ):
            drawn = number(row.get(column))
            expected = number(burst.get(roster_column))
            result.require(
                drawn is not None
                and expected is not None
                and abs(drawn - expected) <= COORDINATE_TOLERANCE_DEG,
                f"{nickname}: Figure 3 {column} {drawn} disagrees with the roster "
                f"{expected}",
            )
        drawn_z = number(row.get("frb_z"))
        roster_z = number(burst.get("z_spec"))
        result.require(
            (drawn_z is None and roster_z is None)
            or (
                drawn_z is not None
                and roster_z is not None
                and abs(drawn_z - roster_z) <= REDSHIFT_ABSOLUTE_TOLERANCE
            ),
            f"{nickname}: Figure 3 host redshift {drawn_z} disagrees with the roster "
            f"{roster_z}",
        )

    # --- every drawn system is a confirmed, non-duplicate census system ---
    confirmed = {
        (row["nickname"].strip().lower(), str(row["obj"]).strip()): row
        for row in data["registry"]
        if row.get("final_verdict", "").strip() == "confirmed"
    }
    duplicates = {
        (row["nickname"].strip().lower(), str(row["duplicate_obj"]).strip())
        for row in data["duplicates"]
    }
    for row in systems:
        key = (row["nickname"].strip().lower(), str(row["object_id"]).strip())
        source = confirmed.get(key)
        if source is None:
            result.failures.append(
                f"{key[0]}/{key[1]}: drawn in Figure 3 but not confirmed in the census"
            )
            continue
        result.require(
            key not in duplicates,
            f"{key[0]}/{key[1]}: drawn in Figure 3 despite being a cross-listed "
            "duplicate",
        )
        result.require(
            row["system_type"].strip() == source["type"].strip(),
            f"{key[0]}/{key[1]}: Figure 3 draws a {row['system_type']} where the "
            f"census records a {source['type']}",
        )
        drawn_z = number(row.get("system_z"))
        census_z = number(source.get("best_z"))
        result.require(
            drawn_z is not None
            and census_z is not None
            and abs(drawn_z - census_z) <= REDSHIFT_ABSOLUTE_TOLERANCE,
            f"{key[0]}/{key[1]}: Figure 3 system redshift {drawn_z} disagrees with "
            f"the census {census_z}",
        )
        drawn_b = number(row.get("impact_kpc"))
        census_b = number(source.get("impact_kpc"))
        result.require(
            drawn_b is not None
            and census_b is not None
            and abs(drawn_b - census_b) <= 1.0e-6,
            f"{key[0]}/{key[1]}: Figure 3 impact parameter {drawn_b} disagrees with "
            f"the census {census_b}",
        )
        # A drawn system whose geometry did not pass must say so rather than
        # appear as an ordinary measurement.
        status = row.get("geometry_status", "").strip()
        result.require(
            status in {"pass", "invalid_foreground_redshift", "missing_sourced_geometry"},
            f"{key[0]}/{key[1]}: undeclared geometry status {status!r}",
        )
        if status != "pass":
            result.require(
                number(row.get("mass_msun")) is None
                and number(row.get("radius_kpc")) is None,
                f"{key[0]}/{key[1]}: geometry status {status!r} but a mass or radius "
                "is still drawn",
            )

    missing = sorted((set(confirmed) - duplicates) - {
        (row["nickname"].strip().lower(), str(row["object_id"]).strip())
        for row in systems
    })
    result.require(
        not missing,
        f"confirmed census systems absent from Figure 3: {missing}",
    )

    # The census carries twelve sightlines but the figure draws only those with
    # an established host redshift: without one, neither the host marker nor the
    # foreground cut can be placed. Assert that the omission is exactly that
    # rule, so a silently dropped panel cannot hide behind it.
    drawn_panels = {
        row["nickname"].strip().lower()
        for row in hosts
        if number(row.get("frb_z")) is not None
    }
    established = {
        burst["nickname"].strip().lower()
        for burst in data["bursts"]
        if number(burst.get("z_spec")) is not None
    }
    result.require(
        drawn_panels == established,
        f"Figure 3 draws panels for {sorted(drawn_panels)} but the sightlines with "
        f"an established host redshift are {sorted(established)}",
    )
    drawn_systems = [
        row
        for row in systems
        if row.get("geometry_status", "").strip() == "pass"
        and number(row.get("system_z")) is not None
        and number(row.get("impact_kpc")) is not None
        and number(row.get("mass_msun")) is not None
        and number(row.get("radius_kpc")) is not None
    ]
    result.require(
        {row["nickname"].strip().lower() for row in drawn_systems} <= drawn_panels,
        "a foreground system is drawn on a sightline that has no panel",
    )

    # --- the installed figure carries this content ------------------------
    rendered_matches: bool | None = None
    render_note = ""
    local_render_sha256: str | None = None
    if not render:
        render_note = "rendering comparison skipped by caller"
    elif not figure.is_file():
        result.failures.append(f"installed Figure 3 is missing at {figure}")
    else:
        with tempfile.TemporaryDirectory(prefix="fig3-census-") as tmp:
            out = Path(tmp)
            first = out / "a"
            second = out / "b"
            command = [
                sys.executable,
                "-m",
                "foregrounds.visualization.sightline_halo_grid",
                "--halo-csv",
                str(CENSUS / INPUT_PATHS["halo_grid"]),
                "--out-dir",
            ]
            renders: list[Path] = []
            for target in (first, second):
                run = subprocess.run(
                    [*command, str(target)],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                pdf = target / "sightline_halo_grid.pdf"
                if run.returncode or not pdf.is_file():
                    result.failures.append(
                        f"Figure 3 did not regenerate from the committed input: "
                        f"{run.stderr.strip()[:400]}"
                    )
                    renders = []
                    break
                renders.append(pdf)
            if len(renders) == 2:
                digests = [sha256_file(pdf) for pdf in renders]
                result.require(
                    digests[0] == digests[1],
                    "Figure 3 does not render deterministically from its committed "
                    "input",
                )
                installed_text = _pdf_text(figure)
                rendered_text = _pdf_text(renders[0])
                rendered_matches = installed_text == rendered_text
                result.require(
                    rendered_matches,
                    "the installed Figure 3 does not carry the same content as a "
                    "fresh render of the committed census",
                )
                local_render_sha256 = digests[0]
                if digests[0] != sha256_file(figure):
                    render_note = (
                        "installed bytes differ from the local render; the extracted "
                        "content is identical, so the difference is renderer "
                        "version, not science"
                    )

    # If the producing render is still on disk, the installed figure can be tied
    # to it byte for byte, which is a stronger statement than content equality
    # against a re-render on a different renderer version.
    staged_matches: bool | None = None
    if figure.is_file() and STAGED_FIGURE.is_file():
        staged_matches = sha256_file(STAGED_FIGURE) == sha256_file(figure)
        result.require(
            staged_matches,
            "the staged Figure 3 render and the installed manuscript figure are "
            "different bytes, so the installed figure is not the one the figure "
            "workflow produced",
        )

    try:
        import matplotlib

        renderer = f"matplotlib {matplotlib.__version__}"
    except Exception:  # pragma: no cover
        renderer = "unknown"

    try:
        display_path = str(figure.relative_to(ROOT.parent))
    except ValueError:
        display_path = str(figure)

    result.facts = {
        "figure3_host_rows": len(hosts),
        "figure3_system_rows": len(systems),
        "figure3_panels_drawn": sorted(drawn_panels),
        "figure3_systems_drawn": len(drawn_systems),
        "panels_omitted_for_lack_of_a_host_redshift": sorted(
            {row["nickname"].strip().lower() for row in hosts} - drawn_panels
        ),
        "confirmed_census_systems_after_deduplication": len(set(confirmed) - duplicates),
        "installed_figure3": display_path,
        "installed_figure3_sha256": sha256_file(figure) if figure.is_file() else None,
        "local_render_sha256": local_render_sha256,
        "local_renderer": renderer,
        "staged_render": str(STAGED_FIGURE.relative_to(ROOT)) if STAGED_FIGURE.is_file() else None,
        "installed_matches_staged_render_byte_for_byte": staged_matches,
        "installed_content_matches_fresh_render": rendered_matches,
        "byte_note": render_note,
    }
    return result


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------


CHECKS: dict[str, Callable[..., CheckResult]] = {
    "sourced_redshifts": check_sourced_redshifts,
    "hostless_fail_closed": check_hostless_fail_closed,
    "deterministic_matching": check_deterministic_matching,
    "survey_coverage": check_survey_coverage,
    "mass_radius_conventions": check_mass_radius_conventions,
    "census_matches_figure3": check_census_matches_figure3,
}


def run(
    *,
    figure: Path = MANUSCRIPT_FIGURE,
    only: Sequence[str] | None = None,
    render: bool = True,
) -> dict[str, Any]:
    data = Inputs.load()
    selected = list(only) if only else list(CHECKS)
    results: list[CheckResult] = []
    for name in selected:
        function = CHECKS[name]
        if name == "census_matches_figure3":
            results.append(function(data, figure=figure, render=render))
        else:
            results.append(function(data))

    return {
        "schema_version": 1,
        "artifact": "foreground_census_analysis_only_validation",
        "scope": "analysis/ only; no pipeline repository or external submodule is read",
        "status": "passed" if all(r.passed for r in results) else "failed",
        "input_sha256": data.hashes,
        "checks": [
            {
                "id": r.name,
                "title": r.title,
                "status": "passed" if r.passed else "failed",
                "failures": r.failures,
                "facts": r.facts,
            }
            for r in results
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--figure",
        type=Path,
        default=MANUSCRIPT_FIGURE,
        help="installed manuscript Figure 3 to compare against",
    )
    parser.add_argument(
        "--check",
        action="append",
        choices=sorted(CHECKS),
        help="run only the named check (repeatable)",
    )
    parser.add_argument("--output", type=Path, help="write the JSON receipt here")
    parser.add_argument(
        "--skip-render",
        action="store_true",
        help="skip regenerating Figure 3 (leaves the installed figure unchecked)",
    )
    args = parser.parse_args(argv)

    report = run(
        figure=args.figure.resolve(), only=args.check, render=not args.skip_render
    )

    for check in report["checks"]:
        marker = "PASS" if check["status"] == "passed" else "FAIL"
        print(f"[{marker}] {check['id']}: {check['title']}")
        for failure in check["failures"]:
            print(f"       - {failure}")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"receipt: {args.output}")

    print(f"status: {report['status']}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
