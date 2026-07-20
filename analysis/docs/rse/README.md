# `docs/rse/` — research-software execution store

Layout for Faber2026 workflow artifacts. Agents write new docs into the
folders below; do not leave binaries or loose markdown at `specs/` root.

## Directories

| Path | Role |
|------|------|
| `specs/` | **Markdown only**, under **prefix subfolders** (see below) |
| `wayfinder/` | Wayfinder skill outputs (project store; not `.scratch/`) |
| `BOARD.md`, `board/` | Faber execution dashboard |
| `decks/` | Committed review/evidence binaries (PNG/PDF/HTML/JSON closeouts) |
| `patches/` | Diff patches kept for provenance |
| `../scripts/` (+ `scripts/verify/`) | Runnable helpers / CAS checks (not under `specs/`) |
| `../data/` | Script inputs (CSV etc.) shared with analysis tools |

## `specs/` prefix folders

New workflow docs go to `docs/rse/specs/<prefix>/<prefix>-….md`.

| Folder | Filename prefix |
|--------|-----------------|
| `research/` | `research-*` |
| `plan/` | `plan-*` |
| `experiment/` | `experiment-*` |
| `implement/` | `implement-*` |
| `validation/` | `validation-*` |
| `handoff/` | `handoff-*` |
| `decision/` | `decision-*` |
| `runbook/` | `runbook-*` |
| `results/` | `results-*` |
| `report/` | `report-*` |
| `dm/` | `dm-*` (memos; PNGs live under `decks/`) |
| `jointmodel/` | `jointmodel-*` |
| `assessment/`, `audit/`, `charter/`, `checklist/`, `definition/`, `draft/`, `memo/`, `prd/`, `triage/`, `v6/` | matching `<prefix>-*` |
| `misc/` | Irregular names (`ne2025_*`, `owner-*`, `machine-*`, `figure-*`, `dirty-*`, `verified-*`, `undermind-*`, …) |

**Override vs rse-plugins:** upstream skills still mention flat
`docs/rse/specs/handoff/handoff-….md`. In this repo, always use the prefix
subfolder. Do not reintroduce non-markdown files under `specs/`.

## Related surfaces

- `verification-protocol.md` — CAS / science verification gates
- `results-registry.toml` — results inventory
- `journal.jsonl` — append-only session journal (historical paths may be stale)
