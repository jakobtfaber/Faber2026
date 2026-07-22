#!/usr/bin/env python3
"""Inventory local Git checkouts without network or repository mutation."""

from __future__ import annotations

import argparse
import html
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Callable


KNOWN_GITHUB_REPOS = {
    "jakobtfaber/Faber2026",
    "jakobtfaber/Faber2026-analysis",
    "jakobtfaber/dsa110-FLITS",
}
PARENT_REPOSITORY = "jakobtfaber/Faber2026"
ANALYSIS_REPOSITORY = "jakobtfaber/Faber2026-analysis"
PIPELINE_REPOSITORY = "jakobtfaber/dsa110-FLITS"
TOOL_VERSION = "2.0.0"
SCHEMA_URI = "https://faber2026.jakobtfaber.com/schemas/checkout-inventory-v2.schema.json"
PATH_HINTS = (
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
    "prunable",
    "obsolete",
    "disposable",
    "abandoned",
    "safe-to-delete",
)


@dataclass(frozen=True)
class GitResult:
    stdout: str
    stderr: str
    returncode: int


Runner = Callable[..., subprocess.CompletedProcess[str]]


def git_args_allowed(args: list[str]) -> bool:
    if args in (
        ["remote", "-v"],
        ["ls-tree", "-r", "HEAD"],
        ["rev-parse", "--verify", "HEAD^{commit}"],
        ["symbolic-ref", "-q", "HEAD"],
        ["symbolic-ref", "-q", "--short", "HEAD"],
        ["rev-parse", "--show-toplevel"],
        ["rev-parse", "--git-dir"],
        ["rev-parse", "--git-common-dir"],
        ["rev-parse", "--is-bare-repository"],
        ["status", "--porcelain=v1", "-b", "--untracked-files=all", "--ignore-submodules=none"],
        ["for-each-ref", "--format=%(refname)"],
        ["worktree", "list", "--porcelain"],
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
        ["rev-parse", "--symbolic-full-name", "@{upstream}"],
        ["rev-list", "--left-right", "--count", "HEAD...@{upstream}"],
    ):
        return True
    if args[:3] == ["rev-list", "--reverse", "HEAD"]:
        return len(args) == 3 or (len(args) >= 5 and args[3] == "--not")
    if len(args) == 3 and args[:2] == ["cat-file", "-e"]:
        return args[2].endswith("^{commit}")
    if len(args) == 4 and args[:2] == ["for-each-ref", "--format=%(refname)"] and args[2] == "--contains":
        return True
    if len(args) == 4 and args[:2] == ["merge-base", "--is-ancestor"]:
        return True
    return False


