#!/usr/bin/env python3
"""Plan or execute the resumable one-event absolute-DM workflow."""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from one_event_workflow import (
    STAGES,
    canonical_json,
    event_binding_sha256,
    load_config,
    sha256_file,
)

CONTAINER_REPO = Path("/workflow")


def _resolve(path: str, repo_root: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else repo_root / candidate


def _output_paths(config: dict[str, Any]) -> dict[str, Path]:
    root = Path(config["paths"]["output_root"])
    return {
        "root": root,
        "state": root / "workflow-state.json",
        "provenance": root / "run-provenance.json",
        "dsa_audit": root / "dsa_state_audit.json",
        "chime_dir": root / "products" / "chime",
        "chime_result": root / "products" / "chime" / "chime_hybrid_result.json",
        "dsa_dir": root / "products" / "dsa",
        "dsa_result": root / "products" / "dsa" / "dsa_hybrid_result.json",
        "geometry": root / "geometry.json",
        "packet_svg": root / "review" / "one_event_hybrid_packet.svg",
        "packet_png": root / "review" / "one_event_hybrid_packet.png",
        "packet_receipt": root / "review" / "one_event_hybrid_packet_receipt.json",
        "manifest": root / "manifests" / "workflow-manifest.json",
    }


def _container_config(
    path: Path,
    repo_root: Path,
) -> tuple[Path, list[str]]:
    try:
        return (
            CONTAINER_REPO / path.resolve().relative_to(repo_root.resolve()),
            [],
        )
    except ValueError:
        mount = Path("/workflow-config")
        return mount / path.name, ["-v", f"{path.parent}:{mount}:ro"]


def build_stage_commands(
    config: dict[str, Any],
    *,
    config_path: Path,
    repo_root: Path,
) -> dict[str, list[str] | None]:
    """Return exact argv for each stage; no command is run here."""

    paths = _output_paths(config)
    python = sys.executable
    config_path = config_path.resolve()
    repo_root = repo_root.resolve()
    data_mount = config["workflow"]["container_data_mount"]
    container_config, config_mount = _container_config(config_path, repo_root)
    chime_command = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{data_mount}:{data_mount}",
        "-v",
        f"{repo_root}:{CONTAINER_REPO}:ro",
        *config_mount,
        config["workflow"]["chime_container_image"],
        "python3",
        str(CONTAINER_REPO / "scripts/run_one_event_hybrid_absolute_dm_h17.py"),
        "--config",
        str(container_config),
        "--output-dir",
        str(paths["chime_dir"]),
    ]
    return {
        "preflight": None,
        "dsa_audit": [
            python,
            str(repo_root / "scripts/audit_one_event_dsa_state_h17.py"),
            "--config",
            str(config_path),
            "--output",
            str(paths["dsa_audit"]),
        ],
        "chime_hybrid": chime_command,
        "dsa_products": [
            python,
            str(repo_root / "scripts/build_one_event_dsa_hybrid_h17.py"),
            "--config",
            str(config_path),
            "--chime-result",
            str(paths["chime_result"]),
            "--dsa-audit",
            str(paths["dsa_audit"]),
            "--output-dir",
            str(paths["dsa_dir"]),
        ],
        "geometry": [
            python,
            str(repo_root / "scripts/recompute_geometry_dm.py"),
            "--timing-results",
            str(_resolve(config["paths"]["timing_results"], repo_root)),
            "--trigger-recovery",
            str(_resolve(config["paths"]["trigger_recovery"], repo_root)),
            "--reproduction-fixture",
            str(_resolve(config["paths"]["reproduction_fixture"], repo_root)),
            "--event",
            config["event"],
            "--event-binding-sha256",
            config["event_binding_sha256"],
            "--output",
            str(paths["geometry"]),
        ],
        "packet": [
            python,
            str(repo_root / "scripts/render_one_event_hybrid_packet.py"),
            "--config",
            str(config_path),
            "--chime-result",
            str(paths["chime_result"]),
            "--dsa-result",
            str(paths["dsa_result"]),
            "--dsa-audit",
            str(paths["dsa_audit"]),
            "--run-provenance",
            str(paths["provenance"]),
            "--accepted-chime-reference",
            config["paths"]["accepted_chime_reference"],
            "--accepted-dsa-reference",
            config["paths"]["accepted_dsa_reference"],
            "--output-svg",
            str(paths["packet_svg"]),
            "--output-png",
            str(paths["packet_png"]),
            "--receipt",
            str(paths["packet_receipt"]),
        ],
        "manifests": None,
    }


