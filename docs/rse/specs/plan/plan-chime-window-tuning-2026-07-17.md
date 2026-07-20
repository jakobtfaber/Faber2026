# Plan: CHIME scintillation window tuning + sample-wide bandwidth measurement

**Date:** 2026-07-17
**Lane:** `chime-window-tuning`
**Owner directive:** solve window tuning and measure scintillation bandwidths to the
best accuracy and precision possible across **all 12** CHIME bursts — do not give up
on current non-detections. Current `window_choices.json` entries are provisional
(owner: "not final, they still need tuning"), including casey's hand edit.
**Method constraint (standing):** one uniform estimation methodology for all 12 bursts;
morphology differences become per-burst systematics, never per-burst method choices.
Accept/reject by visual vetting of diagnostic figures, not GoF gates alone.

## Ground truth at plan time

- Machinery from FLITS #191 (`window_tuning.ipynb`, `window_refit.py`,
  `auto_rfi_flag.py`) is on FLITS main `8e54589`; **no superproject pin contains it**
  (origin/main pin `79b7b0e` is on a results-library side branch).
- The batch driver `run_persubband_fits.py`, `window_choices.json`, results JSONL and
  all figures live only in `~/Developer/scratch/` — unlanded, irreproducible from repos.
- Default-window per-subband scoreboard (resolved subbands /4): chromatica 4,
  zach 4 (α=−6.4 unphysical → contaminated), whitney 3 (m≤2.6), isha 2, phineas 2
  (α=−7.6), freya 2 (α=+14.5), casey 2, oran 1 (3 subbands FAIL), mahi/wilhelm/
  hamilton/johndoeII 0 — several with sub-threshold hints.
- **Nondeterminism found (2026-07-17 smoke test):** notebook backend vs batch driver
  disagree (chromatica 517 MHz flips resolved↔unresolved; m offsets ~0.2–0.6) — MC
  noise template in `calculate_acfs_for_subbands` is unseeded. Diagnosis delegated
  (subagent), fix lands before any campaign runs.
- Fit-quality levers currently unused: per-lag ACF errors (`subband_acfs_err`) ignored
  (unweighted `curve_fit`); no finite-scintle error term anywhere; `resolved` flag is
  heuristic; σ_self computed but unused by the per-subband path.
- Data: all 12 `{nick}_chime.npz` + `_hi` variants local under
  `~/Data/Faber2026/dsa110/scintillation-data/` (2.8 GB).
- Work surface: FLITS worktree `~/Developer/scratch/worktrees/flits-window-tuning`,
  branch `scint/window-tuning-campaign` off FLITS main.

## Phases

**P0 — infrastructure (done 2026-07-17):** Faber2026 pulled to `c8e5639b`; submodule
synced to pin; worktree + `flits` env + data symlink verified end-to-end.

**P1 — objective windows (in progress):** `window_optimize.py` — deterministic uniform
rule (MAD-iterated k·σ core around peak; merge multi-component runs within
width-scaled gap; expand edges to k_edge·σ for scattering tails; off = longest clear
stretch behind a width-scaled guard). Scannable thresholds
(k_core ∈ {1.5,2,3} × k_edge ∈ {0.3,0.5,1}) make window choice a measured systematic,
not an aesthetic. Preview figures for all 12 → owner visual vetting.

**P2 — fit upgrades (before any campaign numbers):**
1. Seed / fix MC noise-template nondeterminism (per subagent diagnosis).
2. Weighted Lorentzian fits using `subband_acfs_err`.
3. Finite-scintle fractional error added in quadrature:
   Δγ/γ ≈ [f_filled · N_scint]^(−1/2), N_scint ≈ 1 + η·B_sub/γ (Cordes-style); also
   applied to m.
4. Physicality guards as flags (not silent gates): m>1, γ(ν) falling with ν,
   comb-residual proximity.
5. Reconcile notebook backend ↔ batch driver to byte-identical numbers.

**P3 — excavation of the full sample:**
- Subband ladder run identically on all 12: full-band / 2 / 4 equal-S/N subbands
  (detection scan at fixed criteria; 4-subband remains the α surface).
- `_hi` products for narrow-γ candidates (johndoeII 630 MHz γ≈0.12 hint; mahi).
- Diagnose FAIL subbands (mask coverage, oran high band).
- Censored upper/lower limits from the fitted noise floor where nothing resolves —
  every burst leaves with a number or a bound, no shrugs.
- Window-sensitivity scan (P1 grid × refit) → per-subband γ_sys + stability flag.

**P4 — validation before quoting:** injection-recovery harness (subagent-built,
`~/Developer/scratch/scint-injection-harness/`): known-γ synthetic scintles with
radiometer noise, optional intrinsic-envelope + comb contamination, pushed through
the identical fit path. Acceptance thresholds fixed before unblinding real-sample
updates. Full 12-burst diagnostic figure sets for owner vetting.

**P5 — landing:** FLITS PR (optimizer + campaign driver + upgraded fits + results
artifacts per results-library conventions); Faber2026 pin bump as its own reviewed
PR; manuscript numbers/figures gated on owner ratification. The off-main pin knot
(pin `79b7b0e` vs FLITS main) must be reconciled at pin-bump time.

## Error budget per γ (target shape of the final table)

γ ± σ_fit (weighted curve_fit) ± σ_scintle (finite-scintle) ± σ_win (window-scan
half-spread), with resolved/censored status, m, per-subband; α from resolved
subbands with n≥3 (n=2 flagged provisional, matching #191 semantics).

## Risks

- Envelope contamination (P3′/P4 history): the intrinsic spectral envelope mimics
  broad scintles; the per-subband + physicality-flag approach *bounds* but does not
  remove it. Injection harness quantifies the bias with envelope ON.
- MC-template variance may dominate marginal subbands even after seeding (seeding
  fixes reproducibility, not variance) — n_draws may need raising; measure first.
- Runtime: 12 bursts × ~10 window variants × ladder ≈ hours — background + parallel.
