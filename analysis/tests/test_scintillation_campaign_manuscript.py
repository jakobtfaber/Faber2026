"""Parity checks for the pinned CHIME objective-window campaign."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PIPELINE = "17d9d26675702e9f8917da655621bef3231f0ddb"
sys.path.insert(0, str(ROOT / "scripts"))

import build_scintillation_campaign_summary as campaign_builder  # noqa: E402


def test_pipeline_pin_contains_merged_window_campaign() -> None:
    pinned = subprocess.check_output(
        ["git", "rev-parse", ":pipeline"], cwd=ROOT, text=True
    ).strip()
    assert pinned == EXPECTED_PIPELINE


def test_results_report_single_qualified_chime_sightline() -> None:
    results = (ROOT / "sections/results.tex").read_text(encoding="utf-8")
    assert "one qualified CHIME-band sightline" in results
    assert "FRB~20240203A" in results
    assert "all twelve bursts are demoted to diagnostic status" not in results
    assert "No CHIME-band decorrelation bandwidth survives" not in results


def test_rejected_dsa_only_summary_is_not_compiled() -> None:
    results = (ROOT / "sections/results.tex").read_text(encoding="utf-8")
    assert "\\includegraphics[width=\\textwidth]{figures/dsa_lorentzian_summary.pdf}" not in results
    assert "JOINT DSA+CHIME SCINTILLATION SUMMARY" in results


def test_campaign_table_is_generated_input() -> None:
    results = (ROOT / "sections/results.tex").read_text(encoding="utf-8")
    table = ROOT / "chime_scintillation_campaign_table.tex"
    assert "\\input{chime_scintillation_campaign_table}" in results
    assert table.exists()
    text = table.read_text(encoding="utf-8")
    assert "FRB~20240203A" in text
    assert "qualified" in text


def test_campaign_loader_enforces_the_reviewed_measurement_contract() -> None:
    campaign = campaign_builder.load_campaign()
    measurements = [
        record["name"]
        for record in campaign.records.values()
        if record.get("science_status") == "measurement"
    ]
    assert measurements == ["chromatica_hi"]
    assert campaign.validation["n_records"] == 24
    assert campaign.validation["n_diagnostic_only"] == 23


def test_dsa_loader_enforces_qualification_gates() -> None:
    dsa = campaign_builder.load_dsa_measurement()
    assert dsa["center_frequency_mhz"] == 1328.235796841934
    assert dsa["calibrated_measurement"]["dnu_mhz"] == 0.44624819758756973
