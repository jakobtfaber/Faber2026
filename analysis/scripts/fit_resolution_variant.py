#!/usr/bin/env python3
"""Run the mandatory factor-halved fit from one authorized base config."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path

from fit_one_event_joint_burst import run
from one_event_workflow import load_config, validate_resolution_lock


def load_variant(base_path: Path, variant_path: Path) -> dict:
    base = load_config(base_path, require_execution_authorized=True)
    variant = json.loads(variant_path.read_text())
    expected = deepcopy(base)
    expected["joint_fit"]["resolution"] = deepcopy(
        variant["joint_fit"]["resolution"]
    )
    if variant != expected:
        raise ValueError("resolution variant changed fields outside joint_fit.resolution")
    if variant["event_binding_sha256"] != base["event_binding_sha256"]:
        raise ValueError("resolution variant must retain the authorized event binding")
    validate_resolution_lock(variant["joint_fit"]["resolution"])
    variant["_config_path"] = str(variant_path.resolve())
    return variant


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-config", type=Path, required=True)
    parser.add_argument("--variant-config", type=Path, required=True)
    parser.add_argument("--chime-observation", type=Path, required=True)
    parser.add_argument("--dsa-observation", type=Path, required=True)
    parser.add_argument("--geometry-constraint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = load_variant(args.base_config, args.variant_config)
    result = run(
        config,
        chime_path=args.chime_observation,
        dsa_path=args.dsa_observation,
        geometry_path=args.geometry_constraint,
        output_dir=args.output_dir,
        repo_root=Path(__file__).resolve().parents[1],
    )
    print(json.dumps({"status": result["status"], "event": result["event"]}))


if __name__ == "__main__":
    main()
