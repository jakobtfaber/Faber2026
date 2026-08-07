from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import generate_phase_b_workflow_configs as config_generator  # noqa: E402
import inventory_absolute_dm_inputs_h17 as input_inventory  # noqa: E402
import preflight_phase_b_workflows_h17 as phase_b_preflight  # noqa: E402
import run_authorized_workflows_h17 as campaign_runner  # noqa: E402
import run_one_event_absolute_dm_workflow as workflow_runner  # noqa: E402
from fit_one_event_joint_burst import _require_locked_product_metadata  # noqa: E402
from one_event_workflow import (  # noqa: E402
    STAGES,
    apply_review_decision,
    authorize_reviewed_config,
    build_review_decision_template,
    event_binding_sha256,
    load_config,
    validate_config,
    validate_resolution_lock,
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
    for instrument in ("chime", "dsa"):
        config["joint_fit"]["resolution"][
            f"{instrument}_fit_frequency_average_factor"
        ] = 1
        config["joint_fit"]["resolution"][f"{instrument}_fit_time_average_factor"] = 1
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


def _resolution_products(tmp_path: Path) -> dict[str, Path]:
    paths = workflow_runner._output_paths(
        {
            "event": "casey",
            "paths": {"output_root": str(tmp_path)},
        }
    )
    for instrument, path in (
        ("chime", paths["chime_dir"] / "chime_anchor_before_residual.npz"),
        ("dsa", paths["dsa_dir"] / "dsa_anchor_dm.npz"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        waterfall = np.arange(24, dtype=np.float32).reshape(3, 8)
        if instrument == "dsa":
            waterfall = waterfall + np.float32(100.0)
        np.savez_compressed(
            path,
            waterfall=waterfall,
            pixel_valid=np.ones_like(waterfall, dtype=bool),
            noise_estimation_mask=np.ones_like(waterfall, dtype=bool),
            noise_std=np.asarray([1.0, 1.5, 2.0], dtype=np.float64),
            frequency_mhz=np.asarray([400.0, 401.0, 402.0], dtype=np.float64),
            channel_width_mhz=np.ones(3, dtype=np.float64),
            sample_interval_s=np.asarray(2.56e-6, dtype=np.float64),
            frequency_bin_factor=np.asarray(1),
            time_bin_factor=np.asarray(2),
            time0_unix_ns=np.asarray(1_700_000_000_000_000_000, dtype=np.int64),
        )
    return paths


def _complete_fit_resolution_lock(proposal: dict) -> dict:
    completed = copy.deepcopy(proposal)
    for instrument in ("chime", "dsa"):
        completed[f"{instrument}_fit_frequency_average_factor"] = 1
        completed[f"{instrument}_fit_time_average_factor"] = 1
        completed[f"{instrument}_fit_observation_sha256"] = completed[
            f"{instrument}_waterfall_sha256"
        ]
        completed[f"{instrument}_max_residual_intra_bin_smearing_s"] = 0.0
        completed[f"{instrument}_smearing_calculation_sha256"] = completed[
            f"{instrument}_frequency_grid_sha256"
        ]
    return completed


def test_resolution_lock_binds_pixels_noise_and_time_axis(tmp_path: Path) -> None:
    paths = _resolution_products(tmp_path)
    proposal = _complete_fit_resolution_lock(
        workflow_runner.resolution_lock_proposal(paths)
    )

    for instrument in ("chime", "dsa"):
        assert len(proposal[f"{instrument}_waterfall_sha256"]) == 64
        assert len(proposal[f"{instrument}_noise_std_sha256"]) == 64
        assert len(proposal[f"{instrument}_time_axis_sha256"]) == 64

    proposal["status"] = "reviewed"
    proposal["crop_and_off_pulse_padding_locked"] = True
    validate_resolution_lock(proposal)


@pytest.mark.parametrize(
    ("array_name", "message"),
    (
        ("waterfall", "locked waterfall pixels changed"),
        ("noise_std", "locked noise estimates changed"),
    ),
)
def test_fit_preflight_rejects_changed_science_arrays_before_sampling(
    tmp_path: Path,
    array_name: str,
    message: str,
) -> None:
    paths = _resolution_products(tmp_path)
    resolution = workflow_runner.resolution_lock_proposal(paths)
    product_path = paths["chime_dir"] / "chime_anchor_before_residual.npz"
    with np.load(product_path, allow_pickle=False) as original:
        payload = {key: original[key] for key in original.files}
    payload[array_name] = np.asarray(payload[array_name]).copy()
    payload[array_name].flat[0] += 1
    np.savez_compressed(product_path, **payload)

    with np.load(product_path, allow_pickle=False) as changed:
        with pytest.raises(ValueError, match=message):
            _require_locked_product_metadata(changed, "chime", resolution)


def test_fit_preflight_rejects_changed_time_axis_before_sampling(tmp_path: Path) -> None:
    paths = _resolution_products(tmp_path)
    resolution = workflow_runner.resolution_lock_proposal(paths)
    product_path = paths["chime_dir"] / "chime_anchor_before_residual.npz"
    with np.load(product_path, allow_pickle=False) as original:
        payload = {key: original[key] for key in original.files}
    payload["sample_interval_s"] = np.asarray(3.0e-6, dtype=np.float64)
    np.savez_compressed(product_path, **payload)

    with np.load(product_path, allow_pickle=False) as changed:
        with pytest.raises(ValueError, match="locked time axis changed"):
            _require_locked_product_metadata(changed, "chime", resolution)


def test_ready_resolution_requires_science_array_hashes(tmp_path: Path) -> None:
    proposal = _complete_fit_resolution_lock(
        workflow_runner.resolution_lock_proposal(_resolution_products(tmp_path))
    )
    proposal["status"] = "reviewed"
    proposal["crop_and_off_pulse_padding_locked"] = True
    del proposal["chime_waterfall_sha256"]

    with pytest.raises(ValueError, match="chime_waterfall_sha256"):
        validate_resolution_lock(proposal)


def test_ready_schema_requires_science_array_hashes(tmp_path: Path) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / "analysis-configs/absolute-dm/schema.json").read_text())
    config = _config()
    joint_fit = config["joint_fit"]
    joint_fit.update(
        {
            "status": "ready",
            "execution_authorized": True,
            "blockers": [],
            "components": [
                {
                    "instrument": instrument,
                    "component_id": f"{instrument}_c1",
                    "center_sample": 4.0,
                    "half_width_samples": 2.0,
                    "width_bounds_s": [1.0e-5, 1.0e-3],
                    "width_index_bounds": [-2.0, 2.0],
                }
                for instrument in ("chime", "dsa")
            ],
            "associations": joint_fit["review_plan"]["association_hypotheses"],
            "dm_bounds_pc_cm3": [491.0, 491.5],
            "morphologies": ["gaussian"],
            "scattering_tau_1ghz_bounds_s": [1.0e-6, 1.0e-3],
            "scattering_alpha_bounds": [-5.0, -3.0],
            "gain_variance": 1.0,
            "sampler": {"seed": 1, "nlive": 20, "dlogz": 1.0},
                "acceptance": {
                    "maximum_reduced_residual_power": 2.0,
                    "maximum_structured_residual_correlation": 0.5,
                    "posterior_edge_fraction": 0.1,
                    "maximum_prior_edge_mass": 0.1,
                    "resolution_convergence_required": True,
                    "maximum_resolution_dm_shift_combined_sigma": 0.5,
                    "maximum_resolution_dm_shift_pc_cm3": 0.005,
                    "maximum_resolution_toa_shift_combined_sigma": 0.5,
                    "resolution_interval_width_ratio": [0.8, 1.25],
                    "maximum_resolution_model_weight_l1_difference": 0.1,
                },
            "review_decision": {
                "status": "approved",
                "event": "casey",
                "source_event_binding_sha256": "1" * 64,
                "component_proposal_sha256": "2" * 64,
                "resolution_proposal_sha256": "3" * 64,
                "fit_settings_sha256": "4" * 64,
                "components_sha256": "5" * 64,
                "associations_sha256": "6" * 64,
                "approved_resolution_sha256": "7" * 64,
                "reviewer": "reviewer",
                "review_date": "2026-07-29",
                "note": "test",
            },
            "authorization": {
                "status": "explicitly_authorized",
                "source_reviewed_event_binding_sha256": "8" * 64,
                "date": "2026-07-29",
                "note": "test",
                "requires_receipt_rebuild": [
                    "preflight",
                    "dsa_audit",
                    "chime_products",
                    "dsa_products",
                    "geometry_constraint",
                ],
            },
        }
    )
    resolution = _complete_fit_resolution_lock(
        workflow_runner.resolution_lock_proposal(_resolution_products(tmp_path))
    )
    resolution["status"] = "reviewed"
    resolution["crop_and_off_pulse_padding_locked"] = True
    joint_fit["resolution"] = resolution
    jsonschema.validate(config, schema)

    del resolution["dsa_noise_std_sha256"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(config, schema)


def _approved_transition_inputs(tmp_path: Path) -> tuple[dict, dict, dict]:
    config = _config()
    resolution = _complete_fit_resolution_lock(
        workflow_runner.resolution_lock_proposal(_resolution_products(tmp_path))
    )
    components = [
        {
            "instrument": instrument,
            "component_id": f"{instrument}_c1",
            "center_sample": 4.0,
            "half_width_samples": 2.0,
            "matched_filter_width_samples": 2,
            "width_bounds_s": [1.0e-5, 1.0e-3],
        }
        for instrument in ("chime", "dsa")
    ]
    proposal = {
        "schema_version": 1,
        "status": "proposal_pending_owner_review",
        "approved": False,
        "event": "casey",
        "event_binding_sha256": config["event_binding_sha256"],
        "review_plan": copy.deepcopy(config["joint_fit"]["review_plan"]),
        "observation_contracts": {
            instrument: {
                "sample_interval_s": resolution[
                    f"{instrument}_sample_interval_s"
                ],
                "shape": resolution[f"{instrument}_shape"],
                "frequency_grid_sha256": resolution[
                    f"{instrument}_frequency_grid_sha256"
                ],
                "valid_mask_sha256": resolution[
                    f"{instrument}_valid_mask_sha256"
                ],
            }
            for instrument in ("chime", "dsa")
        },
        "components": components,
        "association_hypotheses": copy.deepcopy(
            config["joint_fit"]["review_plan"]["association_hypotheses"]
        ),
    }
    template = build_review_decision_template(
        config,
        component_proposal=proposal,
        component_proposal_sha256="1" * 64,
        resolution_proposal=resolution,
        resolution_proposal_sha256="2" * 64,
    )
    template.update(
        {
            "status": "approved",
            "approved": True,
            "reviewer": "independent reviewer",
            "review_date": "2026-07-29",
            "note": "C1D1 windows and fit grids approved",
        }
    )
    template["resolution_lock"]["status"] = "reviewed"
    template["resolution_lock"]["crop_and_off_pulse_padding_locked"] = True
    return config, proposal, template


def test_review_and_authorization_are_separate_bound_transitions(tmp_path: Path) -> None:
    config, proposal, decision = _approved_transition_inputs(tmp_path)
    original = copy.deepcopy(config)
    resolution = copy.deepcopy(decision["resolution_lock"])
    resolution["status"] = "pending_owner_review"
    resolution["crop_and_off_pulse_padding_locked"] = False

    reviewed = apply_review_decision(
        config,
        decision,
        component_proposal=proposal,
        component_proposal_sha256="1" * 64,
        resolution_proposal=resolution,
        resolution_proposal_sha256="2" * 64,
    )

    assert config == original
    assert reviewed["joint_fit"]["status"] == "reviewed_execution_disabled"
    assert reviewed["joint_fit"]["execution_authorized"] is False
    assert reviewed["workflow"]["execution_authorized"] is False
    assert reviewed["event_binding_sha256"] != config["event_binding_sha256"]
    validate_config(reviewed)
    changed_components = copy.deepcopy(reviewed)
    changed_components["joint_fit"]["components"][0]["center_sample"] += 1
    changed_components["event_binding_sha256"] = event_binding_sha256(
        changed_components
    )
    with pytest.raises(ValueError, match="reviewed components changed"):
        validate_config(changed_components)

    authorized = authorize_reviewed_config(
        reviewed,
        note="Owner delegated Casey science execution after independent review",
        authorization_date="2026-07-29",
    )
    assert reviewed["joint_fit"]["execution_authorized"] is False
    assert authorized["joint_fit"]["status"] == "ready"
    assert authorized["joint_fit"]["execution_authorized"] is True
    assert authorized["workflow"]["execution_authorized"] is True
    assert authorized["event_binding_sha256"] != reviewed["event_binding_sha256"]
    assert authorized["joint_fit"]["authorization"]["requires_receipt_rebuild"] == list(
        STAGES[:5]
    )
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / "analysis-configs/absolute-dm/schema.json").read_text())
    jsonschema.validate(reviewed, schema)
    jsonschema.validate(authorized, schema)


