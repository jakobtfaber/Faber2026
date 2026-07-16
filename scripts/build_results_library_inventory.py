#!/usr/bin/env python3
"""Build the Faber2026 results-library inventory from the YAML catalog.

Catalog (edit campaigns here)::

    scripts/results_library_catalog.yaml

Pipeline: load → validate trust ∈ legend → probe → optional symlink → emit
``INDEX.md`` + ``_inventory/inventory.yaml`` under the results library root.

Always run from the git checkout. Do not copy this script into the library.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from results_library import DEFAULT_LIBRARY, results_library_root

CATALOG_SCHEMA = "faber2026-results-library-catalog/v1"
INVENTORY_SCHEMA = "faber2026-results-library/v1"
CATALOG_REL = Path("scripts/results_library_catalog.yaml")


def repo_root_from_script(*, cli_root: Path | None) -> Path:
    if cli_root is not None:
        return cli_root.expanduser().resolve()
    env = os.environ.get("FABER2026_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def load_catalog(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"catalog missing: {path}")
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"catalog must be a mapping: {path}")
    schema = data.get("schema")
    if schema != CATALOG_SCHEMA:
        raise ValueError(
            f"unsupported catalog schema {schema!r}; expected {CATALOG_SCHEMA!r}"
        )
    if "trust_legend" not in data or not isinstance(data["trust_legend"], dict):
        raise ValueError("catalog requires trust_legend mapping")
    if "entries" not in data or not isinstance(data["entries"], list):
        raise ValueError("catalog requires entries list")
    return data


def validate_trust(entries: list[dict[str, Any]], legend: dict[str, Any]) -> None:
    known = set(legend)
    bad: list[str] = []
    for entry in entries:
        trust = entry.get("trust")
        eid = entry.get("id", "<missing-id>")
        if trust not in known:
            bad.append(f"{eid}: unknown trust {trust!r}")
    if bad:
        raise SystemExit(
            "trust tags must appear in trust_legend:\n  " + "\n  ".join(bad)
        )


def _count_files(path: Path) -> int:
    if path.is_file():
        return 1
    if not path.is_dir():
        return 0
    n = 0
    for root, _dirs, files in os.walk(path):
        n += len(files)
        # keep walk cheap on huge trees
        if n > 100_000:
            return n
    return n


def _du_bytes(path: Path) -> int | None:
    try:
        if path.is_file():
            return path.stat().st_size
        total = 0
        for root, _dirs, files in os.walk(path):
            for name in files:
                fp = Path(root) / name
                try:
                    total += fp.stat().st_size
                except OSError:
                    continue
            if total > 50 * 1024**3:
                return total
        return total
    except OSError:
        return None


def resolve_repo_source(root: Path, spec: dict[str, Any]) -> Path:
    rel = spec.get("path")
    if not rel:
        raise ValueError(f"source missing path: {spec!r}")
    return (root / rel).resolve()


def resolve_external(spec: dict[str, Any]) -> Path | None:
    """Resolve an external_paths item: ``{env, default}`` or ``{path}``."""
    if "env" in spec:
        env_name = spec["env"]
        raw = os.environ.get(env_name) or spec.get("default")
        if not raw:
            return None
        return Path(str(raw)).expanduser()
    if "path" in spec:
        return Path(str(spec["path"])).expanduser()
    raise ValueError(f"external_paths item needs env/default or path: {spec!r}")


def probe_path(path: Path) -> dict[str, Any]:
    exists = path.exists()
    kind = "absent"
    if path.is_file():
        kind = "file"
    elif path.is_dir():
        kind = "dir"
    elif path.is_symlink():
        kind = "symlink-broken" if not exists else "symlink"
    info: dict[str, Any] = {
        "path": str(path),
        "status": "present" if exists else "absent",
        "kind": kind,
    }
    if exists:
        info["n_files"] = _count_files(path)
        du = _du_bytes(path)
        if du is not None:
            info["bytes"] = du
    return info


def link_dest(library: Path, slot: str, source: Path, *, multi: bool, name: str | None) -> Path:
    """Destination under the library for a source.

    - single repo source → ``library / slot``
    - multi repo sources → ``library / slot / basename``
    - external (multi or named) → ``library / slot / name``
    """
    slot_path = library.joinpath(*slot.split("/"))
    if name is not None:
        return slot_path / name
    if multi:
        return slot_path / source.name
    return slot_path


def ensure_link(dest: Path, source: Path, *, force: bool, dry_run: bool) -> str:
    dest_parent = dest.parent
    if dry_run:
        return f"dry-run link {dest} -> {source}"
    dest_parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() or dest.exists():
        if not force:
            return f"skip existing {dest}"
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        elif dest.is_dir() and not dest.is_symlink():
            # refuse to rm trees; only replace empty dirs
            try:
                dest.rmdir()
            except OSError:
                return f"refuse non-empty dir {dest}"
    dest.symlink_to(source, target_is_directory=source.is_dir())
    return f"linked {dest} -> {source}"


def render_index(
    *,
    library: Path,
    catalog_path: Path,
    trust_legend: dict[str, Any],
    rows: list[dict[str, Any]],
    generated: str,
) -> str:
    lines = [
        "# Faber2026 results library",
        "",
        f"Generated: `{generated}`",
        "",
        "Navigable symlink inventory of fit/campaign products. "
        "**Fitting code stays in git** (Faber2026 + `pipeline/`). "
        "Trust tags are science-policy labels; this inventory does not certify measurements.",
        "",
        f"- Library root: `{library}`",
        f"- Catalog (edit campaigns): `{catalog_path}`",
        "- Refresh (always from git checkout):",
        "",
        "```bash",
        "python3 scripts/build_results_library_inventory.py --dry-run",
        "python3 scripts/build_results_library_inventory.py --link --force",
        "```",
        "",
        "## Trust legend",
        "",
    ]
    for tag, desc in trust_legend.items():
        lines.append(f"- `{tag}` — {desc}")
    lines += ["", "## Campaigns", ""]
    lines.append("| id | slot | trust | status | n_files | notes |")
    lines.append("|----|------|-------|--------|---------|-------|")
    for row in rows:
        notes = row.get("title") or ""
        status = row.get("aggregate_status", "")
        n_files = row.get("n_files_total", "")
        lines.append(
            f"| `{row['id']}` | `{row['slot']}` | `{row['trust']}` | "
            f"{status} | {n_files} | {notes} |"
        )
    lines += [
        "",
        "## How to use",
        "",
        "1. Edit `scripts/results_library_catalog.yaml` to add/change campaigns.",
        "2. Run the builder from the Faber2026 checkout (never a library-side copy).",
        "3. Resolve paths in producers via `scripts/results_library.py` "
        "(`results_slot(...)`).",
        "",
    ]
    return "\n".join(lines)


def process_entry(
    entry: dict[str, Any],
    *,
    root: Path,
    library: Path,
    do_link: bool,
    force: bool,
    dry_run: bool,
) -> dict[str, Any]:
    eid = entry.get("id")
    slot = entry.get("slot")
    trust = entry.get("trust")
    if not eid or not slot or not trust:
        raise ValueError(f"entry requires id, slot, trust: {entry!r}")

    sources = entry.get("sources") or []
    external = entry.get("external_paths") or []
    if not sources and not external:
        raise ValueError(f"entry {eid}: need sources and/or external_paths")

    probed: list[dict[str, Any]] = []
    link_actions: list[str] = []
    n_files_total = 0
    present = 0
    absent = 0

    multi_repo = len(sources) > 1
    for spec in sources:
        src = resolve_repo_source(root, spec)
        info = probe_path(src)
        info["origin"] = "repo"
        probed.append(info)
        if info["status"] == "present":
            present += 1
            n_files_total += int(info.get("n_files") or 0)
            if do_link:
                dest = link_dest(
                    library, slot, src, multi=multi_repo, name=None
                )
                link_actions.append(
                    ensure_link(dest, src, force=force, dry_run=dry_run)
                )
        else:
            absent += 1

    multi_ext = len(external) > 1 or (bool(external) and bool(sources))
    for i, spec in enumerate(external):
        ext = resolve_external(spec)
        if ext is None:
            info = {
                "path": None,
                "status": "absent",
                "kind": "unresolved",
                "origin": "external",
                "spec": spec,
            }
            probed.append(info)
            absent += 1
            continue
        info = probe_path(ext)
        info["origin"] = "external"
        info["spec"] = spec
        probed.append(info)
        if info["status"] == "present":
            present += 1
            n_files_total += int(info.get("n_files") or 0)
            if do_link:
                name = ext.name if multi_ext or len(external) > 1 else ext.name
                # external always lands under slot / name
                dest = link_dest(
                    library, slot, ext, multi=True, name=name
                )
                link_actions.append(
                    ensure_link(dest, ext, force=force, dry_run=dry_run)
                )
        else:
            absent += 1

    if present and not absent:
        aggregate = "present"
    elif present and absent:
        aggregate = "partial"
    else:
        aggregate = "absent"

    return {
        "id": eid,
        "slot": slot,
        "trust": trust,
        "title": entry.get("title"),
        "aggregate_status": aggregate,
        "n_files_total": n_files_total,
        "sources": probed,
        "link_actions": link_actions,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Faber2026 repo root (default: parent of scripts/ or FABER2026_ROOT)",
    )
    parser.add_argument(
        "--library",
        type=Path,
        default=None,
        help=f"results library root (default: {DEFAULT_LIBRARY} or FABER2026_RESULTS_LIBRARY)",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=None,
        help="catalog YAML path (default: <root>/scripts/results_library_catalog.yaml)",
    )
    parser.add_argument(
        "--link",
        action="store_true",
        help="create/update symlinks under the library",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace existing symlinks when --link",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="probe + validate only; do not write library files or create links",
    )
    args = parser.parse_args(argv)

    root = repo_root_from_script(cli_root=args.root)
    catalog_path = (
        args.catalog.expanduser().resolve()
        if args.catalog
        else (root / CATALOG_REL).resolve()
    )
    library = (
        args.library.expanduser().resolve()
        if args.library
        else results_library_root()
    )

    catalog = load_catalog(catalog_path)
    legend = catalog["trust_legend"]
    entries = catalog["entries"]
    validate_trust(entries, legend)

    rows: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError(f"entry must be mapping: {entry!r}")
        rows.append(
            process_entry(
                entry,
                root=root,
                library=library,
                do_link=bool(args.link) and not args.dry_run,
                force=bool(args.force),
                dry_run=bool(args.dry_run) and bool(args.link),
            )
        )

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    inventory = {
        "schema": INVENTORY_SCHEMA,
        "generated": generated,
        "repo_root": str(root),
        "library": str(library),
        "catalog": str(catalog_path),
        "trust_legend": legend,
        "entries": rows,
    }

    print(f"catalog: {catalog_path}")
    print(f"repo:    {root}")
    print(f"library: {library}")
    print(f"entries: {len(rows)}")
    for row in rows:
        print(
            f"  [{row['aggregate_status']:7}] {row['id']}: "
            f"{row['n_files_total']} files → {row['slot']}"
        )
        for action in row.get("link_actions") or []:
            print(f"           {action}")

    if args.dry_run:
        print("dry-run: no writes")
        return 0

    library.mkdir(parents=True, exist_ok=True)
    inv_dir = library / "_inventory"
    inv_dir.mkdir(parents=True, exist_ok=True)
    inv_path = inv_dir / "inventory.yaml"
    with inv_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(inventory, fh, sort_keys=False, allow_unicode=True)

    index_text = render_index(
        library=library,
        catalog_path=catalog_path,
        trust_legend=legend,
        rows=rows,
        generated=generated,
    )
    (library / "INDEX.md").write_text(index_text, encoding="utf-8")
    print(f"wrote {inv_path}")
    print(f"wrote {library / 'INDEX.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
