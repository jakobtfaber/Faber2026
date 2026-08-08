#!/usr/bin/env python3
"""Read-only advisory triage over a checkout inventory JSON.

This script consumes the deterministic JSON produced by
scripts/checkout_inventory.py and emits an advisory classification report.
It does not scan the filesystem, invoke Git, access the network, or modify
any discovered checkout or canonical project state.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


TOOL_VERSION = "1.0.0"
SCHEMA_VERSION = 1
SCHEMA_URI = "https://faber2026.jakobtfaber.com/schemas/checkout-triage-v1.schema.json"

ALLOWED_CLASSIFICATIONS = (
    "author-scratch",
    "active",
    "candidate",
    "review-ready",
    "superseded",
    "potentially-orphaned",
    "unknown",
)

ALLOWED_CONFIDENCE = ("low", "medium", "high")

PATH_HINTS = (
    "scratch",
    "tmp",
    "review",
    "publish",
    "recovery",
    "archive",
    "quarantine",
    "codex",
    "author",
)

FORBIDDEN_TERMS = (
    "safe-to-delete",
    "disposable",
    "obsolete",
    "prune",
    "cleanup-ready",
    "archive-now",
)


def fail(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    sys.exit(code)


def atomic_write_outputs(
    outputs: tuple[tuple[Path, str], ...], overwrite: bool
) -> None:
    temporary_paths: list[tuple[Path, Path]] = []
    backup_paths: list[tuple[Path, Path | None]] = []
    created_paths: list[Path] = []
    try:
        for path, content in outputs:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                delete=False,
                prefix=f".{path.name}-",
            ) as tmp:
                tmp.write(content)
                temporary_paths.append((Path(tmp.name), path))
        if overwrite:
            for _, output_path in temporary_paths:
                backup_path: Path | None = None
                if output_path.exists():
                    with tempfile.NamedTemporaryFile(
                        dir=output_path.parent,
                        delete=False,
                        prefix=f".{output_path.name}-backup-",
                    ) as backup:
                        backup_path = Path(backup.name)
                    os.unlink(backup_path)
                    os.link(output_path, backup_path)
                backup_paths.append((output_path, backup_path))
            try:
                for temporary_path, output_path in temporary_paths:
                    os.replace(temporary_path, output_path)
                    created_paths.append(output_path)
            except OSError:
                for output_path, backup_path in reversed(backup_paths):
                    if output_path not in created_paths:
                        continue
                    if backup_path is None:
                        if output_path.exists():
                            os.unlink(output_path)
                    else:
                        os.replace(backup_path, output_path)
                raise
        else:
            try:
                for temporary_path, output_path in temporary_paths:
                    os.link(temporary_path, output_path)
                    created_paths.append(output_path)
            except OSError:
                for created_path in created_paths:
                    if created_path.exists():
                        os.unlink(created_path)
                raise
    except OSError as exc:
        fail(f"could not write paired outputs: {exc}", 2)
    finally:
        for temporary_path, _ in temporary_paths:
            if temporary_path.exists():
                os.unlink(temporary_path)
        for _, backup_path in backup_paths:
            if backup_path is not None and backup_path.exists():
                os.unlink(backup_path)


def validate_no_forbidden_terms(text: str, label: str) -> None:
    lowered = text.lower()
    for word in FORBIDDEN_TERMS:
        if word in lowered:
            fail(f"{label} contains forbidden cleanup wording: {word}", 3)


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only advisory triage over a checkout inventory JSON."
    )
    parser.add_argument(
        "--inventory",
        required=True,
        type=Path,
        help="Path to the checkout inventory JSON produced by checkout_inventory.py.",
    )
    parser.add_argument(
        "--json-output", required=True, type=Path, help="Path for deterministic JSON triage output."
    )
    parser.add_argument(
        "--html-output", required=True, type=Path, help="Path for static HTML triage report."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Explicitly permit replacement of existing JSON and HTML outputs.",
    )
    return parser


def validate_output_paths(
    inventory: Path, json_out: Path, html_out: Path, overwrite: bool
) -> None:
    if json_out.resolve() == html_out.resolve():
        fail("JSON and HTML output paths must not be identical", 2)
    if json_out.exists() and html_out.exists() and os.path.samefile(json_out, html_out):
        fail("JSON and HTML output paths must not identify the same file", 2)
    for out in (json_out, html_out):
        if out.resolve() == inventory.resolve():
            fail(f"refusing to overwrite inventory file: {out}", 2)
        if out.is_dir():
            fail(f"output path is a directory: {out}", 2)
        if out.exists() and not overwrite:
            fail(f"output path already exists; pass --overwrite to replace it: {out}", 2)
        if not out.parent.is_dir():
            fail(f"output directory does not exist: {out.parent}", 2)


def validate_and_read_inventory(path: Path) -> tuple[dict[str, Any], str]:
    if not path.is_file():
        fail(f"inventory file not found: {path}", 2)
    data = path.read_bytes()
    if not data:
        fail(f"inventory file is empty: {path}", 2)
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        fail(f"inventory JSON parse error: {exc}", 2)
    if not isinstance(payload, dict):
        fail("inventory root must be a JSON object", 2)
    required = (
        "schema_version",
        "schema_uri",
        "tool_version",
        "scan_roots",
        "warnings",
        "scan_problems",
        "workspace_bundles",
        "checkout_triage",
        "branch_divergence_groups",
        "dirty_checkout_details",
        "missing_registration_details",
        "method",
    )
    missing = [k for k in required if k not in payload]
    if missing:
        fail(f"inventory missing required keys: {missing}", 2)
    if payload["schema_version"] != 2:
        fail("inventory schema_version must be 2", 2)
    if (
        payload["schema_uri"]
        != "https://faber2026.jakobtfaber.com/schemas/checkout-inventory-v2.schema.json"
    ):
        fail("inventory schema_uri is not the checkout inventory v2 schema", 2)
    if not isinstance(payload["tool_version"], str) or not payload["tool_version"]:
        fail("inventory tool_version must be a non-empty string", 2)
    if (
        not isinstance(payload["scan_roots"], list)
        or not all(
            isinstance(root, str) and bool(root) for root in payload["scan_roots"]
        )
        or len(payload["scan_roots"]) != len(set(payload["scan_roots"]))
    ):
        fail("inventory scan_roots must be unique non-empty strings", 2)
    if not isinstance(payload["checkout_triage"], list):
        fail("inventory checkout_triage must be an array", 2)
    object_arrays = (
        "branch_divergence_groups",
        "dirty_checkout_details",
        "missing_registration_details",
        "workspace_bundles",
    )
    for key in object_arrays:
        value = payload.get(key, [])
        if not isinstance(value, list) or not all(
            isinstance(item, dict) for item in value
        ):
            fail(f"inventory {key} must be an array of objects", 2)
    seen_paths: set[str] = set()
    for index, item in enumerate(payload["checkout_triage"]):
        if not isinstance(item, dict):
            fail(f"checkout_triage[{index}] must be an object", 2)
        path_value = item.get("checkout_path")
        if not isinstance(path_value, str) or not path_value:
            fail(f"checkout_triage[{index}].checkout_path must be a non-empty string", 2)
        if path_value in seen_paths:
            fail(f"duplicate checkout_path in inventory: {path_value}", 2)
        seen_paths.add(path_value)
        facts = item.get("facts")
        if not isinstance(facts, dict):
            fail(f"checkout_triage[{index}].facts must be an object", 2)
        for key in (
            "branch",
            "checkout_kind",
            "full_head_commit",
            "git_common_dir",
            "git_dir",
            "repository",
            "scan_problem_classification",
            "scan_problem_detail",
        ):
            if key in facts and facts[key] is not None and not isinstance(
                facts[key], str
            ):
                fail(
                    f"checkout_triage[{index}].facts.{key} must be a string or null",
                    2,
                )
        if "detached_head" in facts and not isinstance(
            facts["detached_head"], bool
        ):
            fail(
                f"checkout_triage[{index}].facts.detached_head must be boolean",
                2,
            )
        for key in ("local_upstream", "status"):
            if key in facts and not isinstance(facts[key], dict):
                fail(f"checkout_triage[{index}].facts.{key} must be an object", 2)
        upstream = facts.get("local_upstream", {})
        if "has_upstream" in upstream and not isinstance(
            upstream["has_upstream"], bool
        ):
            fail(
                f"checkout_triage[{index}].facts.local_upstream.has_upstream must be boolean",
                2,
            )
        for key in ("ahead", "behind"):
            if key in upstream and not (
                upstream[key] is None
                or isinstance(upstream[key], int)
                and not isinstance(upstream[key], bool)
            ):
                fail(
                    f"checkout_triage[{index}].facts.local_upstream.{key} must be integer or null",
                    2,
                )
        status = facts.get("status", {})
        for key in (
            "staged_file_paths",
            "unstaged_file_paths",
            "untracked_file_paths",
        ):
            if key in status and not isinstance(status[key], list):
                fail(
                    f"checkout_triage[{index}].facts.status.{key} must be an array",
                    2,
                )
        unique_commits = facts.get("locally_unique_looking_full_commits", [])
        if not isinstance(unique_commits, list) or not all(
            isinstance(commit, str) for commit in unique_commits
        ):
            fail(
                f"checkout_triage[{index}].facts.locally_unique_looking_full_commits must be an array of strings",
                2,
            )
        if facts.get("scan_problem_classification") and not facts.get(
            "scan_problem_detail"
        ):
            fail(
                f"checkout_triage[{index}].facts.scan_problem_detail is required for scan problems",
                2,
            )
    for index, group in enumerate(payload.get("branch_divergence_groups", [])):
        if not isinstance(group.get("repository"), str) or not isinstance(
            group.get("branch"), str
        ):
            fail(
                f"branch_divergence_groups[{index}] repository and branch must be strings",
                2,
            )
        for key in ("checkout_paths", "distinct_full_head_commits"):
            value = group.get(key)
            if not isinstance(value, list) or not all(
                isinstance(item, str) and bool(item) for item in value
            ):
                fail(
                    f"branch_divergence_groups[{index}].{key} must be an array of non-empty strings",
                    2,
                )
        relationships = group.get("locally_computable_reachability_relationships")
        if not isinstance(relationships, list) or not all(
            isinstance(item, dict) for item in relationships
        ):
            fail(
                f"branch_divergence_groups[{index}].locally_computable_reachability_relationships must be an array of objects",
                2,
            )
        for relation_index, relation in enumerate(relationships):
            required_relationship_keys = (
                "checked_from_checkout_path",
                "left_checkout_path",
                "relationship",
                "right_checkout_path",
            )
            if not all(
                isinstance(relation.get(key), str) and bool(relation.get(key))
                for key in required_relationship_keys
            ):
                fail(
                    f"branch_divergence_groups[{index}].locally_computable_reachability_relationships[{relation_index}] has invalid fields",
                    2,
                )
    for index, item in enumerate(payload.get("dirty_checkout_details", [])):
        if not isinstance(item.get("checkout_path"), str) or not item.get(
            "checkout_path"
        ):
            fail(
                f"dirty_checkout_details[{index}].checkout_path must be a non-empty string",
                2,
            )
    for index, item in enumerate(payload.get("missing_registration_details", [])):
        if not isinstance(item.get("registered_path"), str) or not item.get(
            "registered_path"
        ):
            fail(
                f"missing_registration_details[{index}].registered_path must be a non-empty string",
                2,
            )
    return payload, hashlib.sha256(data).hexdigest()


def path_has_hint(path: str) -> bool:
    lowered = path.lower()
    parts = [p for p in re.split(r"[/_.-]", lowered) if p]
    # Skip the first non-empty path component (e.g. root directory) so that
    # common roots such as /tmp or /Users are not treated as hints.
    candidates = parts[1:] if len(parts) > 1 else []
    for hint in PATH_HINTS:
        pattern = rf"\b{re.escape(hint)}\b"
        for part in candidates:
            if re.search(pattern, part):
                return True
    return False


def build_indexes(inventory: dict[str, Any]) -> dict[str, Any]:
    triage = {
        item["checkout_path"]: item for item in inventory.get("checkout_triage", [])
    }
    dirty = {
        item["checkout_path"]: item for item in inventory.get("dirty_checkout_details", [])
    }
    bundles: dict[str, dict[str, Any]] = {}
    for bundle in inventory.get("workspace_bundles", []):
        for key in ("parent_checkout", "analysis_checkout", "pipeline_checkout"):
            path = bundle.get(key)
            if path:
                bundles[path] = bundle

    by_repo: dict[str, list[str]] = {}
    by_head: dict[str, list[str]] = {}
    by_common_dir: dict[str, list[str]] = {}
    for path, item in triage.items():
        facts = item["facts"]
        repo = facts.get("repository")
        head = facts.get("full_head_commit")
        common = facts.get("git_common_dir")
        if repo:
            by_repo.setdefault(repo, []).append(path)
        if head:
            by_head.setdefault(head, []).append(path)
        if common:
            by_common_dir.setdefault(common, []).append(path)

    reachability: dict[str, list[dict[str, Any]]] = {p: [] for p in triage}
    for group in inventory.get("branch_divergence_groups", []):
        for rel in group.get("locally_computable_reachability_relationships", []):
            for key in ("left_checkout_path", "right_checkout_path"):
                reachability.setdefault(rel[key], []).append(rel)

    return {
        "triage": triage,
        "dirty": dirty,
        "bundles": bundles,
        "by_repo": by_repo,
        "by_head": by_head,
        "by_common_dir": by_common_dir,
        "reachability": reachability,
    }


def _record(
    label: str,
    confidence: str,
    evidence: list[dict[str, str]],
    counterevidence: list[dict[str, str]],
    missing_evidence: list[str],
    human_questions: list[str],
) -> dict[str, Any]:
    return {
        "proposed_classification": label,
        "confidence": confidence,
        "evidence": evidence,
        "counterevidence": counterevidence,
        "missing_evidence": missing_evidence,
        "conflicts": [],
        "human_questions": human_questions,
    }


def _counter_for_review_ready(signals: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if signals["branch"] == "main":
        out.append(
            {
                "basis": "branch",
                "detail": "commits are on main branch; review target may differ",
            }
        )
    if signals["behind"] is None:
        out.append(
            {"basis": "upstream", "detail": "upstream ref availability is unknown"}
        )
    if signals["ahead"] == 1:
        out.append(
            {"basis": "commit count", "detail": "only one commit ahead; may be trivial"}
        )
    return out


def _counter_for_superseded(signals: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if not signals["has_upstream"]:
        out.append(
            {"basis": "upstream", "detail": "no locally known upstream; reachability is local-only"}
        )
    if signals["ancestor_of"] and len(signals["ancestor_of"]) == 1:
        out.append(
            {
                "basis": "ancestry",
                "detail": "only one local checkout shows ancestry; other machines may hold newer state",
            }
        )
    return out


def _counter_for_candidate(signals: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if signals["behind"] is not None and signals["behind"] > 0:
        out.append(
            {
                "basis": "upstream divergence",
                "detail": "HEAD is behind upstream; branch may need rebasing before integration",
            }
        )
    if not signals["has_upstream"]:
        out.append(
            {"basis": "upstream", "detail": "no locally known upstream for this branch"}
        )
    return out


def _counter_for_active(signals: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if signals["behind"] is not None and signals["behind"] > 0:
        out.append(
            {
                "basis": "upstream divergence",
                "detail": "HEAD is behind upstream; local work is on an outdated base",
            }
        )
    if signals["is_dirty"] and not (signals["ahead"] or signals["unique_commits"]):
        out.append(
            {
                "basis": "working tree",
                "detail": "dirty state alone is not sufficient to establish active authority",
            }
        )
    if not signals["has_upstream"] and not signals["unique_commits"]:
        out.append(
            {
                "basis": "provenance",
                "detail": "no upstream and no locally unique commits reduce active confidence",
            }
        )
    return out


def _counter_for_author_scratch(signals: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if signals["branch"] and signals["branch"] != "main":
        out.append(
            {
                "basis": "branch",
                "detail": "named non-main branch may be more than scratch work",
            }
        )
    if signals["has_upstream"]:
        out.append(
            {
                "basis": "upstream",
                "detail": "upstream exists; scratch may already be tracked remotely",
            }
        )
    if signals["ahead"] is not None and signals["ahead"] > 0:
        out.append(
            {
                "basis": "commits",
                "detail": "commits ahead of upstream may be intended for landing",
            }
        )
    return out


def _counter_for_orphaned(signals: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    if signals["unique_commits"]:
        out.append(
            {
                "basis": "commits",
                "detail": "locally unique commits contradict an orphaned reading",
            }
        )
    if signals["is_dirty"]:
        out.append(
            {
                "basis": "working tree",
                "detail": "uncommitted changes suggest recent activity",
            }
        )
    return out


def classify(signals: dict[str, Any]) -> dict[str, Any]:
    evidence: list[dict[str, str]] = []
    counter: list[dict[str, str]] = []
    missing: list[str] = []
    questions: list[str] = []

    if signals["is_broken"]:
        evidence.append(
            {
                "basis": "inventory scan problem",
                "detail": f"checkout metadata is broken or inaccessible: {signals['scan_problem']}",
            }
        )
        questions.append("Is this path expected to exist and be readable?")
        return _record(
            "potentially-orphaned",
            "medium",
            evidence,
            _counter_for_orphaned(signals),
            missing,
            questions,
        )

    has_reviewable_commits = (
        signals["ahead"] is not None and signals["ahead"] > 0
    ) or bool(signals["unique_commits"])
    if (
        not signals["is_dirty"]
        and signals["has_upstream"]
        and signals["behind"] == 0
        and has_reviewable_commits
        and not signals["superseded_by"]
    ):
        evidence.extend(
            [
                {
                    "basis": "working tree",
                    "detail": "no staged, unstaged, untracked, or submodule dirt present",
                },
                {
                    "basis": "upstream ref",
                    "detail": "checkout has a locally known upstream",
                },
                {
                    "basis": "divergence",
                    "detail": (
                        f"HEAD is ahead of upstream by {signals['ahead']} commit(s) and not behind"
                        if signals["ahead"] is not None and signals["ahead"] > 0
                        else f"{len(signals['unique_commits'])} locally unique commit(s) not behind upstream"
                    ),
                },
            ]
        )
        questions.append("Who should review these commits?")
        return _record(
            "review-ready",
            "high",
            evidence,
            _counter_for_review_ready(signals),
            [
                "Remote pull request or review state is not inferable from local inventory."
            ],
            questions,
        )

    has_local_commits = bool(
        signals["unique_commits"]
        or (signals["ahead"] is not None and signals["ahead"] > 0)
        or signals["descendant_of"]
    )
    if (
        not signals["is_dirty"]
        and not has_local_commits
        and signals["superseded_by"]
    ):
        if "local_upstream" in signals["superseded_by"]:
            evidence.append(
                {
                    "basis": "upstream ref",
                    "detail": f"HEAD is behind upstream by {signals['behind']} commit(s) and has no local commits ahead",
                }
            )
        for other in signals["ancestor_of"]:
            evidence.append(
                {
                    "basis": "local ancestry",
                    "detail": f"HEAD is an ancestor of {other}",
                }
            )
        missing.append("Upstream or sibling checkout authority is not proven.")
        questions.append(
            "Confirm whether this checkout can be retired after verifying no unique work."
        )
        return _record(
            "superseded",
            "high",
            evidence,
            _counter_for_superseded(signals),
            missing,
            questions,
        )

    candidate_commits = bool(signals["unique_commits"]) or (
        signals["ahead"] is not None and signals["ahead"] > 0
    )
    if (
        not signals["is_dirty"]
        and signals["branch"]
        and signals["branch"] != "main"
        and candidate_commits
        and not signals["superseded_by"]
    ):
        evidence.extend(
            [
                {"basis": "working tree", "detail": "clean working tree"},
                {
                    "basis": "branch",
                    "detail": f"branch '{signals['branch']}' is not main",
                },
                {
                    "basis": "local commits",
                    "detail": f"{len(signals['unique_commits'])} commit(s) not reachable from other local refs",
                },
            ]
        )
        missing.append("Remote branch or pull request state is not inferable.")
        questions.append("Is this branch intended for integration?")
        return _record(
            "candidate",
            "medium",
            evidence,
            _counter_for_candidate(signals),
            missing,
            questions,
        )

    active_signal = (
        signals["is_dirty"]
        or (signals["ahead"] is not None and signals["ahead"] > 0)
        or bool(signals["unique_commits"])
        or bool(signals["descendant_of"])
    )
    if (
        signals["branch"]
        and signals["branch"] != "main"
        and active_signal
        and not signals["superseded_by"]
    ):
        evidence.append(
            {
                "basis": "branch",
                "detail": f"branch '{signals['branch']}' is not main",
            }
        )
        if signals["is_dirty"]:
            evidence.append(
                {
                    "basis": "working tree",
                    "detail": "has uncommitted or staged changes",
                }
            )
        if signals["ahead"] is not None and signals["ahead"] > 0:
            evidence.append(
                {
                    "basis": "upstream divergence",
                    "detail": f"ahead of upstream by {signals['ahead']} commit(s)",
                }
            )
        if signals["unique_commits"]:
            evidence.append(
                {
                    "basis": "local commits",
                    "detail": f"{len(signals['unique_commits'])} locally unique commit(s)",
                }
            )
        if signals["descendant_of"]:
            evidence.append(
                {
                    "basis": "local ancestry",
                    "detail": f"HEAD is a descendant of {signals['descendant_of'][0]}",
                }
            )
        missing.append("Owner intent and remote state are not inferable.")
        questions.append("What work is active here and where should it land?")
        return _record(
            "active",
            "medium",
            evidence,
            _counter_for_active(signals),
            missing,
            questions,
        )

    if signals["is_dirty"] and signals["path_hint"] and not signals["superseded_by"]:
        evidence.append(
            {"basis": "working tree", "detail": "has uncommitted or staged changes"}
        )
        evidence.append(
            {
                "basis": "pathname inference",
                "detail": "path contains a scratch/review/codex/author hint",
            }
        )
        if not signals["has_upstream"]:
            evidence.append(
                {"basis": "upstream", "detail": "no locally known upstream"}
            )
        if signals["unique_commits"]:
            evidence.append(
                {
                    "basis": "local commits",
                    "detail": "has locally unique commits",
                }
            )
        missing.append("Process ownership and intended landing place are not inferable.")
        questions.append(
            "Is this scratch work that should be landed, discarded, or moved?"
        )
        counter = _counter_for_author_scratch(signals)
        confidence = "medium"
        if (signals["ahead"] is not None and signals["ahead"] > 0) or (
            signals["branch"] and signals["branch"] != "main" and signals["has_upstream"]
        ):
            confidence = "low"
            counter.append(
                {
                    "basis": "landing signals",
                    "detail": "non-main tracked branch or commits ahead contradict a scratch reading",
                }
            )
        return _record(
            "author-scratch",
            confidence,
            evidence,
            counter,
            missing,
            questions,
        )

    if (
        (signals["detached"] and not signals["has_upstream"] and not signals["unique_commits"] and not signals["is_dirty"])
        or (
            not signals["branch"]
            and not signals["has_upstream"]
            and not signals["is_dirty"]
            and not signals["unique_commits"]
        )
    ):
        evidence.append(
            {
                "basis": "checkout state",
                "detail": "no usable branch or upstream and no local commits",
            }
        )
        if signals["detached"]:
            evidence.append(
                {"basis": "HEAD", "detail": "checkout is on detached HEAD"}
            )
        missing.append("Owner and origin of HEAD are not inferable.")
        questions.append("Is this checkout retained intentionally?")
        return _record(
            "potentially-orphaned",
            "medium" if signals["detached"] else "low",
            evidence,
            _counter_for_orphaned(signals),
            missing,
            questions,
        )

    evidence.append(
        {
            "basis": "insufficient signals",
            "detail": "inventory facts do not support a narrower classification",
        }
    )
    if signals["is_dirty"]:
        evidence.append(
            {"basis": "working tree", "detail": "has uncommitted or staged changes"}
        )
    if signals["branch"]:
        evidence.append(
            {"basis": "branch", "detail": f"branch is {signals['branch']}"}
        )
    if signals["has_upstream"]:
        evidence.append(
            {"basis": "upstream", "detail": "upstream exists locally"}
        )
    questions.append(
        "What additional provenance is needed to classify this checkout?"
    )
    return _record("unknown", "low", evidence, [], [], questions)


def signals_for(
    checkout_id: str, inventory: dict[str, Any], indexes: dict[str, Any]
) -> dict[str, Any]:
    triage = indexes["triage"][checkout_id]
    facts = triage["facts"]
    dirty = indexes["dirty"].get(checkout_id)
    status = facts.get("status", {})
    branch = facts.get("branch")
    repo = facts.get("repository")
    head = facts.get("full_head_commit")
    upstream = facts.get("local_upstream", {})
    kind = facts.get("checkout_kind")
    ahead = upstream.get("ahead")
    behind = upstream.get("behind")
    has_upstream = upstream.get("has_upstream", False)
    is_broken = kind is None and facts.get("scan_problem_classification") is not None

    is_dirty = dirty is not None or bool(
        status.get("staged_file_paths")
        or status.get("unstaged_file_paths")
        or status.get("untracked_file_paths")
    )
    unique_commits = facts.get("locally_unique_looking_full_commits", [])
    detached = facts.get("detached_head") is True or kind == "detached"

    ancestor_of: list[str] = []
    descendant_of: list[str] = []
    for rel in indexes["reachability"].get(checkout_id, []):
        if rel["relationship"] == "unrelated_or_not_locally_computable":
            continue
        if rel["left_checkout_path"] == checkout_id:
            if rel["relationship"] == "left_ancestor_of_right":
                ancestor_of.append(rel["right_checkout_path"])
            elif rel["relationship"] == "right_ancestor_of_left":
                descendant_of.append(rel["right_checkout_path"])
        elif rel["right_checkout_path"] == checkout_id:
            if rel["relationship"] == "right_ancestor_of_left":
                ancestor_of.append(rel["left_checkout_path"])
            elif rel["relationship"] == "left_ancestor_of_right":
                descendant_of.append(rel["left_checkout_path"])

    superseded_by: list[str] = []
    if (
        behind is not None
        and behind > 0
        and (ahead is None or ahead == 0)
        and not unique_commits
        and not is_dirty
    ):
        superseded_by.append("local_upstream")
    for other in ancestor_of:
        superseded_by.append(f"checkout:{other}")

    same_repo = [p for p in indexes["by_repo"].get(repo, []) if p != checkout_id] if repo else []
    same_head = [p for p in indexes["by_head"].get(head, []) if p != checkout_id] if head else []
    same_common = [
        p
        for p in indexes["by_common_dir"].get(facts.get("git_common_dir"), [])
        if p != checkout_id
    ]

    return {
        "checkout_id": checkout_id,
        "repo": repo,
        "branch": branch,
        "head": head,
        "kind": kind,
        "is_dirty": is_dirty,
        "unique_commits": unique_commits,
        "path_hint": path_has_hint(checkout_id),
        "detached": detached,
        "has_upstream": has_upstream,
        "ahead": ahead,
        "behind": behind,
        "is_broken": is_broken,
        "scan_problem": facts.get("scan_problem_classification"),
        "ancestor_of": sorted(ancestor_of),
        "descendant_of": sorted(descendant_of),
        "superseded_by": sorted(superseded_by),
        "same_repo": sorted(same_repo),
        "same_head": sorted(same_head),
        "same_common_dir": sorted(same_common),
    }


def build_relationships(
    inventory: dict[str, Any], indexes: dict[str, Any]
) -> list[dict[str, Any]]:
    relationships: list[dict[str, Any]] = []
    triage = indexes["triage"]

    repo_heads: dict[tuple[str, str], list[str]] = {}
    for path, item in triage.items():
        facts = item["facts"]
        repo = facts.get("repository")
        head = facts.get("full_head_commit")
        if repo and head:
            repo_heads.setdefault((repo, head), []).append(path)
    for (repo, head), members in repo_heads.items():
        if len(members) >= 2:
            relationships.append(
                {
                    "kind": "same_repository_same_head",
                    "checkout_ids": sorted(members),
                    "detail": f"repository {repo} has same HEAD {head}",
                }
            )

    for group in inventory.get("branch_divergence_groups", []):
        relationships.append(
            {
                "kind": "same_repository_divergent_heads",
                "checkout_ids": sorted(group["checkout_paths"]),
                "detail": f"repository {group['repository']} branch {group['branch']} has {len(group['distinct_full_head_commits'])} distinct HEADs",
            }
        )

    for common, members in indexes["by_common_dir"].items():
        if len(members) < 2:
            continue
        relationships.append(
            {
                "kind": "linked_worktrees",
                "checkout_ids": sorted(members),
                "detail": f"share git common directory {common}",
            }
        )

    for repo, members in indexes["by_repo"].items():
        common_groups: dict[str, list[str]] = {}
        for path in members:
            common = triage[path]["facts"].get("git_common_dir")
            common_groups.setdefault(common or "independent", []).append(path)
        independent = []
        for common, paths in common_groups.items():
            if len(paths) != 1:
                continue
            path = paths[0]
            facts = triage[path]["facts"]
            if (
                facts.get("checkout_kind") == "standalone_clone"
                and facts.get("git_dir") == common
            ):
                independent.append(path)
        if len(independent) >= 2:
            relationships.append(
                {
                    "kind": "independent_clones",
                    "checkout_ids": sorted(independent),
                    "detail": f"independent clones of {repo}",
                }
            )

    seen_pairs: set[tuple[str, str]] = set()
    for group in inventory.get("branch_divergence_groups", []):
        for rel in group.get("locally_computable_reachability_relationships", []):
            if rel["relationship"] == "unrelated_or_not_locally_computable":
                continue
            pair = tuple(sorted([rel["left_checkout_path"], rel["right_checkout_path"]]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            relationships.append(
                {
                    "kind": "contained_checkouts",
                    "checkout_ids": sorted([rel["left_checkout_path"], rel["right_checkout_path"]]),
                    "detail": f"{rel['relationship']} checked from {rel['checked_from_checkout_path']}",
                }
            )

    dirty_paths = set(indexes["dirty"])
    for repo, members in indexes["by_repo"].items():
        d = sorted(p for p in members if p in dirty_paths)
        if len(d) >= 2:
            relationships.append(
                {
                    "kind": "dirty_checkouts_same_repository",
                    "checkout_ids": d,
                    "detail": f"repository {repo}",
                }
            )

    branch_groups: dict[tuple[str, str], list[str]] = {}
    for path, item in triage.items():
        branch = item["facts"].get("branch")
        repo = item["facts"].get("repository")
        if branch and repo and path in dirty_paths:
            branch_groups.setdefault((repo, branch), []).append(path)
    for (repo, branch), members in sorted(branch_groups.items()):
        if len(members) >= 2:
            relationships.append(
                {
                    "kind": "dirty_checkouts_same_branch",
                    "checkout_ids": sorted(members),
                    "detail": f"repository {repo} branch {branch}",
                }
            )

    detached = sorted(
        p
        for p, item in triage.items()
        if item["facts"].get("detached_head")
        or item["facts"].get("checkout_kind") == "detached"
    )
    if detached:
        relationships.append(
            {
                "kind": "detached_checkouts",
                "checkout_ids": detached,
                "detail": "checkouts on detached HEAD",
            }
        )

    inaccessible = sorted(
        p
        for p, item in triage.items()
        if item["facts"].get("checkout_kind") is None
        and item["facts"].get("scan_problem_classification")
    )
    for path in inaccessible:
        relationships.append(
            {
                "kind": "inaccessible_checkout",
                "checkout_ids": [path],
                "detail": triage[path]["facts"]["scan_problem_detail"],
            }
        )

    for missing in inventory.get("missing_registration_details", []):
        relationships.append(
            {
                "kind": "missing_registered_worktree",
                "checkout_ids": [missing["registered_path"]],
                "detail": f"registered branch/ref {missing.get('branch_or_ref')}",
            }
        )

    return sorted(relationships, key=lambda item: (item["kind"], item["checkout_ids"]))


def build_conflicts(
    records: list[dict[str, Any]],
    signals_map: dict[str, dict[str, Any]],
    inventory: dict[str, Any],
    indexes: dict[str, Any],
) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []

    for rec in records:
        cid = rec["checkout_id"]
        sig = signals_map[cid]
        if sig["superseded_by"] and rec["proposed_classification"] not in (
            "superseded",
            "potentially-orphaned",
            "unknown",
        ):
            conflicts.append(
                {
                    "kind": "superseded_signal_present",
                    "checkout_ids": [cid],
                    "detail": f"classified as {rec['proposed_classification']} but local inventory shows it is behind or an ancestor of another checkout",
                }
            )
        if rec["proposed_classification"] in ("review-ready", "candidate") and sig["is_dirty"]:
            conflicts.append(
                {
                    "kind": "clean_classification_with_dirt",
                    "checkout_ids": [cid],
                    "detail": "classified as clean/review but inventory shows dirty working tree",
                }
            )
        if rec["proposed_classification"] == "superseded" and (
            sig["is_dirty"] or sig["unique_commits"]
        ):
            conflicts.append(
                {
                    "kind": "superseded_with_local_work",
                    "checkout_ids": [cid],
                    "detail": "classified as superseded but checkout has local work or unique commits",
                }
            )
        if rec["proposed_classification"] == "author-scratch":
            if sig["branch"] and sig["branch"] != "main" and sig["has_upstream"]:
                conflicts.append(
                    {
                        "kind": "scratch_vs_tracked_branch",
                        "checkout_ids": [cid],
                        "detail": "path hints suggest scratch but branch is tracked and has upstream",
                    }
                )
            if sig["ahead"] is not None and sig["ahead"] > 0:
                conflicts.append(
                    {
                        "kind": "scratch_with_commits_ahead",
                        "checkout_ids": [cid],
                        "detail": "path hints suggest scratch but commits are ahead of upstream",
                    }
                )

    for group in inventory.get("branch_divergence_groups", []):
        if len(group["distinct_full_head_commits"]) > 1:
            conflicts.append(
                {
                    "kind": "divergent_clones",
                    "checkout_ids": sorted(group["checkout_paths"]),
                    "detail": f"same repository/branch {group['repository']}/{group['branch']} has multiple HEADs",
                }
            )

    for repo, paths in indexes["by_repo"].items():
        standalone_paths = [
            path
            for path in paths
            if indexes["triage"][path]["facts"].get("checkout_kind")
            == "standalone_clone"
            and indexes["triage"][path]["facts"].get("git_dir")
            == indexes["triage"][path]["facts"].get("git_common_dir")
        ]
        if len(standalone_paths) >= 2:
            heads = {
                indexes["triage"][p]["facts"].get("full_head_commit")
                for p in standalone_paths
            }
            if len(heads) > 1:
                conflicts.append(
                    {
                        "kind": "independent_clones_divergent",
                        "checkout_ids": sorted(standalone_paths),
                        "detail": f"independent clones of {repo} have divergent HEADs",
                    }
                )

    return sorted(conflicts, key=lambda item: (item["kind"], item["checkout_ids"]))


def build_questions(records: list[dict[str, Any]], conflicts: list[dict[str, Any]]) -> list[str]:
    questions: set[str] = set()
    for rec in records:
        for q in rec["human_questions"]:
            questions.add(q)
    for conflict in conflicts:
        if conflict["kind"] == "divergent_clones":
            questions.add(
                "Which of the divergent checkouts is the intended successor?"
            )
        elif conflict["kind"] == "independent_clones_divergent":
            questions.add(
                "Do these independent clones represent parallel work or stale copies?"
            )
        elif conflict["kind"] == "superseded_signal_present":
            questions.add(
                "Confirm whether the older checkout can be retired without losing work."
            )
    return sorted(questions)


def aggregate_counts(
    records: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    questions: list[str],
) -> dict[str, Any]:
    classification_counts = {c: 0 for c in ALLOWED_CLASSIFICATIONS}
    confidence_counts = {c: 0 for c in ALLOWED_CONFIDENCE}
    for rec in records:
        classification_counts[rec["proposed_classification"]] += 1
        confidence_counts[rec["confidence"]] += 1
    return {
        "total_checkouts": len(records),
        "classification_counts": classification_counts,
        "confidence_counts": confidence_counts,
        "relationship_count": len(relationships),
        "conflict_count": len(conflicts),
        "unresolved_question_count": len(questions),
    }


def build_payload(
    inventory: dict[str, Any],
    input_sha256: str,
    records: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    questions: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "schema_uri": SCHEMA_URI,
        "tool_version": TOOL_VERSION,
        "input_sha256": input_sha256,
        "inventory_identity": {
            "schema_version": inventory.get("schema_version"),
            "schema_uri": inventory.get("schema_uri"),
            "tool_version": inventory.get("tool_version"),
            "scan_roots": inventory.get("scan_roots", []),
        },
        "advisory_records": records,
        "relationships": relationships,
        "conflicts": conflicts,
        "unresolved_human_questions": questions,
        "aggregate_counts": aggregate_counts(records, relationships, conflicts, questions),
    }


def _html_table(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
    out = [
        "<table><tr>"
        + "".join(f"<th>{esc(column)}</th>" for column in columns)
        + "</tr>"
    ]
    for row in rows:
        out.append(
            "<tr>"
            + "".join(
                f"<td><code>{esc(row.get(column))}</code></td>" for column in columns
            )
            + "</tr>"
        )
    out.append("</table>")
    return out


def render_html(payload: dict[str, Any]) -> str:
    counts = payload["aggregate_counts"]
    out = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>Checkout Advisory Triage</title>",
        "<style>",
        "body{font:14px system-ui,sans-serif;margin:2rem;line-height:1.4}",
        "h1,h2{color:#333}",
        ".notice{background:#fff3cd;border:1px solid #ffeeba;padding:1rem;margin:1rem 0}",
        "table{border-collapse:collapse;width:100%;margin:1rem 0}",
        "th,td{border:1px solid #ddd;padding:.5rem;text-align:left;vertical-align:top}",
        "th{background:#f5f5f5}",
        "code{font-family:monospace;font-size:.9em}",
        ".card{border:1px solid #ddd;padding:1rem;margin:1rem 0}",
        ".evidence-list{margin:.25rem 0;padding-left:1.5rem}",
        "</style>",
        "</head><body>",
        "<h1>Checkout Advisory Triage</h1>",
        '<div class="notice"><strong>Advisory only:</strong> These are proposals for human review. No checkout should be moved, deleted, reset, rebased, archived, or modified from this output. Human confirmation and additional provenance are required before canonical classification. Scientific authority cannot be inferred from Git state.</div>',
        "<h2>Summary</h2>",
    ]
    out.append(f"<p>Input SHA-256: <code>{esc(payload['input_sha256'])}</code></p>")
    out.append(f"<p>Total checkouts: {counts['total_checkouts']}</p>")
    out.append("<p>Classifications:</p><ul>")
    for cls, n in counts["classification_counts"].items():
        out.append(f"<li>{esc(cls)}: {n}</li>")
    out.append("</ul>")
    out.append(
        f"<p>Relationships: {counts['relationship_count']} | Conflicts: {counts['conflict_count']} | Unresolved questions: {counts['unresolved_question_count']}</p>"
    )

    out.append("<h2>Advisory classifications</h2>")
    for rec in payload["advisory_records"]:
        out.append('<div class="card">')
        out.append(f"<h3>{esc(rec['checkout_id'])}</h3>")
        out.append(
            f"<p><strong>Proposal:</strong> {esc(rec['proposed_classification'])} &nbsp; <strong>Confidence:</strong> {esc(rec['confidence'])}</p>"
        )
        out.append("<p>Evidence:</p><ul class=\"evidence-list\">")
        for ev in rec["evidence"]:
            out.append(
                f"<li>{esc(ev.get('basis', ''))}: {esc(ev.get('detail', ''))}</li>"
            )
        out.append("</ul>")
        if rec["counterevidence"]:
            out.append("<p>Counter-evidence:</p><ul class=\"evidence-list\">")
            for ev in rec["counterevidence"]:
                out.append(
                    f"<li>{esc(ev.get('basis', ''))}: {esc(ev.get('detail', ''))}</li>"
                )
            out.append("</ul>")
        if rec["missing_evidence"]:
            out.append("<p>Missing evidence:</p><ul class=\"evidence-list\">")
            for q in rec["missing_evidence"]:
                out.append(f"<li>{esc(q)}</li>")
            out.append("</ul>")
        if rec["human_questions"]:
            out.append("<p>Questions:</p><ul class=\"evidence-list\">")
            for q in rec["human_questions"]:
                out.append(f"<li>{esc(q)}</li>")
            out.append("</ul>")
        out.append("</div>")

    out.append("<h2>Relationships</h2>")
    out.extend(_html_table(payload["relationships"], ["kind", "checkout_ids", "detail"]))
    out.append("<h2>Conflicts</h2>")
    out.extend(_html_table(payload["conflicts"], ["kind", "checkout_ids", "detail"]))
    out.append("<h2>Unresolved questions</h2>")
    out.append("<ul>")
    for q in payload["unresolved_human_questions"]:
        out.append(f"<li>{esc(q)}</li>")
    out.append("</ul>")
    out.append("</body></html>\n")
    rendered = "\n".join(out)
    validate_no_forbidden_terms(rendered, "HTML")
    return rendered


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    validate_output_paths(
        args.inventory, args.json_output, args.html_output, args.overwrite
    )
    inventory, input_sha256 = validate_and_read_inventory(args.inventory)
    indexes = build_indexes(inventory)
    records: list[dict[str, Any]] = []
    signals_map: dict[str, dict[str, Any]] = {}
    for checkout_id in sorted(indexes["triage"]):
        signals = signals_for(checkout_id, inventory, indexes)
        signals_map[checkout_id] = signals
        records.append({"checkout_id": checkout_id, **classify(signals)})

    relationships = build_relationships(inventory, indexes)
    conflicts = build_conflicts(records, signals_map, inventory, indexes)
    by_checkout_conflicts: dict[str, list[str]] = {
        rec["checkout_id"]: [] for rec in records
    }
    for conflict in conflicts:
        for cid in conflict["checkout_ids"]:
            if cid in by_checkout_conflicts:
                by_checkout_conflicts[cid].append(conflict["kind"])
    for rec in records:
        rec["conflicts"] = sorted(set(by_checkout_conflicts[rec["checkout_id"]]))
    questions = build_questions(records, conflicts)
    payload = build_payload(
        inventory, input_sha256, records, relationships, conflicts, questions
    )
    json_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    validate_no_forbidden_terms(json_text, "JSON")
    html = render_html(payload)
    atomic_write_outputs(
        ((args.json_output, json_text), (args.html_output, html)), args.overwrite
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
