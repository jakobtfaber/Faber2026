#!/usr/bin/env python3
"""Build a navigable results-library inventory for Faber2026 + FLITS pipeline.

Loads ``results_library_catalog.yaml``, probes sources, writes
``inventory.yaml`` + ``INDEX.md``, and optionally creates symlinks under the
library taxonomy. Does not delete source trees.

Always invoke from the git checkout (this script), not a library copy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import yaml

from results_library import DEFAULT_LIBRARY

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
CATALOG_PATH = SCRIPT_DIR / "results_library_catalog.yaml"

RepoKind = Literal["pipeline", "parent", "external"]
LinkMode = Literal["link_only", "materialize"]


@dataclass(frozen=True)
class ExternalPathSpec:
    """Resolved later; either env+default or a literal path string."""

    env: str | None = None
    default: str | None = None
    path: str | None = None

    def resolve(self) -> Path:
        if self.env is not None:
            raw = os.environ.get(self.env) or self.default or ""
            if not raw:
                raise ValueError(f"external path env {self.env!r} empty and no default")
            return Path(raw).expanduser()
        if self.path is not None:
            return Path(self.path).expanduser()
        raise ValueError("external path needs env or path")


@dataclass(frozen=True)
class CatalogEntry:
    id: str
    domain: str
    slot: str
    trust: str
    repo: RepoKind
    sources: tuple[str, ...]
    notes: str
    mode: LinkMode = "link_only"
    external_paths: tuple[ExternalPathSpec, ...] = ()
    destinations: dict[str, str] | None = None
    result_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Catalog:
    trust_legend: dict[str, str]
    entries: tuple[CatalogEntry, ...]


def _repo_root(cli_root: Path | None) -> Path:
    if cli_root is not None:
        return cli_root.expanduser().resolve()
    env = os.environ.get("FABER2026_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return REPO_ROOT


def load_catalog(path: Path = CATALOG_PATH) -> Catalog:
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict):
        raise SystemExit(f"catalog root must be a mapping: {path}")

    legend = raw.get("trust_legend") or {}
    if not isinstance(legend, dict) or not legend:
        raise SystemExit("catalog.trust_legend must be a non-empty mapping")
    allowed = set(legend)

    entries_raw = raw.get("entries")
    if not isinstance(entries_raw, list) or not entries_raw:
        raise SystemExit("catalog.entries must be a non-empty list")

    entries: list[CatalogEntry] = []
    seen_ids: set[str] = set()
    for i, item in enumerate(entries_raw):
        if not isinstance(item, dict):
            raise SystemExit(f"entries[{i}] must be a mapping")
        for key in ("id", "domain", "slot", "trust", "repo", "notes"):
            if key not in item:
                raise SystemExit(f"entries[{i}] missing {key!r}")
        eid = str(item["id"])
        if eid in seen_ids:
            raise SystemExit(f"duplicate entry id: {eid}")
        seen_ids.add(eid)
        trust = str(item["trust"])
        if trust not in allowed:
            raise SystemExit(
                f"entry {eid!r}: trust {trust!r} not in trust_legend "
                f"({sorted(allowed)})"
            )
        repo = str(item["repo"])
        if repo not in ("pipeline", "parent", "external"):
            raise SystemExit(f"entry {eid!r}: repo must be pipeline|parent|external")
        sources = item.get("sources") or []
        if not isinstance(sources, list):
            raise SystemExit(f"entry {eid!r}: sources must be a list")
        result_ids = item.get("result_ids")
        if not isinstance(result_ids, list):
            raise SystemExit(f"entry {eid!r}: result_ids must be a list")
        destinations = item.get("destinations") or {}
        if not isinstance(destinations, dict):
            raise SystemExit(f"entry {eid!r}: destinations must be a mapping")
        unknown_destinations = sorted(set(destinations) - {str(s) for s in sources})
        if unknown_destinations:
            raise SystemExit(
                f"entry {eid!r}: destinations name unknown sources: "
                f"{unknown_destinations}"
            )
        normalized_destinations: dict[str, str] = {}
        for source, destination in destinations.items():
            rel_dest = Path(str(destination))
            if rel_dest.is_absolute() or ".." in rel_dest.parts:
                raise SystemExit(
                    f"entry {eid!r}: destination must stay inside slot: "
                    f"{destination!r}"
                )
            normalized_destinations[str(source)] = str(rel_dest)
        ext_specs: list[ExternalPathSpec] = []
        for j, ext in enumerate(item.get("external_paths") or []):
            if not isinstance(ext, dict):
                raise SystemExit(f"entry {eid!r} external_paths[{j}] must be a mapping")
            if "env" in ext:
                ext_specs.append(
                    ExternalPathSpec(env=str(ext["env"]), default=ext.get("default"))
                )
            elif "path" in ext:
                ext_specs.append(ExternalPathSpec(path=str(ext["path"])))
            else:
                raise SystemExit(
                    f"entry {eid!r} external_paths[{j}] needs env or path"
                )
        mode_raw = str(item.get("mode", "link_only"))
        if mode_raw not in ("link_only", "materialize"):
            raise SystemExit(
                f"entry {eid!r}: mode must be link_only|materialize, got {mode_raw!r}"
            )
        entries.append(
            CatalogEntry(
                id=eid,
                domain=str(item["domain"]),
                slot=str(item["slot"]),
                trust=trust,
                repo=repo,  # type: ignore[arg-type]
                sources=tuple(str(s) for s in sources),
                notes=str(item["notes"]),
                mode=mode_raw,  # type: ignore[arg-type]
                external_paths=tuple(ext_specs),
                destinations=normalized_destinations,
                result_ids=tuple(str(result_id) for result_id in result_ids),
            )
        )
    return Catalog(trust_legend={str(k): str(v) for k, v in legend.items()}, entries=tuple(entries))


def _du_human(path: Path) -> str:
    if not path.exists():
        return "missing"
    try:
        out = subprocess.check_output(
            ["du", "-sh", str(path)], text=True, stderr=subprocess.DEVNULL
        )
        return out.split()[0]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "?"


def _count_files(path: Path, limit: int = 50_000) -> tuple[int, bool]:
    """Return (count, truncated)."""
    if not path.exists():
        return 0, False
    if path.is_file():
        return 1, False
    n = 0
    for p in path.rglob("*"):
        if p.is_file():
            n += 1
            if n >= limit:
                return limit, True
    return n, False


def _git_tracked_hint(repo: Path, rel: str) -> str:
    target = repo / rel
    if not target.exists():
        return "missing"
    try:
        ignored = subprocess.run(
            ["git", "-C", str(repo), "check-ignore", "-q", rel],
            check=False,
        ).returncode
        if ignored == 0:
            return "gitignored"
        tracked = subprocess.run(
            ["git", "-C", str(repo), "ls-files", "--error-unmatch", rel],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        if tracked == 0:
            return "tracked"
        listed = subprocess.check_output(
            ["git", "-C", str(repo), "ls-files", rel],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if listed:
            return "tracked-partial"
        return "untracked"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def link_dest(entry: CatalogEntry, rel: str | None, *, external_name: str | None) -> Path:
    """Library-relative destination for a single source or external path."""
    slot = Path(entry.slot)
    n_src = len(entry.sources)
    n_ext = len(entry.external_paths)
    if rel is not None:
        explicit = (entry.destinations or {}).get(rel)
        if explicit is not None:
            return slot / Path(explicit)
        if n_src == 1 and n_ext == 0:
            return slot
        return slot / Path(rel).name
    assert external_name is not None
    if n_ext == 1 and n_src == 0:
        return slot
    return slot / external_name


def select_entries(catalog: Catalog, only: list[str] | tuple[str, ...]) -> Catalog:
    """Return an exact ordered catalog subset; reject ambiguous selection."""
    requested = list(only)
    if not requested:
        return catalog
    duplicates = sorted({entry_id for entry_id in requested if requested.count(entry_id) > 1})
    if duplicates:
        raise SystemExit(f"duplicate --only catalog entry: {duplicates}")
    by_id = {entry.id: entry for entry in catalog.entries}
    unknown = [entry_id for entry_id in requested if entry_id not in by_id]
    if unknown:
        raise SystemExit(f"unknown catalog entry: {unknown}")
    return Catalog(
        trust_legend=catalog.trust_legend,
        entries=tuple(by_id[entry_id] for entry_id in requested),
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_manifest(path: Path) -> dict[str, Any]:
    """Deterministic regular-file manifest for a file or directory."""
    target = path.resolve() if path.is_symlink() else path
    if target.is_file():
        return {"files": 1, "bytes": target.stat().st_size, "sha256": _sha256_file(target)}
    files = sorted(
        (
            candidate
            for candidate in target.rglob("*")
            if candidate.is_file() and not candidate.is_symlink()
        ),
        key=lambda candidate: candidate.relative_to(target).as_posix(),
    )
    digest = hashlib.sha256()
    total_bytes = 0
    for candidate in files:
        rel = candidate.relative_to(target).as_posix()
        size = candidate.stat().st_size
        total_bytes += size
        digest.update(rel.encode())
        digest.update(b"\0")
        digest.update(str(size).encode())
        digest.update(b"\0")
        digest.update(_sha256_file(candidate).encode())
        digest.update(b"\n")
    return {"files": len(files), "bytes": total_bytes, "sha256": digest.hexdigest()}


def snapshot_path(path: Path, *, manifest: bool) -> dict[str, Any]:
    """Capture lstat-aware path state without mistaking broken links for absence."""
    if path.is_symlink():
        info = path.lstat()
        resolved = path.resolve(strict=False)
        result: dict[str, Any] = {
            "path": str(path),
            "type": "symlink",
            "inode": info.st_ino,
            "mode": oct(stat.S_IMODE(info.st_mode)),
            "uid": info.st_uid,
            "size": info.st_size,
            "raw_link_target": os.readlink(path),
            "resolved_target": str(resolved),
            "resolves": path.exists(),
        }
        if manifest and path.exists():
            result["manifest"] = tree_manifest(path)
        return result
    if not path.exists():
        return {"path": str(path), "type": "absent"}
    info = path.stat()
    kind = "directory" if path.is_dir() else "file"
    result = {
        "path": str(path),
        "type": kind,
        "inode": info.st_ino,
        "mode": oct(stat.S_IMODE(info.st_mode)),
        "uid": info.st_uid,
        "size": info.st_size,
    }
    if manifest:
        result["manifest"] = tree_manifest(path)
    return result


def build_receipt(
    inventory: dict[str, Any],
    *,
    selected_ids: list[str],
    parent_commit: str,
    pipeline_commit: str,
) -> dict[str, Any]:
    """Build a machine-readable post-action receipt from inventory metadata."""
    entries: list[dict[str, Any]] = []
    for entry in inventory["entries"]:
        sources: list[dict[str, Any]] = []
        for source in entry["sources"]:
            source_path = source.get("abs")
            destination_path = source.get("dest")
            sources.append(
                {
                    "rel": source.get("rel"),
                    "link_status": source.get("link_status"),
                    "source": snapshot_path(Path(source_path), manifest=True)
                    if source_path
                    else None,
                    "destination": snapshot_path(Path(destination_path), manifest=False)
                    if destination_path
                    else None,
                }
            )
        entries.append({"id": entry["id"], "sources": sources})
    return {
        "schema": "faber2026-results-library-repair-receipt/v1",
        "observed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "selected_ids": selected_ids,
        "library_root": inventory["library_root"],
        "faber2026_root": inventory["faber2026_root"],
        "git": {
            "parent_commit": parent_commit,
            "pipeline_commit": pipeline_commit,
        },
        "entries": entries,
    }


def _git_head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def _resolves_equal(a: Path, b: Path) -> bool:
    try:
        return a.resolve() == b.resolve()
    except FileNotFoundError:
        return False


def ensure_link(
    src: Path,
    dest: Path,
    *,
    force: bool,
    dry_run: bool,
    mode: LinkMode = "link_only",
) -> str:
    """Phase A: library slot → repo source. Never clobber a real library dir.

    After Phase B materialize, ``dest`` is real bytes and ``src`` is a symlink
    back into the library — leave that alone.
    """
    # Already materialized: repo path points at library real dir
    if dest.exists() and not dest.is_symlink() and src.is_symlink() and _resolves_equal(
        src, dest
    ):
        return "materialized-ok"

    # Real library content (do not replace with symlink back to repo)
    if dest.exists() and not dest.is_symlink() and dest.is_dir():
        return "skip-real-dir"

    if dry_run:
        if not src.exists() and not src.is_symlink():
            return "would-missing-src"
        if dest.is_symlink() or dest.exists():
            return "would-replace" if force else "would-exists"
        if mode == "materialize":
            return "would-link-pending-materialize"
        return "would-link"

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() or dest.exists():
        if not force:
            return "exists"
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        else:
            return "skip-dir"
    if not src.exists() and not src.is_symlink():
        return "missing-src"
    dest.symlink_to(src.resolve())
    return "linked"


def probe_path(path: Path, *, repo: Path | None, rel: str | None) -> dict[str, Any]:
    n, truncated = _count_files(path) if path.exists() else (0, False)
    git = "external"
    if repo is not None and rel is not None:
        git = _git_tracked_hint(repo, rel)
    return {
        "rel": rel,
        "abs": str(path),
        "size": _du_human(path) if path.exists() else ("missing" if rel else "absent"),
        "n_files": n,
        "n_files_truncated": truncated,
        "git": git,
    }


def base_for(entry: CatalogEntry, root: Path) -> Path | None:
    return {"pipeline": root / "pipeline", "parent": root, "external": None}[entry.repo]


def build(
    library: Path,
    root: Path,
    catalog: Catalog,
    *,
    link: bool,
    force: bool,
    dry_run: bool,
) -> dict[str, Any]:
    pipeline = root / "pipeline"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    records: list[dict[str, Any]] = []

    for entry in catalog.entries:
        base = base_for(entry, root)
        sources_meta: list[dict[str, Any]] = []

        for rel in entry.sources:
            if base is None:
                raise SystemExit(f"{entry.id}: sources require non-external repo")
            src = base / rel
            meta = probe_path(src, repo=base, rel=rel)
            dest = library / link_dest(entry, rel, external_name=None)
            meta["dest"] = str(dest)
            if link or dry_run:
                meta["link_status"] = ensure_link(
                    src, dest, force=force, dry_run=dry_run, mode=entry.mode
                )
            meta["mode"] = entry.mode
            sources_meta.append(meta)

        for spec in entry.external_paths:
            try:
                p = spec.resolve()
            except ValueError:
                sources_meta.append(
                    {
                        "rel": None,
                        "abs": None,
                        "size": "absent",
                        "n_files": 0,
                        "n_files_truncated": False,
                        "git": "external",
                        "link_status": "absent",
                    }
                )
                continue
            meta = probe_path(p, repo=None, rel=None)
            dest = library / link_dest(entry, None, external_name=p.name)
            meta["dest"] = str(dest)
            if not p.exists():
                meta["size"] = "absent"
                meta["link_status"] = "absent"
            elif link or dry_run:
                meta["link_status"] = ensure_link(
                    p, dest, force=force, dry_run=dry_run
                )
            sources_meta.append(meta)

        records.append(
            {
                "id": entry.id,
                "domain": entry.domain,
                "slot": entry.slot,
                "trust": entry.trust,
                "repo": entry.repo,
                "mode": entry.mode,
                "result_ids": list(entry.result_ids),
                "notes": entry.notes,
                "sources": sources_meta,
            }
        )

    return {
        "schema": "faber2026-results-library/v1",
        "catalog_schema": "faber2026-results-library-catalog/v1",
        "generated_at": now,
        "library_root": str(library),
        "faber2026_root": str(root),
        "pipeline_root": str(pipeline),
        "catalog_path": str(CATALOG_PATH),
        "env": {
            "FABER2026_RESULTS_LIBRARY": str(library),
            "FLITS_RUNS": os.environ.get("FLITS_RUNS", ""),
        },
        "entries": records,
    }


def write_index(library: Path, inventory: dict[str, Any], catalog: Catalog) -> None:
    lines = [
        "# Faber2026 results library",
        "",
        f"Generated: `{inventory['generated_at']}`",
        "",
        f"**Library root:** `{inventory['library_root']}`  ",
        f"**Code root:** `{inventory['faber2026_root']}`  ",
        f"**Pipeline:** `{inventory['pipeline_root']}`",
        "",
        "This tree is the **navigable inventory** of scientific results.",
        "Fitting / analysis *code* stays in `Faber2026` and `pipeline/` (FLITS).",
        "`mode: materialize` slots hold real bytes here; repo paths are symlinks back.",
        "`mode: link_only` slots stay as library → repo (Overleaf / small live catalogs).",
        "Trust tags follow the 2026-07-06 trust reset + later provisional gates.",
        "",
        "## Trust legend",
        "",
        "| Tag | Meaning |",
        "|-----|---------|",
    ]
    for tag in sorted(catalog.trust_legend):
        meaning = catalog.trust_legend[tag].replace("|", "/")
        lines.append(f"| `{tag}` | {meaning} |")
    lines.extend(["", "## Domains", ""])

    by_domain: dict[str, list[dict[str, Any]]] = {}
    for e in inventory["entries"]:
        by_domain.setdefault(e["domain"], []).append(e)

    for domain in sorted(by_domain):
        lines.append(f"### `{domain}/`")
        lines.append("")
        lines.append("| Slot | Trust | Size | Git | Notes |")
        lines.append("|------|-------|------|-----|-------|")
        for e in by_domain[domain]:
            sizes = ", ".join(
                f"`{s.get('size')}`" for s in e["sources"] if s.get("size")
            ) or "—"
            gits = ", ".join(sorted({s.get("git", "?") for s in e["sources"]}))
            notes = e["notes"].replace("|", "/")
            lines.append(
                f"| [`{e['slot']}`]({e['slot']}) | `{e['trust']}` | {sizes} | {gits} | {notes} |"
            )
        lines.append("")

    lines.extend(
        [
            "## How to use",
            "",
            "```bash",
            f"export FABER2026_RESULTS_LIBRARY={inventory['library_root']}",
            "ls \"$FABER2026_RESULTS_LIBRARY\"/scattering",
            f"python3 {SCRIPT_DIR / 'build_results_library_inventory.py'} --link",
            "```",
            "",
            "Machine-readable: [`_inventory/inventory.yaml`](_inventory/inventory.yaml).",
            f"Catalog (git): `{inventory.get('catalog_path', CATALOG_PATH)}`.",
            "",
            "## Not materialized (link_only)",
            "",
            "- Overleaf `figures/`, `figure_review/`, `repro_manifest.csv`.",
            "- Small live catalogs (`tau_consistency_catalog.csv`, TeX `exports/`).",
            "- Mixed analysis trees without a results-only carve-out.",
            "- Analysis **driver scripts** stay under `pipeline/analysis/<campaign>/`.",
            "- Raw `.npy` bursts under Drive / `~/Data/Faber2026/dsa110/` (see `DATA_LOCATIONS.md`).",
            "",
        ]
    )
    (library / "INDEX.md").write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    ap.add_argument("--root", type=Path, default=None, help="Faber2026 checkout (default: parent of scripts/)")
    ap.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    ap.add_argument("--link", action="store_true", help="create/update symlinks")
    ap.add_argument("--force", action="store_true", help="replace existing symlinks")
    ap.add_argument(
        "--only",
        action="append",
        default=[],
        help="Limit to exact catalog entry id(s); repeatable",
    )
    ap.add_argument(
        "--receipt",
        type=Path,
        default=None,
        help="Write a machine-readable post-action receipt",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="probe + report link actions without writing library files or links",
    )
    args = ap.parse_args(argv)

    if args.dry_run and args.receipt is not None:
        ap.error("--receipt cannot be combined with --dry-run")

    catalog = select_entries(
        load_catalog(Path(args.catalog).expanduser().resolve()),
        list(args.only),
    )
    root = _repo_root(args.root)
    library = args.library.expanduser().resolve()

    inventory = build(
        library,
        root,
        catalog,
        link=bool(args.link) and not args.dry_run,
        force=args.force,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print(yaml.safe_dump(inventory, sort_keys=False, allow_unicode=True))
        print(f"dry-run: entries={len(inventory['entries'])} (no writes)", file=sys.stderr)
        return

    library.mkdir(parents=True, exist_ok=True)
    inv_dir = library / "_inventory"
    inv_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = inv_dir / "inventory.yaml"
    yaml_path.write_text(yaml.safe_dump(inventory, sort_keys=False, allow_unicode=True))
    write_index(library, inventory, catalog)

    print(f"Wrote {yaml_path}")
    print(f"Wrote {library / 'INDEX.md'}")
    print(f"entries={len(inventory['entries'])} link={args.link}")

    if args.receipt is not None:
        receipt_path = args.receipt.expanduser().resolve()
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt = build_receipt(
            inventory,
            selected_ids=[entry.id for entry in catalog.entries],
            parent_commit=_git_head(root),
            pipeline_commit=_git_head(root / "pipeline"),
        )
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print(f"Wrote {receipt_path}")


if __name__ == "__main__":
    main()
