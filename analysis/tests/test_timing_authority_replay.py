from __future__ import annotations

import json
import os
import sys
import types
from datetime import UTC, datetime
from pathlib import Path

import h5py
import numpy as np
import pytest

from scripts import replay_one_event_timing_authorities as timing

CASEY_TRIGGER = {
    "mjds_T2": 60369.37095224303,
    "mjd_trigger_exact": 60369.37095221912,
    "specnum": 34373444,
    "status": "VERIFIED",
}
CASEY_TIME_ORIGIN = {
    "status": "owner_approved_trigger_peak_anchor",
    "trigger_mjd_utc": "60369.37095221912",
    "trigger_reference_frequency_mhz": 1530.0,
    "trigger_reference_frequency_status": (
        "proposed_modeling_convention_pending_owner_decision"
    ),
    "trigger_reference_frequency_sensitivity_required": True,
    "filterbank_product_dm_pc_cm3": 491.211,
    "filterbank_peak_sample_index": 15259,
    "filterbank_peak_offset_s": 0.500006912,
    "alternative_pretrigger_convention": {
        "sample_index": 15256,
        "status": "unverified_alternative_for_sensitivity_only",
    },
    "mapping_ambiguity_s": 0.000098304,
    "mapping_uncertainty_treatment": (
        "pending_owner_decision_discrete_two_anchor_sensitivity"
    ),
    "rounded_tstart_allowed": False,
    "owner_approval_date": "2026-08-01",
    "owner_decision_receipt": (
        "analysis-configs/absolute-dm/decisions/casey-trigger-peak.json"
    ),
    "owner_decision_receipt_sha256": (
        "eff1e306ffe75ed5efe9e93137e6faecec1d077b2ca5a35853aec883087becb0"
    ),
}
TRIGGER_AUTHORITY_SHA256 = "87852969eb41c2abfa4c6534557ad03ed4f3e16e64cf1b28bd9da35f4ff89a0e"
OWNER_DECISION_SHA256 = "eff1e306ffe75ed5efe9e93137e6faecec1d077b2ca5a35853aec883087becb0"
ORIGINAL_AUDIT_CHIME = timing.audit_chime
ORIGINAL_AUDIT_DSA = timing.audit_dsa


def _write_chime_fixture(path: Path) -> None:
    frequency_mhz = np.array([400.0, 500.0, 650.0, 800.0])
    delta_time_s = 2.56e-6
    dispersion_delay_s = timing.K_DM_S_MHZ2 * 491.0 * (
        1.0 / frequency_mhz**2 - 1.0 / timing.REFERENCE_FREQUENCY_MHZ**2
    )
    fpga_count = np.rint((dispersion_delay_s - dispersion_delay_s.min()) / delta_time_s)
    # Store the affine relation exactly: a shared integer ctime plus a
    # sub-relation offset of fpga_count * delta_time_s (float64 error
    # ~1e-15 s). Composing 1.7e9 + fpga*dt in float64 first rounds at the
    # ~1e-7 s level, which the audit's extended-precision (Linux x86
    # longdouble) affine cross-check correctly rejects as >1 ns.
    ctime_offset_s = fpga_count * delta_time_s
    dtype = np.dtype(
        [("ctime", "<i8"), ("ctime_offset", "<f8"), ("fpga_count", "<u8")]
    )
    time0 = np.zeros(frequency_mhz.size, dtype=dtype)
    time0["ctime"] = np.int64(1_700_000_000)
    time0["ctime_offset"] = ctime_offset_s
    time0["fpga_count"] = fpga_count.astype(np.uint64)
    event_unix_s = float(1_700_000_000 + ctime_offset_s.max() + 0.01)
    frequency_dtype = np.dtype([("centre", "<f8")])
    frequency = np.zeros(frequency_mhz.size, dtype=frequency_dtype)
    frequency["centre"] = frequency_mhz
    with h5py.File(path, "w") as handle:
        handle.create_dataset("time0", data=time0)
        handle.create_dataset("index_map/freq", data=frequency)
        handle.create_dataset(
            "tiedbeam_baseband",
            shape=(frequency_mhz.size, 1, 20_000),
            dtype=np.int8,
        )
        handle.attrs["delta_time"] = delta_time_s
        handle.attrs["event_date"] = datetime.fromtimestamp(
            event_unix_s, tz=UTC
        ).replace(tzinfo=None).isoformat()
        handle.attrs["event_id"] = 1
        handle.attrs["baseband-analysis_git_sha"] = "fixture"
        handle.attrs["archive_version"] = "fixture"


