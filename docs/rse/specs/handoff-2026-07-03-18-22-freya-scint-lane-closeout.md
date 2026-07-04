# Handoff: freya scintillation lane closeout (#117 review/merge + #118 fit-quality fixes)

---
**Date:** 2026-07-03 18:22
**Author:** AI Assistant
**Status:** Handoff
**Branch:** `main` (Faber2026 `43b5596`, in sync with origin) · dsa110-FLITS `main` at `9ebe02cf`
**Commit:** Faber2026 `43b5596` · FLITS `9ebe02cf` · pipeline pin `bffd875` (intentionally behind FLITS main — see Other Notes)

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| Track `.agents/` agent-orchestration lane in Faber2026 | ✅ Complete | `0a5f8ed`, 12 md files, secret-scan clean (one `ta**sk-1**1` false positive) |
| PR #117 (freya scintillation CLI, Codex-session authored) adversarial review | ✅ Complete | Round 1 REQUEST_CHANGES at `ab58fd43`; 3 of 5 findings fixed by the coordinating Codex session (`8276051`/`36ab454`/`bffd875`) before the round completed; verdict posted on PR |
| PR #117 merge | ✅ Complete (by coordinating session) | Fast-forward at `bffd875` after its own round-4 re-review; pin `44d081a` → `bffd875` resolves; remote branch deleted by this session |
| Issue #118 (surviving findings 3–5) | ✅ Complete | Filed by this session, then implemented same-day |
| PR #119 (#118 fixes: fail-closed fit contract + baseline-guard parity + tests) | ✅ Complete | Codex round-1 **APPROVE zero P1/P2**; two P3 test nits fixed in `9f07662`; merged squash `9ebe02cf` (owner-authorized), CI 4/4, issue auto-closed |
| Post-merge closeout | ✅ Complete | Worktree/branches removed, canonical clone at `9ebe02cf`, ledger union-merged, summary doc `implement-freya-scint-fit-quality.md` pushed |
| Real-data freya scintillation run | 📋 Planned | Blocked on `scintillation/data/freya.npz` staging (see Next Steps) |

**Current Workflow Phase:** Validate (code merged; real-data validation pending)

## Workflow Artifacts

**Implementation Summaries:**
- [implement-freya-scint-fit-quality.md](implement-freya-scint-fit-quality.md) — #118 lane (this session); merge record `9ebe02cf`
- [implement-freya-beta-verdict.md](implement-freya-beta-verdict.md) — #106, closing node of the β co-model DAG (grade PASS, provisional-citable TRUE)
- [implement-freya-production-joint-fit.md](implement-freya-production-joint-fit.md) — #104 production numbers the manuscript will cite

**Plan/PRD:**
- [prd-freya-beta-comodel-real-data-fit.md](prd-freya-beta-comodel-real-data-fit.md) — the β co-model DAG PRD (all 8 nodes complete as of this session)

**External provenance:** dsa110-FLITS issues #117/#118, PRs #117/#119 (review verdicts as PR comments); Codex-session handoff (temp file, may be gone): `/var/folders/.../T/faber2026-freya-scintillation-handoff.md` — its durable content is captured in PR #117's description and this doc.

## Critical References

- `pipeline/scintillation/scint_analysis/freya_scintillation.py` — the freya scintillation CLI; fit-quality contract lives in `measure_scintillation_bandwidth` (fail-closed branches after `curve_fit`) and `prepare_spectrum_from_config` (>50-bin baseline guard)
- [implement-freya-scint-fit-quality.md](implement-freya-scint-fit-quality.md) — full #118 lane record incl. caveats
- `CONTEXT.md` (repo root) — domain-language contract; read before any manuscript prose motion

## Recent Changes

- `scintillation/scint_analysis/freya_scintillation.py` (FLITS `9ebe02cf`): fail-closed returns for non-finite `pcov` and γ within 1% (`_GAMMA_BOUND_REL_TOL`) of either bound (0.25×channel_width lower / `fit_lag_mhz` upper); `_failed_fit_result(..., acf_model=...)` retains the attempted-fit curve for figures; baseline guard `+2` → `+50` bins with skip-warning (parity with `pipeline.py:178`)
- `scintillation/scint_analysis/tests/test_freya_scintillation.py`: +6 tests (known-width recovery ≤2%, both bound rails, non-finite covariance, guard edges {30,50→skip; 51,90→subtract})
- Faber2026: `.agents/` tracked (`0a5f8ed`); `44d081a` pin bump → `bffd875` (authored by coordinating Codex session); summary docs `30fc9be`/`43b5596`

