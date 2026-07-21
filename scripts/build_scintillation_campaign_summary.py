#!/usr/bin/env python3
"""Build the manuscript CHIME scintillation gate table from reviewed FLITS JSON.

The builder is deliberately fail closed: it accepts only the reviewed PR #192
campaign snapshot and status contract.  The pipeline pin may advance, but it
must contain that reviewed commit.  Later files at the same paths cannot
silently change manuscript claims.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "pipeline"
CAMPAIGN_RELATIVE = Path("analysis/window-tuning-campaign-2026-07-17/results")
CAMPAIGN = PIPELINE / CAMPAIGN_RELATIVE
TABLE_PATH = ROOT / "chime_scintillation_campaign_table.tex"
PROVENANCE_PATH = ROOT / "analysis/scintillation-summary/campaign_provenance.json"
FIGURE_PROVENANCE_PATH = ROOT / "analysis/scintillation-summary/joint_figure_provenance.json"
DSA_VALIDATION_RELATIVE = Path(
    "analysis/scintillation-dsa-lorentzian-2026-07-07/results/"
    "oran_qualified/validation.json"
)
DSA_VALIDATION = PIPELINE / DSA_VALIDATION_RELATIVE
REVIEWED_PIPELINE = "17d9d26675702e9f8917da655621bef3231f0ddb"
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


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def pipeline_revision() -> str:
    return subprocess.check_output(
        ["git", "-C", str(PIPELINE), "rev-parse", "HEAD"], text=True
    ).strip()


def pipeline_contains_reviewed_campaign() -> bool:
    return subprocess.run(
        [
            "git",
            "-C",
            str(PIPELINE),
            "merge-base",
            "--is-ancestor",
            REVIEWED_PIPELINE,
            "HEAD",
        ],
        check=False,
    ).returncode == 0


def reviewed_blob(path: Path) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(PIPELINE), "show", f"{REVIEWED_PIPELINE}:{path.as_posix()}"]
    )


def load_campaign(campaign_dir: Path | None = None) -> Campaign:
    if campaign_dir is None:
        validation_text = reviewed_blob(CAMPAIGN_RELATIVE / "validation.json").decode()
        records_text = reviewed_blob(CAMPAIGN_RELATIVE / "campaign_results.jsonl").decode()
    else:
        validation_text = (campaign_dir / "validation.json").read_text()
        records_text = (campaign_dir / "campaign_results.jsonl").read_text()

    validation = json.loads(validation_text)
    records = {
        record["name"]: record
        for line in records_text.splitlines()
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


def load_dsa_measurement(path: Path | None = None) -> dict:
    if path is None:
        record = json.loads(reviewed_blob(DSA_VALIDATION_RELATIVE))
    else:
        record = json.loads(path.read_text())
    gates = record.get("gates", {})
    required = (
        "calibrated_interval",
        "fit_window_stability",
        "independent_offpulse_null",
        "low_lag_stability",
    )
    if any(gates.get(name, {}).get("pass") is not True for name in required):
        raise ValueError("Oran DSA qualification gates no longer all pass")
    measurement = record.get("calibrated_measurement", {})
    interval = measurement.get("confidence_interval_68_mhz", [])
    if len(interval) != 2 or not interval[0] < measurement.get("dnu_mhz", 0) < interval[1]:
        raise ValueError("Oran DSA calibrated interval is missing or inconsistent")
    return record


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
        CAMPAIGN_RELATIVE / "validation.json",
        CAMPAIGN_RELATIVE / "campaign_results.jsonl",
        CAMPAIGN_RELATIVE / "injection_recovery.json",
        CAMPAIGN_RELATIVE / "figures.review.json",
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
            {
                "path": str(Path("pipeline") / path),
                "sha256": sha256_bytes(reviewed_blob(path)),
            }
            for path in inputs
        ],
        "output": {
            "path": str(TABLE_PATH.relative_to(ROOT)),
            "sha256": hashlib.sha256(table.encode()).hexdigest(),
        },
        "parent_base_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "pipeline_revision": pipeline_revision(),
        "source_revision": REVIEWED_PIPELINE,
        "python": sys.version.split()[0],
        "recorded_date": "2026-07-17",
    }


def total_chime_error(row: dict) -> float:
    return math.sqrt(
        row["gamma_err"] ** 2
        + row["gamma_win_sys"] ** 2
        + row["gamma_scintle_err"] ** 2
    )


def render_joint_figure(candidate_root: Path) -> Path:
    import matplotlib.pyplot as plt
    import numpy as np

    if not pipeline_contains_reviewed_campaign():
        raise ValueError("pipeline pin does not contain the reviewed PR #192 campaign")
    campaign = load_campaign()
    dsa = load_dsa_measurement()
    chime = campaign.records[EXPECTED_MEASUREMENT]
    subbands = [row for row in chime["subbands"] if row.get("resolved")]

    output = candidate_root / "figures/dsa_lorentzian_summary.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    with plt.rc_context(fname=PIPELINE / "matplotlibrc"):
        figure, axes = plt.subplots(1, 2, figsize=(9.0, 3.8), constrained_layout=True)
        left, right = axes

        dsa_measurement = dsa["calibrated_measurement"]
        dsa_value = dsa_measurement["dnu_mhz"]
        dsa_low, dsa_high = dsa_measurement["confidence_interval_68_mhz"]
        left.errorbar(
            [dsa["center_frequency_mhz"]],
            [dsa_value],
            yerr=[[dsa_value - dsa_low], [dsa_high - dsa_value]],
            fmt="o",
            color="tab:blue",
            capsize=4,
            markersize=7,
        )
        left.set_xlim(1200, 1450)
        left.set_ylim(0, 0.82)
        left.set_xlabel(r"$\nu_{\rm c}$ (MHz)")
        left.set_ylabel(r"$\gamma \equiv \Delta\nu_{\rm d}$ (MHz)")
        left.text(0.04, 0.94, "(a) DSA-110, FRB 20220506D", transform=left.transAxes, va="top")
        left.text(
            0.04,
            0.08,
            "injection calibrated\n68% interval",
            transform=left.transAxes,
            fontsize=11,
        )

        frequencies = np.array([row["center_mhz"] for row in subbands])
        widths = np.array([row["gamma"] for row in subbands])
        errors = np.array([total_chime_error(row) for row in subbands])
        order = np.argsort(frequencies)
        frequencies, widths, errors = frequencies[order], widths[order], errors[order]
        right.errorbar(
            frequencies,
            widths,
            yerr=errors,
            fmt="o",
            color="tab:green",
            capsize=4,
            markersize=7,
            label="qualified sub-bands",
        )
        alpha = chime["alpha"]["alpha"]
        log_norm = np.average(
            np.log(widths) - alpha * np.log(frequencies / 661.1),
            weights=(widths / errors) ** 2,
        )
        grid = np.linspace(610, 765, 200)
        right.plot(
            grid,
            np.exp(log_norm) * (grid / 661.1) ** alpha,
            color="tab:green",
            alpha=0.75,
            label=rf"within-burst fit: $\alpha={alpha:.2f}\pm{chime['alpha']['alpha_err']:.2f}$",
        )
        right.set_xlim(610, 765)
        right.set_ylim(0.035, 0.16)
        right.set_xlabel(r"$\nu_{\rm c}$ (MHz)")
        right.text(0.04, 0.94, "(b) CHIME/FRB, FRB 20240203A", transform=right.transAxes, va="top")
        right.legend(loc="lower right", fontsize=10)
        figure.savefig(output)
        plt.close(figure)

    record = {
        "artifact_sha256": sha256(output),
        "campaign_measurement": EXPECTED_MEASUREMENT,
        "chime_input": {
            "path": str((CAMPAIGN / "chromatica_hi_campaign.json").relative_to(ROOT)),
            "sha256": sha256_bytes(
                reviewed_blob(CAMPAIGN_RELATIVE / "chromatica_hi_campaign.json")
            ),
            "status": chime["science_status"],
        },
        "command": (
            "env -i HOME=/Users/jakobfaber "
            "PATH=/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin "
            "/opt/anaconda3/bin/conda run -n py312 python "
            "scripts/build_scintillation_campaign_summary.py --figure-root <candidate-root> "
            "--chime-figure-source <PR192-results-library-directory>"
        ),
        "dsa_input": {
            "path": str(DSA_VALIDATION.relative_to(ROOT)),
            "sha256": sha256_bytes(reviewed_blob(DSA_VALIDATION_RELATIVE)),
            "status": "qualified",
        },
        "generator_sha256": sha256(Path(__file__)),
        "output": "figures/dsa_lorentzian_summary.pdf",
        "pipeline_revision": pipeline_revision(),
        "source_revision": REVIEWED_PIPELINE,
        "policy": "different bursts; separate panels; no cross-burst scaling or shared-screen inference",
        "python": sys.version.split()[0],
        "recorded_date": "2026-07-17",
    }
    FIGURE_PROVENANCE_PATH.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output


def stage_chime_acf_candidates(candidate_root: Path, source_dir: Path) -> list[dict]:
    review = json.loads(reviewed_blob(CAMPAIGN_RELATIVE / "figures.review.json"))
    verdicts = {
        item["path"]: item
        for item in review.get("verdicts", [])
        if item["path"].endswith("_acf_fits.png")
    }
    expected = {
        f"{nick}{suffix}_acf_fits.png"
        for nick, _ in BURSTS
        for suffix in ("", "_hi")
    }
    if set(verdicts) != expected:
        raise ValueError("PR #192 ACF review roster differs from the 24-product contract")

    staged: list[dict] = []
    for filename in sorted(expected):
        source = source_dir / filename
        if not source.is_file():
            raise ValueError(f"missing reviewed CHIME ACF render: {source}")
        actual = sha256(source)
        reviewed = verdicts[filename]["sha256"]
        if actual != reviewed:
            raise ValueError(f"CHIME ACF render hash differs from PR #192 review: {filename}")
        stem = filename.removesuffix("_acf_fits.png")
        if stem.endswith("_hi"):
            nick = stem.removesuffix("_hi")
            product = "high_resolution"
        else:
            nick = stem
            product = "standard"
        target = candidate_root / f"figures/chime_scint_acf/{nick}_{product}_acf_fits.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        staged.append(
            {
                "source": filename,
                "target": str(target.relative_to(candidate_root)),
                "sha256": actual,
                "review_verdict": verdicts[filename]["verdict"],
                "science_disposition": verdicts[filename]["notes"],
            }
        )
    return staged


def write_outputs(check: bool = False) -> None:
    revision = pipeline_revision()
    if not pipeline_contains_reviewed_campaign():
        raise ValueError(
            f"pipeline pin {revision} does not contain reviewed {REVIEWED_PIPELINE}"
        )
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
    parser.add_argument(
        "--figure-root",
        type=Path,
        help="render the joint candidate below this isolated root",
    )
    parser.add_argument(
        "--chime-figure-source",
        type=Path,
        help="directory containing the 24 hash-reviewed PR #192 ACF PNGs",
    )
    args = parser.parse_args()
    if not args.figure_root or args.check:
        write_outputs(check=args.check)
    if args.figure_root:
        render_joint_figure(args.figure_root)
        if args.chime_figure_source:
            staged = stage_chime_acf_candidates(args.figure_root, args.chime_figure_source)
            record = json.loads(FIGURE_PROVENANCE_PATH.read_text())
            record["chime_acf_candidates"] = staged
            FIGURE_PROVENANCE_PATH.write_text(
                json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )


if __name__ == "__main__":
    main()