def _install_fake_blimpy(
    monkeypatch: pytest.MonkeyPatch,
    *,
    tstart: float = 60_000.0,
    peak_sample: int = 15259,
) -> None:
    class FakeWaterfall:
        def __init__(self, _path: str, *, load_data: bool) -> None:
            self.header = {"tstart": tstart, "tsamp": 32.768e-6}
            if load_data:
                baseline = np.arange(16000, dtype=float)[:, None] % 7
                self.data = np.broadcast_to(baseline[:, None, :], (16000, 1, 16)).copy()
                self.data[peak_sample, 0, :] += 100.0

    monkeypatch.setitem(sys.modules, "blimpy", types.SimpleNamespace(Waterfall=FakeWaterfall))


def _write_dsa_support(path: Path) -> Path:
    np.save(path, np.broadcast_to(np.arange(32), (16, 32)).astype(np.float32))
    return path


def test_peak_audit_uses_accepted_support_and_ignores_dead_row_rfi(
    tmp_path: Path,
) -> None:
    class Reader:
        pass

    reader = Reader()
    baseline = np.arange(200, dtype=float) % 7
    reader.data = np.broadcast_to(baseline[:, None, None], (200, 1, 16)).copy()
    reader.data[100, 0, 1:] += 20.0
    reader.data[120, 0, 0] += 10_000.0
    reference = np.broadcast_to(np.arange(32), (16, 32)).astype(np.float32).copy()
    reference[0] = 0.0
    reference_path = tmp_path / "accepted.npy"
    np.save(reference_path, reference)
    assert timing._dsa_peak_sample(reader, reference_path) == 100


def test_casey_trigger_recovery_matches_locked_microsecond_value() -> None:
    replay = timing.recover_trigger(CASEY_TRIGGER)
    assert replay["itime"] == 8595268
    assert replay["serialized_token_s"] == 2253.2
    assert replay["elapsed_true_s"] == 2253.1979345920004
    assert replay["correction_us"] == -2065.407999452873
    assert replay["recovered_mjd"] == 60369.37095221912


def test_trigger_recovery_rejects_alternative_precision_at_token_boundary() -> None:
    replay = timing.recover_trigger({"mjds_T2": 60_000.0, "specnum": 34_300_000})
    assert replay["itime"] == 8_576_907
    assert replay["serialized_token_s"] == 2248.39
    float64_mutant_token = float(format(8_576_907 * 262.144e-6, ".6g"))
    assert float64_mutant_token == 2248.38
    assert replay["serialized_token_s"] != float64_mutant_token


def test_chime_audit_accepts_internal_counter_and_schedule_oracles(tmp_path: Path) -> None:
    path = tmp_path / "chime.h5"
    _write_chime_fixture(path)
    result = timing.audit_chime(path)
    assert result["status"] == "pass_internal_counter_and_capture_schedule_cross_check"
    assert result["external_clock_certification"] == "not supplied"


@pytest.mark.parametrize(
    ("failure", "message"),
    [
        ("event_window", "outside the 400 MHz capture window"),
        ("counter", "disagree with the FPGA counter"),
        ("schedule", "do not follow a cold-plasma schedule"),
    ],
)
def test_chime_audit_rejects_each_timing_failure(
    tmp_path: Path, failure: str, message: str
) -> None:
    path = tmp_path / "chime.h5"
    _write_chime_fixture(path)
    with h5py.File(path, "r+") as handle:
        if failure == "event_window":
            handle.attrs["event_date"] = "2000-01-01T00:00:00"
        else:
            time0 = handle["time0"][:]
            if failure == "counter":
                time0["ctime_offset"][1] += 1.0e-6
            else:
                time0["ctime_offset"][1] += 40 * 2.56e-6
                time0["fpga_count"][1] += 40
            del handle["time0"]
            handle.create_dataset("time0", data=time0)
    with pytest.raises(RuntimeError, match=message):
        timing.audit_chime(path)


