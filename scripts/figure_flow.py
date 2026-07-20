#!/usr/bin/env python3
"""Deterministic manuscript figure flow from figures/catalog.yaml.

No LLM on the plot path. Agents should consult figures/ax/SKILL.md and call
this CLI instead of opening producer scripts.

Commands:
  list | stale | regen [--id ID ...] [--manuscript] [--clone-ok] [--dry-run]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_DEFAULT = ROOT / "figures" / "catalog.yaml"
RECEIPTS_DIR = ROOT / "figures" / ".receipts"


class FigureFlowError(Exception):
    """Typed failure for catalog / regen problems."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise FigureFlowError(
            "MISSING_DEP",
            "PyYAML required (pip install pyyaml / conda env with yaml)",
        ) from exc
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict) or "figures" not in data:
        raise FigureFlowError("BAD_CATALOG", f"invalid catalog: {path}")
    return data


def expand_path(raw: str, *, root: Path = ROOT) -> Path:
    """Expand ~ and repo-relative paths."""
    text = os.path.expanduser(raw)
    path = Path(text)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def load_catalog(path: Path = CATALOG_DEFAULT) -> list[dict[str, Any]]:
    data = _load_yaml(path)
    figures = data["figures"]
    if not isinstance(figures, list):
        raise FigureFlowError("BAD_CATALOG", "figures must be a list")
    ids = [f.get("id") for f in figures]
    if len(ids) != len(set(ids)):
        raise FigureFlowError("BAD_CATALOG", "duplicate figure ids")
    for fig in figures:
        if not fig.get("id"):
            raise FigureFlowError("BAD_CATALOG", "figure missing id")
        if "producer" not in fig or not fig["producer"].get("argv"):
            raise FigureFlowError("BAD_CATALOG", f"{fig['id']}: missing producer.argv")
        if not fig.get("outputs"):
            raise FigureFlowError("BAD_CATALOG", f"{fig['id']}: missing outputs")
    return figures


