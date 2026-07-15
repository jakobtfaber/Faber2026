# Handoff: P4 exploratory intrinsic-envelope modeling — development & testing phase

---
**Date:** 2026-07-15 06:50 (PDT)
**Author:** AI Assistant (Claude Fable 5, session 01Bm6mdK)
**Status:** Handoff
**Branch:** `main` (Faber2026 at `78b5517`; pipeline pinned at FLITS `563645c`)
**Commit:** post-PR-#74 merge (pin bump carrying the P3′ calibrated + unblinded record)

---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| P3 predeclaration + Gate 0b forecast | ✅ Complete | Frozen spec failed the forecast (1.24σ); block demeaning identified as the killer (PRs #69, #71) |
| P3′ amendment (owner-sanctioned) | ✅ Complete | No demeaning, k≥11 envelope cut, null-mean-subtracted z (PR #72) |
| P3′ estimator + blinded G1″/G2″ calibration | ✅ Complete | **First passing blinded calibration of the campaign** (FLITS #181, pin #74) |
| Owner-authorized one-time on-pulse computation | ✅ Complete | z_max = 40.4 pinned at the 400 kHz scan edge; â ≈ 10⁻³ (11× the scintillation ceiling) → intrinsic spectral envelope; **declined as a Δν_d measurement** (fail-closed) |
| **P4 exploratory envelope modeling + subtraction** | 📋 Planned | **Owner-sanctioned 2026-07-15 in-session. This handoff is its implementation plan.** |

**Current Workflow Phase:** Plan (P4 plan below; next phase = predeclare what can still be frozen → Implement)

## Workflow Artifacts

**Experiment records:**
- [experiment-chime-scint-p3-optimal-estimator.md](experiment-chime-scint-p3-optimal-estimator.md) — P3 predeclaration + §Gate 0b result + §P3′ amendment; P4 inherits its discipline where applicable
- P3′ results: pinned pipeline `analysis/chime-scintillation/experiments/p3-optimal-estimator/` — `RESULT.md`, `unblind_onpulse.json` (the full z/â curves from the single permitted on-pulse computation), `frozen_config.json` (sha `0baf4ea2…`), `scan_assets.npz`, gate JSONs, figures
- [experiment-chime-scint-gate0-detectability.md](experiment-chime-scint-gate0-detectability.md) — idealized ceiling; still governs admissibility thinking

**Research/assessment:**
- [research-chime-scint-successor-routes.md](research-chime-scint-successor-routes.md) — the sanctioned route tree P3/P4 descend from
- [handoff-2026-07-15-04-00-p3-optimal-estimator-dev.md](handoff-2026-07-15-04-00-p3-optimal-estimator-dev.md) — prior handoff; its Learnings section still applies

**Decision records:**
- [decision-2026-07-15-p1-scope-fork.md](decision-2026-07-15-p1-scope-fork.md) §Owner amendment — CHIME measurement remains an active paper goal

## Critical References (read these first, in order)

1. Pinned pipeline `analysis/chime-scintillation/experiments/p3-optimal-estimator/RESULT.md` — §One-shot unblinding: what was found in freya's on-pulse spectrum and why it was declined as a measurement. P4 exists to attack exactly this foreground.
2. Pipeline `scintillation/scint_analysis/optimal_dnu.py` — the calibrated matched-scan estimator P4 reuses on residuals (do not rewrite it; wrap it).
3. Pipeline `analysis/chime-scintillation/experiments/p3-optimal-estimator/p3_calibration.py` — the harness pattern (freeze → calibrate → gates → verdict) P4's harness copies.

## Status honesty — what P4 is and is not

The single permitted blind on-pulse computation has been **spent** (owner-authorized, 2026-07-15). Freya's CHIME on-pulse ratio spectrum has been seen at the aggregate matched-scan level (25-point z and â curves). Therefore:

- **P4 is exploratory by construction.** No P4 result can carry blind-analysis evidential weight; every P4 statement in the manuscript is labeled exploratory/post-hoc.
- **Partial freezing is still real and required.** The sub-band statistics, component-resolved spectra, envelope-model residuals, and all thresholds below have NOT been inspected. Freeze them in a predeclared record (`experiment-chime-scint-p4-envelope-model.md`) BEFORE computing any of them. That is the difference between "exploratory but disciplined" and "fishing."
- **The owner's standing constraints hold:** in-house data only; figures with every substantive step; journal every ≤10 min (`bash scripts/journal-append.sh claude <lane> working|done|blocked|info "..."`); board via `program-state.toml` + `python3 scripts/sync_state.py` only.

## The P4 plan — model the intrinsic envelope, search the residuals

### Why (one paragraph)

P3′ produced a fully calibrated, common-mode-immune matched estimator and then found freya's on-pulse spectrum dominated by broad intrinsic spectral structure: â ≈ 0.8–1.2×10⁻³ at every scan width (implied modulation ~0.6, versus the 0.15–0.17 scintillation prior), z rising monotonically to the 400 kHz scan edge. Any true scintle at the calibrated ceiling ((f_b·m)² ≈ 7×10⁻⁵) is a ≤10 % perturbation on that foreground. P4 asks: can the envelope be modeled and divided out well enough that the residual regains scintillation sensitivity, and does any residual structure pass the physical discriminants (ν⁴ scaling, component correlation, DSA-band consistency)?

### E0 — envelope characterization (first; cheap; mostly already-permitted data)

1. Load the on-pulse ratio spectrum `R(ν)` via `optimal_dnu.split_ratio_fields(..., allow_unblind=True)` — P4 code passes the flag explicitly and every such call site carries a `# P4 exploratory: post-unblinding, owner-sanctioned 2026-07-15` comment.
2. Characterize the envelope: delay power spectrum of `R(ν)` (full k range, no cut), autocorrelation scale(s), amplitude distribution across the band, and its behavior across the two S2 time-split halves (the split cross-power already proved it is time-stable; quantify the half-to-half correlation coefficient).
3. **Profile inspection:** plot freya's on-pulse time profile (samples 250–350) and determine whether it resolves into ≥2 sub-components with per-component S/N sufficient for per-component spectra. This decides whether discriminant E3b is available. (Component structure is currently UNKNOWN — nothing in the campaign has looked at the CHIME-band profile at this resolution.)
4. Deliverables: `e0_envelope.json` + figures (envelope spectrum, delay power, half-to-half stability, profile).

### E1 — envelope models (three families, all predeclared)

All models are fit to `R(ν)` and produce a residual `r(ν) = R(ν)/E(ν) − 1` (multiplicative, matching the signal model — scintillation multiplies the envelope):

- **M1 spline:** cubic smoothing spline in ν with knot spacing Λ swept over the frozen grid `Λ ∈ {0.5, 1, 2, 5, 10} MHz`.
- **M2 Gaussian process:** squared-exponential kernel, length scale ℓ on the same grid, fit by marginal likelihood on the off-pulse-calibrated noise level.
- **M3 delay-domain high-pass:** zero delay bins `k < k_env` and inverse-transform; `k_env` swept over `{25, 50, 100, 200}` (structure smoother than ~5.6, 2.8, 1.4, 0.7 MHz removed respectively).

The smoothing scale is the central trade-off: too little removes nothing; too much absorbs the scintle itself. E2 measures both sides of that trade; the operating point per model is chosen by a **frozen rule** (max injected-recovery significance at Δν_d = 213 kHz subject to false-structure control, below) — never by looking at the real residual first.

### E2 — injection calibration on the real envelope (the heart of P4)

Because the on-pulse data may now be read, injections can ride the *real* envelope:

1. **Recovery arm:** multiply the real on-pulse frames by synthetic scintle gains `(1 + m·δ(ν))` (grid: `m ∈ {0.15, 0.17}`, `Δν_d ∈ {77, 127, 213, 352} kHz`, 50 realizations, seed base `600000 + 1000·cell + r`), run model→subtract→matched scan (templates REBUILT through the same model+subtract chain — see Learnings item 1), and certify recovery: median width within ±30 %, amplitude within the pull gate, per cell and per model/Λ.
2. **False-structure arm (control):** run the identical chain on the real on-pulse data with NO injection, over model/Λ, plus on 100 off-pulse nulls (seed base `650000 + i`) to separate envelope-subtraction artifacts from radiometer noise. The post-subtraction null distribution defines the **confusion floor**; the frozen certification requires the no-injection real-data residual z to be interpretable against it.
3. **Operating-point freeze:** per model family, the (Λ or k_env) maximizing certified recovery at 213 kHz subject to the false-structure control passing. Written into `frozen_config.json` before E3 runs.

**Fail branch (frozen):** if no model/Λ certifies recovery at any `Δν_d ≥ 127 kHz` while controlling false structure, P4 closes as `DOCUMENTED-FAIL (envelope not separable)` — itself the quantitative closure statement for the manuscript.

### E3 — physical discriminants (frozen thresholds BEFORE computation)

Any residual structure surviving E2's operating point must then pass:

- **E3a sub-band scaling:** split 627–800 MHz into 4 equal sub-bands; measure residual matched-scan width per sub-band; fit `Δν_d(ν) ∝ ν^α`. Scintillation-consistency band frozen at `α ∈ [3, 5]`; intrinsic structure expected `α ≈ 0`. Power caveat (record it): per-sub-band sensitivity is ~2× worse than full-band, so this discriminates only if the residual is strong (full-band z ≳ 10).
- **E3b component correlation (only if E0 finds ≥2 components):** per-component residual spectra; Pearson correlation between components; null distribution from off-pulse split pairs. Scintillation → correlated (frozen: r above the null 95th percentile); intrinsic → may decorrelate (informative either way).
- **E3c DSA-band consistency:** a scintillation candidate's width must be consistent with the DSA-band measurement extrapolated by `ν^4.4` within a factor of 3 (frozen). Inconsistent → reported as structure, not propagation.

### Verdict taxonomy (frozen; all exploratory-labeled)

1. **Exploratory scintillation candidate** — residual passes E2 certification + E3a + E3c (E3b if available): reported with full post-hoc caveats; never upgraded to a blind-equivalent claim.
2. **Exploratory upper limit** — no residual above the post-subtraction confusion floor: quantified sensitivity from E2, replacing P3′'s unquantified envelope-censoring.
3. **DOCUMENTED-FAIL (envelope not separable)** — E2 fail branch.

## Infrastructure / execution details

- **Repo:** FLITS, branch `scint/p4-envelope-model` off main `563645c`. Worktree: `git -C ~/Developer/scratch/worktrees/flits-p1-window-upchan worktree add ~/Developer/scratch/worktrees/flits-p4-envelope-model -b scint/p4-envelope-model origin/main` (never work on another lane's checkout; the in-repo `pipeline/` submodule checkout is a preserved separate lane on `scint/c1-allpairs-crossgp`).
- **Code:** new `scintillation/scint_analysis/envelope_model.py` (M1/M2/M3 + residual construction) + unit tests; harness `analysis/chime-scintillation/experiments/p4-envelope-model/p4_calibration.py` mirroring `p3_calibration.py` (`freeze → e0 → e2 → e3 → verdict`). Reuse `optimal_dnu.MatchedScan` — rebuild templates through the model+subtract chain per operating point.
- **Data:** same pinned npy set `~/Data/Faber2026/dsa110/upchan_codetections/crossacf-2026-07-14/` (SHA-256s in P3′ `frozen_config.json.inputs_sha256`, matching pipeline `DATA_MANIFEST.yaml`). h17 not needed.
- **Runtime:** conda `py312` (`/opt/anaconda3/bin/conda run -n py312 python …`). E2 ≈ 400 injections × (fit + scan) — M1/M3 are fast; M2 (GP on 19 465 channels) needs care: use a sparse/binned GP or fit on 4× decimated grid; budget ~30–60 min total.
- **Seeds (disjoint from every prior space):** E2 injections `600000 + 1000·cell + r`; E2/E0 nulls `650000 + i`. Prior spaces to avoid: `1000·cell+r` (G1), `8000+r` (Gate 0b check), `700000+…` (Gate 0b templates), `750000+…` (scan templates), `900000–900199` (P2/P3 nulls), `5000000+` (tbattery).
- **Landing:** predeclaration PR to Faber2026 FIRST (record + new lane), then FLITS PR (`gh pr create --repo jakobtfaber/dsa110-FLITS` — the `upstream` remote otherwise hijacks resolution), then ancestor-checked gitlink-only pin bump (`git update-index --cacheinfo 160000,<sha>,pipeline`; pattern: PRs #50/#65/#74).
- **Control system:** every lane needs a GitHub issue (`--check` RULE); `pr` field carries a merged PR only on terminal lanes; regenerate views with `python3 scripts/sync_state.py` + `bash scripts/board-refresh.sh`; never hand-edit generated files.

## Reproducibility & Data State

- **Environment:** conda `py312` (numpy 2.4, scipy 1.17, matplotlib 3.10); no lockfile — record versions in the P4 RESULT.
- **Data:** pinned npys above; freya only (the twelve-burst sample-wide question is explicitly deferred until P4 resolves).
- **Partial results directly reusable:** P3′ `scan_assets.npz` (templates + calibration-null variance — valid only for the NO-subtraction chain; P4 must rebuild per operating point), `unblind_onpulse.json` (the aggregate curves already seen), P2/P3 null machinery.
- **In-flight jobs:** none. All background tasks from this session completed; Faber2026 main and FLITS main both green and deployed.

## Verification State / Known-Broken

- **Faber2026 main `78b5517`:** clean; PRs #69–#74 merged; live `--check` PASSED; board deployed (https://jakobtfaber.github.io/Faber2026/board/).
- **FLITS main `563645c`:** P3′ record complete; 18/18 relevant tests pass (`test_optimal_dnu.py` + `test_routeb_voltage.py`).
- **Known quirks, not broken:** P3′ T2 recorded a **+12 % amplitude bias** in the matched estimator (signal-noise coupling of the ratio) — P4's E2 inherits and re-measures it through the subtraction chain; P3′ nulls carry a ~1σ positive mean offset — always null-mean-subtract.
- **Preserved separate lanes (do not touch):** in-repo `pipeline/` checkout on `scint/c1-allpairs-crossgp` [dirty b4 figures], `.devin/`, untracked `docs/rse/specs/research-chime-scint-instrumental-common-mode.md` (codex lane; its "Origin" section is stale — P1 refuted FFT-leakage origin — amend when its owner lands it).

## Learnings (non-obvious, will bite you otherwise)

1. **Every filter's transfer must live inside the Monte-Carlo templates.** Block demeaning silently destroyed P3's window because the template didn't carry it; Gate 0b caught it only because the templates were built through the real chain. P4's envelope subtraction is a much stronger filter — rebuild `T(k)` through model+subtract for EVERY model/Λ operating point, never reuse P3′ templates for residual scans.
2. **The envelope is time-stable and polarization-common** — it survives the S2 split cross and the pol mean exactly like a scintle. Nothing in the P2/P3 statistic family can reject it; only modeling (P4) or physical discriminants (E3) can.
3. **Amplitude admissibility is as important as width admissibility.** P3′'s unblinding formally satisfied the literal G3 rules (z ≥ 5, width ≥ 77 kHz) and was still correctly declined because â was 11× the physical ceiling. P4's record should carry an explicit amplitude-admissibility clause from the start.
4. **`gh pr merge` can silently no-op** (prints the `--auto` hint, exits 0) when the base moved — always verify `state == MERGED` afterward; PR #71 was "merged" twice because of this.
5. **PNG/npz/log are globally gitignored in FLITS** — `git add -f` experiment figures and assets (P2 precedent), or the record lands without its evidence.
6. **Journal states are `working|done|blocked|info`** (not `active`); invoke as `bash scripts/journal-append.sh`.
7. **RTK prefixes:** use `rtk git`/`rtk grep`/`rtk ls`; `RTK_DISABLED=1` only when rtk can't express the command.

## Action Items & Next Steps (priority order)

1. [ ] **Write and land the P4 predeclaration** `experiment-chime-scint-p4-envelope-model.md`: freeze E1 model families + Λ grids, E2 grids/seeds/certification + the operating-point rule + fail branch, E3a/b/c thresholds (α ∈ [3,5], component-correlation null rule, DSA ν^4.4 factor-3), verdict taxonomy, amplitude-admissibility clause. File the lane issue, add lane `chime-p4-envelope-model` to `program-state.toml`, PR to Faber2026.
2. [ ] **Create the FLITS worktree/branch** `scint/p4-envelope-model` off `563645c`.
3. [ ] **E0** envelope characterization + profile/component inspection; figures; journal.
4. [ ] **Implement** `envelope_model.py` (M1/M2/M3) + unit tests (model recovers synthetic smooth envelopes; residual preserves injected scintles at machine precision when Λ ≫ scintle scale; blinding-flag call sites labeled).
5. [ ] **E2** injection calibration + false-structure control; freeze operating points; figures. If the fail branch triggers, stop and report — that is a complete P4 outcome.
6. [ ] **E3** discriminants on the surviving residual; verdict per the frozen taxonomy.
7. [ ] **Land:** FLITS PR → merge → pin bump → lane/board closeout → owner review of the exploratory verdict and the manuscript wording (which remained deliberately unratified when the owner chose P4 over immediate closure).

**Recommended Next Skill:** `ai-research-workflows:implementing-plans` against this handoff's "The P4 plan" section (the owner sanction is already given; step 1's predeclaration is part of implementation, not a gate on it).

## Other Notes

- P4 is freya-only. Whether to run P3′/P4 sample-wide across the other eleven co-detections is a separate owner decision after P4 resolves.
- Honest framing for expectations: P4's most likely scientific product is verdict 2 (exploratory upper limit with quantified post-subtraction sensitivity) or 3 (envelope not separable). Verdict 1 additionally requires passing ν⁴ scaling with the power caveat noted in E3a. All three close the CHIME question quantitatively; none reopens a blind claim.

---

**Handoff created by AI Assistant on 2026-07-15**
