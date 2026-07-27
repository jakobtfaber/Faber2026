# Handoff: Data-provenance lane opened — P0.1/P2.1/P2.2 closed, machine inventory live-verified

---
**Date:** 2026-07-06 22:30
**Author:** AI Assistant (claude-fable-5/session-provenance)
**Status:** Handoff
**Branch:** Faber2026 `main` (local `0922930`, ahead 10 of origin, unpushed) · pipeline worktree `provenance/data-manifest` @ `80966d6` (4 commits ahead of dsa110-FLITS `origin/main`, unpushed)
**Commit:** see per-repo state below

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Machine inventory verification (which hosts hold project work) | ✅ Complete | Two-layer: exhaustive repo+pipeline grep, then live read-only probes of every doc-grounded host. Doc: `machine-inventory-verification-2026-07-06.md` |
| P0.1 — pin scattering-input manifest | ✅ Complete | All 24 rows sha256'd from `~/Data/Faber2026`; tests added (`de74d97`) |
| Manifest arc_path defect (12 CHIME rows) | ✅ Complete | Live `vls` proved CHIME cubes live at `data/CHIME_bursts/dmphase/`, not `DSA_bursts/`; fixed (`540e16a`) |
| P2.1 — locate cube builder | ✅ Complete (verdict: UNVERIFIED_BUILDER) | Evidence captured to `scattering/scat_analysis/builders_arc/` + ORIGIN.md (`7cc07b9`) |
| P2.2 — archive↔local byte cross-check | ✅ Complete | 24/24 sha256-identical arc↔local; manifest → `ARC_BYTE_MATCH`; xfail retired (`80966d6`) |
| Entire hook clobber (machine-wide git spam) | ✅ Complete | `push-gate-dispatch` restored from chezmoi + `uchg` relocked; commit test clean |
| gdrive↔iacobus parity | ✅ Sampled only | metadata 7/7 md5 + one 251 MB npy match; full-tree parity NOT run |
| Local data hygiene | ✅ Complete | 24 dangling symlinks (→ deleted `~/Developer/dsa110-local-data`) removed after verifying real files in `DSA_bursts/` |
| P2.3 cube-integrity tests, P2.4 DATA_SOURCES reconciliation, P0.2–P0.4 | 📋 Planned | Next lanes; P2.3/P0.2 fully specified in the plan |

**Current Workflow Phase:** Implement (executing `plan-trust-reset-revalidation.md` Phases 0 & 2)

## Workflow Artifacts

**Plan Documents:**
- [plan-trust-reset-revalidation.md](../plan/plan-trust-reset-revalidation.md) — the §V re-validation program being executed (P0.x/P1.x/P2.x…P6.x)
- [plan-circulation-readiness.md](../plan/plan-circulation-readiness.md) — parent plan; §V is gate zero

**Research Documents:**
- [research-trust-reset-revalidation.md](../research/research-trust-reset-revalidation.md) — V1–V6 surfaces map (defects, gates, rail definitions)
- [machine-inventory-verification-2026-07-06.md](../notes/machine-inventory-verification-2026-07-06.md) — **produced this session**; live-verified host table + closures appendix

**Previous Handoffs (context chain):**
- [handoff-2026-07-06-14-50-chime-sample-regeneration.md](../handoff/handoff-2026-07-06-14-50-chime-sample-regeneration.md) — the h17 upchan regeneration campaign (separate scint lineage)

## Critical References

1. `docs/rse/specs/notes/machine-inventory-verification-2026-07-06.md` — verified host topology + what was closed and how; read first.
2. `docs/rse/specs/plan/plan-trust-reset-revalidation.md:158-891` — Phases 0–2; P0.2/P0.3/P0.4/P2.3/P2.4 are the specified next tasks.
3. `~/Developer/scratch/worktrees/flits-provenance/scattering/scat_analysis/builders_arc/ORIGIN.md` — builder-hunt verdict and its consequences for trust rung (i).

## Recent Changes

Pipeline worktree `~/Developer/scratch/worktrees/flits-provenance` (branch `provenance/data-manifest`, off dsa110-FLITS `origin/main` = `9b6cf8b`):
- `data-manifest.csv` — sha256/bytes filled (24/24), arc_path corrected (12 rows), `status=ARC_BYTE_MATCH`, new `builder=UNVERIFIED_BUILDER` column
- `tests/test_data_manifest.py` — 3 tests incl. byte-verified pin; xfail removed
- `scripts/fill_data_manifest.py` — new
- `scattering/scat_analysis/builders_arc/{get_stokes.ipynb,utils.py,ORIGIN.md}` — captured evidence

