from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from one_event_workflow import (  # noqa: E402
    STAGES,
    event_binding_sha256,
    load_config,
    validate_config,
)
import run_one_event_absolute_dm_workflow as workflow_runner  # noqa: E402
from run_one_event_absolute_dm_workflow import outputs_match  # noqa: E402

CONFIG = ROOT / "dm-toa-geometry-20260728/casey-hybrid/workflow-config.json"


def _config() -> dict:
    return json.loads(CONFIG.read_text())


def _substituted_config() -> dict:
    config = _config()
    config["event"] = "replacement"
    config["identity"]["reviewed_event"] = "replacement"
    config["identity"]["disallowed_event_tokens"] = sorted(
        config["identity"]["disallowed_event_tokens"] + ["casey"]
    )
    for key in (
        "raw_chime_h5",
        "accepted_chime_reference",
        "raw_dsa_filterbank",
        "accepted_dsa_reference",
        "output_root",
    ):
        config["paths"][key] = config["paths"][key].replace("casey", "replacement")
    for key in (
        "raw_chime_h5",
        "accepted_chime_reference",
        "raw_dsa_filterbank",
        "accepted_dsa_reference",
    ):
        config["identity"]["input_basenames"][key] = Path(
            config["paths"][key]
        ).name
    config["identity"]["output_root_basename"] = Path(
        config["paths"]["output_root"]
    ).name
    return config


def test_casey_regression_fixture_validates() -> None:
    config = load_config(CONFIG)
    assert config["event"] == "casey"
    assert config["chime"]["upchannel_factor"] == 16
    assert config["geometry"]["reference_frequency_mhz"] == 400.0
    assert config["dsa"]["gates"]["edge_fail_closed"] is True


def test_schema_accepts_casey_fixture_when_jsonschema_is_available() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (ROOT / "dm-toa-geometry-20260728/one-event-workflow.schema.json").read_text()
    )
    jsonschema.validate(_config(), schema)


def test_event_substitution_cannot_retain_casey_paths() -> None:
    config = _config()
    config["event"] = "replacement"
    with pytest.raises(ValueError):
        validate_config(config)


def test_event_substitution_cannot_retain_casey_dms_or_support_binding() -> None:
    config = _substituted_config()
    with pytest.raises(ValueError, match="event binding mismatch"):
        validate_config(config)


def test_reviewed_basename_and_known_cross_event_token_are_fail_closed() -> None:
    basename = _config()
    basename["paths"]["raw_chime_h5"] = basename["paths"]["raw_chime_h5"].replace(
        "singlebeam_362593221.h5",
        "casey-other.h5",
    )
    basename["event_binding_sha256"] = event_binding_sha256(basename)
    with pytest.raises(ValueError, match="basename differs"):
        validate_config(basename)
    cross_event = _config()
    cross_event["paths"]["raw_chime_h5"] = (
        "/data/Faber2026/data/chime-frb/chromatica/singlebeam_362593221.h5"
    )
    cross_event["event_binding_sha256"] = event_binding_sha256(cross_event)
    with pytest.raises(ValueError, match="cross-event path token"):
        validate_config(cross_event)


def test_full_config_binding_rejects_every_science_or_runtime_mutation() -> None:
    for mutation in (
        "dm",
        "support",
        "threshold",
        "grid",
        "crop",
        "status",
        "container",
        "stages",
    ):
        config = _config()
        if mutation == "dm":
            config["chime"]["anchor_dm_pc_cm3"] += 0.01
        elif mutation == "support":
            config["chime"]["accepted_support"][
                "h5_present_accepted_dead_ids"
            ][0] = 2
        elif mutation == "threshold":
            config["chime"]["gates"]["oracle_material_threshold_pc_cm3"] += 0.001
        elif mutation == "grid":
            config["chime"]["grid"]["fine_step_pc_cm3"] += 0.0001
        elif mutation == "crop":
            config["dsa"]["padding_samples"] += 1
        elif mutation == "status":
            config["result_status"] += "_changed"
        elif mutation == "container":
            config["workflow"]["container_data_mount"] = "/different-data"
        else:
            config["workflow"]["stages"] = config["workflow"]["stages"][:-1]
        with pytest.raises(ValueError, match="event binding mismatch|workflow.stages"):
            validate_config(config)


