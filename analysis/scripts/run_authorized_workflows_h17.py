#!/usr/bin/env python3
"""Gate an experimental diagnostic campaign with bounded concurrency.

Phase B is currently paused. Any future output is not science authority.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from one_event_workflow import load_config, sha256_file

CAMPAIGN_STATE_RELATIVE = Path(
    "analysis-configs/absolute-dm/phase-b/campaign-state.json"
)


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def require_campaign_authorization(
    repo_root: Path,
    configs: list[tuple[Path, dict]],
) -> dict:
    """Require the tracked, review-bound campaign receipt before any launch."""

    path = repo_root / CAMPAIGN_STATE_RELATIVE
    if not path.is_file():
        raise PermissionError(f"campaign authorization receipt is missing: {path}")
    try:
        receipt = json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise PermissionError("campaign authorization receipt is unreadable") from error
    status = receipt.get("status")
    if status != "authorized" or receipt.get("execution_authorized") is not True:
        raise PermissionError(f"campaign is {status or 'not authorized'}; no launch")
    if receipt.get("campaign") != "phase-b-absolute-dm":
        raise PermissionError("campaign authorization receipt names another campaign")
    authorized = receipt.get("authorized_configs")
    if not isinstance(authorized, dict):
        raise PermissionError("campaign receipt lacks authorized config bindings")
    review = receipt.get("independent_review")
    if not isinstance(review, dict):
        raise PermissionError("campaign receipt lacks independent review binding")
    try:
        review_path = Path(review["path"])
        if not review_path.is_absolute():
            review_path = repo_root / review_path
        review_sha256 = review["sha256"]
    except (KeyError, TypeError) as error:
        raise PermissionError("campaign review binding is incomplete") from error
    if (
        not review_path.is_file()
        or sha256_file(review_path) != review_sha256
    ):
        raise PermissionError("campaign independent review hash does not match")
    configured_events = set()
    for config_path, config in configs:
        event = config["event"]
        configured_events.add(event)
        expected = authorized.get(event)
        actual = {
            "config_sha256": sha256_file(config_path),
            "event_binding_sha256": config["event_binding_sha256"],
        }
        if expected != actual:
            raise PermissionError(
                f"{event}: config is absent from or differs from campaign receipt"
            )
    if set(authorized) != configured_events:
        raise PermissionError(
            "campaign receipt event set differs from requested config set"
        )
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "status": status,
        "independent_review": {
            "path": str(review_path),
            "sha256": review_sha256,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, action="append", required=True)
    parser.add_argument("--max-workers", type=int, default=2)
    parser.add_argument("--log-dir", type=Path, required=True)
    parser.add_argument("--progress", type=Path, required=True)
    args = parser.parse_args()
    if args.max_workers < 1:
        raise ValueError("--max-workers must be positive")
    rows = []
    configs = []
    seen_events = set()
    seen_outputs = set()
    for path in args.config:
        config = load_config(path)
        event = config["event"]
        output_root = config["paths"]["output_root"]
        if event in seen_events or output_root in seen_outputs:
            raise ValueError("duplicate event or output root")
        seen_events.add(event)
        seen_outputs.add(output_root)
        configs.append((path, config))
        rows.append(
            {
                "event": event,
                "config_path": str(path),
                "config_sha256": sha256_file(path),
                "event_binding_sha256": config["event_binding_sha256"],
                "output_root": output_root,
                "status": "pending",
            }
        )
    campaign_authorization = require_campaign_authorization(args.repo_root, configs)
    for _, config in configs:
        if config["workflow"]["execution_authorized"] is not True:
            raise PermissionError(
                f"{config['event']}: config execution_authorized is false"
            )
    args.log_dir.mkdir(parents=True, exist_ok=True)
    progress = {
        "schema_version": 1,
        "status": "running",
        "max_workers": args.max_workers,
        "started_unix": time.time(),
        "stop_launch_after_failure": True,
        "campaign_authorization": campaign_authorization,
        "rows": rows,
    }
    _write(args.progress, progress)
    pending = list(rows)
    active: dict[str, tuple[subprocess.Popen, object, object, dict]] = {}
    launch_stopped = False
    runner = args.repo_root / "scripts/run_one_event_absolute_dm_workflow.py"
    while pending or active:
        while pending and len(active) < args.max_workers and not launch_stopped:
            try:
                current_authorization = require_campaign_authorization(
                    args.repo_root,
                    configs,
                )
            except PermissionError as error:
                launch_stopped = True
                progress["campaign_authorization_error"] = str(error)
                progress["campaign_authorization_revoked_unix"] = time.time()
                _write(args.progress, progress)
                break
            if current_authorization["sha256"] != campaign_authorization["sha256"]:
                launch_stopped = True
                progress["campaign_authorization_error"] = (
                    "campaign authorization receipt changed after controller start"
                )
                progress["campaign_authorization_revoked_unix"] = time.time()
                _write(args.progress, progress)
                break
            row = pending.pop(0)
            stdout_path = args.log_dir / f"{row['event']}.stdout"
            stderr_path = args.log_dir / f"{row['event']}.stderr"
            stdout = stdout_path.open("w")
            stderr = stderr_path.open("w")
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(runner),
                    "--config",
                    row["config_path"],
                    "--repo-root",
                    str(args.repo_root),
                    "--execute",
                ],
                stdout=stdout,
                stderr=stderr,
                env={
                    **os.environ,
                    "ONE_EVENT_WORKFLOW_STDOUT_LOG": str(stdout_path),
                    "ONE_EVENT_WORKFLOW_STDERR_LOG": str(stderr_path),
                },
            )
            row.update(
                {
                    "status": "running",
                    "pid": process.pid,
                    "started_unix": time.time(),
                    "stdout_path": str(stdout_path),
                    "stderr_path": str(stderr_path),
                }
            )
            active[row["event"]] = (process, stdout, stderr, row)
            _write(args.progress, progress)
        completed = []
        for event, (process, stdout, stderr, row) in active.items():
            returncode = process.poll()
            if returncode is None:
                continue
            stdout.close()
            stderr.close()
            row.update(
                {
                    "status": "completed" if returncode == 0 else "failed",
                    "returncode": returncode,
                    "completed_unix": time.time(),
                }
            )
            if returncode != 0:
                launch_stopped = True
            completed.append(event)
        for event in completed:
            del active[event]
        if completed:
            _write(args.progress, progress)
        if not completed and (pending or active):
            time.sleep(2.0)
        if launch_stopped and not active:
            break
    if pending:
        for row in pending:
            row["status"] = (
                "not_launched_campaign_authorization_revoked"
                if "campaign_authorization_error" in progress
                else "not_launched_after_failure"
            )
    failures = [row for row in rows if row["status"] != "completed"]
    progress.update(
        {
            "status": "completed" if not failures else "failed",
            "completed_unix": time.time(),
            "completed_count": sum(
                row["status"] == "completed" for row in rows
            ),
            "failure_count": len(failures),
        }
    )
    _write(args.progress, progress)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