def expected_stage_outputs(stage: str, paths: dict[str, Path]) -> list[Path]:
    if stage == "dsa_audit":
        return [paths["dsa_audit"]]
    if stage == "chime_hybrid":
        return [
            paths["chime_result"],
            paths["chime_dir"] / "chime_anchor_before_residual.npz",
            paths["chime_dir"] / "chime_hybrid_fit_dm.npz",
            paths["chime_dir"] / "chime_geometry_dm.npz",
        ]
    if stage == "dsa_products":
        return [
            paths["dsa_result"],
            paths["dsa_dir"] / "dsa_input_dm.npz",
            paths["dsa_dir"] / "dsa_accepted_reference_dm.npz",
            paths["dsa_dir"] / "dsa_anchor_dm.npz",
            paths["dsa_dir"] / "dsa_hybrid_fit_dm.npz",
            paths["dsa_dir"] / "dsa_geometry_dm.npz",
        ]
    if stage == "geometry":
        return [paths["geometry"]]
    if stage == "packet":
        return [paths["packet_svg"], paths["packet_png"], paths["packet_receipt"]]
    if stage == "manifests":
        return [paths["manifest"]]
    return []


def outputs_match(
    record: dict[str, Any],
    expected_paths: list[Path] | None = None,
) -> bool:
    """A completed stage is reusable only while every output hash still matches."""

    outputs = record.get("outputs", [])
    expected = (
        [str(path) for path in expected_paths]
        if expected_paths is not None
        else record.get("expected_outputs", [])
    )
    if sorted(item.get("path", "") for item in outputs) != sorted(expected):
        return False
    if record.get("expected_outputs") != expected:
        return False
    if not outputs and record.get("stage") != "preflight":
        return False
    for item in outputs:
        path = Path(item["path"])
        if not path.is_file() or sha256_file(path) != item["sha256"]:
            return False
    return record.get("status") == "completed"


def _hash_payload(value: Any) -> str:
    import hashlib

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _control_files(stage: str, repo_root: Path, config_path: Path) -> list[Path]:
    shared = [
        config_path,
        repo_root / "scripts/one_event_workflow.py",
        repo_root / "scripts/run_one_event_absolute_dm_workflow.py",
    ]
    stage_files = {
        "preflight": [],
        "dsa_audit": [
            repo_root / "scripts/audit_one_event_dsa_state_h17.py",
            repo_root / "scripts/absolute_dm_voltage.py",
        ],
        "chime_hybrid": [
            repo_root / "scripts/run_one_event_hybrid_absolute_dm_h17.py",
            repo_root / "scripts/one_event_hybrid_dm.py",
            repo_root / "scripts/absolute_dm_voltage.py",
        ],
        "dsa_products": [
            repo_root / "scripts/build_one_event_dsa_hybrid_h17.py",
            repo_root / "scripts/absolute_dm_voltage.py",
        ],
        "geometry": [repo_root / "scripts/recompute_geometry_dm.py"],
        "packet": [
            repo_root / "scripts/render_one_event_hybrid_packet.py",
            repo_root / "scripts/absolute_dm_voltage.py",
        ],
        "manifests": [
            repo_root / "dm-toa-geometry-20260728/one-event-workflow.schema.json"
        ],
    }
    return shared + stage_files[stage]


def stage_control_sha256(
    stage: str,
    repo_root: Path,
    config_path: Path,
) -> str:
    rows = [
        {"path": str(path), "sha256": sha256_file(path)}
        for path in _control_files(stage, repo_root, config_path)
    ]
    return _hash_payload(rows)


def _stage_input_files(
    stage: str,
    config: dict[str, Any],
    repo_root: Path,
    paths: dict[str, Path],
) -> list[Path]:
    source = config["paths"]
    if stage == "preflight":
        return [
            _resolve(source[key], repo_root) for key in config["input_sha256"]
        ]
    if stage == "dsa_audit":
        return [
            _resolve(source["raw_dsa_filterbank"], repo_root),
            _resolve(source["accepted_dsa_reference"], repo_root),
        ]
    if stage == "chime_hybrid":
        return [
            _resolve(source["raw_chime_h5"], repo_root),
            _resolve(source["accepted_chime_reference"], repo_root),
        ]
    if stage == "dsa_products":
        return [
            paths["chime_result"],
            paths["dsa_audit"],
            _resolve(source["raw_dsa_filterbank"], repo_root),
            _resolve(source["accepted_dsa_reference"], repo_root),
        ]
    if stage == "geometry":
        return [
            _resolve(source["timing_results"], repo_root),
            _resolve(source["trigger_recovery"], repo_root),
            _resolve(source["reproduction_fixture"], repo_root),
        ]
    if stage == "packet":
        return [
            paths["chime_result"],
            paths["dsa_result"],
            paths["dsa_audit"],
            paths["provenance"],
            _resolve(source["accepted_chime_reference"], repo_root),
            _resolve(source["accepted_dsa_reference"], repo_root),
        ]
    if stage == "manifests":
        return [
            path
            for path in sorted(paths["root"].rglob("*"))
            if path.is_file()
            and path not in {paths["state"], paths["manifest"]}
            and "logs" not in path.parts
        ]
    raise ValueError(f"unknown stage {stage}")