Faber2026 `main` (this session's commits): `310c212` (verification doc), `0922930` (closures + journal + board).

## Reproducibility & Data State

- **Data:** all 24 cubes byte-verified against arc; hashes pinned in `data-manifest.csv`. Local root `~/Data/Faber2026/dsa110/DSA_bursts/` (physical), consumers symlink per ~/Data convention.
- **Environment:** conda `flits` (pytest run via `conda run -n flits`).
- **Arc access:** works from this Mac — `vls`/`vcp` (vos 3.6.4) + `~/.ssl/cadcproxy.pem`. VOSpace has **no MD5 node property**; content comparison requires byte download.
- **Partial results:** arc byte-crosscheck log in session scratchpad (ephemeral; results are pinned in the manifest + commit message).
- **In-flight jobs:** none (background download completed; temp dir empty).

## Verification State / Known-Broken

- **Tests:** `tests/test_data_manifest.py` 3/3 pass in the worktree. Full pipeline suite NOT run this session.
- **Unpushed:** BOTH repos. Pipeline branch `provenance/data-manifest` (4 commits) needs a PR to dsa110-FLITS; Faber2026 `main` is 10 ahead of origin (mix of this session's 2 + concurrent sessions' commits). Pushing = owner one-way door.
- **Uncommitted (separate lanes — do NOT sweep):** `CLAUDE.md` (owner's open vim session, `.CLAUDE.md.swp` present) and one `docs/rse/protocols/journal.jsonl` line appended by the concurrent session `9f491a6c` after `0922930`.
- **Unverified:** gdrive↔iacobus full-tree parity (sampled only). `DATA_SOURCES.md:90-111` reconciliation failure (P2.4) untouched. Cube content integrity (wraps/centering, P2.3) untouched — byte-identity to arc ≠ defect-free.

## Learnings

- **h17 holds no manifest cubes.** The plan's P2.2 premise ("h17-resident rows") was wrong; the only archive copy is arc. Only a stray `phineas_dsa_I_610_274_5121b_cntr_bpc.npy` (different window) exists on h17/iacobus in `arc_trash_2026-06/stokes_cubes_npy/`.
- **The cntr_bpc builder is genuinely lost** from all live hosts. Chain reconstructed: `<id>_fullstokes.pkl` → `Codetections_Analysis.ipynb` → DM-grid npys → [missing final windowing/bandpass step] → cubes (arc dates 2025-05-19). The found stage (`get_stokes.ipynb`) uses safe `time_shift=False`.
- **Machine ground truth lives at `pipeline/machine_inventory.yaml`** (schema 3, query via `scripts/query_machine_inventory.py`) — don't re-derive host topology from `~/.ssh/config`, which carries many non-project hosts.
- **Entire CLI keeps clobbering `~/.git-hooks-global/push-gate-dispatch`** (recurrence of the documented 2026-07-01 incident). Symptom: `[entire] Pushing entire/checkpoints/v1 to 0` on every commit (post-index-change passes `$1=0`). Fix: `chezmoi apply --force` on the file + `chflags uchg`. If spam recurs, check `stat -f %Sf` for the missing lock.
- **`~/Data/Faber2026/dsa110/flits-runs/data/` symlink layer was dead** (pointed at pre-migration `~/Developer/dsa110-local-data`); real files live in `DSA_bursts/`. If a config references `flits-runs/data/*.npy`, it now needs the `DSA_bursts` path (or fresh symlinks).
- Concurrent-writer reality: multiple live agents commit to Faber2026 `main`; use pathspec-only commits and journal every ≤10 min (`scripts/journal-append.sh`, protocol `docs/rse/protocols/journal-protocol.md`; board redeploy via Artifact url `fdc8d749-f3a6-4296-bbd2-9f1052fe57f6`).

## Action Items & Next Steps

1. [ ] **Owner:** review + push `provenance/data-manifest` and open the dsa110-FLITS PR; push Faber2026 `main` (Overleaf pulls from it).
2. [ ] **P2.3** — implement `tests/test_cube_integrity.py` + `scripts/cube_crosscheck.py` exactly per `plan-trust-reset-revalidation.md:800-866` (pre-registered edge/centering/cross-lineage criteria; thumbnail-grid figure is the visibility deliverable).
3. [ ] **P0.2** — restore frozen census CSVs + adjudication scripts from `~/Developer/scratch/worktrees/flits-rerun/scratch/codetection/` per plan `:257-326` (hash-pinned test first).
4. [ ] **P0.3/P0.4** — fit-generation inventory + table-emitter parity tests (plan `:327-428`).
5. [ ] **P2.4** — reproduce + adjudicate the `DATA_SOURCES.md:90-111` reconciliation failure using the now-pinned hashes.
6. [ ] **P2.5** — per-burst provenance table doc in Faber2026 embedding the P2.3 outputs.

**Recommended Next Skill:** `ai-research-workflows:implementing-plans` (the plan is approved and mid-execution; next concrete step is P2.3 in the `flits-provenance` worktree).

## Other Notes

- Work pipeline-side ONLY in the worktree (`~/Developer/scratch/worktrees/flits-provenance`); never commit in the pinned `pipeline/` submodule checkout (detached HEAD is intentional) and never commit on FLITS `main` (protected-branch guard blocks it).
- The journal cadence hooks fire mid-turn after ~10 min staleness — append, don't fight them.
- Trust-reset context: every analysis product is currently revoked (CONTEXT.md waves 1–3); this lane exists to rebuild trust bottom-up. Nothing verified here makes any manuscript number citable yet — that requires the full V-ladders.

---

**Handoff created by AI Assistant on 2026-07-06**
