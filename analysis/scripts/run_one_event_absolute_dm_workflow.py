#!/usr/bin/env python3
"""Plan or execute the resumable one-event absolute-DM workflow."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from one_event_workflow import (
    STAGES,
    apply_review_decision,
    arrays_sha256,
    authorize_reviewed_config,
    build_review_decision_template,
    canonical_json,
    event_binding_sha256,
    load_config,
    sample_time_axis_ns,
    sha256_file,
    validate_timing_uncertainties,
)

CONTAINER_REPO = Path("/workflow")


def _require_supported_python() -> None:
    if sys.version_info < (3, 12):  # noqa: UP036 - direct script use bypasses packaging
        raise RuntimeError(
            "workflow requires Python 3.12 or newer; run with `uv run --locked python`"
        )


def _stage_environment(repo_root: Path) -> dict[str, str]:
    """Make the current checkout importable without an editable installation."""

    environment = os.environ.copy()
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = os.pathsep.join(
        value for value in (str(repo_root.resolve()), existing) if value
    )
    return environment


def _require_preparation_geometry(config: dict[str, Any]) -> None:
    geometry = config["joint_fit"]["geometry"]
    try:
        validate_timing_uncertainties(geometry)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"input preparation preflight rejected timing inputs: {exc}; "
            "no data processing started"
        ) from exc


def _resolve(path: str, repo_root: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else repo_root / candidate


def _output_paths(config: dict[str, Any]) -> dict[str, Path]:
    root = Path(config["paths"]["output_root"])
    return {
        "root": root,
        "state": root / "workflow-state.json",
        "preparation_state": root / "preparation-state.json",
        "provenance": root / "run-provenance.json",
        "dsa_audit": root / "dsa_state_audit.json",
        "chime_dir": root / "products" / "chime",
        "chime_result": root / "products" / "chime" / "chime_hybrid_result.json",
        "dsa_dir": root / "products" / "dsa",
        "dsa_result": root / "products" / "dsa" / "dsa_hybrid_result.json",
        "fit_dir": root / "products" / "fit",
        "chime_fit_observation": root / "products" / "fit" / "chime-fit-observation.npz",
        "dsa_fit_observation": root / "products" / "fit" / "dsa-fit-observation.npz",
        "chime_fit_resolution": root / "products" / "fit" / "chime-fit-resolution.json",
        "dsa_fit_resolution": root / "products" / "fit" / "dsa-fit-resolution.json",
        "geometry_constraint": root / "geometry-constraint.json",
        "fit_result": root / "fit-result.json",
        "posterior": root / "posterior.npz",
        "model_products": root / "model-products.npz",
        "fine_config": root / "resolution-convergence" / "fine-config.json",
        "fine_fit_dir": root / "resolution-convergence" / "fine-fit",
        "fine_fit_result": root / "resolution-convergence" / "fine-fit" / "fit-result.json",
        "fine_posterior": root / "resolution-convergence" / "fine-fit" / "posterior.npz",
        "fine_model_products": (
            root / "resolution-convergence" / "fine-fit" / "model-products.npz"
        ),
        "fine_provenance": (
            root / "resolution-convergence" / "fine-fit" / "run-provenance.json"
        ),
        "fine_chime_fit_observation": (
            root / "resolution-convergence" / "fit" / "chime-fit-observation.npz"
        ),
        "fine_dsa_fit_observation": (
            root / "resolution-convergence" / "fit" / "dsa-fit-observation.npz"
        ),
        "fine_chime_fit_resolution": (
            root / "resolution-convergence" / "fit" / "chime-fit-resolution.json"
        ),
        "fine_dsa_fit_resolution": (
            root / "resolution-convergence" / "fit" / "dsa-fit-resolution.json"
        ),
        "resolution_convergence": root / "resolution-convergence.json",
        "chime_oracle_dir": root / "oracles" / "chime",
        "chime_oracle_result": root / "oracles" / "chime" / "chime_hybrid_result.json",
        "dsa_oracle_dir": root / "oracles" / "dsa",
        "dsa_oracle_result": root / "oracles" / "dsa" / "dsa_hybrid_result.json",
        "oracle_verification": root / "oracle-verification.json",
        "packet_pdf": root / "review-packet.pdf",
        "component_proposal": root / "component-proposal.json",
        "component_proposal_pdf": root / "component-proposal.pdf",
        "high_resolution_component_diagnostic": (
            root / "high-resolution-component-diagnostic.json"
        ),
        "high_resolution_component_diagnostic_pdf": (
            root / "high-resolution-component-diagnostic.pdf"
        ),
        "resolution_proposal": root / "resolution-lock-proposal.json",
        "review_decision_template": root / "review-decision-template.json",
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
    preparation_only: bool = False,
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
        "-e",
        f"PYTHONPATH={CONTAINER_REPO}",
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
            *(["--preparation-only"] if preparation_only else []),
        ],
        "chime_products": [
            *chime_command,
            *(["--preparation-only"] if preparation_only else []),
        ],
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
            *(["--preparation-only"] if preparation_only else []),
        ],
        "geometry_constraint": [
            python,
            str(repo_root / "scripts/build_geometry_constraint.py"),
            "--config",
            str(config_path),
            "--output",
            str(paths["geometry_constraint"]),
        ],
        "joint_fit": [
            python,
            str(repo_root / "scripts/fit_one_event_joint_burst.py"),
            "--config",
            str(config_path),
            "--chime-observation",
            str(paths["chime_fit_observation"]),
            "--dsa-observation",
            str(paths["dsa_fit_observation"]),
            "--geometry-constraint",
            str(paths["geometry_constraint"]),
            "--output-dir",
            str(paths["root"]),
        ],
        "resolution_fit": [
            python,
            str(repo_root / "scripts/fit_resolution_variant.py"),
            "--base-config",
            str(config_path),
            "--variant-config",
            str(paths["fine_config"]),
            "--chime-observation",
            str(paths["fine_chime_fit_observation"]),
            "--dsa-observation",
            str(paths["fine_dsa_fit_observation"]),
            "--geometry-constraint",
            str(paths["geometry_constraint"]),
            "--output-dir",
            str(paths["fine_fit_dir"]),
        ],
        "resolution_check": [
            python,
            str(repo_root / "scripts/verify_joint_fit_resolution_convergence.py"),
            "--coarse-fit-result",
            str(paths["fit_result"]),
            "--fine-fit-result",
            str(paths["fine_fit_result"]),
            "--coarse-config",
            str(config_path),
            "--fine-config",
            str(paths["fine_config"]),
            "--coarse-chime-receipt",
            str(paths["chime_fit_resolution"]),
            "--coarse-dsa-receipt",
            str(paths["dsa_fit_resolution"]),
            "--fine-chime-receipt",
            str(paths["fine_chime_fit_resolution"]),
            "--fine-dsa-receipt",
            str(paths["fine_dsa_fit_resolution"]),
            "--output",
            str(paths["resolution_convergence"]),
        ],
        "chime_oracle": [
            *chime_command[:-2],
            "--joint-fit-result",
            str(paths["fit_result"]),
            "--output-dir",
            str(paths["chime_oracle_dir"]),
        ],
        "dsa_oracle": [
            python,
            str(repo_root / "scripts/build_one_event_dsa_hybrid_h17.py"),
            "--config",
            str(config_path),
            "--chime-result",
            str(paths["chime_result"]),
            "--dsa-audit",
            str(paths["dsa_audit"]),
            "--output-dir",
            str(paths["dsa_oracle_dir"]),
            "--joint-fit-result",
            str(paths["fit_result"]),
        ],
        "oracle_check": [
            python,
            str(repo_root / "scripts/verify_joint_fit_oracles.py"),
            "--config",
            str(config_path),
            "--fit-result",
            str(paths["fit_result"]),
            "--chime-result",
            str(paths["chime_oracle_result"]),
            "--dsa-result",
            str(paths["dsa_oracle_result"]),
            "--posterior",
            str(paths["posterior"]),
            "--model-products",
            str(paths["model_products"]),
            "--geometry-constraint",
            str(paths["geometry_constraint"]),
            "--chime-observation",
            str(paths["chime_dir"] / "chime_anchor_before_residual.npz"),
            "--dsa-observation",
            str(paths["dsa_dir"] / "dsa_anchor_dm.npz"),
            "--output",
            str(paths["oracle_verification"]),
        ],
        "packet": [
            python,
            str(repo_root / "scripts/render_joint_fit_packet.py"),
            "--chime-observation",
            str(paths["chime_dir"] / "chime_anchor_before_residual.npz"),
            "--dsa-observation",
            str(paths["dsa_dir"] / "dsa_anchor_dm.npz"),
            "--chime-posterior-observation",
            str(paths["chime_oracle_dir"] / "chime_fully_coherent_posterior_median.npz"),
            "--dsa-posterior-observation",
            str(paths["dsa_oracle_dir"] / "dsa_posterior_median.npz"),
            "--fit-result",
            str(paths["fit_result"]),
            "--posterior",
            str(paths["posterior"]),
            "--model-products",
            str(paths["model_products"]),
            "--geometry-constraint",
            str(paths["geometry_constraint"]),
            "--oracle-verification",
            str(paths["oracle_verification"]),
            "--resolution-convergence",
            str(paths["resolution_convergence"]),
            "--fine-fit-result",
            str(paths["fine_fit_result"]),
            "--coarse-config",
            str(config_path),
            "--fine-config",
            str(paths["fine_config"]),
            "--coarse-chime-receipt",
            str(paths["chime_fit_resolution"]),
            "--coarse-dsa-receipt",
            str(paths["dsa_fit_resolution"]),
            "--fine-chime-receipt",
            str(paths["fine_chime_fit_resolution"]),
            "--fine-dsa-receipt",
            str(paths["fine_dsa_fit_resolution"]),
            "--output",
            str(paths["packet_pdf"]),
        ],
        "manifests": None,
    }


def expected_stage_outputs(
    stage: str,
    paths: dict[str, Path],
    config: dict[str, Any] | None = None,
) -> list[Path]:
    if stage == "dsa_audit":
        return [paths["dsa_audit"]]
    if stage == "chime_products":
        return [
            paths["chime_result"],
            paths["chime_dir"] / "chime_anchor_before_residual.npz",
            paths["chime_dir"] / "chime_hybrid_fit_dm.npz",
            paths["chime_dir"] / "chime_geometry_dm.npz",
        ]
    if stage == "dsa_products":
        outputs = [
            paths["dsa_result"],
            paths["dsa_dir"] / "dsa_input_dm.npz",
            paths["dsa_dir"] / "dsa_accepted_reference_dm.npz",
            paths["dsa_dir"] / "dsa_anchor_dm.npz",
            paths["dsa_dir"] / "dsa_hybrid_fit_dm.npz",
            paths["dsa_dir"] / "dsa_geometry_dm.npz",
        ]
        if config is not None and not config["workflow"]["regression_fixture"]:
            for label in ("anchor_dm", "hybrid_fit_dm", "geometry_dm"):
                for endpoint in ("low", "high"):
                    outputs.append(paths["dsa_dir"] / f"dsa_{label}_input_{endpoint}.npz")
        return outputs
    if stage == "geometry_constraint":
        return [paths["geometry_constraint"]]
    if stage == "joint_fit":
        return [
            paths["chime_fit_observation"],
            paths["dsa_fit_observation"],
            paths["chime_fit_resolution"],
            paths["dsa_fit_resolution"],
            paths["fit_result"],
            paths["posterior"],
            paths["model_products"],
            paths["provenance"],
        ]
    if stage == "resolution_fit":
        return [
            paths["fine_config"],
            paths["fine_chime_fit_observation"],
            paths["fine_dsa_fit_observation"],
            paths["fine_chime_fit_resolution"],
            paths["fine_dsa_fit_resolution"],
            paths["fine_fit_result"],
            paths["fine_posterior"],
            paths["fine_model_products"],
            paths["fine_provenance"],
        ]
    if stage == "resolution_check":
        return [paths["resolution_convergence"]]
    if stage == "chime_oracle":
        outputs = [
            paths["chime_oracle_result"],
            paths["chime_oracle_dir"] / "chime_anchor_before_residual.npz",
            paths["chime_oracle_dir"] / "chime_hybrid_fit_dm.npz",
            paths["chime_oracle_dir"] / "chime_geometry_dm.npz",
        ]
        outputs.extend(
            paths["chime_oracle_dir"] / f"chime_fully_coherent_posterior_{label}.npz"
            for label in ("lower", "median", "upper")
        )
        return outputs
    if stage == "dsa_oracle":
        outputs = [
            paths["dsa_oracle_result"],
            paths["dsa_oracle_dir"] / "dsa_input_dm.npz",
            paths["dsa_oracle_dir"] / "dsa_accepted_reference_dm.npz",
        ]
        for label in ("lower", "median", "upper"):
            outputs.append(paths["dsa_oracle_dir"] / f"dsa_posterior_{label}.npz")
            if config is not None and not config["workflow"]["regression_fixture"]:
                for endpoint in ("low", "high"):
                    outputs.append(
                        paths["dsa_oracle_dir"] / f"dsa_posterior_{label}_input_{endpoint}.npz"
                    )
        return outputs
    if stage == "oracle_check":
        return [paths["oracle_verification"]]
    if stage == "packet":
        return [paths["packet_pdf"]]
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
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _array_sha256(*arrays: Any) -> str:
    return arrays_sha256(*arrays)


def resolution_lock_proposal(
    paths: dict[str, Path],
    *,
    observation_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    """Read-only proposal for owner-reviewed locks after product preparation."""

    import numpy as np

    proposal: dict[str, Any] = {
        "status": "pending_owner_review",
        "crop_and_off_pulse_padding_locked": False,
        "chime_fit_frequency_average_factor": None,
        "chime_fit_time_average_factor": None,
        "dsa_fit_frequency_average_factor": None,
        "dsa_fit_time_average_factor": None,
        "chime_fit_observation_sha256": None,
        "dsa_fit_observation_sha256": None,
        "chime_max_residual_intra_bin_smearing_s": None,
        "dsa_max_residual_intra_bin_smearing_s": None,
        "chime_smearing_calculation_sha256": None,
        "dsa_smearing_calculation_sha256": None,
    }
    observation_paths = observation_paths or {
        "chime": paths["chime_dir"] / "chime_anchor_before_residual.npz",
        "dsa": paths["dsa_dir"] / "dsa_anchor_dm.npz",
    }
    for instrument, path in observation_paths.items():
        with np.load(path, allow_pickle=False) as product:
            waterfall = product["waterfall"]
            sample_interval_s = float(product["sample_interval_s"])
            time0_unix_ns = int(product["time0_unix_ns"])
            proposal.update(
                {
                    f"{instrument}_shape": list(waterfall.shape),
                    f"{instrument}_sample_interval_s": sample_interval_s,
                    f"{instrument}_frequency_bin_factor": int(product["frequency_bin_factor"]),
                    f"{instrument}_time_bin_factor": int(product["time_bin_factor"]),
                    f"{instrument}_frequency_grid_sha256": _array_sha256(
                        product["frequency_mhz"],
                        product["channel_width_mhz"],
                    ),
                    f"{instrument}_valid_mask_sha256": _array_sha256(product["pixel_valid"]),
                    f"{instrument}_off_pulse_mask_sha256": _array_sha256(
                        product["noise_estimation_mask"]
                    ),
                    f"{instrument}_waterfall_sha256": _array_sha256(waterfall),
                    f"{instrument}_noise_std_sha256": _array_sha256(product["noise_std"]),
                    f"{instrument}_time_axis_sha256": _array_sha256(
                        sample_time_axis_ns(
                            time0_unix_ns=time0_unix_ns,
                            sample_interval_s=sample_interval_s,
                            sample_count=waterfall.shape[1],
                        )
                    ),
                    f"{instrument}_time0_unix_ns": time0_unix_ns,
                }
            )
    return proposal


def materialize_reviewed_fit_observations(
    resolution: dict[str, Any],
    *,
    repo_root: Path,
    paths: dict[str, Path],
) -> tuple[dict[str, Path], dict[str, Path]]:
    """Build separate fit-grid products and enforce any approved identities."""

    source_observations = {
        "chime": paths["chime_dir"] / "chime_anchor_before_residual.npz",
        "dsa": paths["dsa_dir"] / "dsa_anchor_dm.npz",
    }
    fit_observations = {
        "chime": paths["chime_fit_observation"],
        "dsa": paths["dsa_fit_observation"],
    }
    fit_receipts = {
        "chime": paths["chime_fit_resolution"],
        "dsa": paths["dsa_fit_resolution"],
    }
    for instrument in ("chime", "dsa"):
        frequency_factor = resolution.get(
            f"{instrument}_fit_frequency_average_factor"
        )
        time_factor = resolution.get(f"{instrument}_fit_time_average_factor")
        if not isinstance(frequency_factor, int) or frequency_factor < 1:
            raise ValueError(f"{instrument} fit frequency factor is not reviewed")
        if time_factor != 1:
            raise ValueError("formal fit grids must retain native time sampling")
        subprocess.run(
            [
                sys.executable,
                str(repo_root / "scripts/materialize_joint_fit_observations.py"),
                "--source-observation",
                str(source_observations[instrument]),
                "--frequency-bin-factor",
                str(frequency_factor),
                "--time-bin-factor",
                "1",
                "--minimum-valid-fraction",
                "1.0",
                "--output-observation",
                str(fit_observations[instrument]),
                "--output-receipt",
                str(fit_receipts[instrument]),
            ],
            check=True,
            cwd=repo_root,
            env=_stage_environment(repo_root),
        )
        expected = resolution.get(f"{instrument}_fit_observation_sha256")
        if expected is not None and sha256_file(fit_observations[instrument]) != expected:
            raise ValueError(f"{instrument} materialized fit-grid identity changed")
    return fit_observations, fit_receipts


def materialize_resolution_variant(
    config: dict[str, Any],
    *,
    repo_root: Path,
    paths: dict[str, Path],
) -> None:
    """Materialize the mandatory factor-halved grids and bind a fit variant."""

    from radio_pipeline.fitting import load_band_observation_product
    from radio_pipeline.fitting.resolution import residual_smearing_calculation

    coarse = config["joint_fit"]["resolution"]
    fine_seed = copy.deepcopy(coarse)
    for instrument in ("chime", "dsa"):
        factor = int(coarse[f"{instrument}_fit_frequency_average_factor"])
        if factor > 1 and factor % 2:
            raise ValueError(
                f"{instrument} reviewed frequency factor cannot be exactly halved"
            )
        fine_seed[f"{instrument}_fit_frequency_average_factor"] = (
            1 if factor == 1 else factor // 2
        )
        fine_seed[f"{instrument}_fit_observation_sha256"] = None
    fine_paths = dict(paths)
    fine_paths.update(
        {
            "chime_fit_observation": paths["fine_chime_fit_observation"],
            "dsa_fit_observation": paths["fine_dsa_fit_observation"],
            "chime_fit_resolution": paths["fine_chime_fit_resolution"],
            "dsa_fit_resolution": paths["fine_dsa_fit_resolution"],
        }
    )
    observations, _ = materialize_reviewed_fit_observations(
        fine_seed,
        repo_root=repo_root,
        paths=fine_paths,
    )
    fine = resolution_lock_proposal(paths, observation_paths=observations)
    fine["status"] = coarse["status"]
    fine["crop_and_off_pulse_padding_locked"] = coarse[
        "crop_and_off_pulse_padding_locked"
    ]
    source_paths = {
        "chime": paths["chime_dir"] / "chime_anchor_before_residual.npz",
        "dsa": paths["dsa_dir"] / "dsa_anchor_dm.npz",
    }
    for instrument in ("chime", "dsa"):
        factor = fine_seed[f"{instrument}_fit_frequency_average_factor"]
        fine[f"{instrument}_fit_frequency_average_factor"] = factor
        fine[f"{instrument}_fit_time_average_factor"] = 1
        fine[f"{instrument}_fit_observation_sha256"] = sha256_file(
            observations[instrument]
        )
        calculation = residual_smearing_calculation(
            load_band_observation_product(source_paths[instrument]),
            absolute_dm_bounds_pc_cm3=tuple(config["joint_fit"]["dm_bounds_pc_cm3"]),
            frequency_bin_factor=factor,
        )
        fine[f"{instrument}_max_residual_intra_bin_smearing_s"] = calculation[
            "maximum_smearing_s"
        ]
        fine[f"{instrument}_smearing_calculation_sha256"] = hashlib.sha256(
            canonical_json(calculation).encode()
        ).hexdigest()
    variant = copy.deepcopy(config)
    variant["joint_fit"]["resolution"] = fine
    _write_json(paths["fine_config"], variant)


def prepare_review_artifacts(
    config: dict[str, Any],
    *,
    config_path: Path,
    repo_root: Path,
    paths: dict[str, Path],
) -> dict[str, Any]:
    """Materialize a reviewed fit grid before proposing fit-grid components."""

    def run_component_proposal(
        chime_observation: Path,
        dsa_observation: Path,
        output_json: Path,
        output_pdf: Path,
    ) -> None:
        subprocess.run(
            [
                sys.executable,
                str(repo_root / "scripts/propose_joint_fit_components.py"),
                "--config",
                str(config_path),
                "--event",
                config["event"],
                "--chime-observation",
                str(chime_observation),
                "--dsa-observation",
                str(dsa_observation),
                "--output-json",
                str(output_json),
                "--output-pdf",
                str(output_pdf),
            ],
            check=True,
            cwd=repo_root,
            env=_stage_environment(repo_root),
        )

    high_resolution_observations = {
        "chime": paths["chime_dir"] / "chime_anchor_before_residual.npz",
        "dsa": paths["dsa_dir"] / "dsa_anchor_dm.npz",
    }
    if not paths["resolution_proposal"].is_file():
        _write_json(paths["resolution_proposal"], resolution_lock_proposal(paths))
    if not paths["high_resolution_component_diagnostic"].is_file():
        run_component_proposal(
            high_resolution_observations["chime"],
            high_resolution_observations["dsa"],
            paths["high_resolution_component_diagnostic"],
            paths["high_resolution_component_diagnostic_pdf"],
        )

    reviewed_resolution = json.loads(paths["resolution_proposal"].read_text())
    required_reviewed_fields = [
        f"{instrument}_{suffix}"
        for instrument in ("chime", "dsa")
        for suffix in (
            "fit_frequency_average_factor",
            "fit_time_average_factor",
            "max_residual_intra_bin_smearing_s",
            "smearing_calculation_sha256",
        )
    ]
    if any(reviewed_resolution.get(key) is None for key in required_reviewed_fields):
        return {
            "status": "fit_resolution_review_required",
            "resolution_lock_proposal": reviewed_resolution,
            "high_resolution_component_diagnostic": {
                "path": str(paths["high_resolution_component_diagnostic"]),
                "sha256": sha256_file(paths["high_resolution_component_diagnostic"]),
            },
            "high_resolution_component_diagnostic_pdf": {
                "path": str(paths["high_resolution_component_diagnostic_pdf"]),
                "sha256": sha256_file(
                    paths["high_resolution_component_diagnostic_pdf"]
                ),
            },
        }
    if any(
        int(reviewed_resolution[f"{instrument}_fit_time_average_factor"]) != 1
        for instrument in ("chime", "dsa")
    ):
        raise ValueError("formal fit-grid review must retain native time sampling")

    fit_observations, _ = materialize_reviewed_fit_observations(
        reviewed_resolution,
        repo_root=repo_root,
        paths=paths,
    )

    resolution = resolution_lock_proposal(
        paths,
        observation_paths=fit_observations,
    )
    for key in required_reviewed_fields:
        resolution[key] = reviewed_resolution[key]
    for instrument in ("chime", "dsa"):
        resolution[f"{instrument}_fit_observation_sha256"] = sha256_file(
            fit_observations[instrument]
        )
    _write_json(paths["resolution_proposal"], resolution)
    run_component_proposal(
        fit_observations["chime"],
        fit_observations["dsa"],
        paths["component_proposal"],
        paths["component_proposal_pdf"],
    )
    component_proposal = json.loads(paths["component_proposal"].read_text())
    decision = build_review_decision_template(
        config,
        component_proposal=component_proposal,
        component_proposal_sha256=sha256_file(paths["component_proposal"]),
        resolution_proposal=resolution,
        resolution_proposal_sha256=sha256_file(paths["resolution_proposal"]),
    )
    _write_json(paths["review_decision_template"], decision)
    return {
        "status": "component_and_resolution_review_required",
        "resolution_lock_proposal": resolution,
        "component_proposal": {
            "path": str(paths["component_proposal"]),
            "sha256": sha256_file(paths["component_proposal"]),
        },
        "component_proposal_pdf": {
            "path": str(paths["component_proposal_pdf"]),
            "sha256": sha256_file(paths["component_proposal_pdf"]),
        },
        "review_decision_template": {
            "path": str(paths["review_decision_template"]),
            "sha256": sha256_file(paths["review_decision_template"]),
        },
    }


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
        "chime_products": [
            repo_root / "scripts/run_one_event_hybrid_absolute_dm_h17.py",
            repo_root / "scripts/one_event_hybrid_dm.py",
            repo_root / "scripts/absolute_dm_voltage.py",
        ],
        "dsa_products": [
            repo_root / "scripts/build_one_event_dsa_hybrid_h17.py",
            repo_root / "scripts/absolute_dm_voltage.py",
        ],
        "geometry_constraint": [repo_root / "scripts/build_geometry_constraint.py"],
        "joint_fit": [
            repo_root / "scripts/materialize_joint_fit_observations.py",
            repo_root / "scripts/fit_one_event_joint_burst.py",
            repo_root / "radio_pipeline/fitting/joint_burst.py",
            repo_root / "radio_pipeline/fitting/products.py",
            repo_root / "radio_pipeline/fitting/_pulse_kernels.py",
            repo_root / "radio_pipeline/fitting/resolution.py",
        ],
        "resolution_fit": [
            repo_root / "scripts/materialize_joint_fit_observations.py",
            repo_root / "scripts/fit_resolution_variant.py",
            repo_root / "scripts/fit_one_event_joint_burst.py",
            repo_root / "radio_pipeline/fitting/joint_burst.py",
            repo_root / "radio_pipeline/fitting/products.py",
            repo_root / "radio_pipeline/fitting/_pulse_kernels.py",
            repo_root / "radio_pipeline/fitting/resolution.py",
        ],
        "resolution_check": [
            repo_root / "scripts/verify_joint_fit_resolution_convergence.py",
        ],
        "chime_oracle": [
            repo_root / "scripts/run_one_event_hybrid_absolute_dm_h17.py",
            repo_root / "scripts/one_event_hybrid_dm.py",
            repo_root / "scripts/absolute_dm_voltage.py",
        ],
        "dsa_oracle": [
            repo_root / "scripts/build_one_event_dsa_hybrid_h17.py",
            repo_root / "scripts/absolute_dm_voltage.py",
        ],
        "oracle_check": [
            repo_root / "scripts/verify_joint_fit_oracles.py",
            repo_root / "radio_pipeline/fitting/products.py",
            repo_root / "radio_pipeline/fitting/joint_burst.py",
        ],
        "packet": [
            repo_root / "scripts/render_joint_fit_packet.py",
            repo_root / "scripts/verify_joint_fit_resolution_convergence.py",
        ],
        "manifests": [repo_root / "analysis-configs/absolute-dm/schema.json"],
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
        return [_resolve(source[key], repo_root) for key in config["input_sha256"]]
    if stage == "dsa_audit":
        inputs = [
            _resolve(source["raw_dsa_filterbank"], repo_root),
            _resolve(source["accepted_dsa_reference"], repo_root),
        ]
        for key in ("dsa_state_reconstruction", "dsa_state_calibration"):
            if key in source:
                inputs.append(_resolve(source[key], repo_root))
        return inputs
    if stage == "chime_products":
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
    if stage == "geometry_constraint":
        return []
    if stage == "joint_fit":
        return [
            paths["chime_dir"] / "chime_anchor_before_residual.npz",
            paths["dsa_dir"] / "dsa_anchor_dm.npz",
            paths["chime_fit_observation"],
            paths["dsa_fit_observation"],
            paths["chime_fit_resolution"],
            paths["dsa_fit_resolution"],
            paths["geometry_constraint"],
        ]
    if stage == "resolution_fit":
        return [
            paths["chime_dir"] / "chime_anchor_before_residual.npz",
            paths["dsa_dir"] / "dsa_anchor_dm.npz",
            paths["fit_result"],
            paths["geometry_constraint"],
        ]
    if stage == "resolution_check":
        return [
            paths["fit_result"],
            paths["fine_fit_result"],
            paths["fine_config"],
            paths["chime_fit_resolution"],
            paths["dsa_fit_resolution"],
            paths["fine_chime_fit_resolution"],
            paths["fine_dsa_fit_resolution"],
        ]
    if stage == "chime_oracle":
        return [
            paths["fit_result"],
            _resolve(source["raw_chime_h5"], repo_root),
            _resolve(source["accepted_chime_reference"], repo_root),
        ]
    if stage == "dsa_oracle":
        return [
            paths["fit_result"],
            paths["chime_result"],
            paths["dsa_audit"],
            _resolve(source["raw_dsa_filterbank"], repo_root),
            _resolve(source["accepted_dsa_reference"], repo_root),
        ]
    if stage == "oracle_check":
        return [
            paths["fit_result"],
            paths["posterior"],
            paths["model_products"],
            paths["geometry_constraint"],
            paths["chime_dir"] / "chime_anchor_before_residual.npz",
            paths["dsa_dir"] / "dsa_anchor_dm.npz",
            paths["chime_oracle_result"],
            paths["dsa_oracle_result"],
            *[
                path
                for path in expected_stage_outputs("chime_oracle", paths, config)
                if path.suffix == ".npz"
            ],
            *[
                path
                for path in expected_stage_outputs("dsa_oracle", paths, config)
                if path.suffix == ".npz"
            ],
        ]
    if stage == "packet":
        inputs = [
            paths["chime_dir"] / "chime_anchor_before_residual.npz",
            paths["dsa_dir"] / "dsa_anchor_dm.npz",
            paths["chime_oracle_dir"] / "chime_fully_coherent_posterior_median.npz",
            paths["dsa_oracle_dir"] / "dsa_posterior_median.npz",
            paths["fit_result"],
            paths["posterior"],
            paths["model_products"],
            paths["geometry_constraint"],
            paths["oracle_verification"],
            paths["resolution_convergence"],
            paths["fine_fit_result"],
            paths["fine_config"],
            paths["chime_fit_resolution"],
            paths["dsa_fit_resolution"],
            paths["fine_chime_fit_resolution"],
            paths["fine_dsa_fit_resolution"],
        ]
        return inputs
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
    if stage in {"preflight", "chime_products", "dsa_products"}:
        json_path = {
            "chime_products": paths["chime_result"],
            "dsa_products": paths["dsa_result"],
        }.get(stage)
        if json_path is None:
            return True
    elif stage == "dsa_audit":
        json_path = paths["dsa_audit"]
    elif stage == "geometry_constraint":
        json_path = paths["geometry_constraint"]
    elif stage == "joint_fit":
        json_path = paths["fit_result"]
    elif stage == "resolution_fit":
        json_path = paths["fine_fit_result"]
    elif stage == "resolution_check":
        try:
            value = json.loads(paths["resolution_convergence"].read_text())
        except (OSError, ValueError):
            return False
        return (
            value.get("event") == config["event"]
            and value.get("status") == "passed"
            and value.get("passed") is True
            and value.get("input_sha256", {}).get("coarse_fit_result")
            == sha256_file(paths["fit_result"])
        )
    elif stage == "chime_oracle":
        json_path = paths["chime_oracle_result"]
    elif stage == "dsa_oracle":
        json_path = paths["dsa_oracle_result"]
    elif stage == "oracle_check":
        json_path = paths["oracle_verification"]
    elif stage == "packet":
        return paths["packet_pdf"].is_file()
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
    recorded_event = value.get("event", value.get("burst"))
    return recorded_event == config["event"]


def _output_set_exact(stage: str, expected: list[Path]) -> bool:
    if stage not in {
        "chime_products",
        "dsa_products",
        "chime_oracle",
        "dsa_oracle",
        "manifests",
    }:
        return True
    if not expected:
        return False
    parent = expected[0].parent
    actual = {path for path in parent.iterdir() if path.is_file()} if parent.is_dir() else set()
    return actual == set(expected)


def _all_workflow_files(
    paths: dict[str, Path],
    config: dict[str, Any],
) -> set[Path]:
    expected = {paths["state"], paths["provenance"]}
    if paths["preparation_state"].is_file():
        expected.add(paths["preparation_state"])
    for key in (
        "component_proposal",
        "component_proposal_pdf",
        "resolution_proposal",
        "review_decision_template",
        "high_resolution_component_diagnostic",
        "high_resolution_component_diagnostic_pdf",
        "chime_fit_observation",
        "dsa_fit_observation",
        "chime_fit_resolution",
        "dsa_fit_resolution",
    ):
        if paths[key].is_file():
            expected.add(paths[key])
    for stage in STAGES:
        expected.update(expected_stage_outputs(stage, paths, config))
    return expected


def _workflow_output_set_valid(
    paths: dict[str, Path],
    config: dict[str, Any],
    *,
    require_complete: bool = False,
) -> bool:
    root = paths["root"]
    actual = {path for path in root.rglob("*") if path.is_file()} if root.is_dir() else set()
    expected = _all_workflow_files(paths, config)
    return actual == expected if require_complete else actual.issubset(expected)


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
    expected = expected_stage_outputs(stage, paths, config)
    try:
        return (
            record.get("event_binding_sha256") == config["event_binding_sha256"]
            and record.get("control_sha256") == stage_control_sha256(stage, repo_root, config_path)
            and record.get("command_sha256") == _hash_payload(command)
            and record.get("input_sha256") == stage_input_sha256(stage, config, repo_root, paths)
            and outputs_match(record, expected)
            and _output_set_exact(stage, expected)
            and _workflow_output_set_valid(paths, config)
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


def verify_geometry_constraint(config: dict[str, Any], path: Path) -> None:
    result = json.loads(path.read_text())
    if result.get("event") != config["event"]:
        raise RuntimeError("geometry constraint event differs from configuration")
    if result.get("event_binding_sha256") != config["event_binding_sha256"]:
        raise RuntimeError("geometry constraint binding differs from configuration")
    if float(result["reference_frequency_mhz"]) != 400.0:
        raise RuntimeError("geometry constraint reference frequency changed")


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
    plan = {
        "schema_version": 1,
        "mode": "dry-run",
        "event": config["event"],
        "event_binding_sha256": config["event_binding_sha256"],
        "output_root": config["paths"]["output_root"],
        "stages": [{"stage": stage, "command": commands[stage]} for stage in selected],
        "writes_performed": False,
    }
    if "joint_fit" in config:
        plan["joint_fit_readiness"] = {
            "status": config["joint_fit"]["status"],
            "execution_authorized": config["joint_fit"]["execution_authorized"],
            "blockers": config["joint_fit"]["blockers"],
            "active_inference": (
                "geometry-constrained shared absolute DM and geocentric "
                "400 MHz component arrival times"
            ),
        }
    return plan


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, allow_nan=False) + "\n"
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _log_refs() -> dict[str, str]:
    refs = {}
    for label, variable in (
        ("stdout", "ONE_EVENT_WORKFLOW_STDOUT_LOG"),
        ("stderr", "ONE_EVENT_WORKFLOW_STDERR_LOG"),
    ):
        value = os.environ.get(variable)
        if value:
            refs[label] = value
    return refs


def _existing_output_receipts(paths: list[Path]) -> tuple[list[dict], list[str]]:
    outputs = []
    unreadable = []
    for path in paths:
        if not path.is_file():
            continue
        try:
            outputs.append({"path": str(path), "sha256": sha256_file(path)})
        except OSError as error:
            unreadable.append(f"{path}: {type(error).__name__}: {error}")
    return outputs, unreadable


def _failed_stage_message(stages: list[str]) -> str:
    flags = " ".join(f"--retry-failed-stage {stage}" for stage in stages)
    return (
        f"workflow state contains failed stage(s) {', '.join(stages)}; "
        f"inspect the failure receipt, then retry explicitly with {flags}"
    )


def _write_provenance(
    config: dict[str, Any],
    state: dict[str, Any],
    path: Path,
) -> None:
    cutoff = STAGES.index("packet")
    completed = {
        stage: record
        for stage, record in state["stages"].items()
        if stage in STAGES and STAGES.index(stage) < cutoff and record.get("status") == "completed"
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
        repo_root / "analysis-configs/absolute-dm/schema.json",
        repo_root / "scripts/one_event_workflow.py",
        repo_root / "scripts/one_event_hybrid_dm.py",
        repo_root / "scripts/audit_one_event_dsa_state_h17.py",
        repo_root / "scripts/run_one_event_hybrid_absolute_dm_h17.py",
        repo_root / "scripts/build_one_event_dsa_hybrid_h17.py",
        repo_root / "scripts/build_geometry_constraint.py",
        repo_root / "scripts/fit_one_event_joint_burst.py",
        repo_root / "scripts/fit_resolution_variant.py",
        repo_root / "scripts/materialize_joint_fit_observations.py",
        repo_root / "scripts/verify_joint_fit_resolution_convergence.py",
        repo_root / "scripts/render_joint_fit_packet.py",
        repo_root / "radio_pipeline/fitting/joint_burst.py",
        repo_root / "radio_pipeline/fitting/products.py",
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
            "controls": [{"path": str(path), "sha256": sha256_file(path)} for path in controls],
            "products": [{"path": str(path), "sha256": sha256_file(path)} for path in products],
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
    retry_failed_stage: set[str] | None = None,
    preparation_only: bool = False,
) -> dict[str, Any]:
    retry_failed_stage = set(retry_failed_stage or ())
    paths = _output_paths(config)
    if preparation_only:
        paths["state"] = paths["preparation_state"]
    commands = build_stage_commands(
        config,
        config_path=config_path,
        repo_root=repo_root,
        preparation_only=preparation_only,
    )
    stage_environment = _stage_environment(repo_root)
    verified_inputs = verify_inputs(config, repo_root)
    if paths["state"].is_file():
        state = json.loads(paths["state"].read_text())
        if state.get("event_binding_sha256") != config["event_binding_sha256"]:
            raise RuntimeError("state belongs to another event binding")
    else:
        state = {
            "schema_version": 1,
            "status": "pending",
            "event": config["event"],
            "event_binding_sha256": config["event_binding_sha256"],
            "stages": {},
        }

    selected_stages = _stage_window(from_stage, through_stage)
    interrupted_stages = [
        stage for stage, record in state["stages"].items() if record.get("status") == "running"
    ]
    if interrupted_stages:
        interrupted_at = time.time()
        for stage in interrupted_stages:
            record = state["stages"][stage]
            expected = [Path(path) for path in record.get("expected_outputs", [])]
            partial_outputs, unreadable_outputs = _existing_output_receipts(expected)
            record.update(
                {
                    "status": "failed",
                    "failed_unix": interrupted_at,
                    "wall_seconds": max(
                        0.0,
                        interrupted_at - float(record.get("started_unix", interrupted_at)),
                    ),
                    "outputs": partial_outputs,
                    "missing_outputs": [str(path) for path in expected if not path.is_file()],
                    "error": {
                        "type": "InterruptedStageState",
                        "message": ("prior process ended without a terminal stage receipt"),
                    },
                }
            )
            if unreadable_outputs:
                record["unreadable_outputs"] = unreadable_outputs
        state.update(
            {
                "status": "failed",
                "failed_stage": sorted(
                    interrupted_stages,
                    key=STAGES.index,
                )[0],
                "failed_unix": interrupted_at,
            }
        )
        state.pop("active_stage", None)
        _write_json(paths["state"], state)
    failed_stages = sorted(
        (stage for stage, record in state["stages"].items() if record.get("status") == "failed"),
        key=STAGES.index,
    )
    unapproved_retries = [stage for stage in failed_stages if stage not in retry_failed_stage]
    if unapproved_retries:
        raise RuntimeError(_failed_stage_message(unapproved_retries))
    unused_retries = retry_failed_stage - set(failed_stages)
    if unused_retries:
        raise RuntimeError(
            "--retry-failed-stage names a stage without a durable failed receipt: "
            + ", ".join(sorted(unused_retries, key=STAGES.index))
        )
    if any(stage not in selected_stages for stage in failed_stages):
        raise RuntimeError(
            "retry window does not include failed stage(s): "
            + ", ".join(stage for stage in failed_stages if stage not in selected_stages)
        )
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
            raise RuntimeError(f"{from_stage}: prerequisite stage {prerequisite} is not resumable")

    for stage in selected_stages:
        previous = state["stages"].get(stage, {})
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
        started = time.time()
        expected_outputs = expected_stage_outputs(stage, paths, config)
        record: dict[str, Any] = {
            "stage": stage,
            "status": "running",
            "started_unix": started,
            "event_binding_sha256": config["event_binding_sha256"],
            "command": commands[stage],
            "command_sha256": _hash_payload(commands[stage]),
            "expected_outputs": [str(path) for path in expected_outputs],
            "outputs": [],
            "log_refs": _log_refs(),
        }
        if previous:
            history = copy.deepcopy(previous.get("attempt_history", []))
            history.append(
                {
                    key: copy.deepcopy(value)
                    for key, value in previous.items()
                    if key != "attempt_history"
                }
            )
            record["attempt_history"] = history
        state["stages"][stage] = record
        state["status"] = "running"
        state["active_stage"] = stage
        _write_json(paths["state"], state)
        try:
            if stage == "joint_fit":
                materialize_reviewed_fit_observations(
                    config["joint_fit"]["resolution"],
                    repo_root=repo_root,
                    paths=paths,
                )
            elif stage == "resolution_fit":
                materialize_resolution_variant(
                    config,
                    repo_root=repo_root,
                    paths=paths,
                )
            record.update(
                {
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
                }
            )
            _write_json(paths["state"], state)
            if stage == "preflight":
                record["verified_inputs"] = verified_inputs
            elif stage == "packet":
                subprocess.run(commands[stage], check=True, env=stage_environment)
            elif stage == "manifests":
                _write_manifest(config, config_path, repo_root, paths)
            else:
                subprocess.run(commands[stage], check=True, env=stage_environment)
                if stage == "geometry_constraint":
                    verify_geometry_constraint(config, paths["geometry_constraint"])
            completed = time.time()
            outputs = [
                {"path": str(path), "sha256": sha256_file(path)} for path in expected_outputs
            ]
            if not _output_set_exact(stage, expected_outputs):
                raise RuntimeError(f"{stage}: unexpected output file set")
            if not _workflow_output_set_valid(paths, config):
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
            state.pop("active_stage", None)
            _write_json(paths["state"], state)
        except BaseException as error:
            failed = time.time()
            partial_outputs, unreadable_outputs = _existing_output_receipts(expected_outputs)
            record.update(
                {
                    "status": "failed",
                    "failed_unix": failed,
                    "wall_seconds": failed - started,
                    "outputs": partial_outputs,
                    "missing_outputs": [
                        str(path) for path in expected_outputs if not path.is_file()
                    ],
                    "error": {
                        "type": type(error).__name__,
                        "message": str(error),
                    },
                }
            )
            if unreadable_outputs:
                record["unreadable_outputs"] = unreadable_outputs
            state.update(
                {
                    "status": "failed",
                    "failed_stage": stage,
                    "failed_unix": failed,
                }
            )
            state.pop("active_stage", None)
            _write_json(paths["state"], state)
            raise
    if through_stage == STAGES[-1] and not _workflow_output_set_valid(
        paths,
        config,
        require_complete=True,
    ):
        raise RuntimeError("final workflow output set is incomplete or unexpected")
    state["status"] = "completed" if through_stage == STAGES[-1] else "partial_completed"
    state["completed_unix"] = time.time()
    state.pop("active_stage", None)
    state.pop("failed_stage", None)
    state.pop("failed_unix", None)
    _write_json(paths["state"], state)
    return state


def main() -> None:
    _require_supported_python()
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument(
        "--prepare-reviewed-inputs",
        action="store_true",
        help=(
            "build only audited observation products and geometry so their "
            "exact locks can be reviewed"
        ),
    )
    mode.add_argument("--print-binding", action="store_true")
    mode.add_argument(
        "--apply-review-decision",
        type=Path,
        metavar="DECISION_JSON",
        help="write a reviewed execution-disabled config from exact approved proposals",
    )
    mode.add_argument(
        "--authorize-reviewed-config",
        action="store_true",
        help="write a separately bound execution-authorized config",
    )
    parser.add_argument("--component-proposal", type=Path)
    parser.add_argument("--resolution-proposal", type=Path)
    parser.add_argument("--output-config", type=Path)
    parser.add_argument("--authorization-note")
    parser.add_argument("--authorization-date")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--from-stage", choices=STAGES, default=STAGES[0])
    parser.add_argument("--through-stage", choices=STAGES, default=STAGES[-1])
    parser.add_argument("--force-stage", choices=STAGES, action="append", default=[])
    parser.add_argument(
        "--retry-failed-stage",
        choices=STAGES,
        action="append",
        default=[],
        help="explicitly retry a stage that has a durable failed receipt",
    )
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
    if "joint_fit" not in config:
        raise RuntimeError(
            "historical anchored-hybrid configuration is compatibility-only; "
            "add a reviewed joint_fit section before using the active command"
        )
    if args.apply_review_decision is not None:
        required_paths = {
            "--component-proposal": args.component_proposal,
            "--resolution-proposal": args.resolution_proposal,
            "--output-config": args.output_config,
        }
        missing = [name for name, value in required_paths.items() if value is None]
        if missing:
            raise ValueError(
                "--apply-review-decision requires " + ", ".join(missing)
            )
        assert args.component_proposal is not None
        assert args.resolution_proposal is not None
        assert args.output_config is not None
        if args.output_config.resolve() == config_path:
            raise ValueError("review transition must not overwrite its source config")
        component_proposal = json.loads(args.component_proposal.read_text())
        resolution_proposal = json.loads(args.resolution_proposal.read_text())
        reviewed = apply_review_decision(
            config,
            json.loads(args.apply_review_decision.read_text()),
            component_proposal=component_proposal,
            component_proposal_sha256=sha256_file(args.component_proposal),
            resolution_proposal=resolution_proposal,
            resolution_proposal_sha256=sha256_file(args.resolution_proposal),
        )
        _write_json(args.output_config, reviewed)
        print(
            canonical_json(
                {
                    "status": reviewed["joint_fit"]["status"],
                    "execution_authorized": False,
                    "output_config": str(args.output_config),
                    "event_binding_sha256": reviewed["event_binding_sha256"],
                }
            )
        )
        return
    if args.authorize_reviewed_config:
        if args.output_config is None or not args.authorization_note:
            raise ValueError(
                "--authorize-reviewed-config requires --output-config and "
                "--authorization-note"
            )
        if args.output_config.resolve() == config_path:
            raise ValueError("authorization must not overwrite its source config")
        authorized = authorize_reviewed_config(
            config,
            note=args.authorization_note,
            authorization_date=args.authorization_date,
        )
        _write_json(args.output_config, authorized)
        print(
            canonical_json(
                {
                    "status": authorized["joint_fit"]["status"],
                    "execution_authorized": True,
                    "output_config": str(args.output_config),
                    "event_binding_sha256": authorized["event_binding_sha256"],
                    "receipt_rebuild_required": authorized["joint_fit"]["authorization"][
                        "requires_receipt_rebuild"
                    ],
                }
            )
        )
        return
    if args.prepare_reviewed_inputs:
        if args.from_stage != STAGES[0] or args.through_stage != STAGES[-1]:
            raise ValueError("input preparation owns its fixed pre-fit stage window")
        _require_preparation_geometry(config)
        state = execute(
            config,
            config_path=config_path,
            repo_root=repo_root,
            from_stage="preflight",
            through_stage="geometry_constraint",
            force_stage=set(args.force_stage),
            retry_failed_stage=set(args.retry_failed_stage),
            preparation_only=True,
        )
        review_artifacts = prepare_review_artifacts(
            config,
            config_path=config_path,
            repo_root=repo_root,
            paths=_output_paths(config),
        )
        print(
            json.dumps(
                {
                    "state": state,
                    **review_artifacts,
                    "owner_review_required": True,
                },
                indent=2,
                allow_nan=False,
            )
        )
        return
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
    _require_preparation_geometry(config)
    state = execute(
        config,
        config_path=config_path,
        repo_root=repo_root,
        from_stage=args.from_stage,
        through_stage=args.through_stage,
        force_stage=set(args.force_stage),
        retry_failed_stage=set(args.retry_failed_stage),
    )
    print(json.dumps(state, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