## Reproducibility & Data State

- **Environment:** conda `flits` env; it editable-installs the **canonical clone** (`~/Developer/repos/github.com/jakobtfaber/dsa110-FLITS`, now at `9ebe02cf`) — run from inside `pipeline/` to get pinned (`bffd875`) code instead; print `module.__file__` when in doubt
- **Seeds:** new tests use fixed rngs (41 for crafted ACF; 17/23 in pre-existing synthetic helpers) — fully deterministic
- **Data:** raw freya waterfalls ARE local (verified 2026-07-03): `~/Data/Faber2026/dsa110/DSA_bursts/freya_dsa_I_912_4_2500b_cntr_bpc.npy` (117 MB) and `freya_chime_I_912_4067_32000b_cntr_bpc.npy` (125 MB). What's missing is only the scintillation-format conversion — an `.npz` with `power_2d`/`frequencies_mhz`/`times_s` keys (`DynamicSpectrum.from_numpy_file` contract); precedent: `~/Data/Faber2026/dsa110/scintillation-data/casey_chime{,_hi}.npz`.
- **Upchannelized CHIME product: DONE (2026-07-03, owner-requested).** freya added to `h17:.../scripts/upchannelize_chime.py` TARGETS (id 278720455, DM 912.4, **U=64**) and run in the `chimefrb/baseband-analysis` docker image (coherent dedisp + PFB `_upchannel`). Products at `h17:.../upchan_codetections/freya_chime_{upchan,freq}.npy` AND local `~/Data/Faber2026/dsa110/upchan_codetections/` (md5-verified: upchan `c5c958c7…`, freq `ad0ddb20…`). Shape (57024, 437), df = 6.1036 kHz, 400.2–799.8 MHz, 92% finite, dt = 0.328 ms; burst detected at z=8.6 (600–800 MHz band sum), ~13–23 bins >5σ around bin ~250, fading toward 400 MHz as the steep scattering predicts. **U=64 sizing rationale** (recorded in the target's `note`): NE2025 MW floor 1.6421 MHz @1.405 GHz → ~38.8 kHz @600 MHz (ν^-4.4, census convention: `analysis/scattering-refit-2026-06/scint_census/scint_mw_models.py`, C1=1.16) → 6.4 fine channels across it (≥4 rule). Time wall: intrinsic FWHM 0.401 ms gives only 1.2 elements at dt=0.328 ms, justified by the scattering-broadened CHIME profile (τ(600 MHz)≈1.07 ms per the #104 β co-model fit → ≥3 observed elements) — this is a *config assumption riding on a current-model result*. The contested ~0.51 MHz DSA sub-floor candidate (~10 kHz @600 MHz) is NOT resolvable at any U inside the time wall.
- **In-flight jobs:** none

## Verification State / Known-Broken

- **Tests:** FLITS scint suite green at merge (focused 14 passed; suite 107 passed at `751acb69`, +3 parametrized at `9f07662`); PR #119 CI 4/4
- **Uncommitted / unpushed:** none anywhere except `docs/entire-tracing-checkpoints.md` dirty in the canonical FLITS clone — **conventionally rides dirty on main** (hook-appended ledger; union-merge on pull via scratchpad `ledger_union.py`, session-local)
- **Unverified:** the scintillation CLI has never run on real freya data (synthetic-only validation); mixed `scint_analysis.*` vs `scintillation.scint_analysis.*` import pattern hit a Numba cache load failure once in the #117 r4 review sandbox — pre-existing, unchecked in the installed runtime
- **Epistemic status of Δν_d (CHIME side, updated after E1–E4):** best current value Δν_d ≈ 45–68 kHz @700 MHz on the gapless grid (44.7 ± 7.9 kHz stat at the default fit window; fit-window systematic dominates) — a *current-model result from experiment code*, NOT citable until the gapless regrid + modulation_index fix land as production pipeline code, the branch merges, and the real freya redshift replaces the z=1.0000 placeholder. DSA-side Δν_d: no measured value exists yet.

## Learnings

- **A parallel Codex session actively works these repos under the same user identity.** This session twice collided with it mid-flight: (1) an unpushed pin bump referencing a commit absent from the remote (fixed by publishing `ab58fd43` as a branch); (2) it pushed fix commits, re-reviewed (r4), fast-forward-merged #117, and pushed the pin bump `44d081a` itself while this session's review was running. Before any push/merge in these repos: re-check `git status`/`ls-remote`/PR state immediately beforehand, and `procs codex` to see if the peer is live.
- **Fast-forward vs squash matters for the submodule pin:** #117 was ff-merged precisely so the pinned SHA (`bffd875`) stayed reachable; #119 could be squashed because nothing pins its SHAs.
- Codex read-only review sandboxes can't run pytest (no writable tmp for matplotlib/dill/Numba caches) — reviewers fall back to direct source import; treat "could not collect" as environmental, not a red flag.
- `verify-gate` Stop hook fires on worktree edits under `~/Developer/scratch/worktrees/`; record `test`/`cross-check` methods with concrete evidence strings to clear it.
- rtk secret-scan regexes: `sk-` matches inside "task-11" — check matches before treating as a finding.

## Action Items & Next Steps

1. [ ] **Convert + first real run (DSA side is unblocked):** build `freya.npz` (`power_2d`/`frequencies_mhz`/`times_s`, mirroring `scintillation-data/casey_chime.npz`) from `~/Data/Faber2026/dsa110/DSA_bursts/freya_dsa_I_912_4_2500b_cntr_bpc.npy` + the freya_dsa frequency/time axes (freya_dsa_run.yaml in `~/Data/Faber2026/dsa110/flits-runs/configs/` records them); place it where `freya_dsa.yaml`'s `input_data_path` points; then `conda run -n flits python -m scintillation.scint_analysis.freya_scintillation scintillation/configs/bursts/freya_dsa.yaml --out scintillation/plots/freya` and **inspect the three figures before citing any number** (dynamic spectrum+window, ACF+fit, structure function). Mind frequency resolution: scintillation needs the finest available channelization, not the fit-downsampled product
2. [x] ~~If CHIME scintillation is wanted: add freya to the h17 upchannelization target list and generate the products~~ — **done 2026-07-03** (U=64; see Reproducibility & Data State). Untracked-h17-edit risk closed: verbatim snapshot + `PROVENANCE.md` (Codex-authored) live in `~/Data/Faber2026/dsa110/upchan_codetections/` (snapshot md5 `9f7db7c0…` = live h17 copy).
   **CHIME-side first-look run also done (2026-07-03, Codex agent, worktree `flits-chime-scint`):** npz pair `freya_chime{,_hi}.npz` built in `~/Data/Faber2026/dsa110/scintillation-data/` (casey storage convention, loader-verified: burst at bin 257, 600–800 MHz correct); configs on branch `feat/freya-chime-scint-config` (commit `5d1fbd67`, pushed; now part of **PR #121** — see below). Result JSON (600–800 MHz crop): `success=true`, Δν_d = 0.0468 ± 0.0139 MHz, structure cross-check 0.083 MHz, mod index 3.68; full band consistent (0.0451 ± 0.0122).
   **⚠ FAILS figure inspection — not citable:** the ACF is dominated by a large periodic ripple at ~0.39–0.5 MHz ≈ the CHIME coarse-channel spacing (0.390625 MHz) — residual PFB coarse-channel bandpass scallop the constant-baseline Lorentzian cannot absorb; heavy RFI speckle survives masking (620–630, 725–760 MHz); modulation index 3.68 ≫ 1 confirms non-scintillation spectral power. The 47 kHz spike may be real MW scintillation (floor prediction ~39 kHz @600 / ~76 kHz @700) but cannot be separated from intra-coarse-channel structure yet. The #118 fail-closed contract passed because the fit converged in-bounds — bandpass ripple is exactly the failure mode only figure inspection catches.
   **Pass 2 (2026-07-03/04, Claude subagent, same branch, commits `40fdb1f5` + `41816c7d`, pushed):** flag-gated per-fine-channel off-pulse flat-fielding added to `freya_scintillation.py` (`normalize_bandpass()` at :370; default off; fail-loud <50-bin off-window guard; non-positive/non-finite/gain-starved channels masked, not divided; applied BEFORE baseline logic) + `freya_chime_hi.yaml` RFI tightening. Two agent deviations, both justified and documented in the config: **time-domain flagging kept OFF** (enabling it robust-z-masks the burst itself — bins 244–268 are the largest time-domain outliers; verified "spectrum contains no finite samples") with freq_threshold_sigma 5.0→3.0 instead (~14% channels masked, burst band preserved); **baseline_subtraction disabled** (flat-fielding removes the full multiplicative bandpass; an order-1 poly can't follow the scallop and running both depresses the on-pulse mean). Tests 14 → **17 passed**, ruff clean (independently re-run by orchestrator). Result (`plots/freya_chime_pass2/`): `success=true`, **Δν_d = 0.0496 ± 0.0090 MHz** (consistent with pass 1, tighter), **modulation index 3.68 → 0.187** — pass-1's spectral power was overwhelmingly static bandpass structure, now removed. ACF figure (orchestrator-inspected): zero-lag spike normalized correctly, narrow ~50 kHz central component now clearly separated; residual ~0.5 MHz ripple down ~30× (±0.1 about a 0.09 baseline vs ±3.5 about 2.4). Caveats keeping this at *first-look, owner inspection pending*: (a) structure-function cross-check now returns exactly one channel width (7.5 kHz) — the noise-dominated per-channel variance defeats it at m≈0.19, so the 50 kHz value rests on the weighted ACF fit alone; (b) a subdominant periodic ripple persists at **0.497 MHz** (agent-measured; NOT the coarse-channel 0.390625 — origin unidentified; amplitude 0.44× the central component, which is why the agent rightly skipped the optional 0.39 MHz cosine term); (c) m≈0.19 ≪ 1 wants a quenching interpretation (two-screen geometry) before the number enters any budget; (d) **channel-grid systematic (agent-surfaced, unresolved):** the hi npz is 26,528 channels — not the 32,768 a gapless 600–800 crop would give — so the band has missing-coarse-channel gaps, and `DynamicSpectrum.channel_width_mhz` = mean(diff) = 7.532 kHz vs the native fine spacing 6.1036 kHz. If `calculate_acf` labels lags with the mean spacing over a gapped grid, the lag axis (hence Δν_d) could be overstated by up to ~23% (49.6 → ~40 kHz). Next pass must check gap handling before the number is quoted. Comparison: NE2025 MW floor ~55–76 kHz at 650–700 MHz vs measured 49.6 ± 9.0 — same scale, slightly below.
   **Experiment pass E1–E4 (2026-07-03, orchestrator, `running-experiments` skill) — all four pass-2 caveats resolved or bounded.** Full doc: `docs/rse/specs/experiment-freya-chime-dnu-science-readiness.md`; archived code+data: `~/Data/Faber2026/dsa110/scintillation-data/exp-dnu-2026-07-03/`. (E1/caveat d CONFIRMED) the gapped grid stretches the lag axis 1.2340× and gap-straddling index lags mix distant channels — a gapless NaN-filled regrid at native 6.1035 kHz is the correct fix (naive ÷1.234 is not equivalent: 40.2 vs 44.7 kHz). (E2/caveat b RESOLVED) the "0.497 MHz" ripple relocated to **0.4024 MHz** on the physical axis — grid-locked instrumental structure, ≈ the coarse spacing but 3% high (origin still open; survives flat-fielding → burst-locked PFB leakage hypothesis). (E3 PASSED) half-band ratio **1.95 ± 0.48 vs ν^4.4 prediction 1.88** (achromatic/instrumental 1.00 rejected ~2σ); time halves consistent. (E4/caveat c RESOLVED as reporting bug) reported m=0.187 is std/mean without off-subtraction; physical **m_burst = √(ACF amp 0.266) ≈ 0.52**; two-screen coherence permissive at any plausible z (limit 1426.8 kpc² at PLACEHOLDER z=1). **Current best (still not citable): Δν_d ≈ 45–68 kHz @700 MHz** — gapless 44.7 ± 7.9 kHz (stat) with a dominant fit-window systematic (57.2 ± 2.8 @0.3 MHz window, 67.7 ± 3.8 @0.2 with ripple excluded); half-bands 40.5 ± 8.7 @650 / 78.9 ± 9.9 @750. Citability gates: durable production fix (regrid in pipeline code + modulation_index fix + ripple handling — owner-gated new lane), real freya redshift, branch merge + pin bump.
   **Durable-fix lane OPENED and implemented (2026-07-04, owner-approved): issue #120 → PR #121** (whole branch `feat/freya-chime-scint-config` → main; nothing pins its SHAs, squash OK). Commits `8a91cf0a` (regularize_frequency_grid + modulation_index_acf + fit-window scan; oracle: production regularized run on the ORIGINAL gapped npz reproduces the experiment gapless result to 1.5e-5 — 44.7270 vs 44.7263 kHz, m_acf 0.516), `7665f1d5` (Codex r1 major: subband pipeline shared gating via apply_grid_regularization + _apply_bandpass_normalization; m_acf None without off-level; non-finite scan guard), `79ceb8b0` (Codex r2 P1: cache keys fingerprinted with sha256[:12] of input+downsample+analysis config — stale-reuse scenario pinned by test). Review saga: Codex r1 REQUEST-CHANGES → r2 REQUEST-CHANGES → **r3 APPROVE (no findings)**. Tests 17 → 34 (file), full scint suite 130 passed; CI Python 3.12 pass. **MERGED 2026-07-04 (owner-approved): squash `2931e1bf`**, issue #120 closed, remote+local branch deleted, worktree removed (tree-identity proven), run figures archived to `~/Data/Faber2026/dsa110/scintillation-data/freya-chime-runs-2026-07/`. Canonical clone left on main @ `9ebe02cf` (behind `2931e1bf`; pull deferred — entire-tracing ledger convention). Implement summary: `implement-freya-chime-dnu-durable-fix.md`. Follow-up noted on PR: pre-existing F401 `pipeline.py:345` (CI runs pytest only).
   **⚠ DEDISPERSION DEFECT (2026-07-04, owner-spotted, post-merge): the upchan product was never coherently dedispersed.** The h17 script discarded `coherent_dedisp`'s return value (function copies + returns; writes back only with `write=True`) and upchannelized the raw baseband. Proof: coarse-block-folded sawtooth at full intra-channel-smear magnitude (10.7 ms @650 / 7.0 @750), natural-dispersion sign; `tiedbeam_baseband` has no `DM_coherent` attr while `tiedbeam_power` has 912.4699. **The 0.40 MHz E2 ripple = window-clipped sawtooth — explained, not PFB leakage.** All measured CHIME Δν_d values (44.7 ± 7.9 etc.) DEPRECATED pending product regeneration on h17 (one-line fix: feed `coherent_dedisp`'s return into `_upchannel`, or `write=True`) → rebuild npz pair → rerun. #120/#121 code (grid regularization etc.) unaffected and still required. Addendum with full evidence: `experiment-freya-chime-dnu-science-readiness.md`.
3. [ ] Install-side Numba cache check for the mixed-import risk (r4 residual): run the console entry `flits-scint-freya --help` and one synthetic pass in the installed `flits` env
4. [ ] Faber2026 pin bump to `9ebe02cf` **only when** the manuscript starts citing scintillation numbers (deliberate `build:` commit per PIPELINE.md)
5. [ ] Manuscript β-table row / prose motion citing `analysis/beta_poc/freya/freya_beta_verdict.json` — owner/Step-6 scope, unchanged from the #106 handoff

**Recommended Next Skill:** `ai-research-workflows:running-experiments` (for action item 1 — the real-data run is an experiment with figure-inspection acceptance); `ai-research-workflows:validating-implementations` fits if the owner instead wants an independent validation pass over the merged #118/#119 contract.

## Other Notes

- **Pin discipline:** `pipeline/` in Faber2026 is pinned at `bffd875` (gitlink from `44d081a`) while FLITS main is at `9ebe02cf` — intentional; do not "fix" by bumping without a `build:` decision. `git submodule update` realigns a drifted checkout.
- `.agents/` is now tracked in Faber2026 (`0a5f8ed`); it documents a separate "Ponytail audit" orchestration lane (pool_utils/copy_yaml/create_dummy_db/burstfit_init refactors) that no session has executed — treat as planned-not-started if encountered.
- Overleaf pulls GitHub main via manual GitHub Sync only; pushes to Faber2026 main are outward-facing.
- oneway-guard sticky window was opened earlier today (8h TTL) — merges/pushes may re-prompt after it expires.

---

**Handoff created by AI Assistant on 2026-07-03**
