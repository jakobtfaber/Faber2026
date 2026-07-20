# `docs/rse/` — research-software execution store

Only this README may sit at the root of `docs/rse/`. Everything else lives
under a role or science-strand folder below.

## Top-level layout

| Path | Role |
|------|------|
| `control/` | Execution control plane: program state, ledgers, registries, board |
| `protocols/` | Standing protocols + append-only journal |
| `certificates/` | Machine-checkable certification products (e.g. L0 JSON) |
| `ops/` | Operator docs (knowledge base, …) |
| `wayfinder/` | Wayfinder skill outputs (map + tickets); project store, not `.scratch/` |
| `specs/` | **Markdown only** — workflow docs under prefix folders (see below) |
| `decks/` | Review/evidence binaries, nested by science strand |
| `patches/` | Diff patches kept for provenance |
| `claude-science/` | Session frame archive (do not regroup) |

Runnable helpers live under repo-root `scripts/` (including `scripts/verify/`);
shared CSV inputs under repo-root `data/`.

## `control/`

| File / dir | Notes |
|------------|--------|
| `program-state.toml` | Canonical lanes + owner view (edit this) |
| `evidence-ledger.toml` | Sightline × strand ledger |
| `results-registry.toml` | Results / claim trust inventory |
| `ACTIVE_LANES.md` | **GENERATED** by `scripts/sync_state.py` — do not hand-edit |
| `BOARD.md` | Faber execution dashboard (markdown) |
| `owner-queue-ritual.md` | Owner-queue operating ritual |
| `board/` | `readiness.html`, `owner-view.json`, `claims-audit.md` |

## `protocols/`

| File | Notes |
|------|--------|
| `verification-protocol.md` | CAS / science verification + data-integrity strata |
| `journal-protocol.md` | Agent journal rules |
| `journal.jsonl` | Append-only session journal (historical paths may be stale) |

## `certificates/`

L0 (and later L1) certificate JSON products. New cert artifacts go here, not
under `specs/` or `control/`.

## `decks/` by science strand

Campaign folder names are unchanged; they nest under a strand:

| Strand | Campaigns |
|--------|-----------|
| `decks/dm/` | `dm-campaign-2026-07/`, `casey-dm-calibration-2026-07-19/` |
| `decks/scintillation/` | `acf-review-*`, `waterfall-review-*`, `scint-validation-*`, `remediation-preview-*`, `gate0-detectability/` |
| `decks/budget/` | `cluster-crossing-*`, `thread1-*` |
| `decks/closeouts/` | JSON/HTML closeout packages |

## `specs/` prefix folders

New workflow docs: `docs/rse/specs/<prefix>/<prefix>-….md`.

**First-class prefixes:** `research/`, `plan/`, `experiment/`, `implement/`,
`validation/`, `handoff/`, `decision/`, `runbook/`, `dm/`.

**`specs/notes/`** holds thinner genres (filenames unchanged): `assessment-*`,
`audit-*`, `charter-*`, `checklist-*`, `definition-*`, `draft-*`, `memo-*`,
`prd-*`, `triage-*`, `v6-*`, `jointmodel-*`, `report-*`, `results-*`, plus
irregular names formerly under `misc/` (`owner-*`, `figure-*`, `ne2025_*`, …).

**Override vs rse-plugins:** upstream skills may still mention flat
`docs/rse/specs/handoff-….md`. In this repo, always use the prefix (or
`notes/`) subfolder. No non-markdown files under `specs/`.
