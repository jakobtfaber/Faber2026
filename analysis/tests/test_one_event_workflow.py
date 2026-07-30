from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_phase_b_workflow_configs as config_generator  # noqa: E402
import inventory_absolute_dm_inputs_h17 as input_inventory  # noqa: E402
import preflight_phase_b_workflows_h17 as phase_b_preflight  # noqa: E402
import run_authorized_workflows_h17 as campaign_runner  # noqa: E402
import run_one_event_absolute_dm_workflow as workflow_runner  # noqa: E402
from one_event_workflow import (  # noqa: E402
    STAGES,
    event_binding_sha256,
    load_config,
    validate_config,
)
from run_one_event_absolute_dm_workflow import outputs_match  # noqa: E402

CONFIG = ROOT / "analysis-configs/absolute-dm/casey.json"


def _config() -> dict:
    return json.loads(CONFIG.read_text())


def _local_execution_config(tmp_path: Path) -> tuple[dict, Path]:
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
    config_path = tmp_path / "casey-workflow-config.json"
    config_path.write_text(json.dumps(config))
    return config, config_path


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
        config["identity"]["input_basenames"][key] = Path(config["paths"][key]).name
    config["identity"]["output_root_basename"] = Path(config["paths"]["output_root"]).name
    return config


def test_casey_regression_fixture_validates() -> None:
    config = load_config(CONFIG)
    assert config["event"] == "casey"
    assert config["chime"]["upchannel_factor"] == 16
    assert config["geometry"]["reference_frequency_mhz"] == 400.0
    assert config["dsa"]["gates"]["edge_fail_closed"] is True


def test_schema_accepts_casey_fixture_when_jsonschema_is_available() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / "analysis-configs/absolute-dm/schema.json").read_text())
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
            config["chime"]["accepted_support"]["h5_present_accepted_dead_ids"][0] = 2
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


def test_casey_execution_fails_before_inputs_while_joint_review_is_blocked() -> None:
    with pytest.raises(PermissionError, match="joint fit is blocked"):
        load_config(CONFIG, require_execution_authorized=True)


def test_resume_requires_matching_output_hash(tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    output.write_text("{}")
    import hashlib

    expected = hashlib.sha256(output.read_bytes()).hexdigest()
    record = {
        "stage": "geometry_constraint",
        "status": "completed",
        "expected_outputs": [str(output)],
        "outputs": [{"path": str(output), "sha256": expected}],
    }
    assert outputs_match(record)
    output.write_text('{"changed": true}')
    assert not outputs_match(record)
    extra = tmp_path / "stale.json"
    extra.write_text("{}")
    assert not workflow_runner._output_set_exact("manifests", [output])


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
            from_stage="geometry_constraint",
            through_stage="geometry_constraint",
            force_stage=set(),
        )


def test_failed_stage_is_durable_and_retry_requires_explicit_flag(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, config_path = _local_execution_config(tmp_path)
    monkeypatch.setenv("ONE_EVENT_WORKFLOW_STDOUT_LOG", "/logs/casey.stdout")
    monkeypatch.setenv("ONE_EVENT_WORKFLOW_STDERR_LOG", "/logs/casey.stderr")

    def injected_failure(command: list[str], check: bool, env: dict[str, str]) -> None:
        assert check is True
        assert str(ROOT) in env["PYTHONPATH"]
        raise subprocess.CalledProcessError(23, command)

    monkeypatch.setattr(workflow_runner.subprocess, "run", injected_failure)
    with pytest.raises(subprocess.CalledProcessError):
        workflow_runner.execute(
            config,
            config_path=config_path,
            repo_root=ROOT,
            from_stage="preflight",
            through_stage="dsa_audit",
            force_stage=set(),
        )

    state_path = workflow_runner._output_paths(config)["state"]
    failed_bytes = state_path.read_bytes()
    failed = json.loads(failed_bytes)
    assert failed["status"] == "failed"
    assert failed["failed_stage"] == "dsa_audit"
    assert failed["stages"]["preflight"]["status"] == "completed"
    record = failed["stages"]["dsa_audit"]
    assert record["status"] == "failed"
    assert record["error"]["type"] == "CalledProcessError"
    assert "exit status 23" in record["error"]["message"]
    assert record["failed_unix"] >= record["started_unix"]
    assert record["wall_seconds"] >= 0
    assert record["outputs"] == []
    assert record["log_refs"] == {
        "stderr": "/logs/casey.stderr",
        "stdout": "/logs/casey.stdout",
    }

    with pytest.raises(RuntimeError, match="--retry-failed-stage dsa_audit"):
        workflow_runner.execute(
            config,
            config_path=config_path,
            repo_root=ROOT,
            from_stage="preflight",
            through_stage="dsa_audit",
            force_stage={"dsa_audit"},
        )
    assert state_path.read_bytes() == failed_bytes

    def successful_retry(command: list[str], check: bool, env: dict[str, str]) -> None:
        assert check is True
        assert str(ROOT) in env["PYTHONPATH"]
        output = Path(command[command.index("--output") + 1])
        output.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "event": "casey",
                    "event_binding_sha256": config["event_binding_sha256"],
                }
            )
        )

    monkeypatch.setattr(workflow_runner.subprocess, "run", successful_retry)
    retried = workflow_runner.execute(
        config,
        config_path=config_path,
        repo_root=ROOT,
        from_stage="preflight",
        through_stage="dsa_audit",
        force_stage=set(),
        retry_failed_stage={"dsa_audit"},
    )
    assert retried["stages"]["dsa_audit"]["status"] == "completed"
    history = retried["stages"]["dsa_audit"]["attempt_history"]
    assert len(history) == 1
    assert history[0]["status"] == "failed"
    assert history[0]["log_refs"]["stderr"] == "/logs/casey.stderr"