def test_dsa_audit_preserves_terminal_sample_zero_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_fake_blimpy(monkeypatch)
    result = timing.audit_dsa(tmp_path / "casey.fil", CASEY_TRIGGER)
    assert result["filterbank_sample_zero_status"] == (
        "blocked_missing_exact_trigger_to_sample_mapping"
    )
    assert result["filterbank_tstart_use"] == "diagnostic_only_not_an_absolute_time_authority"
    assert result["fit_observation_time_origin_eligible"] is False
    assert result["trigger_recovery_status"] == "pass_tolerance_bounded_replay"


def test_dsa_audit_admits_owner_approved_trigger_peak_anchor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_fake_blimpy(monkeypatch)
    result = timing.audit_dsa(
        tmp_path / "casey.fil",
        CASEY_TRIGGER,
        CASEY_TIME_ORIGIN,
        _write_dsa_support(tmp_path / "accepted.npy"),
    )
    assert result["filterbank_sample_zero_status"] == (
        "derived_from_owner_approved_trigger_peak_anchor"
    )
    assert result["fit_observation_time_origin_eligible"] is True
    assert result["joint_fit_timing_uncertainty_eligible"] is False
    assert result["filterbank_peak_sample_index"] == 15259
    assert result["mapping_ambiguity_s"] == pytest.approx(0.000098304, abs=1.0e-18)
    assert result["product_reference_frequency_mhz"] == 400.0
    assert result["trigger_to_product_reference_s"] == pytest.approx(
        11.866546044944464,
        abs=1.0e-15,
    )
    assert result["filterbank_tstart_use"] == (
        "diagnostic_only_not_an_absolute_time_authority"
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"status": "pending"}, "not owner approved"),
        ({"rounded_tstart_allowed": True}, "must remain forbidden"),
        ({"trigger_mjd_utc": "60369.0"}, "differs from trigger authority"),
        ({"filterbank_peak_sample_index": 15258}, "peak offset contradicts"),
        ({"mapping_ambiguity_s": 0.0}, "differs from the alternative convention"),
    ],
)
def test_dsa_audit_rejects_mutated_trigger_peak_anchor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: dict,
    message: str,
) -> None:
    _install_fake_blimpy(monkeypatch)
    with pytest.raises(RuntimeError, match=message):
        timing.audit_dsa(
            tmp_path / "casey.fil",
            CASEY_TRIGGER,
            CASEY_TIME_ORIGIN | mutation,
            _write_dsa_support(tmp_path / "accepted.npy"),
        )


def test_dsa_audit_rejects_observed_peak_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_fake_blimpy(monkeypatch, peak_sample=15258)
    with pytest.raises(RuntimeError, match="peak sample differs"):
        timing.audit_dsa(
            tmp_path / "casey.fil",
            CASEY_TRIGGER,
            CASEY_TIME_ORIGIN,
            _write_dsa_support(tmp_path / "accepted.npy"),
        )