def by_id(figures: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {f["id"]: f for f in figures}


def topo_sort(figures: list[dict[str, Any]], selected: set[str]) -> list[str]:
    """Kahn topo-sort over selected ids plus their depends_on closure."""
    index = by_id(figures)
    needed: set[str] = set()

    def visit(fid: str) -> None:
        if fid in needed:
            return
        if fid not in index:
            raise FigureFlowError("UNKNOWN_DEP", f"unknown dependency id: {fid}")
        needed.add(fid)
        for dep in index[fid].get("depends_on") or []:
            visit(dep)

    for fid in selected:
        if fid not in index:
            raise FigureFlowError("UNKNOWN_ID", f"unknown figure id: {fid}")
        visit(fid)

    indeg: dict[str, int] = {fid: 0 for fid in needed}
    edges: dict[str, list[str]] = defaultdict(list)
    for fid in needed:
        for dep in index[fid].get("depends_on") or []:
            if dep not in needed:
                continue
            edges[dep].append(fid)
            indeg[fid] += 1

    queue = deque(sorted(fid for fid, d in indeg.items() if d == 0))
    order: list[str] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for nxt in sorted(edges[node]):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                queue.append(nxt)
    if len(order) != len(needed):
        raise FigureFlowError("CYCLE", "dependency cycle in catalog selection")
    return order


def resolve_outputs(fig: dict[str, Any], *, root: Path = ROOT) -> list[Path]:
    paths: list[Path] = []
    for pattern in fig.get("outputs") or []:
        expanded = os.path.expanduser(str(pattern))
        if any(ch in expanded for ch in "*?[]"):
            if Path(expanded).is_absolute():
                paths.extend(sorted(Path("/").glob(expanded.lstrip("/"))))
            else:
                paths.extend(sorted(root.glob(expanded)))
        else:
            paths.append(expand_path(expanded, root=root))
    return paths


def missing_inputs(
    fig: dict[str, Any],
    *,
    root: Path = ROOT,
    satisfied: set[Path] | None = None,
) -> list[str]:
    """Return missing input paths.

    ``satisfied`` holds paths produced (or planned) by earlier nodes in the
    same regen — so dep outputs like sightline_budget.csv do not false-SKIP
    clusters_icm during dry-run.
    """
    ok = satisfied or set()
    missing: list[str] = []
    for raw in fig.get("inputs") or []:
        path = expand_path(str(raw), root=root)
        if path.exists() or path.resolve() in ok:
            continue
        missing.append(str(raw))
    return missing


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_stale(fig: dict[str, Any], *, root: Path = ROOT) -> bool:
    outputs = resolve_outputs(fig, root=root)
    if not outputs:
        return True
    if any(not p.exists() for p in outputs):
        return True
    newest_out = max(p.stat().st_mtime for p in outputs if p.exists())
    for raw in fig.get("inputs") or []:
        path = expand_path(str(raw), root=root)
        if path.exists() and path.stat().st_mtime > newest_out:
            return True
    return False


def select_ids(
    figures: list[dict[str, Any]],
    *,
    ids: list[str] | None,
    manuscript: bool,
    clone_ok: bool,
) -> set[str]:
    if ids:
        return set(ids)
    selected: set[str] = set()
    for fig in figures:
        if manuscript and not fig.get("manuscript"):
            continue
        if clone_ok and not fig.get("clone_ok"):
            continue
        if manuscript or clone_ok:
            selected.add(fig["id"])
    if not selected and (manuscript or clone_ok):
        return set()
    if not selected and not ids:
        raise FigureFlowError("EMPTY", "pass --id, --manuscript, and/or --clone-ok")
    return selected


def approval_hint(fig: dict[str, Any]) -> str | None:
    slot = fig.get("approval_slot")
    if not slot:
        return None
    candidate_root = fig.get("candidate_root") or "figure_review/staging/" + fig["id"]
    return (
        "APPROVAL_REQUIRED: do not promote silently. Stage a review batch, e.g.\n"
        f"  python3 scripts/figure_review.py new-batch \\\n"
        f"    $(date +%Y-%m-%d)-{fig['id']} \\\n"
        f"    --title \"{fig.get('tex') or fig['id']}\" \\\n"
        f"    --candidate {slot} \\\n"
        f"    --candidate-root {candidate_root} \\\n"
        f"    --pipeline-revision $(git -C pipeline rev-parse HEAD)"
    )


def planned_output_paths(fig: dict[str, Any], *, root: Path = ROOT) -> set[Path]:
    """Concrete output paths for dependency satisfaction (globs omitted)."""
    paths: set[Path] = set()
    for pattern in fig.get("outputs") or []:
        expanded = os.path.expanduser(str(pattern))
        if any(ch in expanded for ch in "*?[]"):
            continue
        paths.add(expand_path(expanded, root=root).resolve())
    return paths


def run_node(
    fig: dict[str, Any],
    *,
    root: Path = ROOT,
    dry_run: bool = False,
    skip_missing: bool = False,
    satisfied: set[Path] | None = None,
) -> dict[str, Any]:
    fid = fig["id"]
    missing = missing_inputs(fig, root=root, satisfied=satisfied)
    if missing:
        msg = f"{fid}: missing inputs: {missing}"
        if skip_missing:
            return {
                "id": fid,
                "status": "SKIP",
                "code": "MISSING_INPUTS",
                "missing_inputs": missing,
                "message": msg,
            }
        raise FigureFlowError("MISSING_INPUTS", msg)

    producer = fig["producer"]
    argv = list(producer["argv"])
    cwd_raw = producer.get("cwd") or "."
    cwd = expand_path(cwd_raw, root=root) if cwd_raw not in (".", "") else root
    if not cwd.is_dir():
        raise FigureFlowError("BAD_CWD", f"{fid}: cwd does not exist: {cwd}")

    receipt: dict[str, Any] = {
        "id": fid,
        "utc": datetime.now(timezone.utc).isoformat(),
        "argv": argv,
        "cwd": str(cwd.relative_to(root)) if cwd.is_relative_to(root) else str(cwd),
        "dry_run": dry_run,
    }

    if dry_run:
        receipt["status"] = "DRY_RUN"
        return receipt

    if fig.get("approval_slot") and fig.get("candidate_root"):
        staging = expand_path(fig["candidate_root"], root=root)
        staging.mkdir(parents=True, exist_ok=True)

    proc = subprocess.run(
        argv,
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )
    receipt["exit_code"] = proc.returncode
    receipt["stdout_tail"] = (proc.stdout or "")[-4000:]
    receipt["stderr_tail"] = (proc.stderr or "")[-4000:]
    if proc.returncode != 0:
        RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
        (RECEIPTS_DIR / f"{fid}.json").write_text(json.dumps(receipt, indent=2) + "\n")
        raise FigureFlowError(
            "PRODUCER_FAILED",
            f"{fid}: exit {proc.returncode}\n{receipt['stderr_tail']}",
        )

    outputs = resolve_outputs(fig, root=root)
    hashes: dict[str, str] = {}
    for path in outputs:
        if path.exists() and path.is_file():
            try:
                rel = str(path.relative_to(root))
            except ValueError:
                rel = str(path)
            hashes[rel] = sha256_file(path)
    receipt["output_sha256"] = hashes
    receipt["status"] = "OK"
    hint = approval_hint(fig)
    if hint:
        receipt["approval_hint"] = hint
        print(hint, file=sys.stderr)

    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    (RECEIPTS_DIR / f"{fid}.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def cmd_list(figures: list[dict[str, Any]]) -> int:
    for fig in figures:
        flags = []
        if fig.get("manuscript"):
            flags.append("manuscript")
        if fig.get("clone_ok"):
            flags.append("clone_ok")
        if fig.get("approval_slot"):
            flags.append(f"slot={fig['approval_slot']}")
        flag_s = ",".join(flags) if flags else "-"
        tex = fig.get("tex") or "-"
        print(f"{fig['id']:28}  {tex:32}  {flag_s}")
    return 0


def cmd_stale(figures: list[dict[str, Any]]) -> int:
    any_stale = False
    for fig in figures:
        if not fig.get("manuscript"):
            continue
        stale = is_stale(fig)
        missing = missing_inputs(fig)
        status = "STALE" if stale else "fresh"
        if missing:
            status = f"MISSING_INPUTS({len(missing)})"
            any_stale = True
        elif stale:
            any_stale = True
        print(f"{fig['id']:28}  {status}")
    return 1 if any_stale else 0


def cmd_regen(
    figures: list[dict[str, Any]],
    *,
    ids: list[str] | None,
    manuscript: bool,
    clone_ok: bool,
    dry_run: bool,
) -> int:
    selected = select_ids(figures, ids=ids, manuscript=manuscript, clone_ok=clone_ok)
    if not selected:
        print("figure_flow: nothing selected", file=sys.stderr)
        return 0
    # Explicit --id fails closed on missing inputs; manuscript sweep skips.
    skip_missing = bool(manuscript or clone_ok) and not ids
    order = topo_sort(figures, selected)
    index = by_id(figures)
    # Only run nodes that are in the original selection OR required deps of them.
    # When --clone-ok, still run deps even if dep is clone_ok (sightline_budget is).
    results: list[dict[str, Any]] = []
    errors = 0
    satisfied: set[Path] = set()
    for fid in order:
        fig = index[fid]
        try:
            receipt = run_node(
                fig,
                dry_run=dry_run,
                skip_missing=skip_missing,
                satisfied=satisfied,
            )
        except FigureFlowError as exc:
            print(f"ERROR {exc}", file=sys.stderr)
            errors += 1
            continue
        results.append(receipt)
        status = receipt.get("status", "?")
        print(f"{status:8}  {fid}")
        if status in {"OK", "DRY_RUN"}:
            satisfied |= planned_output_paths(fig)
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--catalog",
        type=Path,
        default=CATALOG_DEFAULT,
        help="path to catalog.yaml",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list catalog figures")
    sub.add_parser("stale", help="report stale / missing-input manuscript figures")

    regen = sub.add_parser("regen", help="regenerate selected figures")
    regen.add_argument("--id", action="append", dest="ids", help="figure id (repeatable)")
    regen.add_argument(
        "--manuscript",
        action="store_true",
        help="select manuscript:true nodes",
    )
    regen.add_argument(
        "--clone-ok",
        action="store_true",
        help="restrict to clone_ok:true (combine with --manuscript for make figures)",
    )
    regen.add_argument("--dry-run", action="store_true", help="print plan only")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        figures = load_catalog(args.catalog)
    except FigureFlowError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2

    if args.command == "list":
        return cmd_list(figures)
    if args.command == "stale":
        return cmd_stale(figures)
    if args.command == "regen":
        return cmd_regen(
            figures,
            ids=args.ids,
            manuscript=args.manuscript,
            clone_ok=args.clone_ok,
            dry_run=args.dry_run,
        )
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
