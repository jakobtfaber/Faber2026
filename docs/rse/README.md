# `docs/rse/` — research-software execution store

Only this README may sit at the root of `docs/rse/`. Everything else lives
under a role or science-strand folder below.

## Top-level layout

| Path | Role |
|------|------|
| `control/` | Execution control plane: program state, ledgers, registries, board |
| `protocols/` | Standing protocols + append-only journal |
| `certificates/` | Machine-checkable certification products (e.g. L0 JSON) |
| `ops/` | Operator docs (knowledge base, review-status, …) |
| `wayfinder/` | Wayfinder skill outputs (map + tickets); project store, not `.scratch/` |
| `specs/` | **Markdown only** — workflow docs under prefix folders (see below) |
| `decks/` | Review/evidence binaries, nested by science strand |
| `patches/` | Diff patches kept for provenance |

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

| Strand | Live campaigns |
|--------|----------------|
| `decks/dm/` | `casey-dm-calibration-2026-07-19/` (decision figure) |
| `decks/scintillation/` | `acf-review-*`, `waterfall-review-*`, `scint-validation-*`, `remediation-preview-*` |
| `decks/budget/`, `decks/closeouts/` | reserved strands (empty unless a live review lands) |

## `specs/` prefix folders

**Thin live surface only.** Files present under `specs/` are either (a) live
handoffs / definitions / decisions / wishlist, or (b) short stubs for paths
still named by scripts/`CONTEXT.md`. Do not resurrect deleted campaign plans —
frontier is wayfinder + BOARD.

New workflow docs (if needed): `docs/rse/specs/<prefix>/<prefix>-….md`.

**Allowed prefixes:** `research/`, `plan/`, `experiment/`, `implement/`,
`validation/`, `handoff/`, `decision/`, `runbook/`, `dm/`, `notes/`.

**Override vs rse-plugins:** upstream skills may still mention flat
`docs/rse/specs/handoff-….md`. In this repo, always use the prefix (or
`notes/`) subfolder. No non-markdown files under `specs/`.