def test_dsa_replay_tolerance_accepts_one_ulp_and_rejects_two(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_fake_blimpy(monkeypatch)
    recovered = timing.recover_trigger(CASEY_TRIGGER)["recovered_mjd"]
    one_ulp = float(np.nextafter(recovered, np.inf))
    two_ulps = float(np.nextafter(one_ulp, np.inf))
    assert 0.0 < (one_ulp - recovered) * 86400.0 * 1.0e9 < 1000.0
    assert (two_ulps - recovered) * 86400.0 * 1.0e9 > 1000.0
    accepted = timing.audit_dsa(
        tmp_path / "casey.fil", CASEY_TRIGGER | {"mjd_trigger_exact": one_ulp}
    )
    assert accepted["trigger_recovery_status"] == "pass_tolerance_bounded_replay"
    with pytest.raises(RuntimeError, match="locked value"):
        timing.audit_dsa(
            tmp_path / "casey.fil", CASEY_TRIGGER | {"mjd_trigger_exact": two_ulps}
        )


def test_dsa_audit_rejects_unverified_trigger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_fake_blimpy(monkeypatch)
    entry = CASEY_TRIGGER | {"status": "PENDING"}
    with pytest.raises(RuntimeError, match="not verified"):
        timing.audit_dsa(tmp_path / "casey.fil", entry)


def test_dsa_audit_rejects_trigger_replay_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_fake_blimpy(monkeypatch)
    entry = CASEY_TRIGGER | {"mjd_trigger_exact": CASEY_TRIGGER["mjd_trigger_exact"] + 1e-6}
    with pytest.raises(RuntimeError, match="locked value"):
        timing.audit_dsa(tmp_path / "casey.fil", entry)


def _receipt_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict]:
    paths = {
        name: tmp_path / name
        for name in (
            "raw_chime_h5",
            "raw_dsa_filterbank",
            "trigger_recovery",
            "accepted_dsa_reference",
        )
    }
    paths["raw_chime_h5"].write_bytes(b"chime")
    paths["raw_dsa_filterbank"].write_bytes(b"dsa")
    paths["trigger_recovery"].write_text(json.dumps({"casey": CASEY_TRIGGER}))
    with paths["accepted_dsa_reference"].open("wb") as handle:
        np.save(
            handle,
            np.broadcast_to(np.arange(32), (16, 32)).astype(np.float32),
        )
    config = {
        "event": "casey",
        "event_binding_sha256": "binding",
        "paths": {name: str(path) for name, path in paths.items()},
        "input_sha256": {name: timing.sha256_file(path) for name, path in paths.items()},
    }
    config_path = tmp_path / "config.json"
    config_path.write_text("{}")
    monkeypatch.setattr(timing, "load_config", lambda _path: config)
    monkeypatch.setattr(timing, "audit_chime", lambda _path: {"status": "pass"})
    return config_path, config


def test_receipt_is_blocked_when_sample_zero_is_unproven(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, _config = _receipt_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        timing,
        "audit_dsa",
        lambda _path, _entry, _time_origin=None, _reference=None: {
            "filterbank_sample_zero_status": (
                "blocked_missing_exact_trigger_to_sample_mapping"
            ),
            "fit_observation_time_origin_eligible": False,
        },
    )
    receipt = timing.build_receipt(config_path)
    assert receipt["status"] == "timing_replayed_fit_input_blocked"


def test_receipt_records_peak_anchor_but_blocks_pending_mapping_decision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, config = _receipt_fixture(tmp_path, monkeypatch)
    config["dsa"] = {"time_origin": CASEY_TIME_ORIGIN}
    monkeypatch.setattr(
        timing,
        "audit_dsa",
        lambda _path, _entry, _time_origin=None, _reference=None: {
            "filterbank_sample_zero_status": (
                "derived_from_owner_approved_trigger_peak_anchor"
            ),
            "fit_observation_time_origin_eligible": True,
            "joint_fit_timing_uncertainty_eligible": False,
        },
    )
    monkeypatch.setattr(
        timing,
        "_verify_execution_context",
        lambda *_args: {"candidate_manifest_sha256": "a" * 64},
    )
    receipt = timing.build_receipt(
        config_path,
        tmp_path / "candidate-manifest.json",
        tmp_path / "environment-receipt.json",
    )
    assert receipt["status"] == (
        "timing_replayed_fit_input_blocked_pending_mapping_decision"
    )
    assert receipt["reference_frequency_mhz"] == 400.0


def test_peak_anchor_receipt_requires_bound_execution_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, config = _receipt_fixture(tmp_path, monkeypatch)
    config["dsa"] = {"time_origin": CASEY_TIME_ORIGIN}
    with pytest.raises(RuntimeError, match="requires candidate and environment receipts"):
        timing.build_receipt(config_path)


def _execution_context_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    required = [
        "analysis-configs/absolute-dm/casey.json",
        "analysis-configs/absolute-dm/schema.json",
        "radio_pipeline/fitting/products.py",
        "scripts/audit_one_event_dsa_state_h17.py",
        "scripts/build_one_event_dsa_hybrid_h17.py",
        "scripts/one_event_workflow.py",
        "scripts/replay_one_event_timing_authorities.py",
    ]
    for relative in required + ["pyproject.toml", "uv.lock"]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative)
    manifest_path = tmp_path / "candidate-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "base_commit": "a" * 40,
                "candidate_diff_sha256": "b" * 64,
                "paths": {
                    relative: timing.sha256_file(tmp_path / relative)
                    for relative in required
                },
            }
        )
    )
    environment_path = tmp_path / "environment-receipt.json"
    environment_path.write_text(
        json.dumps(
            {
                "h17": {
                    "python_executable": sys.executable,
                    "python_version": timing.platform.python_version(),
                    "packages": {
                        name: timing.importlib.metadata.version(name)
                        for name in timing.RUNTIME_PACKAGES
                    },
                },
                "locks": {
                    "pyproject.toml_sha256": timing.sha256_file(
                        tmp_path / "pyproject.toml"
                    ),
                    "uv.lock_sha256": timing.sha256_file(tmp_path / "uv.lock"),
                },
            }
        )
    )
    return (
        tmp_path,
        tmp_path / "analysis-configs/absolute-dm/casey.json",
        manifest_path,
        environment_path,
    )


