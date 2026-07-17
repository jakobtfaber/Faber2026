#!/usr/bin/env python3
"""Build the manuscript CHIME scintillation gate table from pinned FLITS JSON.

The builder is deliberately fail closed: it accepts only the reviewed PR #192
campaign shape and status contract.  A changed campaign must be adjudicated
explicitly rather than silently changing manuscript claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "pipeline"
CAMPAIGN = PIPELINE / "analysis/window-tuning-campaign-2026-07-17/results"
TABLE_PATH = ROOT / "chime_scintillation_campaign_table.tex"
PROVENANCE_PATH = ROOT / "analysis/scintillation-summary/campaign_provenance.json"
EXPECTED_PIPELINE = "17d9d26675702e9f8917da655621bef3231f0ddb"
EXPECTED_MEASUREMENT = "chromatica_hi"

BURSTS = (
    ("zach", "FRB~20220207C"),
    ("whitney", "FRB~20220310F"),
    ("oran", "FRB~20220506D"),
    ("isha", "FRB~20221113A"),
    ("wilhelm", "FRB~20221203A"),
    ("phineas", "FRB~20230307A"),
    ("freya", "FRB~20230325A"),
    ("johndoeII", "FRB~20230814B"),
    ("hamilton", "FRB~20230913A"),
    ("mahi", "FRB~20240122A"),
    ("chromatica", "FRB~20240203A"),
    ("casey", "FRB~20240229A"),
)

CHECK_LABELS = {
    "off_pulse_null": "off-pulse null",
    "low_lag_stability": "low-lag stability",
    "subband_support": "sub-band support",
}

TABLE_CODES = {
    "off-pulse null": "OP",
    "low-lag stability": "LL",
    "sub-band support": "SB",
    "unphysical within-band slope": r"$\alpha$",
    "figure morphology": "FM",
}


@dataclass(frozen=True)
class Campaign:
    validation: dict
    records: dict[str, dict]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def pipeline_revision() -> str:
    return subprocess.check_output(
        ["git", "-C", str(PIPELINE), "rev-parse", "HEAD"], text=True
    ).strip()


def load_campaign(campaign_dir: Path = CAMPAIGN) -> Campaign:
    validation = json.loads((campaign_dir / "validation.json").read_text())
    records = {
        record["name"]: record
        for line in (campaign_dir / "campaign_results.jsonl").read_text().splitlines()
        if line.strip()
        for record in (json.loads(line),)
    }

    if validation.get("status") != "closed":
        raise ValueError("campaign validation is not closed")
    if validation.get("injection_gate") != "pass":
        raise ValueError("campaign injection gate did not pass")
    if validation.get("n_records") != 24 or len(records) != 24:
        raise ValueError("expected exactly 24 standard/high-resolution records")
    if validation.get("n_measurements") != 1:
        raise ValueError("expected exactly one promoted measurement")

    expected_names = {name for nick, _ in BURSTS for name in (nick, f"{nick}_hi")}
    if set(records) != expected_names:
        raise ValueError("campaign record roster differs from the twelve-burst contract")

    measurements = [
        record for record in records.values() if record.get("science_status") == "measurement"
    ]
    if [record["name"] for record in measurements] != [EXPECTED_MEASUREMENT]:
        raise ValueError("promoted measurement differs from reviewed chromatica_hi record")
    measurement = measurements[0]
    if measurement.get("artifact_validation_status") != "pass":
        raise ValueError("chromatica_hi artifact validation is not a pass")
    if measurement.get("figure_review_status") != "pass":
        raise ValueError("chromatica_hi upstream figure review is not a pass")
    if len([row for row in measurement.get("subbands", []) if row.get("resolved")]) != 4:
        raise ValueError("chromatica_hi no longer has four resolved subbands")
    return Campaign(validation=validation, records=records)


def diagnostic_reasons(records: tuple[dict, dict]) -> list[str]:
    reasons: set[str] = set()
    for record in records:
        failed = record.get("artifact_controls", {}).get("failed_checks", [])
        reasons.update(CHECK_LABELS.get(name, name.replace("_", " ")) for name in failed)
        if record.get("figure_review_status") != "pass":
            reasons.add("figure morphology")
        if record.get("alpha_unphysical"):
            reasons.add("unphysical within-band slope")
    if not reasons:
        raise ValueError("diagnostic-only burst has no recorded gating reason")
    order = (
        "off-pulse null",
        "low-lag stability",
        "sub-band support",
        "unphysical within-band slope",
        "figure morphology",
    )
    return [reason for reason in order if reason in reasons] + sorted(reasons - set(order))


def table_text(campaign: Campaign) -> str:
    rows: list[str] = []
    for nick, tns in BURSTS:
        standard = campaign.records[nick]
        high_resolution = campaign.records[f"{nick}_hi"]
        measurement = next(
            (
                record
                for record in (standard, high_resolution)
                if record.get("science_status") == "measurement"
            ),
            None,
        )
        if measurement is not None:
            status = "qualified (high resolution)"
            evidence = "all qualification gates pass"
        else:
            status = "diagnostic only"
            evidence = ", ".join(
                TABLE_CODES[reason]
                for reason in diagnostic_reasons((standard, high_resolution))
            )
        rows.append(f"{tns} & {status} & {evidence} \\\\")

    return "\n".join(
        [
            "% Generated by scripts/build_scintillation_campaign_summary.py.",
            "% Source: pinned dsa110-FLITS PR #192 campaign JSON; do not hand-edit.",
            "\\begin{deluxetable*}{lll}",
            "\\tablecaption{CHIME-band objective-window campaign outcomes for the standard and high-resolution products. FRB~20240203A is the only qualified sightline; its high-resolution record passes the injection, artifact, support, and upstream figure gates. The other 23 product records remain diagnostic only. An inconclusive control is fail-closed.\\label{tab:chime_scint_gates}}",
            "\\tabletypesize{\\scriptsize}",
            "\\tablehead{\\colhead{FRB} & \\colhead{Campaign status} & \\colhead{Decisive qualification evidence}}",
            "\\startdata",
            *rows,
            "\\enddata",
            "\\tablecomments{Diagnostic codes are the union of decisive standard/high-resolution gates: OP = off-pulse null; LL = low-lag stability; SB = sub-band support; $\\alpha$ = unphysical within-band slope; FM = figure morphology.}",
            "\\end{deluxetable*}",
            "",
        ]
    )


def provenance(table: str) -> dict:
    inputs = (
        CAMPAIGN / "validation.json",
        CAMPAIGN / "campaign_results.jsonl",
        CAMPAIGN / "injection_recovery.json",
        CAMPAIGN / "figures.review.json",
    )
    return {
        "campaign": "CHIME objective-window scintillation campaign",
        "campaign_status": "closed",
        "command": (
            "env -i HOME=/Users/jakobfaber "
            "PATH=/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin "
            "/opt/anaconda3/bin/conda run -n py312 python "
            "scripts/build_scintillation_campaign_summary.py"
        ),
        "expected_measurement": EXPECTED_MEASUREMENT,
        "generator_sha256": sha256(Path(__file__)),
        "inputs": [
            {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)} for path in inputs
        ],
        "output": {
            "path": str(TABLE_PATH.relative_to(ROOT)),
            "sha256": hashlib.sha256(table.encode()).hexdigest(),
        },
        "parent_base_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "pipeline_revision": pipeline_revision(),
        "python": sys.version.split()[0],
        "recorded_date": "2026-07-17",
    }


def write_outputs(check: bool = False) -> None:
    revision = pipeline_revision()
    if revision != EXPECTED_PIPELINE:
        raise ValueError(f"pipeline pin {revision} != reviewed {EXPECTED_PIPELINE}")
    campaign = load_campaign()
    table = table_text(campaign)
    record = json.dumps(provenance(table), indent=2, sort_keys=True) + "\n"

    if check:
        if TABLE_PATH.read_text() != table:
            raise ValueError(f"stale generated table: {TABLE_PATH.relative_to(ROOT)}")
        current = json.loads(PROVENANCE_PATH.read_text())
        expected = json.loads(record)
        # The branch HEAD changes when generated outputs are committed; the
        # recorded base revision is provenance, not a regeneration equality key.
        expected["parent_base_revision"] = current.get("parent_base_revision")
        if current != expected:
            raise ValueError(f"stale provenance: {PROVENANCE_PATH.relative_to(ROOT)}")
        return

    TABLE_PATH.write_text(table, encoding="utf-8")
    PROVENANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_PATH.write_text(record, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify generated outputs")
    args = parser.parse_args()
    write_outputs(check=args.check)


if __name__ == "__main__":
    main()