def test_review_decision_rejects_source_identity_drift(tmp_path: Path) -> None:
    config, proposal, decision = _approved_transition_inputs(tmp_path)
    changed = copy.deepcopy(config)
    changed["chime"]["anchor_dm_pc_cm3"] += 0.001
    changed["event_binding_sha256"] = event_binding_sha256(changed)
    resolution = copy.deepcopy(decision["resolution_lock"])
    resolution["status"] = "pending_owner_review"
    resolution["crop_and_off_pulse_padding_locked"] = False

    with pytest.raises(ValueError, match="source_event_binding_sha256"):
        apply_review_decision(
            changed,
            decision,
            component_proposal=proposal,
            component_proposal_sha256="1" * 64,
            resolution_proposal=resolution,
            resolution_proposal_sha256="2" * 64,
        )


@pytest.mark.parametrize("center_sample", [-1.0, 10_000.0])
def test_review_decision_rejects_component_outside_fit_grid(
    tmp_path: Path,
    center_sample: float,
) -> None:
    config, proposal, decision = _approved_transition_inputs(tmp_path)
    proposal["components"][0]["center_sample"] = center_sample
    resolution = copy.deepcopy(decision["resolution_lock"])
    resolution["status"] = "pending_owner_review"
    resolution["crop_and_off_pulse_padding_locked"] = False

    with pytest.raises(ValueError, match="outside the approved fit grid"):
        apply_review_decision(
            config,
            decision,
            component_proposal=proposal,
            component_proposal_sha256="1" * 64,
            resolution_proposal=resolution,
            resolution_proposal_sha256="2" * 64,
        )


