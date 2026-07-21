import importlib.util
from pathlib import Path
from pathlib import PurePosixPath
import sys


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
