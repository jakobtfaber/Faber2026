#!/usr/bin/env python3
"""Build a navigable results-library inventory for Faber2026 + FLITS pipeline.

Scans known result trees, writes inventory.yaml + INDEX.md, and (re)creates
symlinks under the library taxonomy. Does not delete source trees.
"""

from __future__ import annotations

import argparse
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

DEFAULT_LIBRARY = Path.home() / "Data" / "Faber2026" / "results-library"

# Prefer science-gates worktree when present (current pin + G1a), else main clone.
_CANDIDATES = [
    Path.home()
    / "Developer/scratch/worktrees/Faber2026-science-gates",
    Path.home()
    / "Developer/repos/github.com/jakobtfaber/Faber2026",
]


def _pick_root() -> Path:
    env = os.environ.get("FABER2026_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    for cand in _CANDIDATES:
        if (cand / "pipeline" / "analysis").is_dir():
            return cand.resolve()
    raise SystemExit("Could not locate Faber2026 root (set FABER2026_ROOT)")


def _du_human(path: Path) -> str:
    if not path.exists():
        return "missing"
    try:
        out = subprocess.check_output(["du", "-sh", str(path)], text=True, stderr=subprocess.DEVNULL)
        return out.split()[0]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "?"


def _count_files(path: Path, limit: int = 50_000) -> int | str:
    if not path.exists():
        return 0
    n = 0
    for _ in path.rglob("*"):
        if _.is_file():
            n += 1
            if n >= limit:
                return f">={limit}"
    return n


def _git_tracked_hint(repo: Path, rel: str) -> str:
    """Cheap tracked/ignored hint via git check-ignore / ls-files."""
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
        # directory: any tracked children?
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


def _link(src: Path, dest: Path, *, force: bool) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() or dest.exists():
        if not force:
            return "exists"
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        else:
            return "skip-dir"
    if not src.exists():
        return "missing-src"
    dest.symlink_to(src.resolve())
    return "linked"


# Campaign catalog: library-relative slot → source relative to parent or pipeline
ENTRIES: list[dict] = [
    # --- scattering ---
    {
        "id": "scattering.dm-locked-2026-07-14",
        "domain": "scattering",
        "slot": "scattering/2026-07-14_dm-locked",
        "trust": "provisional",  # accepted_physical fits; not V1-certified measurements
        "repo": "pipeline",
        "sources": [
            "analysis/scattering-dm-locked-2026-07-14/results",
        ],
        "notes": "July DM-locked joint adjudication + fit_summaries + ppc; G1a morphologies live here.",
    },
    {
        "id": "scattering.refit-2026-06",
        "domain": "scattering",
        "slot": "scattering/2026-06_refit",
        "trust": "revoked-2026-07-06",
        "repo": "pipeline",
        "sources": [
            "analysis/scattering-refit-2026-06/_a1_fits",
            "analysis/scattering-refit-2026-06/joint_json",
        ],
        "notes": "Pre-reset June campaign; partial mirror of $FLITS_RUNS. Archival.",
    },
    {
        "id": "scattering.beta-campaign-2026-07",
        "domain": "scattering",
        "slot": "scattering/2026-07_beta-campaign",
        "trust": "revoked-2026-07-06",
        "repo": "pipeline",
        "sources": [
            "analysis/beta_campaign/fits",
            "analysis/beta_campaign/beta_campaign_verdicts.json",
        ],
        "notes": "Full posteriors under $FLITS_RUNS, not in-repo.",
    },
    # --- scintillation ---
    {
        "id": "scintillation.dsa-lorentzian-2026-07-07",
        "domain": "scintillation",
        "slot": "scintillation/2026-07-07_dsa-lorentzian",
        "trust": "provisional",
        "repo": "pipeline",
        "sources": [
            "analysis/scintillation-dsa-lorentzian-2026-07-07",
        ],
        "notes": "Whole campaign dir mixed code+results; library link points at campaign root. Prefer reading results/ CSV+JSON only.",
    },
    {
        "id": "scintillation.chime",
        "domain": "scintillation",
        "slot": "scintillation/chime-diagnostic",
        "trust": "diagnostic_only",
        "repo": "pipeline",
        "sources": [
            "analysis/chime-scintillation",
        ],
        "notes": "CHIME scintillation remains diagnostic_only on main.",
    },
    # --- dispersion ---
    {
        "id": "dispersion.pipeline-results-root",
        "domain": "dispersion",
        "slot": "dispersion/pipeline-results-root",
        "trust": "mixed",
        "repo": "pipeline",
        "sources": [
            "results",
        ],
        "notes": "Flat pipeline/results/ tree; bulk dm_phase/dm_power gitignored.",
    },
    {
        "id": "dispersion.dm-joint-phase-v2-parent",
        "domain": "dispersion",
        "slot": "dispersion/dm-joint-phase-v2",
        "trust": "provisional",
        "repo": "parent",
        "sources": [
            "analysis/dm-joint-phase-v2",
        ],
        "notes": "Parent-repo DM phase analysis products.",
    },
    {
        "id": "dispersion.chime-dm",
        "domain": "dispersion",
        "slot": "dispersion/chime-dm",
        "trust": "mixed",
        "repo": "pipeline",
        "sources": [
            "analysis/chime_dm",
        ],
        "notes": "Mixed campaign dir.",
    },
    # --- foreground ---
    {
        "id": "foreground.tau-consistency-catalog",
        "domain": "foreground",
        "slot": "foreground/tau_consistency_catalog.csv",
        "trust": "pending-refits",
        "repo": "pipeline",
        "sources": [
            "galaxies/foreground/data/tau_consistency_catalog.csv",
        ],
        "notes": "α=4 consistency catalog; eligible rows pending until G1–G3 clear.",
    },
    {
        "id": "foreground.budget-exports",
        "domain": "foreground",
        "slot": "foreground/tex-exports",
        "trust": "manuscript-live",
        "repo": "pipeline",
        "sources": [
            "exports",
        ],
        "notes": "Generated TeX tables consumed by manuscript.",
    },
    {
        "id": "foreground.provisional-propagation",
        "domain": "foreground",
        "slot": "foreground/provisional-propagation",
        "trust": "provisional",
        "repo": "parent",
        "sources": [
            "analysis/provisional_propagation",
        ],
        "notes": "Parent ledger + results.json for joint/DSA/two-screen/foreground tables.",
    },
    {
        "id": "foreground.v3-energetics",
        "domain": "foreground",
        "slot": "foreground/v3-energetics",
        "trust": "partial",
        "repo": "parent",
        "sources": [
            "analysis/v3_energetics",
        ],
        "notes": "DSA data-driven done; CHIME E2 remainder open.",
    },
    # --- manuscript ---
    {
        "id": "manuscript.figures",
        "domain": "manuscript",
        "slot": "manuscript/figures",
        "trust": "owner-approved-bytes",
        "repo": "parent",
        "sources": [
            "figures",
        ],
        "notes": "Final embedded figures. Stay in parent repo for Overleaf; library links for navigation.",
    },
    {
        "id": "manuscript.repro-manifest",
        "domain": "manuscript",
        "slot": "manuscript/repro_manifest.csv",
        "trust": "live",
        "repo": "parent",
        "sources": [
            "repro_manifest.csv",
        ],
        "notes": "Producer→artifact ledger.",
    },
    # --- review ---
    {
        "id": "review.figure-review",
        "domain": "review-ledger",
        "slot": "review-ledger/figure_review",
        "trust": "live",
        "repo": "parent",
        "sources": [
            "figure_review",
        ],
        "notes": "Approval receipts + slots.",
    },
    # --- compute scratch pointers (external) ---
    {
        "id": "compute.flits-runs-default",
        "domain": "compute-scratch",
        "slot": "compute-scratch/FLITS_RUNS",
        "trust": "external",
        "repo": "external",
        "sources": [],
        "external_paths": [
            os.environ.get("FLITS_RUNS", "/central/scratch/jfaber/flits-runs"),
            str(Path.home() / "Developer/scratch/flits-local-runs"),
        ],
        "notes": "Joint-fit posteriors / samples; not git. Env FLITS_RUNS overrides.",
    },
]


def build(library: Path, root: Path, *, link: bool, force: bool) -> dict:
    pipeline = root / "pipeline"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    records = []
    for entry in ENTRIES:
        repo = entry["repo"]
        base = {"pipeline": pipeline, "parent": root, "external": None}.get(repo)
        sources_meta = []
        for rel in entry.get("sources", []):
            src = (base / rel) if base is not None else None
            meta = {
                "rel": rel,
                "abs": str(src) if src else None,
                "size": _du_human(src) if src else None,
                "n_files": _count_files(src) if src else None,
                "git": _git_tracked_hint(base, rel) if src and base else "external",
            }
            sources_meta.append(meta)
            if link and src is not None:
                # Single-source slots link the source; multi-source get numbered children
                if len(entry["sources"]) == 1:
                    dest = library / entry["slot"]
                else:
                    dest = library / entry["slot"] / Path(rel).name
                meta["link_status"] = _link(src, dest, force=force)
        for ext in entry.get("external_paths", []):
            p = Path(ext).expanduser()
            sources_meta.append(
                {
                    "rel": None,
                    "abs": str(p),
                    "size": _du_human(p) if p.exists() else "absent",
                    "n_files": _count_files(p) if p.exists() else 0,
                    "git": "external",
                    "link_status": _link(p, library / entry["slot"] / p.name, force=force)
                    if link and p.exists()
                    else "absent",
                }
            )
        records.append(
            {
                "id": entry["id"],
                "domain": entry["domain"],
                "slot": entry["slot"],
                "trust": entry["trust"],
                "repo": repo,
                "notes": entry["notes"],
                "sources": sources_meta,
            }
        )

    inventory = {
        "schema": "faber2026-results-library/v1",
        "generated_at": now,
        "library_root": str(library),
        "faber2026_root": str(root),
        "pipeline_root": str(pipeline),
        "env": {
            "FABER2026_RESULTS_LIBRARY": str(library),
            "FLITS_RUNS": os.environ.get("FLITS_RUNS", ""),
        },
        "entries": records,
    }
    return inventory


def write_index(library: Path, inventory: dict) -> None:
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
        "Entries are mostly **symlinks** into existing trees (non-destructive).",
        "Trust tags follow the 2026-07-06 trust reset + later provisional gates.",
        "",
        "## Trust legend",
        "",
        "| Tag | Meaning |",
        "|-----|---------|",
        "| `live` / `manuscript-live` | In active manuscript use |",
        "| `owner-approved-bytes` | Figure bytes approved; science may still be provisional |",
        "| `provisional` | Best-so-far; not V1-certified |",
        "| `pending-refits` | Fail-closed until α=4 consistency clears |",
        "| `diagnostic_only` | Must not enter screen/α claims |",
        "| `revoked-2026-07-06` | Pre-reset; archival only |",
        "| `external` | Lives on HPC/scratch/Drive, not git |",
        "",
        "## Domains",
        "",
    ]
    by_domain: dict[str, list] = {}
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
            gits = ", ".join(
                sorted({s.get("git", "?") for s in e["sources"]})
            )
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
            "python3 \"$FABER2026_RESULTS_LIBRARY\"/_inventory/build_inventory.py --link",
            "```",
            "",
            "Machine-readable: [`_inventory/inventory.yaml`](_inventory/inventory.yaml).",
            "",
            "## Not moved (yet)",
            "",
            "- Analysis **driver scripts** remain under `pipeline/analysis/<campaign>/`.",
            "- Raw `.npy` bursts stay under Drive / `~/Data/Faber2026/dsa110/` (see `DATA_LOCATIONS.md`).",
            "- Physical relocation of **git-tracked** fit JSON out of FLITS needs a dedicated FLITS PR.",
            "",
        ]
    )
    (library / "INDEX.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    ap.add_argument("--root", type=Path, default=None)
    ap.add_argument("--link", action="store_true", help="create/update symlinks")
    ap.add_argument("--force", action="store_true", help="replace existing symlinks")
    args = ap.parse_args()
    root = args.root.resolve() if args.root else _pick_root()
    library = args.library.expanduser().resolve()
    library.mkdir(parents=True, exist_ok=True)
    (library / "_inventory").mkdir(parents=True, exist_ok=True)

    inventory = build(library, root, link=args.link, force=args.force)
    yaml_path = library / "_inventory" / "inventory.yaml"
    yaml_path.write_text(yaml.safe_dump(inventory, sort_keys=False, allow_unicode=True))
    write_index(library, inventory)

    # Keep a copy of this builder next to the inventory
    self_path = Path(__file__).resolve()
    dest_builder = library / "_inventory" / "build_inventory.py"
    if self_path != dest_builder:
        dest_builder.write_text(self_path.read_text())

    print(f"Wrote {yaml_path}")
    print(f"Wrote {library / 'INDEX.md'}")
    print(f"entries={len(inventory['entries'])} link={args.link}")


if __name__ == "__main__":
    main()