def test_manual_masks_and_relaxed_fixed_gates_are_rejected() -> None:
    mutations = []
    config = _config()
    config["chime"]["accepted_support"]["manual_bad_channel_ids"] = [1]
    mutations.append(config)
    config = _config()
    config["dsa"]["accepted_support"]["manual_bad_channel_ids"] = [1]
    mutations.append(config)
    config = _config()
    config["dsa"]["gates"]["edge_fail_closed"] = False
    mutations.append(config)
    config = _config()
    config["chime"]["upchannel_factor"] = 8
    mutations.append(config)
    config = _config()
    config["geometry"]["reference_frequency_mhz"] = 600.0
    mutations.append(config)
    for changed in mutations:
        changed["event_binding_sha256"] = event_binding_sha256(changed)
        with pytest.raises(ValueError):
            validate_config(changed)


def test_default_dry_run_lists_all_stages_and_writes_nothing(tmp_path: Path) -> None:
    config = _config()
    output_root = tmp_path / "casey-output"
    config["paths"]["output_root"] = str(output_root)
    config["identity"]["output_root_basename"] = output_root.name
    config["event_binding_sha256"] = event_binding_sha256(config)
    config_path = tmp_path / "casey-config.json"
    config_path.write_text(json.dumps(config))
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/run_one_event_absolute_dm_workflow.py"),
            "--config",
            str(config_path),
            "--repo-root",
            str(ROOT),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    plan = json.loads(completed.stdout)
    assert [row["stage"] for row in plan["stages"]] == list(STAGES)
    assert plan["writes_performed"] is False
    assert not output_root.exists()


def test_resume_requires_matching_output_hash(tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    output.write_text("{}")
    import hashlib

    expected = hashlib.sha256(output.read_bytes()).hexdigest()
    record = {
        "stage": "geometry",
        "status": "completed",
        "expected_outputs": [str(output)],
        "outputs": [{"path": str(output), "sha256": expected}],
    }
    assert outputs_match(record)
    output.write_text('{"changed": true}')
    assert not outputs_match(record)
    extra = tmp_path / "stale.json"
    extra.write_text("{}")
    assert not workflow_runner._output_set_exact("packet", [output])


def test_from_stage_cannot_bypass_input_rehash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*args, **kwargs):
        raise RuntimeError("rehash sentinel")

    monkeypatch.setattr(workflow_runner, "verify_inputs", fail)
    with pytest.raises(RuntimeError, match="rehash sentinel"):
        workflow_runner.execute(
            _config(),
            config_path=CONFIG,
            repo_root=ROOT,
            from_stage="geometry",
            through_stage="geometry",
            force_stage=set(),
        )


