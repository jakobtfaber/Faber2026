import importlib.util
import hashlib
import json
from pathlib import Path
from pathlib import PurePosixPath
import sys

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "h17_source_data_layout.py"
SPEC = importlib.util.spec_from_file_location("h17_source_data_layout", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
layout = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = layout
SPEC.loader.exec_module(layout)

CERT_SCRIPT = Path(__file__).parents[1] / "scripts" / "build_raw_voltage_certificates.py"
CERT_SPEC = importlib.util.spec_from_file_location("build_raw_voltage_certificates", CERT_SCRIPT)
assert CERT_SPEC is not None and CERT_SPEC.loader is not None
cert_builder = importlib.util.module_from_spec(CERT_SPEC)
CERT_SPEC.loader.exec_module(cert_builder)


def test_source_layout_has_twelve_unique_pairs():
    assert len(layout.BURSTS) == 12
    assert len({burst.project_id for burst in layout.BURSTS}) == 12
    assert len({burst.chime_event_id for burst in layout.BURSTS}) == 12
    assert len({burst.dsa_observation_id for burst in layout.BURSTS}) == 12


def test_source_and_target_paths_are_unique_and_typed():
    old_paths = layout.canonical_paths(layout.old_paths)
    new_paths = layout.canonical_paths(layout.new_paths)

    assert len(old_paths) == 24
    assert len(set(old_paths)) == 24
    assert len(new_paths) == 24
    assert len(set(new_paths)) == 24
    assert all(PurePosixPath(path).suffix in {".fil", ".h5"} for path in old_paths)
    assert all(PurePosixPath(path).suffix in {".fil", ".h5"} for path in new_paths)


def test_zach_paths_match_the_approved_layout():
    zach = next(burst for burst in layout.BURSTS if burst.project_id == "zach")

    assert layout.new_paths(zach) == (
        "/data/Faber2026/data/dsa-110/zach/220207aabh_dev_polcal_I.fil",
        "/data/Faber2026/data/chime-frb/zach/singlebeam_210456524.h5",
    )
    assert layout.old_paths(zach) == (
        "/data/research/astrophysics/frbs/chime-dsa-codetections/dsa_filterbanks/"
        "Codetections_DSA_Filterbanks/zach_240203aacl_210456524/"
        "220207aabh_dev_polcal_I.fil",
        "/data/research/astrophysics/frbs/chime-dsa-codetections/chime_singlebeam/"
        "singlebeam_210456524.h5",
    )


def test_three_exclusions_are_outside_the_allowlist():
    canonical = set(layout.canonical_paths(layout.old_paths))

    assert len(layout.EXCLUDED_PATHS) == 3
    assert canonical.isdisjoint(layout.EXCLUDED_PATHS)


def test_remote_finalize_returns_json_for_the_ssh_wrapper():
    assert 'print(json.dumps({"receipt": str(target)}, sort_keys=True))' in layout.REMOTE_FINALIZE


def _complete_probe():
    paths = (
        layout.canonical_paths(layout.old_paths)
        + layout.canonical_paths(layout.new_paths)
        + list(layout.EXCLUDED_PATHS)
    )
    entries = {}
    for index, path in enumerate(paths):
        is_source = path in layout.canonical_paths(layout.old_paths)
        is_exclusion = path in layout.EXCLUDED_PATHS
        entries[path] = (
            {
                "exists": True,
                "is_file": True,
                "size": index + 1,
                "device": 7,
                "inode": 1000 + index,
                "mode": "0o644",
                "uid": 1,
                "gid": 2,
                "mtime_ns": 2000 + index,
                "open_handles": [],
                "sha256": f"{index:064x}",
            }
            if is_source or is_exclusion
            else {"exists": False, "open_handles": []}
        )
    return {
        "host": "lxd110h17",
        "captured_at": "2026-07-21T00:00:00+00:00",
        "data_device": 7,
        "entries": entries,
    }


def test_preflight_manifest_contains_exact_complete_probe():
    probe = _complete_probe()
    manifest = layout.build_preflight_manifest(probe, layout.move_records(), "attempt-1")

    assert manifest["attempt_id"] == "attempt-1"
    assert manifest["probe"] == probe
    assert len(manifest["probe"]["entries"]) == 51
    assert len(manifest["moves"]) == 24
    assert len(manifest["excluded_paths"]) == 3


def test_persist_preflight_writes_local_before_remote_and_matches_digest(
    tmp_path, monkeypatch
):
    attempt_id = "attempt-2"
    expected_local = tmp_path / f"h17-source-data-preflight-{attempt_id}.json"
    observed = []

    def fake_remote(host, program, payload, timeout=900):
        assert host == "h17"
        assert program == layout.REMOTE_PERSIST_PREFLIGHT
        assert expected_local.exists()
        local_bytes = expected_local.read_bytes()
        assert hashlib.sha256(local_bytes).hexdigest() == payload["sha256"]
        assert json.loads(local_bytes) == json.loads(payload["content"])
        observed.append("remote")
        return {"path": payload["path"], "sha256": payload["sha256"]}

    monkeypatch.setattr(layout, "_remote_python", fake_remote)
    reference = layout._persist_preflight(
        "h17",
        tmp_path / "receipt.json",
        _complete_probe(),
        layout.move_records(),
        attempt_id,
    )

    assert observed == ["remote"]
    assert reference["local_path"] == str(expected_local)
    assert reference["sha256"] == hashlib.sha256(expected_local.read_bytes()).hexdigest()


def test_persist_preflight_refuses_remote_digest_mismatch(tmp_path, monkeypatch):
    monkeypatch.setattr(
        layout,
        "_remote_python",
        lambda *args, **kwargs: {"path": "wrong", "sha256": "0" * 64},
    )

    with pytest.raises(RuntimeError, match="remote preflight persistence mismatch"):
        layout._persist_preflight(
            "h17",
            tmp_path / "receipt.json",
            _complete_probe(),
            layout.move_records(),
            "attempt-3",
        )


def test_persistence_failure_prevents_remote_migration(tmp_path, monkeypatch):
    remote_programs = []
    monkeypatch.setattr(layout, "preflight", lambda *args, **kwargs: _complete_probe())
    monkeypatch.setattr(
        layout,
        "_persist_preflight",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("persist failed")),
    )
    monkeypatch.setattr(
        layout,
        "_remote_python",
        lambda host, program, payload, timeout=900: remote_programs.append(program),
    )

    with pytest.raises(RuntimeError, match="persist failed"):
        layout.migrate("h17", tmp_path / "receipt.json")
    assert layout.REMOTE_MIGRATE not in remote_programs