def stage_input_sha256(
    stage: str,
    config: dict[str, Any],
    repo_root: Path,
    paths: dict[str, Path],
) -> str:
    rows = [
        {"path": str(path), "sha256": sha256_file(path)}
        for path in _stage_input_files(stage, config, repo_root, paths)
    ]
    return _hash_payload(rows)


def _output_schema_matches(
    stage: str,
    config: dict[str, Any],
    paths: dict[str, Path],
) -> bool:
    if stage in {"preflight", "chime_hybrid", "dsa_products"}:
        json_path = {
            "chime_hybrid": paths["chime_result"],
            "dsa_products": paths["dsa_result"],
        }.get(stage)
        if json_path is None:
            return True
    elif stage == "dsa_audit":
        json_path = paths["dsa_audit"]
    elif stage == "geometry":
        json_path = paths["geometry"]
    elif stage == "packet":
        json_path = paths["packet_receipt"]
    elif stage == "manifests":
        json_path = paths["manifest"]
    else:
        return False
    try:
        value = json.loads(json_path.read_text())
    except (OSError, ValueError):
        return False
    if value.get("event_binding_sha256") != config["event_binding_sha256"]:
        return False
    if stage == "geometry":
        rows = value.get("results", [])
        recorded_event = rows[0].get("burst") if len(rows) == 1 else None
    else:
        recorded_event = value.get("event", value.get("burst"))
    return recorded_event == config["event"]


def _output_set_exact(stage: str, expected: list[Path]) -> bool:
    if stage not in {"chime_hybrid", "dsa_products", "packet", "manifests"}:
        return True
    if not expected:
        return False
    parent = expected[0].parent
    actual = {path for path in parent.iterdir() if path.is_file()} if parent.is_dir() else set()
    return actual == set(expected)


def _all_workflow_files(paths: dict[str, Path]) -> set[Path]:
    expected = {paths["state"], paths["provenance"]}
    for stage in STAGES:
        expected.update(expected_stage_outputs(stage, paths))
    return expected


def _workflow_output_set_valid(
    paths: dict[str, Path],
    *,
    require_complete: bool = False,
) -> bool:
    root = paths["root"]
    actual = {path for path in root.rglob("*") if path.is_file()} if root.is_dir() else set()
    expected = _all_workflow_files(paths)
    return actual == expected if require_complete else actual.issubset(expected)


def _packet_provenance_matches_receipt(paths: dict[str, Path]) -> bool:
    if not paths["provenance"].is_file() or not paths["packet_receipt"].is_file():
        return False
    try:
        receipt = json.loads(paths["packet_receipt"].read_text())
        expected = receipt["inputs"]["run_provenance"]["sha256"]
    except (OSError, ValueError, KeyError, TypeError):
        return False
    return sha256_file(paths["provenance"]) == expected


def stage_record_matches(
    record: dict[str, Any],
    *,
    stage: str,
    config: dict[str, Any],
    repo_root: Path,
    config_path: Path,
    paths: dict[str, Path],
    command: list[str] | None,
) -> bool:
    expected = expected_stage_outputs(stage, paths)
    try:
        return (
            record.get("event_binding_sha256") == config["event_binding_sha256"]
            and record.get("control_sha256")
            == stage_control_sha256(stage, repo_root, config_path)
            and record.get("command_sha256") == _hash_payload(command)
            and record.get("input_sha256")
            == stage_input_sha256(stage, config, repo_root, paths)
            and outputs_match(record, expected)
            and _output_set_exact(stage, expected)
            and _workflow_output_set_valid(paths)
            and _output_schema_matches(stage, config, paths)
        )
    except (OSError, ValueError, KeyError, TypeError):
        return False