def run_git(
    args: list[str],
    *,
    cwd: Path | None = None,
    git_dir: Path | None = None,
    runner: Runner = subprocess.run,
) -> GitResult:
    if not git_args_allowed(args):
        raise ValueError(f"git command is outside checkout inventory allowlist: {args}")
    command = ["git"]
    if cwd is not None:
        command.extend(["-C", str(cwd)])
    if git_dir is not None:
        command.extend(["--git-dir", str(git_dir)])
    command.extend(args)
    result = runner(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    return GitResult(result.stdout.strip(), result.stderr.strip(), result.returncode)


def resolved(path: Path) -> str:
    return str(path.expanduser().resolve(strict=False))


def is_within_or_same(child: str, parent: str) -> bool:
    child_path = Path(child)
    parent_path = Path(parent)
    return child_path == parent_path or parent_path in child_path.parents


def abs_git_path(value: str, base: Path) -> str:
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    return resolved(path)


def normalize_github_url(url: str) -> str | None:
    cleaned = url.strip()
    if cleaned.startswith("git@github.com:"):
        slug = cleaned.removeprefix("git@github.com:")
    elif cleaned.startswith("ssh://git@github.com/"):
        slug = cleaned.removeprefix("ssh://git@github.com/")
    elif cleaned.startswith("https://github.com/"):
        slug = cleaned.removeprefix("https://github.com/")
    elif cleaned.startswith("http://github.com/"):
        slug = cleaned.removeprefix("http://github.com/")
    else:
        return None
    slug = slug.removesuffix(".git").strip("/")
    parts = slug.split("/")
    if len(parts) < 2:
        return None
    canonical = f"{parts[0]}/{parts[1]}"
    for known in KNOWN_GITHUB_REPOS:
        if canonical.lower() == known.lower():
            return known
    return canonical


def parse_remotes(text: str) -> list[dict[str, str | None]]:
    remotes: list[dict[str, str | None]] = []
    seen: set[tuple[str, str, str]] = set()
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        name, url, role = parts[0], parts[1], parts[2].strip("()")
        key = (name, url, role)
        if key in seen:
            continue
        seen.add(key)
        remotes.append(
            {
                "name": name,
                "url": url,
                "role": role,
                "github_slug": normalize_github_url(url),
            }
        )
    return sorted(
        remotes,
        key=lambda item: (item["name"] or "", item["role"] or "", item["url"] or ""),
    )


def recognized_repository(remotes: list[dict[str, str | None]]) -> str | None:
    for remote in remotes:
        if remote["role"] == "fetch" and remote["github_slug"] in KNOWN_GITHUB_REPOS:
            return str(remote["github_slug"])
    for remote in remotes:
        if remote["github_slug"] in KNOWN_GITHUB_REPOS:
            return str(remote["github_slug"])
    return None


def parse_porcelain_status(text: str) -> dict[str, Any]:
    branch_line = ""
    staged: list[str] = []
    unstaged: list[str] = []
    untracked: list[str] = []
    raw_entries: list[dict[str, str]] = []
    for line in text.splitlines():
        if line.startswith("## "):
            branch_line = line[3:]
            continue
        if len(line) < 3:
            continue
        xy = line[:2]
        path = line[3:]
        raw_entries.append({"xy": xy, "path": path})
        if xy == "??":
            untracked.append(path)
            continue
        if xy == "!!":
            continue
        if xy[0] != " ":
            staged.append(path)
        if xy[1] != " ":
            unstaged.append(path)
    return {
        "branch_line": branch_line,
        "staged_file_paths": sorted(staged),
        "unstaged_file_paths": sorted(unstaged),
        "untracked_file_paths": sorted(untracked),
        "raw_entries": sorted(raw_entries, key=lambda item: (item["path"], item["xy"])),
    }


def local_upstream_state(
    repo: Path, status_branch_line: str, runner: Runner = subprocess.run
) -> dict[str, Any]:
    limits = "Computed from local refs only; no network fetch or remote query used."
    upstream_short = run_git(
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
        cwd=repo,
        runner=runner,
    )
    upstream_full = run_git(
        ["rev-parse", "--symbolic-full-name", "@{upstream}"],
        cwd=repo,
        runner=runner,
    )
    if upstream_short.returncode != 0:
        parsed_upstream = None
        if "..." in status_branch_line:
            parsed_upstream = status_branch_line.split("...", 1)[1].split(" ", 1)[0]
        return {
            "has_upstream": parsed_upstream is not None,
            "upstream": parsed_upstream,
            "upstream_ref": None,
            "ahead": None,
            "behind": None,
            "state": "missing_upstream"
            if parsed_upstream is None
            else "upstream_ref_unavailable_locally",
            "limits": limits,
        }
    counts = run_git(
        ["rev-list", "--left-right", "--count", "HEAD...@{upstream}"],
        cwd=repo,
        runner=runner,
    )
    if counts.returncode != 0:
        return {
            "has_upstream": True,
            "upstream": upstream_short.stdout,
            "upstream_ref": upstream_full.stdout if upstream_full.returncode == 0 else None,
            "ahead": None,
            "behind": None,
            "state": "unavailable",
            "limits": limits,
        }
    ahead_text, _, behind_text = counts.stdout.partition("\t")
    return {
        "has_upstream": True,
        "upstream": upstream_short.stdout,
        "upstream_ref": upstream_full.stdout if upstream_full.returncode == 0 else None,
        "ahead": int(ahead_text),
        "behind": int(behind_text),
        "state": "locally_computed",
        "limits": limits,
    }


def path_matches(path: str, prefix: str) -> bool:
    return (
        path == prefix
        or path.startswith(f"{prefix}/")
        or path.startswith(f"{prefix} -> ")
    )


def submodule_repository(
    repo: Path, rel_path: str, runner: Runner = subprocess.run
) -> str | None:
    subdir = repo / rel_path
    if not (subdir / ".git").exists():
        return None
    remotes = run_git(["remote", "-v"], cwd=subdir, runner=runner)
    if remotes.returncode != 0:
        return None
    return recognized_repository(parse_remotes(remotes.stdout))


def inspect_recorded_submodules(
    repo: Path, runner: Runner = subprocess.run
) -> list[dict[str, Any]]:
    tree = run_git(["ls-tree", "-r", "HEAD"], cwd=repo, runner=runner)
    if tree.returncode != 0:
        return []
    submodules: list[dict[str, Any]] = []
    for line in tree.stdout.splitlines():
        meta, _, rel = line.partition("\t")
        parts = meta.split()
        if len(parts) >= 3 and parts[0] == "160000":
            checkout_present = (repo / rel / ".git").exists()
            head_result = (
                run_git(
                    ["rev-parse", "--verify", "HEAD^{commit}"],
                    cwd=repo / rel,
                    runner=runner,
                )
                if checkout_present
                else GitResult("", "", 1)
            )
            submodules.append(
                {
                    "path": rel,
                    "recorded_pin": parts[2],
                    "checkout_present": checkout_present,
                    "checkout_head": head_result.stdout
                    if head_result.returncode == 0
                    else None,
                    "repository": submodule_repository(repo, rel, runner=runner),
                }
            )
    return sorted(submodules, key=lambda item: item["path"])


def submodule_dirtiness(
    repo: Path, status_entries: list[dict[str, str]], runner: Runner = subprocess.run
) -> list[dict[str, Any]]:
    modules = inspect_recorded_submodules(repo, runner=runner)
    details: list[dict[str, Any]] = []
    for module in modules:
        flags = [
            entry["xy"]
            for entry in status_entries
            if path_matches(entry["path"], module["path"])
        ]
        is_dirty = (
            bool(flags)
            or module["checkout_head"] != module["recorded_pin"]
            or not module["checkout_present"]
        )
        details.append(
            {
                "path": module["path"],
                "repository": module["repository"],
                "recorded_pin": module["recorded_pin"],
                "checkout_head": module["checkout_head"],
                "checkout_present": module["checkout_present"],
                "status_flags": sorted(flags),
                "is_dirty": is_dirty,
            }
        )
    return details


def remove_submodule_status_from_file_lists(
    status: dict[str, Any], modules: list[dict[str, Any]]
) -> dict[str, Any]:
    submodule_paths = [module["path"] for module in modules]

    def keep(path: str) -> bool:
        return not any(
            path_matches(path, submodule_path) for submodule_path in submodule_paths
        )

    cleaned = dict(status)
    cleaned["staged_file_paths"] = [
        path for path in status["staged_file_paths"] if keep(path)
    ]
    cleaned["unstaged_file_paths"] = [
        path for path in status["unstaged_file_paths"] if keep(path)
    ]
    cleaned["untracked_file_paths"] = [
        path for path in status["untracked_file_paths"] if keep(path)
    ]
    return cleaned


def current_branch_ref(repo: Path, runner: Runner = subprocess.run) -> str | None:
    ref = run_git(["symbolic-ref", "-q", "HEAD"], cwd=repo, runner=runner)
    return ref.stdout if ref.returncode == 0 else None


def locally_unique_commits(
    repo: Path, current_ref: str | None, runner: Runner = subprocess.run
) -> dict[str, Any]:
    refs = run_git(["for-each-ref", "--format=%(refname)"], cwd=repo, runner=runner)
    all_refs = sorted(ref for ref in refs.stdout.splitlines() if ref)
    comparison_refs = [ref for ref in all_refs if ref != current_ref]
    command = ["rev-list", "--reverse", "HEAD"]
    if comparison_refs:
        command.extend(["--not", *comparison_refs])
    commits = run_git(command, cwd=repo, runner=runner)
    return {
        "commits": [line for line in commits.stdout.splitlines() if line]
        if commits.returncode == 0
        else [],
        "excluded_current_branch_ref": current_ref,
        "comparison_ref_count": len(comparison_refs),
        "comparison_refs": comparison_refs,
        "limits": "Local ancestry check only; no network fetch and no claim about refs absent from this machine.",
    }


def inspect_checkout(
    repo: Path, runner: Runner = subprocess.run
) -> dict[str, Any] | None:
    top = run_git(["rev-parse", "--show-toplevel"], cwd=repo, runner=runner)
    if top.returncode != 0:
        return None
    path = Path(top.stdout).resolve(strict=False)
    head = run_git(["rev-parse", "--verify", "HEAD^{commit}"], cwd=path, runner=runner)
    branch_short = run_git(
        ["symbolic-ref", "-q", "--short", "HEAD"], cwd=path, runner=runner
    )
    branch_full = current_branch_ref(path, runner=runner)
    remotes = parse_remotes(run_git(["remote", "-v"], cwd=path, runner=runner).stdout)
    git_dir = run_git(["rev-parse", "--git-dir"], cwd=path, runner=runner)
    common_dir = run_git(["rev-parse", "--git-common-dir"], cwd=path, runner=runner)
    status_result = run_git(
        [
            "status",
            "--porcelain=v1",
            "-b",
            "--untracked-files=all",
            "--ignore-submodules=none",
        ],
        cwd=path,
        runner=runner,
    )
    status = parse_porcelain_status(
        status_result.stdout if status_result.returncode == 0 else ""
    )
    recorded_submodules = inspect_recorded_submodules(path, runner=runner)
    file_status = remove_submodule_status_from_file_lists(status, recorded_submodules)
    item: dict[str, Any] = {
        "path": str(path),
        "repository": recognized_repository(remotes),
        "head": head.stdout if head.returncode == 0 else None,
        "branch": branch_short.stdout if branch_short.returncode == 0 else None,
        "branch_ref": branch_full,
        "detached": branch_short.returncode != 0,
        "git_dir": abs_git_path(git_dir.stdout, path)
        if git_dir.returncode == 0
        else None,
        "git_common_dir": abs_git_path(common_dir.stdout, path)
        if common_dir.returncode == 0
        else None,
        "local_upstream": local_upstream_state(
            path, status["branch_line"], runner=runner
        ),
        "remotes": remotes,
        "status": file_status,
        "recorded_submodules": recorded_submodules,
        "locally_unique_looking_commits": locally_unique_commits(
            path, branch_full, runner=runner
        ),
    }
    item["submodule_dirtiness"] = submodule_dirtiness(
        path, status["raw_entries"], runner=runner
    )
    return item


def looks_like_bare(path: Path) -> bool:
    return (
        (path / "HEAD").is_file()
        and (path / "objects").is_dir()
        and (path / "refs").is_dir()
    )


def inspect_bare(repo: Path, runner: Runner = subprocess.run) -> dict[str, Any] | None:
    bare = run_git(["rev-parse", "--is-bare-repository"], git_dir=repo, runner=runner)
    if bare.returncode != 0 or bare.stdout != "true":
        return None
    head = run_git(
        ["rev-parse", "--verify", "HEAD^{commit}"], git_dir=repo, runner=runner
    )
    remotes = parse_remotes(
        run_git(["remote", "-v"], git_dir=repo, runner=runner).stdout
    )
    return {
        "path": resolved(repo),
        "repository": recognized_repository(remotes),
        "head": head.stdout if head.returncode == 0 else None,
        "remotes": remotes,
        "kind": "bare_repository",
    }


def find_git_surfaces(
    scan_root: Path, problems: list[dict[str, str]], runner: Runner = subprocess.run
) -> tuple[set[Path], list[dict[str, Any]]]:
    checkouts: set[Path] = set()
    bare_repos: list[dict[str, Any]] = []
    root = scan_root.expanduser()
    resolved_root = resolved(root)
    if not root.exists():
        problems.append(
            {
                "path": str(root),
                "classification": "inaccessible_path",
                "detail": "scan root does not exist",
            }
        )
        return checkouts, bare_repos
    if not root.is_dir():
        problems.append(
            {
                "path": resolved(root),
                "classification": "inaccessible_path",
                "detail": "scan root is not a directory",
            }
        )
        return checkouts, bare_repos

    def onerror(error: OSError) -> None:
        problems.append(
            {
                "path": error.filename or str(root),
                "classification": "inaccessible_path",
                "detail": str(error),
            }
        )

    for current, dirs, _files in os.walk(root, topdown=True, onerror=onerror):
        dirs[:] = sorted(
            d for d in dirs if d != ".git" and not (Path(current) / d).is_symlink()
        )
        path = Path(current)
        if (path / ".git").exists():
            top = run_git(["rev-parse", "--show-toplevel"], cwd=path, runner=runner)
            if top.returncode == 0:
                top_path = Path(top.stdout).resolve(strict=False)
                if is_within_or_same(str(top_path), resolved_root):
                    checkouts.add(top_path)
                else:
                    problems.append(
                        {
                            "path": str(top_path),
                            "classification": "checkout_outside_scan_root",
                            "detail": "git top-level resolves outside the explicit scan root",
                        }
                    )
            else:
                problems.append(
                    {
                        "path": resolved(path),
                        "classification": "broken_checkout",
                        "detail": "git metadata found but git rev-parse failed",
                    }
                )
        elif looks_like_bare(path):
            bare = inspect_bare(path, runner=runner)
            if bare is not None:
                bare_repos.append(bare)
            dirs[:] = []
    return checkouts, bare_repos


def is_contained(child: str, parent: str) -> bool:
    child_path = Path(child)
    parent_path = Path(parent)
    return child_path != parent_path and parent_path in child_path.parents


def assign_checkout_kinds(checkouts: list[dict[str, Any]]) -> None:
    paths = sorted(item["path"] for item in checkouts)
    by_path = {item["path"]: item for item in checkouts}
    for item in checkouts:
        containing = [parent for parent in paths if is_contained(item["path"], parent)]
        recorded_submodule_parent_paths = [
            parent_path
            for parent_path in containing
            if checkout_is_recorded_submodule_of_parent(item, by_path[parent_path])
        ]
        if item["detached"]:
            kind = "detached"
        elif recorded_submodule_parent_paths:
            kind = "submodule_checkout"
        elif (
            item.get("git_dir")
            and item.get("git_common_dir")
            and item["git_dir"] != item["git_common_dir"]
        ):
            kind = "linked_worktree"
        else:
            kind = "standalone_clone"
        item["checkout_kind"] = kind
        item["containing_checkout_paths"] = containing
        item["recorded_submodule_parent_paths"] = sorted(
            recorded_submodule_parent_paths
        )


def checkout_is_recorded_submodule_of_parent(
    child: dict[str, Any], parent: dict[str, Any]
) -> bool:
    try:
        rel = Path(child["path"]).relative_to(parent["path"]).as_posix()
    except ValueError:
        return False
    return any(module["path"] == rel for module in parent["recorded_submodules"])


def parse_worktree_list(text: str, common_dir: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in text.splitlines() + [""]:
        if not line:
            if current:
                path = Path(current["path"])
                branch_or_ref = current.get("branch") or current.get("detached")
                if isinstance(branch_or_ref, str) and branch_or_ref.startswith(
                    "refs/heads/"
                ):
                    branch_or_ref = branch_or_ref.removeprefix("refs/heads/")
                records.append(
                    {
                        "path": resolved(path),
                        "classification": "registered_path"
                        if path.exists()
                        else "registered_missing_path",
                        "branch_or_ref": branch_or_ref,
                        "head": current.get("HEAD"),
                        "owner_common_dir": common_dir,
                    }
                )
            current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current["path"] = value
        elif key in {"HEAD", "branch", "detached"}:
            current[key] = value
    return records


def registered_worktrees(
    checkouts: list[dict[str, Any]], runner: Runner = subprocess.run
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen_common_dirs = sorted(
        {item["git_common_dir"] for item in checkouts if item.get("git_common_dir")}
    )
    seen_paths: set[str] = set()
    for common_dir in seen_common_dirs:
        result = run_git(
            ["worktree", "list", "--porcelain"], git_dir=Path(common_dir), runner=runner
        )
        if result.returncode != 0:
            continue
        for record in parse_worktree_list(result.stdout, common_dir):
            key = record["path"]
            if key not in seen_paths:
                out.append(record)
                seen_paths.add(key)
    return sorted(out, key=lambda item: (item["classification"], item["path"]))


def refs_containing_commit(
    git_common_dir: str, commit: str, runner: Runner = subprocess.run
) -> dict[str, Any]:
    exists = run_git(
        ["cat-file", "-e", f"{commit}^{{commit}}"],
        git_dir=Path(git_common_dir),
        runner=runner,
    )
    if exists.returncode != 0:
        return {
            "commit_object_available": False,
            "refs_containing_commit": [],
            "limits": "Checked only this local git common directory; no network used.",
        }
    refs = run_git(
        ["for-each-ref", "--format=%(refname)", "--contains", commit],
        git_dir=Path(git_common_dir),
        runner=runner,
    )
    return {
        "commit_object_available": True,
        "refs_containing_commit": sorted(ref for ref in refs.stdout.splitlines() if ref)
        if refs.returncode == 0
        else [],
        "limits": "Checked only this local git common directory and its local refs; no network used.",
    }


def missing_registration_details(
    records: list[dict[str, Any]], runner: Runner = subprocess.run
) -> list[dict[str, Any]]:
    details = []
    for record in records:
        if record["classification"] != "registered_missing_path":
            continue
        details.append(
            {
                "registered_path": record["path"],
                "branch_or_ref": record.get("branch_or_ref"),
                "pointed_to_commit": record.get("head"),
                "source_git_common_dir": record["owner_common_dir"],
                "local_reachability_information": refs_containing_commit(
                    record["owner_common_dir"],
                    record.get("head") or "",
                    runner=runner,
                )
                if record.get("head")
                else {
                    "commit_object_available": False,
                    "refs_containing_commit": [],
                    "limits": "No recorded commit was available in the registration record.",
                },
                "missing_path_statement": "Missing path only means this registered worktree path was not found locally; this is not permission to prune it.",
            }
        )
    return sorted(details, key=lambda item: item["registered_path"])


def dirty_checkout_details(checkouts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    details = []
    for item in checkouts:
        dirty_submodules = [
            module for module in item["submodule_dirtiness"] if module["is_dirty"]
        ]
        status = item["status"]
        if not (
            status["staged_file_paths"]
            or status["unstaged_file_paths"]
            or status["untracked_file_paths"]
            or dirty_submodules
        ):
            continue
        details.append(
            {
                "checkout_path": item["path"],
                "staged_file_paths": status["staged_file_paths"],
                "unstaged_file_paths": status["unstaged_file_paths"],
                "untracked_file_paths": status["untracked_file_paths"],
                "submodule_dirtiness": dirty_submodules,
            }
        )
    return sorted(details, key=lambda item: item["checkout_path"])


def relation_between(
    left: dict[str, Any], right: dict[str, Any], runner: Runner = subprocess.run
) -> dict[str, str]:
    left_head = left["head"]
    right_head = right["head"]
    relation = "unrelated_or_not_locally_computable"
    checked_from = ""
    for item in sorted([left, right], key=lambda entry: entry["path"]):
        repo = Path(item["path"])
        left_exists = (
            run_git(
                ["cat-file", "-e", f"{left_head}^{{commit}}"], cwd=repo, runner=runner
            ).returncode
            == 0
        )
        right_exists = (
            run_git(
                ["cat-file", "-e", f"{right_head}^{{commit}}"], cwd=repo, runner=runner
            ).returncode
            == 0
        )
        if not (left_exists and right_exists):
            continue
        checked_from = item["path"]
        if (
            run_git(
                ["merge-base", "--is-ancestor", left_head, right_head],
                cwd=repo,
                runner=runner,
            ).returncode
            == 0
        ):
            relation = "left_ancestor_of_right"
        elif (
            run_git(
                ["merge-base", "--is-ancestor", right_head, left_head],
                cwd=repo,
                runner=runner,
            ).returncode
            == 0
        ):
            relation = "right_ancestor_of_left"
        break
    return {
        "left_checkout_path": left["path"],
        "left_full_head_commit": left_head,
        "right_checkout_path": right["path"],
        "right_full_head_commit": right_head,
        "relationship": relation,
        "checked_from_checkout_path": checked_from,
        "limits": "Computed only when one local checkout can see both commits; no network used.",
    }


def branch_divergence_groups(
    checkouts: list[dict[str, Any]], runner: Runner = subprocess.run
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in checkouts:
        if item.get("repository") and item.get("branch") and item.get("head"):
            grouped.setdefault((item["repository"], item["branch"]), []).append(item)
    groups: list[dict[str, Any]] = []
    for (repository, branch), members in sorted(grouped.items()):
        distinct_heads = sorted({item["head"] for item in members})
        if len(distinct_heads) < 2:
            continue
        ordered = sorted(members, key=lambda item: (item["path"], item["head"]))
        groups.append(
            {
                "repository": repository,
                "branch": branch,
                "checkout_paths": [item["path"] for item in ordered],
                "distinct_full_head_commits": distinct_heads,
                "locally_computable_reachability_relationships": [
                    relation_between(left, right, runner=runner)
                    for left, right in combinations(ordered, 2)
                    if left["head"] != right["head"]
                ],
            }
        )
    return groups


def component_pin(
    parent: dict[str, Any], repository: str, fallback_path: str
) -> str | None:
    for module in parent["recorded_submodules"]:
        if (
            module["repository"] == repository
            or module["path"] == fallback_path
            or Path(module["path"]).name == fallback_path
        ):
            return module["recorded_pin"]
    return None


def component_checkout(
    parent: dict[str, Any],
    checkouts: list[dict[str, Any]],
    repository: str,
    fallback_path: str,
) -> dict[str, Any] | None:
    candidates = [
        item
        for item in checkouts
        if item["repository"] == repository
        and checkout_is_recorded_submodule_of_parent(item, parent)
        and (
            Path(item["path"]).name == fallback_path
            or fallback_path in Path(item["path"]).parts
        )
    ]
    return sorted(candidates, key=lambda item: item["path"])[0] if candidates else None


def pin_status(values: list[tuple[str | None, str | None]]) -> str:
    comparable = [(pin, head) for pin, head in values if pin and head]
    if any(pin != head for pin, head in comparable):
        return "mismatching"
    if any(pin and not head for pin, head in values):
        return "missing_checkout"
    if any(head and not pin for pin, head in values):
        return "missing_pin"
    if not comparable:
        return "unavailable"
    return "matching"


def aggregate_dirty(items: list[dict[str, Any] | None]) -> str:
    present = [item for item in items if item is not None]
    if not present:
        return "absent/not-applicable"
    for item in present:
        if (
            item["status"]["staged_file_paths"]
            or item["status"]["unstaged_file_paths"]
            or item["status"]["untracked_file_paths"]
            or any(module["is_dirty"] for module in item["submodule_dirtiness"])
        ):
            return "dirty"
    return "clean"


def bundle_for(
    parent: dict[str, Any] | None,
    analysis: dict[str, Any] | None,
    pipeline: dict[str, Any] | None,
) -> dict[str, Any]:
    warnings: list[str] = []
    parent_pin_analysis = (
        component_pin(parent, ANALYSIS_REPOSITORY, "analysis") if parent else None
    )
    parent_pin_pipeline = (
        component_pin(parent, PIPELINE_REPOSITORY, "pipeline") if parent else None
    )
    actual_analysis = analysis.get("head") if analysis else None
    actual_pipeline = pipeline.get("head") if pipeline else None
    if parent is None:
        warnings.append("incomplete_bundle:no_parent_checkout_seen")
    if analysis is None:
        warnings.append("incomplete_bundle:no_analysis_checkout_seen")
    if pipeline is None:
        warnings.append("incomplete_bundle:no_pipeline_checkout_seen")
    if parent is not None and parent_pin_analysis is None:
        warnings.append("absent_pin:parent_records_no_analysis_pin")
    if parent is not None and parent_pin_pipeline is None:
        warnings.append("absent_pin:parent_records_no_pipeline_pin")
    if (
        parent_pin_analysis
        and actual_analysis
        and parent_pin_analysis != actual_analysis
    ):
        warnings.append("pin_mismatch:analysis")
    if (
        parent_pin_pipeline
        and actual_pipeline
        and parent_pin_pipeline != actual_pipeline
    ):
        warnings.append("pin_mismatch:pipeline")

    parent_path = parent["path"] if parent else None
    analysis_path = analysis["path"] if analysis else None
    pipeline_path = pipeline["path"] if pipeline else None
    workspace_id = parent_path or analysis_path or pipeline_path or "unknown"
    return {
        "workspace_id": workspace_id,
        "parent_checkout": parent_path,
        "analysis_checkout": analysis_path,
        "pipeline_checkout": pipeline_path,
        "parent_recorded_analysis_pin": parent_pin_analysis,
        "parent_recorded_pipeline_pin": parent_pin_pipeline,
        "actual_analysis_head": actual_analysis,
        "actual_pipeline_head": actual_pipeline,
        "pin_match_status": pin_status(
            [
                (parent_pin_analysis, actual_analysis),
                (parent_pin_pipeline, actual_pipeline),
            ]
        ),
        "aggregate_dirty_status": aggregate_dirty([parent, analysis, pipeline]),
        "warnings": sorted(warnings),
    }


def workspace_bundles(checkouts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bundles: list[dict[str, Any]] = []
    bundled_component_paths: set[str] = set()
    parents = sorted(
        (item for item in checkouts if item["repository"] == PARENT_REPOSITORY),
        key=lambda item: item["path"],
    )
    for parent in parents:
        analysis = component_checkout(
            parent, checkouts, ANALYSIS_REPOSITORY, "analysis"
        )
        pipeline = component_checkout(
            parent, checkouts, PIPELINE_REPOSITORY, "pipeline"
        )
        if analysis:
            bundled_component_paths.add(analysis["path"])
        if pipeline:
            bundled_component_paths.add(pipeline["path"])
        bundles.append(bundle_for(parent, analysis, pipeline))

    for item in sorted(checkouts, key=lambda entry: entry["path"]):
        if item["path"] in bundled_component_paths:
            continue
        if item["repository"] == ANALYSIS_REPOSITORY:
            bundles.append(bundle_for(None, item, None))
        elif item["repository"] == PIPELINE_REPOSITORY:
            bundles.append(bundle_for(None, None, item))
    return sorted(bundles, key=lambda item: item["workspace_id"])


def hinted_classification(path: str) -> tuple[str | None, list[dict[str, str]]]:
    lowered_parts = [part.lower() for part in Path(path).parts]
    evidence = []
    for hint in PATH_HINTS:
        if any(hint in part for part in lowered_parts):
            evidence.append(
                {
                    "basis": "pathname inference",
                    "detail": f"path contains '{hint}'; this can suggest review context only and does not establish authority",
                }
            )
    if evidence:
        return "path_hint_review", evidence
    return None, []


def checkout_triage(
    checkouts: list[dict[str, Any]], problems: list[dict[str, str]]
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for item in checkouts:
        staged = len(item["status"]["staged_file_paths"])
        unstaged = len(item["status"]["unstaged_file_paths"])
        untracked = len(item["status"]["untracked_file_paths"])
        dirty_submodules = len(
            [module for module in item["submodule_dirtiness"] if module["is_dirty"]]
        )
        unique_commits = item["locally_unique_looking_commits"]["commits"]
        facts = {
            "repository": item["repository"],
            "checkout_kind": item["checkout_kind"],
            "branch": item["branch"],
            "full_head_commit": item["head"],
            "detached_head": item["detached"],
            "git_dir": item["git_dir"],
            "git_common_dir": item["git_common_dir"],
            "local_upstream": item["local_upstream"],
            "remote_github_slugs": sorted(
                {
                    str(remote["github_slug"])
                    for remote in item["remotes"]
                    if remote.get("github_slug")
                }
            ),
            "staged_file_count": staged,
            "unstaged_file_count": unstaged,
            "untracked_file_count": untracked,
            "dirty_submodule_count": dirty_submodules,
            "locally_unique_looking_full_commits": unique_commits,
            "locally_unique_looking_limits": item["locally_unique_looking_commits"][
                "limits"
            ],
        }
        proposed = "inventory_only"
        confidence = "medium"
        evidence: list[dict[str, str]] = [
            {
                "basis": "local fact",
                "detail": f"checkout kind is {item['checkout_kind']}",
            },
        ]
        priority = "low"
        unresolved = [
            "Which checkout is authoritative is not inferable from this local inventory."
        ]
        if staged or unstaged or untracked or dirty_submodules:
            proposed = "preserve_for_dirty_worktree_review"
            confidence = "high"
            priority = "high"
            evidence.append(
                {
                    "basis": "local fact",
                    "detail": "working tree or submodule dirt is present",
                }
            )
            unresolved.append(
                "Decide whether dirty paths should be landed, moved, or intentionally left local."
            )
        if unique_commits:
            proposed = "preserve_for_local_commit_review"
            confidence = "high"
            priority = "high"
            evidence.append(
                {
                    "basis": "local fact",
                    "detail": "HEAD has commits not reachable from other local refs after excluding the current branch ref",
                }
            )
            unresolved.append(
                "Check whether locally unique-looking commits exist on a remote or another machine."
            )
        if item["detached"]:
            proposed = "preserve_for_detached_head_review"
            confidence = "high"
            priority = "high"
            evidence.append(
                {"basis": "local fact", "detail": "checkout is on detached HEAD"}
            )
        elif item["checkout_kind"] == "linked_worktree" and priority != "high":
            proposed = "registered_linked_worktree"
            priority = "medium"
        elif item["checkout_kind"] == "submodule_checkout" and priority != "high":
            proposed = "workspace_component"
            priority = "medium"
        hint_classification, hint_evidence = hinted_classification(item["path"])
        if hint_classification and proposed == "inventory_only":
            proposed = hint_classification
            confidence = "low"
        evidence.extend(hint_evidence)
        entries.append(
            {
                "checkout_path": item["path"],
                "facts": facts,
                "proposed_classification": proposed,
                "classification_confidence": confidence,
                "classification_evidence": evidence,
                "unresolved_questions": sorted(set(unresolved)),
                "preservation_priority": priority,
            }
        )

    for problem in sorted(
        problems, key=lambda entry: (entry["classification"], entry["path"])
    ):
        entries.append(
            {
                "checkout_path": problem["path"],
                "facts": {
                    "scan_problem_classification": problem["classification"],
                    "scan_problem_detail": problem["detail"],
                    "repository": None,
                    "checkout_kind": None,
                },
                "proposed_classification": "inspect_inaccessible_or_broken_path",
                "classification_confidence": "high",
                "classification_evidence": [
                    {"basis": "local fact", "detail": problem["detail"]}
                ],
                "unresolved_questions": [
                    "Inspect the path manually if it is expected to exist or be readable."
                ],
                "preservation_priority": "high",
            }
        )
    return sorted(entries, key=lambda item: item["checkout_path"])


def build_inventory(
    scan_roots: list[Path], runner: Runner = subprocess.run
) -> dict[str, Any]:
    problems: list[dict[str, str]] = []
    checkout_paths: set[Path] = set()
    for root in scan_roots:
        found, _bare = find_git_surfaces(root, problems, runner=runner)
        checkout_paths.update(found)

    checkouts = [
        item
        for item in (
            inspect_checkout(path, runner=runner) for path in sorted(checkout_paths)
        )
        if item is not None and item["repository"] in KNOWN_GITHUB_REPOS
    ]
    checkouts.sort(key=lambda item: item["path"])
    assign_checkout_kinds(checkouts)
    registrations = registered_worktrees(checkouts, runner=runner)
    scan_problems = sorted(
        problems, key=lambda entry: (entry["classification"], entry["path"])
    )
    return {
        "schema_version": 2,
        "schema_uri": SCHEMA_URI,
        "tool_version": TOOL_VERSION,
        "scan_roots": sorted(
            resolved(path) if path.exists() else str(path) for path in scan_roots
        ),
        "warnings": [
            f"{problem['classification']}:{problem['path']}" for problem in scan_problems
        ],
        "scan_problems": scan_problems,
        "workspace_bundles": workspace_bundles(checkouts),
        "checkout_triage": checkout_triage(checkouts, scan_problems),
        "branch_divergence_groups": branch_divergence_groups(checkouts, runner=runner),
        "dirty_checkout_details": dirty_checkout_details(checkouts),
        "missing_registration_details": missing_registration_details(
            registrations, runner=runner
        ),
        "method": {
            "network": "not_used",
            "git_commands": "read_only",
            "locally_unique_commits": "HEAD compared against all locally available refs except the checkout current branch ref.",
            "ordering": "deterministic sorted paths and refs",
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    validate_no_forbidden_terms(json.dumps(payload, sort_keys=True), "JSON")
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def html_table(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
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


def validate_no_forbidden_terms(text: str, label: str) -> None:
    lowered = text.lower()
    for word in FORBIDDEN_TERMS:
        if word in lowered:
            raise RuntimeError(f"{label} contains forbidden cleanup wording: {word}")


def render_html(payload: dict[str, Any]) -> str:
    out = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        "<title>Checkout Inventory</title>",
        "<style>",
        "body{font:14px system-ui,sans-serif;margin:2rem;line-height:1.4}",
        "table{border-collapse:collapse;width:100%;margin:1rem 0}",
        "th,td{border:1px solid #ccc;padding:.35rem;text-align:left;vertical-align:top}",
        "code,pre{font-family:ui-monospace,Menlo,monospace}",
        "pre{white-space:pre-wrap;background:#f7f7f7;padding:.75rem}",
        "</style>",
        "</head><body>",
        "<h1>Checkout Inventory</h1>",
        "<p>Facts are direct local observations. Path-name hints appear only as labelled inference evidence.</p>",
        "<h2>warnings</h2>",
        "<pre>" + esc(json.dumps(payload["warnings"], indent=2, sort_keys=True)) + "</pre>",
        "<h2>scan_problems</h2>",
        "<pre>"
        + esc(json.dumps(payload["scan_problems"], indent=2, sort_keys=True))
        + "</pre>",
        "<h2>workspace_bundles</h2>",
    ]
    out.extend(
        html_table(
            payload["workspace_bundles"],
            [
                "workspace_id",
                "parent_checkout",
                "analysis_checkout",
                "pipeline_checkout",
                "parent_recorded_analysis_pin",
                "parent_recorded_pipeline_pin",
                "actual_analysis_head",
                "actual_pipeline_head",
                "pin_match_status",
                "aggregate_dirty_status",
                "warnings",
            ],
        )
    )
    out.append("<h2>checkout_triage</h2>")
    for item in payload["checkout_triage"]:
        out.append(f"<h3><code>{esc(item['checkout_path'])}</code></h3>")
        out.append("<pre>" + esc(json.dumps(item, indent=2, sort_keys=True)) + "</pre>")
    out.append("<h2>branch_divergence_groups</h2>")
    out.append(
        "<pre>"
        + esc(json.dumps(payload["branch_divergence_groups"], indent=2, sort_keys=True))
        + "</pre>"
    )
    out.append("<h2>dirty_checkout_details</h2>")
    out.append(
        "<pre>"
        + esc(json.dumps(payload["dirty_checkout_details"], indent=2, sort_keys=True))
        + "</pre>"
    )
    out.append("<h2>missing_registration_details</h2>")
    out.append(
        "<pre>"
        + esc(
            json.dumps(
                payload["missing_registration_details"], indent=2, sort_keys=True
            )
        )
        + "</pre>"
    )
    out.append("</body></html>\n")
    rendered = "\n".join(out)
    validate_no_forbidden_terms(rendered, "HTML")
    return rendered


def write_html(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html(payload), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scan-root",
        action="append",
        required=True,
        type=Path,
        help="Directory to scan. Repeat for multiple explicit roots.",
    )
    parser.add_argument("--json-out", required=True, type=Path)
    parser.add_argument("--html-out", required=True, type=Path)
    parser.add_argument(
        "--allow-repo-output",
        action="store_true",
        help="Allow JSON or HTML outputs inside a discovered Git checkout.",
    )
    return parser


def reject_repo_outputs(
    output_paths: list[Path],
    scan_roots: list[Path],
    runner: Runner = subprocess.run,
) -> None:
    problems: list[dict[str, str]] = []
    checkout_paths: set[Path] = set()
    for root in scan_roots:
        found, _bare = find_git_surfaces(root, problems, runner=runner)
        checkout_paths.update(found)
    resolved_outputs = [resolved(path) for path in output_paths]
    for checkout_path in sorted(checkout_paths):
        checkout = resolved(checkout_path)
        for output in resolved_outputs:
            if is_within_or_same(output, checkout):
                raise SystemExit(
                    f"refusing to write output inside discovered Git checkout: {output}; "
                    "pass --allow-repo-output to override"
                )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.allow_repo_output:
        reject_repo_outputs([args.json_out, args.html_out], args.scan_root)
    payload = build_inventory(args.scan_root)
    write_json(args.json_out, payload)
    write_html(args.html_out, payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