def test_execution_context_accepts_exact_manifest_and_environment(tmp_path: Path) -> None:
    args = _execution_context_fixture(tmp_path)
    result = timing._verify_execution_context(*args)
    assert result["candidate_diff_sha256"] == "b" * 64
    assert result["python_executable"] == sys.executable


def test_execution_context_rejects_candidate_path_tamper(tmp_path: Path) -> None:
    args = _execution_context_fixture(tmp_path)
    (tmp_path / "scripts/one_event_workflow.py").write_text("tampered")
    with pytest.raises(RuntimeError, match="candidate manifest path changed"):
        timing._verify_execution_context(*args)


def test_execution_context_rejects_environment_drift(tmp_path: Path) -> None:
    args = _execution_context_fixture(tmp_path)
    environment = json.loads(args[3].read_text())
    environment["h17"]["packages"]["numpy"] = "0.0"
    args[3].write_text(json.dumps(environment))
    with pytest.raises(RuntimeError, match="runtime package differs"):
        timing._verify_execution_context(*args)


def test_receipt_rejects_owner_decision_hash_drift_before_timing_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, config = _receipt_fixture(tmp_path, monkeypatch)
    config["dsa"] = {
        "time_origin": CASEY_TIME_ORIGIN
        | {"owner_decision_receipt_sha256": "0" * 64}
    }
    called = False

    def forbidden_audit(*_args: object, **_kwargs: object) -> dict:
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(timing, "audit_dsa", forbidden_audit)
    with pytest.raises(RuntimeError, match="owner decision receipt hash differs"):
        timing.build_receipt(config_path)
    assert called is False


def test_receipt_refuses_accidental_fit_eligibility(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, _config = _receipt_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        timing,
        "audit_dsa",
        lambda _path, _entry, _time_origin=None, _reference=None: {
            "fit_observation_time_origin_eligible": True
        },
    )
    with pytest.raises(RuntimeError, match="must remain ineligible"):
        timing.build_receipt(config_path)


@pytest.mark.parametrize("input_name", ["raw_chime_h5", "raw_dsa_filterbank", "trigger_recovery"])
def test_receipt_rejects_input_hash_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, input_name: str
) -> None:
    config_path, config = _receipt_fixture(tmp_path, monkeypatch)
    config["input_sha256"][input_name] = "0" * 64
    with pytest.raises(RuntimeError, match=rf"{input_name} hash differs"):
        timing.build_receipt(config_path)