def test_review_decision_rejects_components_from_another_grid(tmp_path: Path) -> None:
    config, proposal, decision = _approved_transition_inputs(tmp_path)
    proposal["observation_contracts"]["chime"]["shape"][1] += 1
    resolution = copy.deepcopy(decision["resolution_lock"])
    resolution["status"] = "pending_owner_review"
    resolution["crop_and_off_pulse_padding_locked"] = False

    with pytest.raises(ValueError, match="another fit grid"):
        apply_review_decision(
            config,
            decision,
            component_proposal=proposal,
            component_proposal_sha256="1" * 64,
            resolution_proposal=resolution,
            resolution_proposal_sha256="2" * 64,
        )


def test_public_transition_modes_write_new_configs_only(tmp_path: Path) -> None:
    config, proposal, _ = _approved_transition_inputs(tmp_path)
    source = tmp_path / "blocked.json"
    component_path = tmp_path / "component-proposal.json"
    resolution_path = tmp_path / "resolution-lock-proposal.json"
    decision_path = tmp_path / "review-decision.json"
    reviewed_path = tmp_path / "reviewed.json"
    authorized_path = tmp_path / "authorized.json"
    source.write_text(json.dumps(config))
    component_path.write_text(json.dumps(proposal))
    resolution = _complete_fit_resolution_lock(
        workflow_runner.resolution_lock_proposal(_resolution_products(tmp_path / "locks"))
    )
    resolution_path.write_text(json.dumps(resolution))
    decision = build_review_decision_template(
        config,
        component_proposal=proposal,
        component_proposal_sha256=workflow_runner.sha256_file(component_path),
        resolution_proposal=resolution,
        resolution_proposal_sha256=workflow_runner.sha256_file(resolution_path),
    )
    decision.update(
        {
            "status": "approved",
            "approved": True,
            "reviewer": "independent reviewer",
            "review_date": "2026-07-29",
            "note": "approved exact fit-grid proposal",
        }
    )
    decision["resolution_lock"]["status"] = "reviewed"
    decision["resolution_lock"]["crop_and_off_pulse_padding_locked"] = True
    decision_path.write_text(json.dumps(decision))
    original = source.read_bytes()

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/run_one_event_absolute_dm_workflow.py"),
            "--config",
            str(source),
            "--apply-review-decision",
            str(decision_path),
            "--component-proposal",
            str(component_path),
            "--resolution-proposal",
            str(resolution_path),
            "--output-config",
            str(reviewed_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/run_one_event_absolute_dm_workflow.py"),
            "--config",
            str(reviewed_path),
            "--authorize-reviewed-config",
            "--authorization-note",
            "explicit test authorization",
            "--authorization-date",
            "2026-07-29",
            "--output-config",
            str(authorized_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert source.read_bytes() == original
    assert json.loads(reviewed_path.read_text())["workflow"]["execution_authorized"] is False
    assert json.loads(authorized_path.read_text())["workflow"]["execution_authorized"] is True


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
    for instrument in ("chime", "dsa"):
        config["joint_fit"]["resolution"][
            f"{instrument}_fit_frequency_average_factor"
        ] = 1
        config["joint_fit"]["resolution"][f"{instrument}_fit_time_average_factor"] = 1
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

    def fake_run(
        command: list[str],
        check: bool,
        env: dict[str, str],
        cwd: Path | None = None,
    ) -> None:
        assert check is True
        assert str(ROOT) in env["PYTHONPATH"]
        if cwd is not None:
            assert cwd == ROOT
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
        elif "materialize_joint_fit_observations.py" in joined:
            output = argument(command, "--output-observation")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"fit-grid")
            write_json(
                argument(command, "--output-receipt"),
                {
                    "schema_version": 1,
                    "status": "candidate_fit_grid_pending_resolution_review",
                    "instrument": "chime" if "chime" in output.name else "dsa",
                },
            )
        elif (
            "fit_one_event_joint_burst.py" in joined
            or "fit_resolution_variant.py" in joined
        ):
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
        elif "verify_joint_fit_resolution_convergence.py" in joined:
            coarse_fit = argument(command, "--coarse-fit-result")
            write_json(
                argument(command, "--output"),
                {
                    "schema_version": 1,
                    "status": "passed",
                    "passed": True,
                    "event": "casey",
                    "input_sha256": {
                        "coarse_fit_result": workflow_runner.sha256_file(coarse_fit)
                    },
                },
            )
        elif "render_joint_fit_packet.py" in joined:
            pdf = argument(command, "--output")
            pdf.parent.mkdir(parents=True, exist_ok=True)
            pdf.write_bytes(b"%PDF-test")
        else:
            raise AssertionError(command)

    def fake_resolution_variant(
        config: dict,
        *,
        repo_root: Path,
        paths: dict[str, Path],
    ) -> None:
        assert repo_root == ROOT
        write_json(paths["fine_config"], config)
        for instrument in ("chime", "dsa"):
            observation = paths[f"fine_{instrument}_fit_observation"]
            observation.parent.mkdir(parents=True, exist_ok=True)
            observation.write_bytes(b"fine-fit-grid")
            write_json(
                paths[f"fine_{instrument}_fit_resolution"],
                {
                    "schema_version": 1,
                    "status": "candidate_fit_grid_pending_resolution_review",
                    "instrument": instrument,
                },
            )

    monkeypatch.setattr(
        workflow_runner,
        "materialize_resolution_variant",
        fake_resolution_variant,
    )
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
    # Rebuilding the fit stage deterministically rematerializes both locked
    # fit-grid observations before the sampler command.
    assert len(calls) == call_count + 3
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


def test_resolution_convergence_is_mandatory_before_packet() -> None:
    config = _config()
    paths = workflow_runner._output_paths(config)
    commands = workflow_runner.build_stage_commands(
        config,
        config_path=CONFIG,
        repo_root=ROOT,
    )
    assert STAGES.index("joint_fit") < STAGES.index("resolution_fit")
    assert STAGES.index("resolution_fit") < STAGES.index("resolution_check")
    assert STAGES.index("resolution_check") < STAGES.index("packet")
    assert paths["resolution_convergence"] in workflow_runner._stage_input_files(
        "packet",
        config,
        ROOT,
        paths,
    )
    packet = commands["packet"]
    assert packet is not None
    assert packet[packet.index("--resolution-convergence") + 1] == str(
        paths["resolution_convergence"]
    )
    resolution_controls = set(
        workflow_runner._control_files("resolution_fit", ROOT, CONFIG)
    )
    for relative in (
        "radio_pipeline/fitting/joint_burst.py",
        "radio_pipeline/fitting/products.py",
        "radio_pipeline/fitting/_pulse_kernels.py",
    ):
        assert ROOT / relative in resolution_controls


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
    dsa_audit_controls = workflow_runner._control_files("dsa_audit", ROOT, CONFIG)
    assert ROOT / "scripts/replay_one_event_timing_authorities.py" in dsa_audit_controls
    dsa_audit_inputs = workflow_runner._stage_input_files(
        "dsa_audit",
        config,
        ROOT,
        workflow_runner._output_paths(config),
    )
    assert Path(config["paths"]["trigger_recovery"]) in dsa_audit_inputs
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


def test_casey_preparation_remains_blocked_pending_mapping_decision() -> None:
    with pytest.raises(ValueError, match="mapping sensitivity is pending owner decision"):
        workflow_runner._require_preparation_geometry(_config())


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("status", "pending", "owner-approved"),
        ("rounded_tstart_allowed", True, "rounded DSA tstart"),
        ("filterbank_peak_offset_s", 0.0, "peak offset contradicts"),
        ("mapping_ambiguity_s", 0.0, "mapping ambiguity contradicts"),
        (
            "trigger_reference_frequency_status",
            "recovered_producer_fact",
            "reference-frequency status is invalid",
        ),
        (
            "trigger_reference_frequency_sensitivity_required",
            False,
            "sensitivity must remain required",
        ),
        ("filterbank_product_dm_pc_cm3", 491.0, "product DM differs"),
        ("trigger_reference_frequency_mhz", 1400.0, "geometry timing reference"),
    ],
)
def test_casey_time_origin_mutations_fail_closed(
    field: str, value: object, message: str
) -> None:
    config = _config()
    config["dsa"]["time_origin"][field] = value
    config["event_binding_sha256"] = event_binding_sha256(config)
    with pytest.raises(ValueError, match=message):
        validate_config(config)


