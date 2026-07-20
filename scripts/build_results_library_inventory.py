#!/usr/bin/env python3
"""Build a navigable results-library inventory for Faber2026 + FLITS pipeline.

Loads ``results_library_catalog.yaml``, probes sources, writes
``inventory.yaml`` + ``INDEX.md``, and optionally creates symlinks under the
library taxonomy. Does not delete source trees.

Always invoke from the git checkout (this script), not a library copy.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import yaml

try:  # Package import in tests; direct import when invoked as a script.
    from scripts.results_library import DEFAULT_LIBRARY
except ModuleNotFoundError:  # pragma: no cover - exercised by CLI invocation
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
    suffix: str | None = None

    def resolve(self) -> Path:
        if self.env is not None:
            raw = os.environ.get(self.env) or self.default or ""
            if not raw:
                raise ValueError(f"external path env {self.env!r} empty and no default")
            base = Path(raw).expanduser()
            return base / self.suffix if self.suffix else base
        if self.path is not None:
            base = Path(self.path).expanduser()
            return base / self.suffix if self.suffix else base
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
                f"entry {eid!r}: trust {trust!r} not in trust_legend ({sorted(allowed)})"
            )
        repo = str(item["repo"])
        if repo not in ("pipeline", "parent", "external"):
            raise SystemExit(f"entry {eid!r}: repo must be pipeline|parent|external")
        sources = item.get("sources") or []
        if not isinstance(sources, list):
            raise SystemExit(f"entry {eid!r}: sources must be a list")
        ext_specs: list[ExternalPathSpec] = []
        for j, ext in enumerate(item.get("external_paths") or []):
            if not isinstance(ext, dict):
                raise SystemExit(f"entry {eid!r} external_paths[{j}] must be a mapping")
            if "env" in ext:
                ext_specs.append(
                    ExternalPathSpec(
                        env=str(ext["env"]),
                        default=ext.get("default"),
                        suffix=str(ext["suffix"]) if ext.get("suffix") else None,
                    )
                )
            elif "path" in ext:
                ext_specs.append(
                    ExternalPathSpec(
                        path=str(ext["path"]),
                        suffix=str(ext["suffix"]) if ext.get("suffix") else None,
                    )
                )
            else:
                raise SystemExit(f"entry {eid!r} external_paths[{j}] needs env or path")
        mode_raw = str(item.get("mode", "link_only"))
        if mode_raw not in ("link_only", "materialize"):
            raise SystemExit(f"entry {eid!r}: mode must be link_only|materialize, got {mode_raw!r}")
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
        if n_src == 1 and n_ext == 0:
            return slot
        return slot / Path(rel).name
    assert external_name is not None
    if n_ext == 1 and n_src == 0:
        return slot
    return slot / external_name


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
    if dest.exists() and not dest.is_symlink() and src.is_symlink() and _resolves_equal(src, dest):
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
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    records: list[dict[str, Any]] = []

    for entry in catalog.entries:
        base = base_for(entry, root)
        sources_meta: list[dict[str, Any]] = []

        for rel in entry.sources:
            if base is None:
                raise SystemExit(f"{entry.id}: sources require non-external repo")
            src = base / rel
            meta = probe_path(src, repo=base, rel=rel)
            if link or dry_run:
                dest = library / link_dest(entry, rel, external_name=None)
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
            if not p.exists():
                meta["size"] = "absent"
                meta["link_status"] = "absent"
            elif link or dry_run:
                dest = library / link_dest(entry, None, external_name=p.name)
                meta["link_status"] = ensure_link(p, dest, force=force, dry_run=dry_run)
            sources_meta.append(meta)

        records.append(
            {
                "id": entry.id,
                "domain": entry.domain,
                "slot": entry.slot,
                "trust": entry.trust,
                "repo": entry.repo,
                "mode": entry.mode,
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
            sizes = ", ".join(f"`{s.get('size')}`" for s in e["sources"] if s.get("size")) or "—"
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
            'ls "$FABER2026_RESULTS_LIBRARY"/scattering',
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
    ap.add_argument(
        "--root", type=Path, default=None, help="Faber2026 checkout (default: parent of scripts/)"
    )
    ap.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    ap.add_argument("--link", action="store_true", help="create/update symlinks")
    ap.add_argument("--force", action="store_true", help="replace existing symlinks")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="probe + report link actions without writing library files or links",
    )
    args = ap.parse_args(argv)

    catalog = load_catalog(Path(args.catalog).expanduser().resolve())
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


if __name__ == "__main__":
    main()
