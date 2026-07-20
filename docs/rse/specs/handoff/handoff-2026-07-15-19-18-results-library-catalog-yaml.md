# Handoff: results library catalog-YAML reshape

---
**Date:** 2026-07-15 19:18
**Author:** AI Assistant (Grok session)
**Status:** Handoff — Phase A partial implemented; **uncommitted**; local `main` behind `origin/main`
**Branch:** `main`
**Commit:** `0f96f1d3` (local tip; **behind** `origin/main` by 5 commits; ahead 0)

---

## Task(s)

This session focused on the **Faber2026 results library** (navigable inventory of fit/campaign products outside git) after a strict maintainability review rejected the first catalog-in-Python design.

| Task | Status | Notes |
|------|--------|-------|
| Survey ruff/mypy/pre-commit (`/code-quality-tools`) | ✅ Complete | `pipeline/` has ruff + nox lint; no mypy / pre-commit |
| Strict review of untracked results-library work (`/code-review`) | ✅ Complete | Not approved as-is; blockers listed below |
| Refactor to catalog-YAML shape | ✅ Complete | Data in YAML; builder loads/validates/probes/links/emits |
| Regenerate library INDEX on disk | ✅ Complete | `~/Data/Faber2026/results-library/` written ~2026-07-16T02:15Z UTC |
| Explain “catalog is data” | ✅ Complete | User question answered in chat |
| Commit / PR results-library files | 📋 Planned | Still untracked; sync `main` first |
| Phase A finish (pointers, DATA_LOCATIONS, producers) | 📋 Planned | See plan open checkboxes |
| Phase B physical separation | 📋 Planned | Needs dedicated PRs; do not mix with manuscript science |

**Current Workflow Phase:** Implement (Phase A partial). Next for this lane: commit after pull, then finish remaining Phase A docs/wiring — or pause for science-gate work on a synced `origin/main`.

**Parallel ledger (not this session’s implementation):** manuscript science gates G1–G7 and unified dirty inventory live in older handoffs (still untracked on this tree). Do not confuse those with the results-library lane.

## Workflow Artifacts

**Plan Documents:**
- [plan-results-library-2026-07-15.md](../plan/plan-results-library-2026-07-15.md) — Phase A/B; honest status after review (partial, not overclaimed)
- [plan-manuscript-science-gates-2026-07-15.md](../plan/plan-manuscript-science-gates-2026-07-15.md) — separate science-gate plan (untracked; not executed this session)

**Pointers / inventory:**
- [results-library-INDEX.md](../results/results-library-INDEX.md) — repo pointer to external library + refresh commands
- On disk: `~/Data/Faber2026/results-library/INDEX.md` + `_inventory/inventory.yaml` (generated; not in git)

**Prior handoffs (related workspace, not results-library code):**
- [handoff-2026-07-15-17-12-manuscript-science-gates.md](../handoff/handoff-2026-07-15-17-12-manuscript-science-gates.md)
- [handoff-2026-07-15-17-14-unified-dirty-and-open-work.md](../handoff/handoff-2026-07-15-17-14-unified-dirty-and-open-work.md) — dirty worktree / open-work ledger (note: that handoff’s checkout branch note may be stale vs current `main`)

## Critical References

Read these first, in order:

1. `scripts/results_library_catalog.yaml` — **only place to add/edit campaigns** (slots, trust, sources)
2. `scripts/build_results_library_inventory.py` — loader, validation, probe, symlink, INDEX emit
3. `docs/rse/specs/plan/plan-results-library-2026-07-15.md` — done vs open vs Phase B

Optional: `scripts/results_library.py` — path helper (`DEFAULT_LIBRARY`, `results_slot`, `require_results_library`); **no producers import it yet**.

## Recent Changes

All **untracked** (no commits this session):

| Path | Change |
|------|--------|
| `scripts/results_library_catalog.yaml` | **New** — 16 entries + `trust_legend`; schema `faber2026-results-library-catalog/v1` |
| `scripts/build_results_library_inventory.py` | **Rewritten** — load catalog → validate trust ∈ legend → probe → optional link → write inventory/INDEX; root = parent of `scripts/` or `FABER2026_ROOT` / `--root`; `--dry-run`; **no** copy of builder into library |
| `scripts/results_library.py` | Path helper; exports `DEFAULT_LIBRARY` (builder imports it) |
| `docs/rse/specs/plan/plan-results-library-2026-07-15.md` | Honest Phase A partial; forbids pipeline-local duplicate helper |
| `docs/rse/specs/results/results-library-INDEX.md` | Points at catalog path + dry-run/refresh |
| Library on disk | INDEX regenerated; stale `_inventory/build_inventory.py` **deleted** |

### Design decisions locked in review + rewrite

1. **Catalog is data** — campaign list lives in YAML; Python only orchestrates.
2. **Single builder source** — always run from git checkout (`scripts/build_…py`), never a library-side copy.
3. **Root discovery** — default `Path(__file__).resolve().parents[1]`; no hardcoded machine worktree candidates.
4. **Trust closed set** — tags must appear in `trust_legend` or build exits non-zero.
5. **Do not add** `pipeline/galaxies/foreground/results_library.py` — one helper in parent `scripts/` only.
6. External FLITS runs: catalog uses `external_paths` with `{env, default}` and `{path}` specs (see compute-scratch entry).

### Review blockers that were addressed

| Blocker | Resolution |
|---------|------------|
| Catalog-in-code (`ENTRIES` list) | → YAML catalog |
| Dual builder (git + library copy) | Copy removed; INDEX “How to use” points at checkout script |
| Hardcoded `_CANDIDATES` roots | → script-relative repo root |
| Freeform trust / hand legend drift | → legend from catalog; validation |
| Plan overclaims | Plan rewritten to match disk |