def test_paused_campaign_receipt_overrides_stale_config_authorization(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "analysis-configs" / "absolute-dm" / "phase-b" / "campaign-state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "campaign": "phase-b-absolute-dm",
                "status": "paused",
                "execution_authorized": False,
                "authorized_configs": {},
            }
        )
    )
    stale = _config()
    stale["workflow"]["execution_authorized"] = True
    with pytest.raises(PermissionError, match="campaign is paused"):
        campaign_runner.require_campaign_authorization(
            tmp_path,
            [(CONFIG, stale)],
        )


def test_all_parameterized_configs_are_execution_disabled_during_pause() -> None:
    campaign_state = json.loads(
        (ROOT / "analysis-configs/absolute-dm/phase-b/campaign-state.json").read_text()
    )
    assert campaign_state["status"] == "paused"
    assert campaign_state["execution_authorized"] is False
    assert campaign_state["authorized_configs"] == {}

    configs = [CONFIG]
    configs.extend(
        sorted((ROOT / "analysis-configs/absolute-dm/phase-b").glob("*/workflow-config.json"))
    )
    assert len(configs) == 12
    for path in configs:
        config = load_config(path)
        assert config["workflow"]["execution_authorized"] is False
        if config["workflow"]["regression_fixture"] is not True:
            assert config["review"]["configuration_status"] == "blocked"
            assert "campaign_paused_no_execution_authorization" in config["review"]["blockers"]


def test_phase_b_control_outputs_are_labeled_paused_and_experimental() -> None:
    statuses = (
        input_inventory.RESULT_STATUS,
        config_generator.SUMMARY_STATUS,
        phase_b_preflight.RESULT_STATUS,
    )
    for status in statuses:
        assert "phase_b_paused" in status
        assert "experimental_diagnostic" in status
        assert "not_science_authority" in status
    review = json.loads(
        (ROOT / "analysis-configs/absolute-dm/phase-b/phase-b-config-review.json").read_text()
    )
    assert review["status"] == config_generator.SUMMARY_STATUS
    assert "Phase B is currently paused" in campaign_runner.__doc__
    assert "not science authority" in campaign_runner.__doc__


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

    def fake_run(command: list[str], check: bool, env: dict[str, str]) -> None:
        assert check is True
        assert str(ROOT) in env["PYTHONPATH"]
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
            names = [
                "chime_anchor_before_residual.npz",
                "chime_hybrid_fit_dm.npz",
                "chime_geometry_dm.npz",
            ]
            if "--joint-fit-result" in command:
                names.extend(
                    f"chime_fully_coherent_posterior_{label}.npz"
                    for label in ("lower", "median", "upper")
                )
            for name in names:
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
            names = [
                "dsa_input_dm.npz",
                "dsa_accepted_reference_dm.npz",
            ]
            if "--joint-fit-result" in command:
                names.extend(f"dsa_posterior_{label}.npz" for label in ("lower", "median", "upper"))
            else:
                names.extend(
                    (
                        "dsa_anchor_dm.npz",
                        "dsa_hybrid_fit_dm.npz",
                        "dsa_geometry_dm.npz",
                    )
                )
            for name in names:
                (output / name).write_bytes(name.encode())
        elif "build_geometry_constraint.py" in joined:
            write_json(
                argument(command, "--output"),
                {
                    "schema_version": 1,
                    "status": "provisional_pending_owner_approval",
                    "event": "casey",
                    "event_binding_sha256": binding,
                    "reference_frequency_mhz": 400.0,
                },
            )
        elif "fit_one_event_joint_burst.py" in joined:
            output = argument(command, "--output-dir")
            write_json(
                output / "fit-result.json",
                {
                    "schema_version": 1,
                    "status": "provisional_pending_owner_approval",
                    "event": "casey",
                    "event_binding_sha256": binding,
                },
            )
            (output / "posterior.npz").write_bytes(b"posterior")
            (output / "model-products.npz").write_bytes(b"model")
            write_json(
                output / "run-provenance.json",
                {
                    "schema_version": 1,
                    "status": "provisional_pending_owner_approval",
                    "event": "casey",
                    "event_binding_sha256": binding,
                },
            )
        elif "verify_joint_fit_oracles.py" in joined:
            write_json(
                argument(command, "--output"),
                {
                    "schema_version": 1,
                    "status": "passed_pending_owner_visual_approval",
                    "event": "casey",
                    "event_binding_sha256": binding,
                },
            )
        elif "render_joint_fit_packet.py" in joined:
            pdf = argument(command, "--output")
            pdf.parent.mkdir(parents=True, exist_ok=True)
            pdf.write_bytes(b"%PDF-test")
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
    paths["provenance"].write_text('{"tampered": true}')
    workflow_runner.execute(
        config,
        config_path=config_path,
        repo_root=ROOT,
        from_stage="joint_fit",
        through_stage="packet",
        force_stage=set(),
    )
    assert len(calls) == call_count + 1
    assert paths["provenance"].read_text() != '{"tampered": true}'
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


