# Handoff: Figure 1 observed-peak lane closed; owner decide pending; dmcorr refuted

---
**Date:** 2026-07-18 14:44
**Author:** AI Assistant (Claude, session 42b5d228)
**Status:** Handoff
**Branch:** primary checkout currently on `ms/results-registry` (another lane's branch — do not assume main); origin/main at `a3307c18`
**Commit:** origin/main `a3307c18`

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Fig1 re-render per owner needs_revision spec (observed-peak + DM-provenance + freq-axis audits) | ✅ Complete | Executed concurrently by two lanes; reconciled. Candidate PR #121 merged (`341e2200`) |
| Codex auto-review on PR #121 (1×P1 + 3×P2) | ✅ Complete | Fixes stranded by a merge race, landed via PR #128 (`33ecbb66`). P1 was stale post-rebase; raw DSA SIGPROC headers now actually read over ssh from iacobus (12/12 match fixture) |
| DM-drift "stem misstatement" corrections (isha +0.234, phineas +0.300) | ✅ Complete — **REFUTED** | Corrected candidate landed via PR #129 (`51aaa3da`), then the interpretation was refuted by marker dependence; refutation record landed via PR #132 (`aed901f0`). Corrected candidate must NOT be promoted |
| Decided model-toa rejection record (`2026-07-17-fig1-model-toa`) | ✅ Complete | Tracked via PR #130 (`711672bd`) — the decision receipt both fig1 lanes executed |
| Owner `decide` on the two staged fig1 candidates | 📋 Planned — **owner-gated** | Recommendation: approve `2026-07-17-fig1-observed-peak-audit` (uncorrected); mark `…-dmcorr` needs_revision citing the refutation |
| Promotion PR after approval (bytes → `figures/codetection_data_grid.pdf`, caption check) | 📋 Planned | Blocked on the decide above |
| Thread 1 Pandhi transmittal | 📋 Planned — owner-side | Draft final at `docs/rse/specs/draft-message-thread1-pandhi-2026-07-17.md` (untracked in primary checkout) |

**Current Workflow Phase:** Validate (complete) → owner decision gate

## Workflow Artifacts

- `docs/rse/specs/validation-fig1-observed-peak-audit.md` — the fig1 validation record, including two addenda: the auto-review disposition and the **marker-dependence refutation** of the dmcorr corrections
- `docs/rse/specs/research-/plan-/implement-fig1-observed-peak-audit.md` — the concurrent lane's workflow docs (merged with #121)
- `docs/rse/specs/draft-message-thread1-pandhi-2026-07-17.md` — Pandhi transmittal draft (owner to send; untracked)
- `figure_review/batches/2026-07-17-fig1-observed-peak-audit/` — the promotable candidate packet
- `figure_review/batches/2026-07-17-fig1-observed-peak-dmcorr/` — refuted candidate; `provenance/marker-dependence-refutation.json` is the kill record

## Critical References

1. `figure_review/batches/2026-07-17-fig1-observed-peak-dmcorr/provenance/marker-dependence-refutation.json` — why the corrections are wrong; read before touching anything DM-drift related
2. `docs/rse/specs/validation-fig1-observed-peak-audit.md` (final two addenda) — full disposition of auto-review + refutation
3. `figure_review/README.md` — the fail-closed decide/promote workflow the next step must follow

## Recent Changes (all merged to main)

- `scripts/audit_fig1_frequency_axes.py` — `--raw-header-host` (remote SIGPROC header read, fail-closed vs fixture), per-product `product_mask_summary`, explicit `header_validation` lineage fields (#128)
- `scripts/audit_fig1_residual_drift.py` — twelve-burst roster validation + 24-measurement requirement before `gate_passed` (#128)
- `scripts/audit_fig1_axes.py` — sharpness-scan drift audit (NEW, #129); valid as a measurement, its stem-misstatement interpretation is refuted
- `scripts/plot_codetection_data_grid.py` — `--dm-correction-json` / `dm_corrections` plumbing (#129); harmless but its only intended use is now refuted
- `scripts/plot_codetection_triptych.py` — `bands_archival(extra_dedisp_pc=…)` (#129)
- `repro_manifest.csv` — stale "PRODUCER NOT YET IN PIN" caveat for `dm_subband_tilt` corrected (FLITS #185 merged `f9d7dfe`, ancestor of pin `17d9d266`) (#128)

## Reproducibility & Data State

- **Environment:** `uv run --project pipeline --frozen` (pipeline submodule pin `17d9d266` = FLITS #192 merge)
- **Seeds:** sharpness-scan and onset tests use seed 20260707
- **Data:** archival products `~/Data/Faber2026/dsa110/DSA_bursts/*_cntr_bpc.npy` (hash-pinned in `pipeline/data-manifest.csv`); CHIME extracted metadata `~/Data/Faber2026/dsa110/upchan_codetections/*_time0_metadata.json`; raw DSA filterbanks on `iacobus:` (ssh reachable)
- **DM diagnostics archive:** the original power-vs-DM diagnostic panels live in `~/Data/Faber2026/results-library/dispersion/dm-joint-phase-v2/diagnostics/` (results-library Phase B, commit `c8e5639b`); curve data is committed in `analysis/dm-joint-phase-v2/results/fits.json` and regenerable via `python -m scripts.render_joint_dm_diagnostics` from `analysis/dm-joint-phase-v2/code/`

## Verification State / Known-Broken

- **Tests:** `make test-science` green at every merge (last: 146 passed, 1 documented xfail); figure approval gate ok
- **Uncommitted (primary checkout):** shared journal/board files (`docs/rse/journal.jsonl`, `docs/rse/board/readiness.html`) plus six untracked spec docs (repository-cleanup lane × 5, Pandhi draft × 1). Primary checkout is on `ms/results-registry` — another active lane owns it; do not reset or switch it
- **Unverified:** none in this lane; the dmcorr refutation itself is triple-sourced (catalog σ=0.005, onset test, peak-scan gradient)

## Learnings

- **Marker-dependence is the DM-error discriminant.** On scattered bursts every intensity-timing marker lags with τ(ν): centroid ≫ peak > onset. A real dedispersion error is marker-independent. isha/phineas CHIME: phase-coherence 0.000±0.005, onset +0.14/+0.16±0.08, peak-sharpness +0.38/+0.30 — a gradient, therefore scattering, not DM. The adopted-DM catalog (`analysis/dm-joint-phase-v2/manuscript_dm_catalog.csv`) outranks any display-level estimator. Memory: `dm-drift-verdicts-need-marker-dependence.md`
- **Merge races are real here.** PR #121 was merged from a snapshot minutes older than a concurrent push to its branch; the pushed commits were silently stranded. After pushing to a PR branch someone else may merge, re-verify content actually reached main (`git show origin/main:<file> | grep …`), not just PR state
- **rtk mangles binary output.** `rtk git show <rev>:<file.pdf> > out` corrupts binaries — use `RTK_DISABLED=1 git show` for byte-exact extraction (same for patch generation: `rtk git diff` output is summarized, not applicable)
- **`--theirs` during cherry-pick takes the whole file** — re-resolve against the target branch's version when the conflict is one hunk (this nearly reverted #127's repro-manifest suppressions)
- **This repo's fig-review evidence pattern:** audit JSONs are attached to batch manifests post-hoc with `source_revision` = the commit whose script generated them (two-commit pattern: code first, then evidence pinned to it)

## Action Items & Next Steps

1. [ ] **Owner:** decide the fig1 candidates —
   `python scripts/figure_review.py decide 2026-07-17-fig1-observed-peak-audit fig1-gallery approved --reviewer "Jakob Faber" --note "…"` and
   `python scripts/figure_review.py decide 2026-07-17-fig1-observed-peak-dmcorr fig1-gallery needs_revision --reviewer "Jakob Faber" --note "refuted: marker-dependence (see provenance/marker-dependence-refutation.json)"`
2. [ ] After approval: promotion PR — `python scripts/figure_review.py promote 2026-07-17-fig1-observed-peak-audit fig1-gallery`, verify caption in `sections/observations.tex:38-57` still matches (its "CHIME correction negligible" sentence is CORRECT — do not add stem-misstatement language, that claim is refuted), `make`, `make test-science`, PR
3. [ ] **Owner:** send the Pandhi transmittal (`docs/rse/specs/draft-message-thread1-pandhi-2026-07-17.md`); Thread 1 Phase 4 Options A/B decision
4. [ ] Optional hygiene: decide whether the six untracked spec docs in the primary checkout should be committed by their owning lanes

**Recommended Next Skill:** none required for step 1 (owner CLI decision); use `ai-research-workflows:validating-implementations` after the promotion PR if a formal validation record is wanted.

## Other Notes

- Reference branch `ms/fig1-dm-drift-closure-20260717` (`001fd81`) is **kept deliberately** — PR #121 comments cite it as provenance. Do not delete as "stale."
- The concurrent-writer environment is active: worktrees for toa-audit, review-prose, dsa-acf-suppress, post-pl-pbf-figure-reconciliation, quarantine, science-gates, scint-joint all exist with live branches; inventory read-only (`git worktree list`, `lane-liveness`) before touching any shared state.
- PR #121's four Codex review threads each carry a reply describing the fix disposition; PR #128/#129/#130/#132 bodies carry the full narrative if the journal is not enough.

---

**Handoff created by AI Assistant on 2026-07-18**