def test_receipt_rejects_missing_event_trigger(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, config = _receipt_fixture(tmp_path, monkeypatch)
    trigger_path = Path(config["paths"]["trigger_recovery"])
    trigger_path.write_text("{}")
    config["input_sha256"]["trigger_recovery"] = timing.sha256_file(trigger_path)
    with pytest.raises(RuntimeError, match="lacks event casey"):
        timing.build_receipt(config_path)


@pytest.mark.parametrize(
    "field", ["specnum", "mjds_T2", "mjd_trigger_exact", "status"]
)
def test_missing_trigger_field_never_changes_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    config_path, config = _receipt_fixture(tmp_path, monkeypatch)
    _install_fake_blimpy(monkeypatch)
    monkeypatch.setattr(timing, "audit_dsa", ORIGINAL_AUDIT_DSA)
    trigger_path = Path(config["paths"]["trigger_recovery"])
    entry = dict(CASEY_TRIGGER)
    del entry[field]
    trigger_path.write_text(json.dumps({"casey": entry}))
    config["input_sha256"]["trigger_recovery"] = timing.sha256_file(trigger_path)
    output = tmp_path / "timing-receipt.json"
    sentinel = b"preserved receipt sentinel\n"
    output.write_bytes(sentinel)
    monkeypatch.setattr(
        sys,
        "argv",
        ["replay_one_event_timing_authorities.py", "--config", str(config_path), "--output", str(output)],
    )
    with pytest.raises((KeyError, RuntimeError)):
        timing.main()
    assert output.read_bytes() == sentinel


@pytest.mark.parametrize("sample_zero_status", [None, "pass"])
def test_receipt_rejects_missing_or_wrong_sample_zero_hold(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sample_zero_status: str | None,
) -> None:
    config_path, _config = _receipt_fixture(tmp_path, monkeypatch)
    dsa = {"fit_observation_time_origin_eligible": False}
    if sample_zero_status is not None:
        dsa["filterbank_sample_zero_status"] = sample_zero_status
    monkeypatch.setattr(
        timing,
        "audit_dsa",
        lambda _path, _entry, _time_origin=None, _reference=None: dsa,
    )
    output = tmp_path / "timing-receipt.json"
    sentinel = b"preserved receipt sentinel\n"
    output.write_bytes(sentinel)
    monkeypatch.setattr(
        sys,
        "argv",
        ["replay_one_event_timing_authorities.py", "--config", str(config_path), "--output", str(output)],
    )
    with pytest.raises(RuntimeError, match="sample-zero provenance hold is absent"):
        timing.main()
    assert output.read_bytes() == sentinel


def test_documented_trigger_authority_is_canonical_and_hash_bound() -> None:
    document = (
        Path(__file__).parents[1] / "docs/rse/specs/dsa-trigger-mjd-timing.md"
    ).read_text()
    normalized_document = " ".join(document.split())
    assert "~/Data/Faber2026/dsa110/trigger_mjd_microsecond_recovery.json" in document
    assert TRIGGER_AUTHORITY_SHA256 in document
    assert "All under `~/Data/Faber2026/review/dsa-origin-metadata-20260727/`" not in document
    assert (
        "The recovered trigger MJD is not, by itself, the time of sample zero"
        in normalized_document
    )
    assert "The rounded `tstart` header must not be substituted" in normalized_document


def test_owner_decision_receipt_binds_exact_context_and_narrow_scope() -> None:
    path = (
        Path(__file__).parents[1]
        / "analysis-configs/absolute-dm/decisions/casey-trigger-peak.json"
    )
    assert timing.sha256_file(path) == OWNER_DECISION_SHA256
    receipt = json.loads(path.read_text())
    assert receipt["proposal"]["source_thread_id"] == (
        "019fb228-b55c-7b63-81c8-bccf963fe419"
    )
    assert receipt["proposal"]["source_turn_id"] == (
        "019fbc9e-690d-7830-8e2c-591121c61c5f"
    )
    assert receipt["proposal"]["source_message_id"] == (
        "msg_0bb62d3dcc0ca429016a6dbe4e13e48194a7f6934af80fcc1b"
    )
    assert timing.hashlib.sha256(receipt["proposal"]["text"].encode()).hexdigest() == (
        receipt["proposal"]["text_sha256"]
    )
    assert receipt["owner_response"]["source_turn_id"] == (
        "019fbe63-7f30-75c3-a733-b310ebe936dd"
    )
    assert receipt["owner_response"]["source_message_id"] == (
        "msg_019fbe63-8edf-7e92-8dd4-fae0fbe70f68"
    )
    assert timing.hashlib.sha256(
        receipt["owner_response"]["text"].encode()
    ).hexdigest() == receipt["owner_response"]["text_sha256"]
    assert receipt["approved_scope"]["filterbank_peak_sample_index"] == 15259
    assert receipt["approved_scope"]["geometry_constraint_retained"] is True
    assert "sampling" in receipt["not_approved"]
    assert "fit resolution" in receipt["not_approved"]
    assert receipt["subsequent_review_corrections"][
        "mapping_ambiguity_is_separate_from_clock_prior"
    ] is True


def test_documented_casey_claim_boundary_preserves_relative_diagnostics_only() -> None:
    document = (
        Path(__file__).parents[1] / "docs/rse/specs/dsa-trigger-mjd-timing.md"
    ).read_text()
    normalized_document = " ".join(document.split())
    assert "491.27737153955155" in normalized_document
    assert "coherent-power and relative-dispersion diagnostic" in normalized_document
    assert "pending independent and owner review" in normalized_document
    assert "491.27924166266934" in normalized_document
    assert "conditional geometry-alignment sensitivity" in normalized_document
    assert "no formal uncertainty" in normalized_document
    assert "sole executed Casey joint absolute-timing fit" in normalized_document
    assert "approximately 11.5583 s origin displacement" in normalized_document
    assert "11.55608945970681" in normalized_document
    assert "7e88c030152b5b967c28be4d0fc9a3a219b199fcf6438f3272e916c2716846a8" in (
        normalized_document
    )
    assert "failed_prior_rail" in normalized_document
    assert "resolution packet inherits that origin and contains no fit" in normalized_document
    assert "lack the producer mapping and contain no traceable fit result" in normalized_document
    assert "legacy fixed-DM crossmatch is unverified" in normalized_document
    assert "No existing Casey product supplies a formally quotable geometry-matching DM" in (
        normalized_document
    )
    assert "geocentric 400 MHz TOA" in normalized_document
    assert "do not invalidate the relative or coherent-power diagnostic" in normalized_document


@pytest.mark.external_data
def test_documented_trigger_authority_resolves_and_matches_hash() -> None:
    authority = (
        Path.home() / "Data/Faber2026/dsa110/trigger_mjd_microsecond_recovery.json"
    )
    assert authority.is_file()
    assert timing.sha256_file(authority) == TRIGGER_AUTHORITY_SHA256


@pytest.mark.external_data
def test_real_casey_filterbank_replays_owner_peak_anchor() -> None:
    path = Path(os.environ["FABER2026_CASEY_DSA_FIL"])
    assert timing.sha256_file(path) == (
        "8eb60706543875363f20f21ab1473d439f356120b8f8852cedaa9e567b938bd1"
    )
    reference = Path(os.environ["FABER2026_CASEY_DSA_REFERENCE"])
    result = timing.audit_dsa(path, CASEY_TRIGGER, CASEY_TIME_ORIGIN, reference)
    assert result["filterbank_peak_sample_index"] == 15259
    assert result["fit_observation_time_origin_eligible"] is True
    assert result["joint_fit_timing_uncertainty_eligible"] is False
    assert result["filterbank_tstart_use"] == (
        "diagnostic_only_not_an_absolute_time_authority"
    )


@pytest.mark.parametrize(
    "failure",
    [
        "hash_chime",
        "hash_dsa",
        "hash_trigger",
        "json",
        "event",
        "status",
        "replay",
        "h5_internal",
        "fil_read",
    ],
)
def test_rejection_never_publishes_or_changes_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    config_path, config = _receipt_fixture(tmp_path, monkeypatch)
    trigger_path = Path(config["paths"]["trigger_recovery"])
    output = tmp_path / "timing-receipt.json"
    sentinel = b"preserved receipt sentinel\n"
    output.write_bytes(sentinel)

    if failure.startswith("hash_"):
        input_name = {
            "hash_chime": "raw_chime_h5",
            "hash_dsa": "raw_dsa_filterbank",
            "hash_trigger": "trigger_recovery",
        }[failure]
        config["input_sha256"][input_name] = "0" * 64
    elif failure == "json":
        trigger_path.write_text("not json")
        config["input_sha256"]["trigger_recovery"] = timing.sha256_file(trigger_path)
    elif failure == "event":
        trigger_path.write_text("{}")
        config["input_sha256"]["trigger_recovery"] = timing.sha256_file(trigger_path)
    elif failure in {"status", "replay"}:
        _install_fake_blimpy(monkeypatch)
        monkeypatch.setattr(timing, "audit_dsa", ORIGINAL_AUDIT_DSA)
        entry = dict(CASEY_TRIGGER)
        if failure == "status":
            entry["status"] = "PENDING"
        else:
            entry["mjd_trigger_exact"] += 1.0e-6
        trigger_path.write_text(json.dumps({"casey": entry}))
        config["input_sha256"]["trigger_recovery"] = timing.sha256_file(trigger_path)
    elif failure == "h5_internal":
        _install_fake_blimpy(monkeypatch)
        monkeypatch.setattr(timing, "audit_dsa", ORIGINAL_AUDIT_DSA)
        monkeypatch.setattr(timing, "audit_chime", ORIGINAL_AUDIT_CHIME)
        chime_path = Path(config["paths"]["raw_chime_h5"])
        _write_chime_fixture(chime_path)
        with h5py.File(chime_path, "r+") as handle:
            time0 = handle["time0"][:]
            time0["ctime_offset"][1] += 1.0e-6
            del handle["time0"]
            handle.create_dataset("time0", data=time0)
        config["input_sha256"]["raw_chime_h5"] = timing.sha256_file(chime_path)
    else:
        class UnreadableWaterfall:
            def __init__(self, _path: str, *, load_data: bool) -> None:
                raise OSError("filterbank cannot be read")

        monkeypatch.setitem(
            sys.modules,
            "blimpy",
            types.SimpleNamespace(Waterfall=UnreadableWaterfall),
        )
        monkeypatch.setattr(timing, "audit_dsa", ORIGINAL_AUDIT_DSA)

    monkeypatch.setattr(
        sys,
        "argv",
        ["replay_one_event_timing_authorities.py", "--config", str(config_path), "--output", str(output)],
    )
    with pytest.raises((RuntimeError, OSError, json.JSONDecodeError)):
        timing.main()
    assert output.read_bytes() == sentinel


def test_valid_casey_receipt_remains_explicitly_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path, config = _receipt_fixture(tmp_path, monkeypatch)
    _install_fake_blimpy(monkeypatch)
    monkeypatch.setattr(timing, "audit_dsa", ORIGINAL_AUDIT_DSA)
    monkeypatch.setattr(timing, "audit_chime", ORIGINAL_AUDIT_CHIME)
    chime_path = Path(config["paths"]["raw_chime_h5"])
    _write_chime_fixture(chime_path)
    config["input_sha256"]["raw_chime_h5"] = timing.sha256_file(chime_path)

    receipt = timing.build_receipt(config_path)

    assert receipt["status"] == "timing_replayed_fit_input_blocked"
    assert receipt["reference_frequency_mhz"] == 400.0
    assert receipt["chime"]["status"] == (
        "pass_internal_counter_and_capture_schedule_cross_check"
    )
    assert receipt["chime"]["external_clock_certification"] == "not supplied"
    assert receipt["dsa"]["trigger_recovery_status"] == "pass_tolerance_bounded_replay"
    assert receipt["dsa"]["filterbank_sample_zero_status"] == (
        "blocked_missing_exact_trigger_to_sample_mapping"
    )
    assert receipt["dsa"]["fit_observation_time_origin_eligible"] is False
    forbidden_true_fields = {
        "timing_complete",
        "geometry_complete",
        "preparation_complete",
        "fit_complete",
        "execution_authorized",
    }

    def visit(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                assert not (key in forbidden_true_fields and child is True)
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(receipt)


@pytest.mark.parametrize("failure_stage", ["fsync", "replace"])
def test_atomic_publication_failure_preserves_existing_receipt_and_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_stage: str,
) -> None:
    output = tmp_path / "timing-receipt.json"
    sentinel = b"preserved receipt sentinel\n"
    output.write_bytes(sentinel)
    monkeypatch.setattr(timing, "build_receipt", lambda *_args: {"status": "blocked"})

    def fail_fsync(_descriptor: int) -> None:
        raise OSError("injected publication failure")

    def fail_replace(_source: object, _target: object) -> None:
        raise OSError("injected publication failure")

    monkeypatch.setattr(
        timing.os,
        failure_stage,
        fail_fsync if failure_stage == "fsync" else fail_replace,
    )
    with pytest.raises(OSError, match="injected publication failure"):
        timing.publish_receipt(tmp_path / "config.json", output)
    assert output.read_bytes() == sentinel
    assert list(tmp_path.glob(".timing-receipt.json.*.tmp")) == []


def test_atomic_publication_writes_complete_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "timing-receipt.json"
    receipt = {"status": "timing_replayed_fit_input_blocked"}
    monkeypatch.setattr(timing, "build_receipt", lambda *_args: receipt)
    timing.publish_receipt(tmp_path / "config.json", output)
    assert json.loads(output.read_text()) == receipt
    assert list(tmp_path.glob(".timing-receipt.json.*.tmp")) == []
