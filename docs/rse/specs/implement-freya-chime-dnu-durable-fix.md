# Implement: freya CHIME Δν_d durable fix (dsa110-FLITS #120 → PR #121)

---
**Date:** 2026-07-04
**Status:** Complete — merged (squash `2931e1bf`, 2026-07-04T08:46Z); issue #120 closed
**Plan reference:** issue #120 body (experiment-backed brief, following the #103–#106/#118 lane pattern)
**Experiment provenance:** [experiment-freya-chime-dnu-science-readiness.md](experiment-freya-chime-dnu-science-readiness.md); archived code+data `~/Data/Faber2026/dsa110/scintillation-data/exp-dnu-2026-07-03/`

---

## What landed (squash of 6 commits on `feat/freya-chime-scint-config`)

The full freya CHIME scintillation lane: configs + npz conventions
(`5d1fbd67`), flag-gated bandpass flat-fielding (`40fdb1f5`), pass-2 config
(`41816c7d`), and the #120 durable fix (`8a91cf0a` + review fixes `7665f1d5`,
`79ceb8b0`):

1. **`regularize_frequency_grid()`** (`scintillation/scint_analysis/freya_scintillation.py`)
   — re-embeds gapped frequency grids onto the uniform native grid
   (median-diff native step, nearest-grid snap, collision-rejecting,
   NaN/masked fillers). Gated on `analysis.grid_regularization` (default off;
   loud warning when off on a non-uniform grid). Shared gating helper
   `apply_grid_regularization()` is called by BOTH entry points
   (`prepare_spectrum_from_config` and `ScintillationAnalysis.prepare_data`),
   before `downsample`.
2. **`modulation_index_acf`** — physical modulation depth √(fitted zero-lag
   ACF amplitude); populated only when an off-pulse mean was supplied
   (without it the amplitude is floor-diluted). Existing `modulation_index`
   documented as a noise-diluted diagnostic.
3. **Fit-window systematic** — `analysis.fitting.fit_lag_scan_mhz` →
   `fit_window_scan` + `fit_window_systematic_mhz` in the result JSON;
   non-finite scan entries recorded as failed entries.
4. **Pipeline parity + cache safety** — `_apply_bandpass_normalization()` in
   the subband pipeline (after window determination, before baseline
   subtraction, fail-closed on <50-bin off windows); cache pickle keys
   fingerprinted with sha256[:12] of input path + downsample + full
   `analysis` block so preprocessing-flag changes can never reuse stale
   caches.

Configs: `freya_chime_hi.yaml` / `freya_chime.yaml` enable regularization;
hi adds the `[1.0, 0.3, 0.2]` MHz fit-window scan.

## Verification

- Tests 17 → **34** in `test_freya_scintillation.py`; full scintillation
  suite **130 passed**; ruff clean on touched files; CI (Python 3.12) pass.
- **Oracle:** production regularized run on the ORIGINAL gapped
  `freya_chime_hi.npz` reproduces the E1/E2 experiment's independently-built
  gapless-npz result to **1.5×10⁻⁵ relative** (44.7270 vs 44.7263 kHz);
  byte-identical across the r1/r2 refactors.
- **Adversarial review (Codex, gpt-5.5 high):** r1 REQUEST-CHANGES (major:
  subband pipeline silently bypassed the new flags) → fixed `7665f1d5`;
  r2 REQUEST-CHANGES (P1: burst_id-only cache keys reused stale pickles
  across flag changes) → fixed `79ceb8b0`; **r3 APPROVE, no findings**.

## Current best number (post-merge epistemic status)

Δν_d(freya, CHIME 600–800 MHz) ≈ **45–68 kHz @ 700 MHz** — 44.7 ± 7.9 kHz
(stat, 1.0 MHz window) with fit-window systematic 23.0 kHz; half-bands
40.5 ± 8.7 @ 650 / 78.9 ± 9.9 @ 750, ν^4.4-consistent (ratio 1.95 ± 0.48 vs
1.88); physical m_burst ≈ 0.52. *Current-model result; still NOT
manuscript-citable* until: real freya redshift (z = 1.0000 placeholder in
`galaxies/foreground/config.py:46`) and a deliberate Faber2026 pipeline pin
bump (`build:` commit per PIPELINE.md; pin currently `bffd875`, FLITS main
now `2931e1bf`).

## Cleanup / state

- Remote + local branch deleted; worktree
  `~/Developer/scratch/worktrees/flits-chime-scint` removed after proving
  tree-identity with merged main; run figures archived to
  `~/Data/Faber2026/dsa110/scintillation-data/freya-chime-runs-2026-07/`
  (pass1 first-look, full-band, pass2, pass3, pass3b).
- Canonical clone `~/Developer/repos/github.com/jakobtfaber/dsa110-FLITS`
  left on main @ `9ebe02cf` (behind remote `2931e1bf`) — pull deferred
  because of the entire-tracing ledger stash/union convention on that clone.
- Follow-up (noted on PR): pre-existing ruff F401 at `pipeline.py:345`.

## Remaining lane work (unchanged from handoff)

DSA-side scintillation run (freya.npz build), real redshift, 0.4024-vs-
0.390625 MHz ripple-offset origin, pin bump when the manuscript cites
scintillation numbers.