def verify_inputs(config: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    """Hash all seven reviewed inputs; fail before any science stage."""

    checked: dict[str, Any] = {}
    for key, expected in config["input_sha256"].items():
        path = _resolve(config["paths"][key], repo_root)
        if not path.is_file():
            raise FileNotFoundError(f"{key}: input does not exist: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"{key}: SHA-256 mismatch")
        checked[key] = {"path": str(path), "sha256": actual}
    return checked


def verify_geometry_result(config: dict[str, Any], path: Path) -> None:
    result = json.loads(path.read_text())
    rows = result.get("results", [])
    if len(rows) != 1 or rows[0].get("burst", "").lower() != config["event"]:
        raise RuntimeError("geometry result does not contain exactly the configured event")
    if result.get("event_binding_sha256") != config["event_binding_sha256"]:
        raise RuntimeError("geometry result binding does not match configuration")
    actual = float(rows[0]["geometry_aligning_dm_pc_cm3"])
    expected = float(config["geometry"]["geometry_dm_pc_cm3"])
    if abs(actual - expected) > 1.0e-12:
        raise RuntimeError("recomputed geometry DM does not match configuration")
    if (
        float(result["method"]["reference_frequency_mhz"])
        != float(config["geometry"]["reference_frequency_mhz"])
    ):
        raise RuntimeError("geometry result reference frequency changed")


def _stage_window(from_stage: str, through_stage: str) -> tuple[str, ...]:
    start = STAGES.index(from_stage)
    stop = STAGES.index(through_stage)
    if start > stop:
        raise ValueError("--from-stage must not follow --through-stage")
    return STAGES[start : stop + 1]


def make_plan(
    config: dict[str, Any],
    *,
    config_path: Path,
    repo_root: Path,
    from_stage: str,
    through_stage: str,
) -> dict[str, Any]:
    commands = build_stage_commands(
        config,
        config_path=config_path,
        repo_root=repo_root,
    )
    selected = _stage_window(from_stage, through_stage)
    return {
        "schema_version": 1,
        "mode": "dry-run",
        "event": config["event"],
        "event_binding_sha256": config["event_binding_sha256"],
        "output_root": config["paths"]["output_root"],
        "stages": [
            {"stage": stage, "command": commands[stage]} for stage in selected
        ],
        "writes_performed": False,
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def _write_provenance(
    config: dict[str, Any],
    state: dict[str, Any],
    path: Path,
) -> None:
    cutoff = STAGES.index("packet")
    completed = {
        stage: record
        for stage, record in state["stages"].items()
        if stage in STAGES
        and STAGES.index(stage) < cutoff
        and record.get("status") == "completed"
    }
    _write_json(
        path,
        {
            "schema_version": 1,
            "status": config["result_status"],
            "event": config["event"],
            "event_binding_sha256": config["event_binding_sha256"],
            "host": socket.gethostname(),
            "chime_container_image": config["workflow"]["chime_container_image"],
            "immutable_cutoff": "completed stages before packet rendering",
            "stages": completed,
            "notes": [
                "one event only",
                "no manuscript value adopted",
                "completed stage outputs are reused only after hash verification",
            ],
        },
    )


def _write_manifest(
    config: dict[str, Any],
    config_path: Path,
    repo_root: Path,
    paths: dict[str, Path],
) -> None:
    controls = [
        config_path,
        repo_root / "dm-toa-geometry-20260728/one-event-workflow.schema.json",
        repo_root / "scripts/one_event_workflow.py",
        repo_root / "scripts/one_event_hybrid_dm.py",
        repo_root / "scripts/audit_one_event_dsa_state_h17.py",
        repo_root / "scripts/run_one_event_hybrid_absolute_dm_h17.py",
        repo_root / "scripts/build_one_event_dsa_hybrid_h17.py",
        repo_root / "scripts/recompute_geometry_dm.py",
        repo_root / "scripts/render_one_event_hybrid_packet.py",
        repo_root / "scripts/run_one_event_absolute_dm_workflow.py",
    ]
    products = [
        path
        for path in sorted(paths["root"].rglob("*"))
        if path.is_file()
        and path not in {paths["state"], paths["manifest"]}
        and "logs" not in path.parts
    ]
    _write_json(
        paths["manifest"],
        {
            "schema_version": 1,
            "event": config["event"],
            "event_binding_sha256": config["event_binding_sha256"],
            "controls": [
                {"path": str(path), "sha256": sha256_file(path)}
                for path in controls
            ],
            "products": [
                {"path": str(path), "sha256": sha256_file(path)}
                for path in products
            ],
        },
    )


def execute(
    config: dict[str, Any],
    *,
    config_path: Path,
    repo_root: Path,
    from_stage: str,
    through_stage: str,
    force_stage: set[str],
) -> dict[str, Any]:
    paths = _output_paths(config)
    commands = build_stage_commands(
        config,
        config_path=config_path,
        repo_root=repo_root,
    )
    verified_inputs = verify_inputs(config, repo_root)
    if paths["state"].is_file():
        state = json.loads(paths["state"].read_text())
        if state.get("event_binding_sha256") != config["event_binding_sha256"]:
            raise RuntimeError("state belongs to another event binding")
    else:
        state = {
            "schema_version": 1,
            "event": config["event"],
            "event_binding_sha256": config["event_binding_sha256"],
            "stages": {},
        }

    selected_stages = _stage_window(from_stage, through_stage)
    for prerequisite in STAGES[: STAGES.index(from_stage)]:
        if not stage_record_matches(
            state["stages"].get(prerequisite, {}),
            stage=prerequisite,
            config=config,
            repo_root=repo_root,
            config_path=config_path,
            paths=paths,
            command=commands[prerequisite],
        ):
            raise RuntimeError(
                f"{from_stage}: prerequisite stage {prerequisite} is not resumable"
            )

    for stage in selected_stages:
        previous = state["stages"].get(stage, {})
        if (
            stage == "packet"
            and previous.get("status") == "completed"
            and stage not in force_stage
            and not _packet_provenance_matches_receipt(paths)
        ):
            raise RuntimeError(
                "packet provenance differs from its receipt; inspect and use "
                "--force-stage packet only after review"
            )
        if stage not in force_stage and stage_record_matches(
            previous,
            stage=stage,
            config=config,
            repo_root=repo_root,
            config_path=config_path,
            paths=paths,
            command=commands[stage],
        ):
            print(f"resume: {stage} output hashes match", flush=True)
            continue
        if stage == "packet":
            _write_provenance(config, state, paths["provenance"])
        started = time.time()
        expected_outputs = expected_stage_outputs(stage, paths)
        record: dict[str, Any] = {
            "stage": stage,
            "status": "running",
            "started_unix": started,
            "event_binding_sha256": config["event_binding_sha256"],
            "command": commands[stage],
            "command_sha256": _hash_payload(commands[stage]),
            "control_sha256": stage_control_sha256(
                stage,
                repo_root,
                config_path,
            ),
            "input_sha256": stage_input_sha256(
                stage,
                config,
                repo_root,
                paths,
            ),
            "expected_outputs": [str(path) for path in expected_outputs],
            "outputs": [],
        }
        state["stages"][stage] = record
        _write_json(paths["state"], state)
        if stage == "preflight":
            record["verified_inputs"] = verified_inputs
        elif stage == "packet":
            subprocess.run(commands[stage], check=True)
        elif stage == "manifests":
            _write_manifest(config, config_path, repo_root, paths)
        else:
            subprocess.run(commands[stage], check=True)
            if stage == "geometry":
                verify_geometry_result(config, paths["geometry"])
        completed = time.time()
        outputs = [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in expected_outputs
        ]
        if not _output_set_exact(stage, expected_outputs):
            raise RuntimeError(f"{stage}: unexpected output file set")
        if not _workflow_output_set_valid(paths):
            raise RuntimeError(f"{stage}: unexpected workflow-root output")
        record.update(
            {
                "status": "completed",
                "completed_unix": completed,
                "wall_seconds": completed - started,
                "outputs": outputs,
            }
        )
        if not _output_schema_matches(stage, config, paths):
            raise RuntimeError(f"{stage}: output schema or event binding mismatch")
        _write_json(paths["state"], state)
    if through_stage == STAGES[-1] and not _workflow_output_set_valid(
        paths,
        require_complete=True,
    ):
        raise RuntimeError("final workflow output set is incomplete or unexpected")
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--print-binding", action="store_true")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--from-stage", choices=STAGES, default=STAGES[0])
    parser.add_argument("--through-stage", choices=STAGES, default=STAGES[-1])
    parser.add_argument("--force-stage", choices=STAGES, action="append", default=[])
    parser.add_argument(
        "--check-inputs",
        action="store_true",
        help="hash all inputs during dry-run; execute always hashes them",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    config_path = args.config.resolve()
    if args.print_binding:
        print(event_binding_sha256(json.loads(config_path.read_text())))
        return
    config = load_config(
        config_path,
        require_execution_authorized=args.execute,
    )
    if not args.execute:
        plan = make_plan(
            config,
            config_path=config_path,
            repo_root=repo_root,
            from_stage=args.from_stage,
            through_stage=args.through_stage,
        )
        if args.check_inputs:
            plan["verified_inputs"] = verify_inputs(config, repo_root)
        print(canonical_json(plan))
        return
    state = execute(
        config,
        config_path=config_path,
        repo_root=repo_root,
        from_stage=args.from_stage,
        through_stage=args.through_stage,
        force_stage=set(args.force_stage),
    )
    print(json.dumps(state, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
