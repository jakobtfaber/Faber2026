#!/usr/bin/env python3
"""Hash-check configs for a paused experimental Phase B diagnostic.

This write-free check does not establish science authority.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from one_event_workflow import load_config, sha256_file

RESULT_STATUS = (
    "phase_b_paused_experimental_diagnostic_preflight_"
    "not_science_authority"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runner = args.repo_root / "scripts/run_one_event_absolute_dm_workflow.py"
    configs = sorted(args.config_root.glob("*/workflow-config.json"))
    if len(configs) != 11:
        raise RuntimeError(f"expected 11 Phase B configs, found {len(configs)}")
    rows = []
    for path in configs:
        config = load_config(path)
        completed = subprocess.run(
            [
                sys.executable,
                str(runner),
                "--config",
                str(path),
                "--repo-root",
                str(args.repo_root),
                "--dry-run",
                "--check-inputs",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        plan = json.loads(completed.stdout)
        if plan["writes_performed"] is not False:
            raise RuntimeError(f"{config['event']}: preflight wrote state")
        rows.append(
            {
                "event": config["event"],
                "config_path": str(path),
                "config_sha256": sha256_file(path),
                "event_binding_sha256": config["event_binding_sha256"],
                "execution_authorized": config["workflow"][
                    "execution_authorized"
                ],
                "configuration_status": config["review"][
                    "configuration_status"
                ],
                "blockers": config["review"]["blockers"],
                "verified_inputs": plan["verified_inputs"],
                "planned_stages": [
                    stage["stage"] for stage in plan["stages"]
                ],
                "writes_performed": False,
            }
        )
        print(config["event"], flush=True)
    result = {
        "schema_version": 1,
        "status": RESULT_STATUS,
        "config_count": len(rows),
        "authorized_count": sum(
            bool(row["execution_authorized"]) for row in rows
        ),
        "blocked_count": sum(bool(row["blockers"]) for row in rows),
        "rows": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "config_count", "authorized_count", "blocked_count")}))


if __name__ == "__main__":
    main()
