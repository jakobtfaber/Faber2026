import csv
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
CORE_PATH = HERE / "campaigns" / "burst_energies" / "energetics_core.py"
SPEC = importlib.util.spec_from_file_location("energetics_core", CORE_PATH)
CORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CORE)
VERIFY_PATH = HERE / "campaigns" / "burst_energies" / "verify_data_driven_energies.py"
VERIFY_SPEC = importlib.util.spec_from_file_location("verify_data_driven_energies", VERIFY_PATH)
VERIFY = importlib.util.module_from_spec(VERIFY_SPEC)
VERIFY_SPEC.loader.exec_module(VERIFY)


FIELDS = [
    "nickname", "band", "fluence_jy_ms_hz", "stat_err_jy_ms_hz",
    "window_status", "window_sensitivity_frac", "calibration_status",
    "noise_status", "review_status", "input_sha256", "calibration_sha256",
    "input_path", "calibration_paths",
]


def accepted_row(nickname="zach", band="CHIME"):
    return dict(
        nickname=nickname, band=band, fluence_jy_ms_hz=1.0e9,
        stat_err_jy_ms_hz=1.0e8, window_status="accepted",
        window_sensitivity_frac=0.01, calibration_status="accepted",
        noise_status="accepted", review_status="accepted",
        input_sha256="a" * 64, calibration_sha256="b" * 64,
        input_path="", calibration_paths="",
    )


def write_receipts(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def bind_real_files(tmp_path, rows):
    calibration = tmp_path / "calibration.csv"
    calibration.write_text("calibration\n")
    for index, row in enumerate(rows):
        source = tmp_path / f"input-{index}.npy"
        source.write_bytes(f"input-{index}".encode())
        row.update(
            input_path=str(source),
            input_sha256=CORE.sha256(source),
            calibration_paths=str(calibration),
            calibration_sha256=CORE.calibration_sha256([calibration]),
        )
    return rows


def test_current_energy_roster_uses_frozen_sources():
    roster = CORE.load_energy_roster(HERE)
    included = {nick for nick, row in roster.items() if row["eligible"]}
    assert included == {
        "chromatica", "hamilton", "isha", "johndoeii",
        "oran", "phineas", "whitney", "zach",
    }
    assert roster["wilhelm"]["redshift"] is None
    assert roster["casey"]["exclusion_reason"] == "photometric redshift only"


def test_receipt_fails_closed_on_unreviewed_or_unstable(tmp_path):
    path = tmp_path / "fluences.csv"
    row = bind_real_files(tmp_path, [accepted_row()])[0]
    row.update(window_sensitivity_frac=0.11, review_status="pending")
    write_receipts(path, [row])
    with pytest.raises(ValueError, match="not accepted"):
        CORE.load_accepted_fluences(path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("fluence_jy_ms_hz", "nan"),
        ("stat_err_jy_ms_hz", -1),
        ("window_sensitivity_frac", "inf"),
        ("input_sha256", "abc"),
        ("calibration_sha256", "g" * 64),
    ],
)
def test_receipt_rejects_invalid_numeric_and_hash_fields(tmp_path, field, value):
    path = tmp_path / "fluences.csv"
    row = bind_real_files(tmp_path, [accepted_row()])[0]
    row[field] = value
    write_receipts(path, [row])
    with pytest.raises(ValueError, match="not accepted"):
        CORE.load_accepted_fluences(path)


def test_energy_conversion_oracle():
    value = CORE.energy_erg(1.0e9, 0.1)
    assert 2.0e38 < value < 3.0e38


def test_builds_exact_eight_row_artifact_from_accepted_receipts(tmp_path):
    roster = CORE.load_energy_roster(HERE)
    included = [nick for nick, row in roster.items() if row["eligible"]]
    path = tmp_path / "accepted.csv"
    rows = [
        accepted_row(nick, band)
        for nick in included
        for band in ("CHIME", "DSA")
    ]
    bind_real_files(tmp_path, rows)
    write_receipts(path, rows)
    artifact = CORE.build_artifact(HERE, path)
    assert len(artifact["results"]) == 8
    assert len(artifact["dispositions"]) == 4
    assert {row["nickname"] for row in artifact["results"]} == set(included)
    assert all(row["energy_erg"] > 0 for row in artifact["results"])


def test_independent_verifier_rejects_tampered_energy(tmp_path):
    roster = CORE.load_energy_roster(HERE)
    rows = [
        accepted_row(nick, band)
        for nick, meta in roster.items()
        if meta["eligible"]
        for band in ("CHIME", "DSA")
    ]
    bind_real_files(tmp_path, rows)
    receipts = tmp_path / "accepted.csv"
    write_receipts(receipts, rows)
    artifact = CORE.build_artifact(HERE, receipts)
    artifact["results"][0]["energy_erg"] *= 2
    artifact_path = tmp_path / "tampered.json"
    artifact_path.write_text(json.dumps(artifact))
    with pytest.raises(ValueError, match="energy mismatch"):
        VERIFY.verify(artifact_path)


def test_independent_verifier_rejects_receipt_hash_substitution(tmp_path):
    roster = CORE.load_energy_roster(HERE)
    rows = [
        accepted_row(nick, band)
        for nick, meta in roster.items()
        if meta["eligible"]
        for band in ("CHIME", "DSA")
    ]
    bind_real_files(tmp_path, rows)
    receipts = tmp_path / "accepted.csv"
    write_receipts(receipts, rows)
    artifact = CORE.build_artifact(HERE, receipts)
    artifact["fluence_receipt_sha256"] = "0" * 64
    artifact_path = tmp_path / "bad-hash.json"
    artifact_path.write_text(json.dumps(artifact))
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        VERIFY.verify(artifact_path)


def test_independent_verifier_rejects_self_consistent_wrong_redshift(tmp_path):
    roster = CORE.load_energy_roster(HERE)
    rows = [
        accepted_row(nick, band)
        for nick, meta in roster.items()
        if meta["eligible"]
        for band in ("CHIME", "DSA")
    ]
    bind_real_files(tmp_path, rows)
    receipts = tmp_path / "accepted.csv"
    write_receipts(receipts, rows)
    artifact = CORE.build_artifact(HERE, receipts)
    result = artifact["results"][0]
    result["redshift"] = 0.9
    result["energy_erg"] = 0.0
    result["stat_err_erg"] = 0.0
    for band in ("CHIME", "DSA"):
        band_row = result["bands"][band]
        band_row["energy_erg"] = CORE.energy_erg(
            band_row["fluence_jy_ms_hz"], result["redshift"]
        )
        result["energy_erg"] += band_row["energy_erg"]
        result["stat_err_erg"] += CORE.energy_erg(
            band_row["stat_err_jy_ms_hz"], result["redshift"]
        ) ** 2
    result["stat_err_erg"] **= 0.5
    artifact_path = tmp_path / "wrong-redshift.json"
    artifact_path.write_text(json.dumps(artifact))
    with pytest.raises(ValueError, match="roster metadata mismatch"):
        VERIFY.verify(artifact_path)