## Reproducibility & Data State

- **Seeds:** N/A (inventory tooling, not fits)
- **Environment:** System `python3` + PyYAML (`import yaml`). No pixi/uv pin for these parent scripts. Pipeline quality tools (context only): `pipeline/pyproject.toml` ruff in `dependency-groups.lint`, `nox -s lint`
- **Data / library:**
  - Default: `~/Data/Faber2026/results-library` (override `FABER2026_RESULTS_LIBRARY`)
  - Generated: `INDEX.md`, `_inventory/inventory.yaml` (schema `faber2026-results-library/v1`)
  - Symlinks into parent + `pipeline/` analysis/results trees; **non-destructive**
- **Partial results:** Library tree populated; trust tags on campaigns remain science-policy (provisional / revoked / etc.) — inventory does not certify measurements
- **In-flight jobs:** None from this session

### Refresh commands

```bash
cd /Users/jakobfaber/Developer/repos/github.com/jakobtfaber/Faber2026
python3 scripts/build_results_library_inventory.py --dry-run
python3 scripts/build_results_library_inventory.py --link --force
```

## Verification State / Known-Broken

> **Known-broken / unverified — do not assume green**

- **Tests:** No unit tests for catalog load, `link_dest`, or trust validation. Manual only:
  - `--dry-run` succeeded
  - `--link --force` wrote INDEX + inventory
  - Unknown-trust catalog rejected (exit 1)
- **Uncommitted / unpushed:** Entire results-library lane untracked. Also untracked (other lanes): science-gate plan + two handoffs. Local `main` is **behind `origin/main` by 5** — pull/rebase before any PR.
- **Unverified:** No CI job runs the builder. File-count/`du` probes are best-effort; external HPC path often `absent` on laptop. Single-file sources now count as 1 file (fixed during rewrite); not regression-tested beyond smoke.
- **Do not treat plan checkboxes from older chats as truth** — earlier Phase A “done” claims for `RESULTS_LIBRARY.md`, `DATA_LOCATIONS.md` section, and pipeline helper were **false**; corrected plan still shows them open.

## Learnings

- **Results vs code ownership:** Fit/analysis code stays in Faber2026 + `pipeline/`; library is a **navigable symlink inventory**, not a second git home for drivers. Phase B physical moves need explicit FLITS PRs.
- **“Catalog is data”** = edit YAML to add campaigns; do not re-open a big Python `ENTRIES` list.
- **`pipeline/` pin is deliberate** — manuscript repo standing rule: do not bump submodule gitlink as a side effect of parent tooling work.
- **Strict review bar** (from `/code-review` skill): dual canonical sources, catalog-in-code, and plan lying about completeness are **presumptive merge blockers**, not nits.
- **Code quality baseline in FLITS:** ruff configured (`line-length=100`, select B/E4/E7/E9/F/I/UP); mypy and pre-commit absent — separate lane if pursued.
- **Standing push/PR auth** exists in `AGENTS.md` for this repo; still prefer focused branch + PR; never force-push shared history.

## Action Items & Next Steps

1. [ ] **`git pull` / sync `main` to `origin/main`** (5 commits behind) before branching.
2. [ ] **Commit results-library lane on a focused branch** (pathspec-only; do not sweep science-gate docs or `pipeline` pin):
   - `scripts/results_library_catalog.yaml`
   - `scripts/build_results_library_inventory.py`
   - `scripts/results_library.py`
   - `docs/rse/specs/plan/plan-results-library-2026-07-15.md`
   - `docs/rse/specs/results/results-library-INDEX.md`
   - this handoff (optional but recommended)
3. [ ] **Finish Phase A open items** (from plan): `RESULTS_LIBRARY.md` pointers; `DATA_LOCATIONS.md` section; first real importer of `results_slot(...)` if a producer is ready.
4. [ ] **Optional hardening:** small unit tests for `load_catalog` / `link_dest` / unknown trust; do not add mypy to whole manuscript tree without scope.
5. [ ] **Do not start Phase B** (physical relocate of gitignored/tracked fit trees) without a dedicated plan/PR and pipeline coordination.
6. [ ] **Separate:** science gates G1–G7 and dirty-worktree hygiene — use [handoff-2026-07-15-17-14-unified-dirty-and-open-work.md](../handoff/handoff-2026-07-15-17-14-unified-dirty-and-open-work.md) + science-gates plan; re-inventory dirt after pull (that handoff’s branch notes may be stale).

**Recommended Next Skill:** `ai-research-workflows:implementing-plans` — for remaining Phase A checklist on [plan-results-library-2026-07-15.md](../plan/plan-results-library-2026-07-15.md) after sync + commit; **or** `ai-research-workflows:validating-implementations` if the next session only needs to verify the catalog-YAML builder against the plan before PR.

If switching to manuscript science instead: re-read science-gates handoff/plan and use `ai-research-workflows:running-experiments` for α=4 / gate work — **after** checkout is on current `origin/main`.

## Other Notes

- Overleaf twin: `~/Developer/overleaf/Faber2026` — respect merge order; results library does not move `figures/` out of git.
- Default library path uses `Path.home() / "Data" / "Faber2026" / "results-library"` (may resolve under `/Users/…/Data/…`).
- Multi-source catalog entries link as `slot / basename`; single-source links as `slot` itself. External multi-path entries use `slot / name`.
- `dependency` for builder: PyYAML must be importable in the python used to run the script.

---

**Handoff created by AI Assistant on 2026-07-15 19:18**