def test_remote_journal_is_bound_to_verified_preflight():
    assert 'preflight_ref = request["preflight"]' in layout.REMOTE_MIGRATE
    assert 'if preflight["moves"] != moves' in layout.REMOTE_MIGRATE
    assert '"preflight": preflight_ref' in layout.REMOTE_MIGRATE


def test_paired_manifest_is_custody_only_and_has_twelve_pairs():
    records = []
    for record in layout.move_records():
        records.append({**record, "after": {"size": 1, "sha256": "0" * 64}})
    receipt = {
        "records": records,
        "created_at": "2026-07-21T00:00:00+00:00",
        "host_alias": "h17",
    }

    manifest = layout.build_source_manifest(receipt)

    assert manifest["status"] == "custody_verified_science_metadata_unverified"
    assert len(manifest["bursts"]) == 12
    zach = manifest["bursts"][0]["source_products"]
    assert zach["dsa-110"]["applied_dm"].startswith("unverified")
    assert zach["dsa-110"]["processing_basis"] == "owner_statement_2026-07-21"
    assert zach["chime-frb"]["dedispersion_state"].startswith("unverified")


def test_raw_voltage_certificates_use_project_scoped_paths():
    certificates = cert_builder.build_voltage_certificates()

    assert len(certificates) == 12
    assert certificates[0]["host_path"] == (
        "/data/Faber2026/data/chime-frb/zach/singlebeam_210456524.h5"
    )
    johndoe = next(item for item in certificates if item["nick"] == "johndoeII")
    assert "/chime-frb/johndoeii/" in johndoe["host_path"]