def test_preparation_mode_only_relaxes_product_builder_authorization(
    tmp_path: Path,
) -> None:
    config = _config()
    commands = workflow_runner.build_stage_commands(
        config,
        config_path=tmp_path / "event.json",
        repo_root=ROOT,
        preparation_only=True,
    )
    for stage in ("dsa_audit", "chime_products", "dsa_products"):
        assert "--preparation-only" in commands[stage]
    assert "PYTHONPATH=/workflow" in commands["chime_products"]
    for stage in (
        "geometry_constraint",
        "joint_fit",
        "chime_oracle",
        "dsa_oracle",
        "oracle_check",
        "packet",
    ):
        command = commands[stage]
        if command is not None:
            assert "--preparation-only" not in command


def test_casey_preparation_geometry_is_reviewed() -> None:
    workflow_runner._require_preparation_geometry(_config())


@pytest.mark.parametrize(
    "mutate",
    [
        lambda geometry: geometry["timing_uncertainty_provenance"].update(
            status="unreviewed"
        ),
        lambda geometry: geometry["timing_uncertainty_provenance"].pop("clock_basis"),
        lambda geometry: geometry["timing_uncertainty_provenance"].update(
            inter_site_clock_sigma_s=2.0e-3
        ),
        lambda geometry: geometry["timing_uncertainty_provenance"].update(
            owner_adoption_date="not-a-date"
        ),
        lambda geometry: geometry["timing_uncertainty_provenance"].update(
            unsupported="value"
        ),
        lambda geometry: geometry.update(
            clock_sigma_s={"chime": 0.6e-3, "dsa": 0.8e-3}
        ),
    ],
)
def test_preparation_geometry_rejects_malformed_timing_budget(mutate) -> None:
    config = _config()
    mutate(config["joint_fit"]["geometry"])
    with pytest.raises(ValueError, match="no data processing started"):
        workflow_runner._require_preparation_geometry(config)


def test_preparation_geometry_fails_before_execution_without_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config()
    del config["joint_fit"]["geometry"]["timing_uncertainty_provenance"]
    config["event_binding_sha256"] = event_binding_sha256(config)
    config_path = tmp_path / "missing-timing-provenance.json"
    config_path.write_text(json.dumps(config))

    def forbidden(*args, **kwargs):
        raise AssertionError("execution started before preparation preflight")

    monkeypatch.setattr(workflow_runner, "execute", forbidden)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_one_event_absolute_dm_workflow.py",
            "--config",
            str(config_path),
            "--prepare-reviewed-inputs",
        ],
    )
    with pytest.raises(ValueError, match="no data processing started"):
        workflow_runner.main()


def test_full_execution_geometry_fails_before_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _config()
    config["joint_fit"]["geometry"]["timing_uncertainty_provenance"][
        "status"
    ] = "unreviewed"

    def forbidden(*args, **kwargs):
        raise AssertionError("execution started before timing preflight")

    monkeypatch.setattr(workflow_runner, "load_config", lambda *args, **kwargs: config)
    monkeypatch.setattr(workflow_runner, "execute", forbidden)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_one_event_absolute_dm_workflow.py",
            "--config",
            str(CONFIG),
            "--execute",
        ],
    )
    with pytest.raises(ValueError, match="no data processing started"):
        workflow_runner.main()