def test_execute_keeps_packet_provenance_and_manifest_hashes_immutable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config()
    names = {
        "raw_chime_h5": "casey-raw-chime.h5",
        "accepted_chime_reference": "casey-chime-reference.npy",
        "raw_dsa_filterbank": "casey-raw-dsa.fil",
        "accepted_dsa_reference": "casey-dsa-reference.npy",
        "timing_results": "casey-timing.json",
        "trigger_recovery": "casey-trigger.json",
        "reproduction_fixture": "casey-fixture.json",
    }
    for key, name in names.items():
        path = tmp_path / name
        path.write_bytes(f"{key}\n".encode())
        config["paths"][key] = str(path)
        config["identity"]["input_basenames"][key] = name
        config["input_sha256"][key] = workflow_runner.sha256_file(path)
    output_root = tmp_path / "casey-workflow"
    config["paths"]["output_root"] = str(output_root)
    config["identity"]["output_root_basename"] = output_root.name
    config["workflow"]["container_data_mount"] = str(tmp_path)
    config["event_binding_sha256"] = event_binding_sha256(config)
    binding = config["event_binding_sha256"]
    config_path = tmp_path / "casey-workflow-config.json"
    config_path.write_text(json.dumps(config))

    calls: list[list[str]] = []

    def argument(command: list[str], flag: str) -> Path:
        return Path(command[command.index(flag) + 1])

    def write_json(path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def fake_run(command: list[str], check: bool) -> None:
        assert check is True
        calls.append(command)
        joined = " ".join(command)
        if "audit_one_event_dsa_state_h17.py" in joined:
            write_json(
                argument(command, "--output"),
                {
                    "schema_version": 1,
                    "event": "casey",
                    "event_binding_sha256": binding,
                },
            )
        elif "run_one_event_hybrid_absolute_dm_h17.py" in joined:
            output = argument(command, "--output-dir")
            write_json(
                output / "chime_hybrid_result.json",
                {
                    "schema_version": 1,
                    "burst": "casey",
                    "event_binding_sha256": binding,
                },
            )
            for name in (
                "chime_anchor_before_residual.npz",
                "chime_hybrid_fit_dm.npz",
                "chime_geometry_dm.npz",
            ):
                (output / name).write_bytes(name.encode())
        elif "build_one_event_dsa_hybrid_h17.py" in joined:
            output = argument(command, "--output-dir")
            write_json(
                output / "dsa_hybrid_result.json",
                {
                    "schema_version": 1,
                    "burst": "casey",
                    "event_binding_sha256": binding,
                },
            )
            for name in (
                "dsa_input_dm.npz",
                "dsa_accepted_reference_dm.npz",
                "dsa_anchor_dm.npz",
                "dsa_hybrid_fit_dm.npz",
                "dsa_geometry_dm.npz",
            ):
                (output / name).write_bytes(name.encode())
        elif "recompute_geometry_dm.py" in joined:
            write_json(
                argument(command, "--output"),
                {
                    "schema_version": 2,
                    "event_binding_sha256": binding,
                    "method": {"reference_frequency_mhz": 400.0},
                    "results": [
                        {
                            "burst": "casey",
                            "geometry_aligning_dm_pc_cm3": config["geometry"][
                                "geometry_dm_pc_cm3"
                            ],
                        }
                    ],
                },
            )
        elif "render_one_event_hybrid_packet.py" in joined:
            provenance = argument(command, "--run-provenance")
            svg = argument(command, "--output-svg")
            png = argument(command, "--output-png")
            svg.parent.mkdir(parents=True, exist_ok=True)
            svg.write_text("<svg/>")
            png.write_bytes(b"png")
            write_json(
                argument(command, "--receipt"),
                {
                    "schema_version": 1,
                    "burst": "casey",
                    "event_binding_sha256": binding,
                    "inputs": {
                        "run_provenance": {
                            "sha256": workflow_runner.sha256_file(provenance)
                        }
                    },
                },
            )
        else:
            raise AssertionError(command)

    monkeypatch.setattr(workflow_runner.subprocess, "run", fake_run)
    state = workflow_runner.execute(
        config,
        config_path=config_path,
        repo_root=ROOT,
        from_stage=STAGES[0],
        through_stage=STAGES[-1],
        force_stage=set(),
    )
    paths = workflow_runner._output_paths(config)
    receipt = json.loads(paths["packet_receipt"].read_text())
    assert receipt["inputs"]["run_provenance"]["sha256"] == (
        workflow_runner.sha256_file(paths["provenance"])
    )
    manifest = json.loads(paths["manifest"].read_text())
    for item in manifest["products"]:
        assert workflow_runner.sha256_file(item["path"]) == item["sha256"]
    call_count = len(calls)
    resumed = workflow_runner.execute(
        config,
        config_path=config_path,
        repo_root=ROOT,
        from_stage=STAGES[0],
        through_stage=STAGES[-1],
        force_stage=set(),
    )
    assert len(calls) == call_count
    assert resumed["stages"]["manifests"]["status"] == "completed"
    assert state["event_binding_sha256"] == binding
    provenance_bytes = paths["provenance"].read_bytes()
    paths["provenance"].write_text('{"tampered": true}')
    with pytest.raises(RuntimeError, match="provenance differs"):
        workflow_runner.execute(
            config,
            config_path=config_path,
            repo_root=ROOT,
            from_stage="packet",
            through_stage="packet",
            force_stage=set(),
        )
    paths["provenance"].write_bytes(provenance_bytes)
    (paths["root"] / "unexpected-root-file.txt").write_text("unexpected")
    with pytest.raises(RuntimeError, match="unexpected workflow-root output"):
        workflow_runner.execute(
            config,
            config_path=config_path,
            repo_root=ROOT,
            from_stage="preflight",
            through_stage="preflight",
            force_stage=set(),
        )


def test_generic_sources_contain_no_event_fixture_literal() -> None:
    paths = [
        "scripts/one_event_hybrid_dm.py",
        "scripts/audit_one_event_dsa_state_h17.py",
        "scripts/run_one_event_hybrid_absolute_dm_h17.py",
        "scripts/build_one_event_dsa_hybrid_h17.py",
        "scripts/render_one_event_hybrid_packet.py",
        "scripts/run_one_event_absolute_dm_workflow.py",
    ]
    for relative in paths:
        assert "casey" not in (ROOT / relative).read_text().lower()