def test_preparation_rejects_missing_dsa_time_origin() -> None:
    config = _config()
    del config["dsa"]["time_origin"]
    with pytest.raises(ValueError, match="owner-approved trigger peak anchor"):
        workflow_runner._require_preparation_geometry(config)


def test_preparation_rejects_trigger_reference_drift() -> None:
    config = _config()
    config["dsa"]["time_origin"]["trigger_reference_frequency_mhz"] = 1400.0
    with pytest.raises(ValueError, match="reference frequencies differ"):
        workflow_runner._require_preparation_geometry(config)


def _shrink_timing_prior(geometry: dict) -> None:
    geometry["clock_sigma_s"] = {
        "chime": 35.35533905932738e-6,
        "dsa": 35.35533905932738e-6,
    }
    geometry["timing_uncertainty_provenance"]["inter_site_clock_sigma_s"] = 50e-6


def test_clock_prior_remains_separate_from_mapping_ambiguity() -> None:
    config = _config()
    clock_basis = config["joint_fit"]["geometry"]["timing_uncertainty_provenance"][
        "clock_basis"
    ]
    assert "separate from the unresolved 15256/15259 mapping ambiguity" in clock_basis
    assert "covers" not in clock_basis
    _shrink_timing_prior(config["joint_fit"]["geometry"])
    config["event_binding_sha256"] = event_binding_sha256(config)
    validate_config(config)
    with pytest.raises(ValueError, match="mapping sensitivity is pending owner decision"):
        workflow_runner._require_preparation_geometry(config)


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
        _shrink_timing_prior,
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
