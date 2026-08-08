#!/usr/bin/env python3
"""Phase B: materialize catalog entries into the results library.

For each entry with ``mode: materialize``:

1. Resolve library destination (same layout as the inventory builder).
2. If the library slot is a symlink into the repo (Phase A), invert it:
   move real bytes into the library, put a symlink at the old repo path.
3. If already materialized (library real + repo symlink back), no-op.
4. Never materialize ``mode: link_only`` (Overleaf figures, small live catalogs).

Does not rewrite git history. After a successful run, ``git status`` in parent
and ``pipeline/`` will show deletes + symlinks for moved trees — commit via
separate PRs.

Usage (from Faber2026 checkout)::

    python3 scripts/materialize_results_library.py --dry-run
    python3 scripts/materialize_results_library.py
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

# Allow `from results_library` / builder helpers when run as a script.
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from build_results_library_inventory import (  # noqa: E402
    CatalogEntry,
    base_for,
    link_dest,
    load_catalog,
    select_entries,
    _repo_root,
)
from results_library import DEFAULT_LIBRARY  # noqa: E402


def _is_link_to(path: Path, target: Path) -> bool:
    if not path.is_symlink():
        return False
    try:
        return path.resolve() == target.resolve()
    except FileNotFoundError:
        return False


def _write_stub_readme(repo_path: Path, library_path: Path) -> None:
    """If parent of symlink wants a sibling README — write next to link when dir moved."""
    # Symlink itself cannot hold README; place RESULTS_LIBRARY.md beside parent campaign
    # only when we moved a nested results/ folder.
    pass


def materialize_one(
    src: Path,
    dest: Path,
    *,
    dry_run: bool,
) -> str:
    """Move ``src`` → ``dest`` and leave ``src`` as symlink to ``dest``.

    Phase A may have pointed ``dest`` at a *different* checkout (e.g. main).
    Treat any library symlink as disposable: move **this** checkout's ``src``,
    never chase the old link target (avoids mutating a live concurrent tree).
    """
    dest_parent = dest.parent

    # Already inverted in this checkout
    if (
        dest.exists()
        and not dest.is_symlink()
        and src.is_symlink()
        and _is_link_to(src, dest)
    ):
        return "would-already-ok" if dry_run else "already-ok"

    # Phase A (or stale) library → somewhere: invert from this checkout's src
    if dest.is_symlink():
        if not src.exists() or src.is_symlink():
            return "would-skip-no-real-src" if dry_run else "skip-no-real-src"
        if dry_run:
            return "would-invert"
        dest.unlink()
        dest_parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        src.symlink_to(dest.resolve())
        return "inverted"

    # Library empty, repo has real content
    if not dest.exists() and src.exists() and not src.is_symlink():
        if dry_run:
            return "would-move"
        dest_parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        src.symlink_to(dest.resolve())
        return "moved"

    # Repo missing link but library has content
    if dest.exists() and not dest.is_symlink() and not src.exists():
        if dry_run:
            return "would-relink-src"
        src.parent.mkdir(parents=True, exist_ok=True)
        src.symlink_to(dest.resolve())
        return "relinked-src"

    if dest.exists() and src.exists() and not src.is_symlink() and not dest.is_symlink():
        return "would-conflict-both-real" if dry_run else "conflict-both-real"

    return "would-skip" if dry_run else "skipped"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    ap.add_argument("--root", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--only",
        action="append",
        default=[],
        help="Limit to entry id(s); repeatable",
    )
    args = ap.parse_args()
    root = _repo_root(args.root)
    library = args.library.expanduser().resolve()
    catalog = select_entries(load_catalog(), list(args.only))

    actions: list[tuple[str, str, str]] = []
    for entry in catalog.entries:
        if entry.mode != "materialize":
            actions.append((entry.id, "(all)", f"skip-mode={entry.mode}"))
            continue
        if entry.repo == "external":
            actions.append((entry.id, "(ext)", "skip-external"))
            continue
        base = base_for(entry, root)
        assert base is not None
        for rel in entry.sources:
            src = base / rel
            dest = library / link_dest(entry, rel, external_name=None)
            status = materialize_one(src, dest, dry_run=args.dry_run)
            actions.append((entry.id, rel, status))

    width = max(len(a[0]) for a in actions) if actions else 10
    for eid, rel, status in actions:
        print(f"{eid:<{width}}  {rel}  →  {status}")

    conflicts = [a for a in actions if "conflict" in a[2]]
    if conflicts:
        raise SystemExit(f"{len(conflicts)} conflict(s); resolve manually")
    print(
        f"{'dry-run' if args.dry_run else 'done'}: "
        f"{sum(1 for a in actions if a[2] in ('inverted', 'moved', 'would-invert', 'would-move'))} "
        f"materialize ops"
    )


if __name__ == "__main__":
    main()
