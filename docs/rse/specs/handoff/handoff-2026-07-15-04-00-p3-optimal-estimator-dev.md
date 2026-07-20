# Handoff: P3 optimal quadratic estimator — development & testing phase

---
**Date:** 2026-07-15 04:00 (PDT)
**Author:** AI Assistant (Claude Fable 5, session 01Bm6mdK)
**Status:** Handoff
**Branch:** `main` (Faber2026; pipeline pinned at FLITS `1085de0`)
**Commit:** post-PR-#65 merge (pin bump); see Verification State for exact tree
---

## Task(s)

| Task | Status | Notes |
|------|--------|-------|
| P1 windowed-upchan record landed on pinned pipeline | ✅ Complete | FLITS #179 + pin PR #50 |
| Hybrid control system (TOML state, generated views, CI drift gate) | ✅ Complete | PR #59; first drift catches already logged |
| Scope-fork amendment + A1 closure, owner-ratified | ✅ Complete | PRs #52, #62; CHIME campaign stays OPEN |
| Gate 0 detectability | ✅ Complete | **GO**, window Δν_d ≳ 77–127 kHz (3σ) / 213–352 kHz (5σ) |
| P2 Route B (ratio statistics, blinded G1/G2) | ✅ Complete | **DOCUMENTED-FAIL** — FLITS #180 + pin PR #65; see Learnings |
| F3 consistency audit | ✅ Complete | Ran in a parallel Devin session, PR #64; findings in `audit-f3-findings.md` |
| **P3 optimal quadratic estimator** | 📋 Planned | **This handoff is its implementation plan. NOT yet owner-sanctioned — see Next Steps 1** |

**Current Workflow Phase:** Plan (P3 plan below is ready; next phase = predeclare → owner sanction → Implement)

## Workflow Artifacts

**Research/assessment:**
- [research-chime-scint-successor-routes.md](../research/research-chime-scint-successor-routes.md) — sanctioned route assessment; Route A (calibrator) DECLINED by owner (no external data requests, in-house only)
- [research-chime-scint-instrumental-common-mode.md](../research/research-chime-scint-instrumental-common-mode.md) — ⚠ still an **untracked file** in `docs/rse/specs/` (codex-authored separate lane); the measured common-mode numbers; its "Origin" section is stale (P1 refuted FFT-leakage origin)

**Experiment records:**
- [experiment-chime-scint-gate0-detectability.md](../experiment/experiment-chime-scint-gate0-detectability.md) — the detectability ceiling P3 must beat; `scripts/gate0_detectability.py`
- [experiment-chime-scint-routeb-voltage.md](../experiment/experiment-chime-scint-routeb-voltage.md) — P2 predeclaration (P3 inherits its discipline verbatim)
- P2 results: pinned pipeline `analysis/chime-scintillation/experiments/p2-routeb-voltage/` (RESULT.md, g1/g2 JSONs, figures, frozen_config sha `cb7b21b7…`)

**Decision records:**
- [decision-2026-07-15-p1-scope-fork.md](../decision/decision-2026-07-15-p1-scope-fork.md) — §Owner amendment (ratified): CHIME measurement stays an active goal

## Critical References (read these first, in order)

1. Pinned pipeline `analysis/chime-scintillation/experiments/p2-routeb-voltage/RESULT.md` — what P2 proved and where it failed; P3 exists to close exactly that gap.
2. Pipeline `scintillation/scint_analysis/routeb_voltage.py` — the S1/S2 ratio-spectrum construction and the structural blinding guard (`ON_PULSE_GUARD=(250,350)`, `BlindingError`, `allow_unblind` flag). **P3 reuses this file's spectrum construction unchanged**; only the statistic downstream of the ratio spectra changes.
3. [experiment-chime-scint-gate0-detectability.md](../experiment/experiment-chime-scint-gate0-detectability.md) — the SNR ceiling formula and the admissibility window that P3's G3 gate inherits.

## The P3 plan — optimal quadratic estimator

### Why (one paragraph)

P2 proved the on/off ratio cancels the 35 kHz common mode algebraically on real data (G2: 0/24 nulls, amplitude 0.586 → ≲0.006, ~100× suppression) but its lag-space cross-ACF + Lorentzian curve-fit cannot recover any injected width at the real effective modulation `f_b·m ≈ 0.0075–0.0085` (G1: 0/6 detectable cells; recovered widths pin at 20–45 kHz regardless of injection; needs ~6× more signal, `s_eff ≳ 0.05`). Gate 0's GO (SNR 5–6.85 at Δν_d ≥ 213 kHz) was priced for the *optimal quadratic estimator*. P3 = build that estimator on the P2-validated ratio spectra. It is the last in-house move; its outcomes are a broad-scintle detection, or a clean radiometer-limited exclusion for the manuscript.

### Estimator specification

Work in the **delay (spectral-Fourier) domain** — mathematically equivalent to the direct quadratic estimator for stationary noise, and O(N log N) instead of O(N²) with a 23 064² covariance:

1. **Inputs:** the two split ratio spectra `r₁(ν), r₂(ν)` from P2's S2 construction (disjoint on/off time halves ⇒ independent noise between splits), high band, block-demeaned within 64-channel coarse blocks exactly as in `routeb_voltage.py`.
2. **Transform:** per coarse block (or tapered full-band; decide by test T5 below), FFT each split: `R₁(τ), R₂(τ)` over delay `τ`.
3. **Cross power:** `P̂(τ) = Re[R₁(τ) R₂*(τ)]` — the cross removes the noise bias term (noise independent between splits), the same trick P2's S2 used in lag space.
4. **Signal template:** a Lorentzian ACF of HWHM `Δν_d` has delay-domain power `T(τ; Δν_d) ∝ exp(−2π Δν_d τ)` (one-sided). Amplitude parameter `a = (f_b·m)²` (times the block-demeaning transfer function — compute it explicitly, see T4).
5. **Noise weighting:** measure the noise power `N(τ)` and its variance empirically from ≥100 off-pulse split-pair realizations (P2's G2 permutation machinery, `seed=900000+i` convention). Do NOT assume white: oversampling makes adjacent-channel noise correlated ⇒ `N(τ)` has known support at large τ; the empirical estimate handles it.
6. **Matched amplitude:** `â(Δν_d) = Σ_τ w(τ) P̂(τ) T(τ) / Σ_τ w(τ) T(τ)²` with `w(τ) = 1/Var[P̂(τ)]_null`; `σ_â = (Σ w T²)^(−1/2)`. Scan `Δν_d ∈` log-grid 20–400 kHz (25 points). Detection statistic: `max_Δν â/σ_â`, trials-corrected against the null distribution from step 5 (empirical, not Gaussian-assumed).
7. **Optional refinement (only if T-tests demand):** replace per-block FFT with a Karhunen–Loève / direct `C_n⁻¹`-weighted quadratic estimator per block (64×64 covariances are cheap); keep the delay-domain version as the reference implementation.

### Gate structure (predeclare in `experiment-chime-scint-p3-optimal-estimator.md` BEFORE implementation)

Copy P2's record structure verbatim, with:
- **G1″ injections:** identical grid — `m ∈ {0.15, 0.17} × Δν_d ∈ {35 control, 77, 127, 213, 352} kHz × 50 realizations`, seeds `1000·cell + realization` (same convention ⇒ directly comparable to P2). PASS: every `Δν_d ≥ 213 kHz` cell certifies (median recovered within ±30%, `|amp pull| ≤ 2`, ≥90% convergence); the 127 kHz cells are reported but not required (they sit between the 3σ and 5σ ceilings); the 35 kHz control must NOT certify.
- **G2″ nulls:** ≥100 off-pulse split-pair realizations; trials-corrected max-significance; family-wise 5%.
- **Gate 0b (new, cheap, first):** before implementing anything, recompute the expected SNR using the *measured* `N(τ)` from P2's null data instead of Gate 0's idealized radiometer algebra. If Gate 0b already shows the 213 kHz ceiling < 3σ, stop — record DOCUMENTED-FAIL-BY-FORECAST and do not build. (Protects against a fourth build-then-fail.)
- **G3:** unchanged admissibility window; one-shot unblinding by the orchestrator only, never by the implementing agent; the `allow_unblind` structural guard stays.

### Testing phase (all before G1″ runs)

- **T1 bandpass invariance:** multiply synthetic frames by arbitrary `g(ν)` (include the measured 35 kHz-shaped realization); `â` invariant to machine precision. Reuse `test_routeb_voltage.py` pattern (P2 achieved ~6e-19).
- **T2 estimator unbiasedness:** pure-synthetic (Gaussian scintle field + radiometer noise at the real `ε² ≈ 2.6`): `⟨â⟩ = a_inj` within errors across the grid.
- **T3 error calibration:** empirical scatter of `â` over realizations / predicted `σ_â` ∈ [0.8, 1.2].
- **T4 block-demeaning transfer:** compute (analytically or numerically) the suppression of `T(τ)` at small τ from 64-channel block-demeaning; verify recovered amplitude corrects for it (this is where a naive implementation silently biases low — P2's Lorentzian fits partially suffered this).
- **T5 block vs full-band decision:** compare per-coarse-block vs tapered-full-band SNR on synthetic; freeze the winner in the record before G1″.
- **T6 blinding guard:** unit test that on-pulse access raises without `allow_unblind`.

### Infrastructure / execution details

- **Repo:** FLITS (`jakobtfaber/dsa110-FLITS`), branch `scint/p3-optimal-estimator` forked from main `1085de0`. Worktree: `git worktree add` from the clone at `~/Developer/scratch/worktrees/flits-p1-window-upchan` (do not work on that checkout itself). New module `scintillation/scint_analysis/optimal_dnu.py` + tests; experiment dir `analysis/chime-scintillation/experiments/p3-optimal-estimator/`.
- **Data:** local pinned npy — `~/Data/Faber2026/dsa110/upchan_codetections/crossacf-2026-07-14/` (pol0/pol1/intensity, 57024×437; verify SHA-256 against `DATA_MANIFEST.yaml` before use). High band = 627–800 MHz, 23 064 channels @ 6.1036 kHz. On-pulse 250–350 (BLINDED), off-pulse 0–200 + post-350 remainder. h17 NOT needed.
- **Runtime:** conda `py312`. G1″ ≈ 500 estimator runs on 23k channels — vectorize; expect minutes, not hours (delay-domain is FFT-cheap).
- **Landing:** FLITS PR (pass `--repo jakobtfaber/dsa110-FLITS` explicitly — the `upstream` remote confuses `gh pr create`), review, merge, then Faber2026 pin-bump PR (pattern: PRs #45/#50/#65). Update `docs/rse/program-state.toml` lane + `python3 scripts/sync_state.py` (owner-view is generated now; never hand-edit `ACTIVE_LANES.md`/`owner-view.json` — CI fails on drift).

## Reproducibility & Data State

- **Seeds:** G1 `1000·cell_index + realization_index`; G2/null `900000 + i`. Keep both conventions in P3.
- **Environment:** conda `py312` (numpy/scipy/matplotlib); pipeline repo Python via its own tooling; no lockfile — record package versions in the P3 RESULT.
- **Data:** the pinned npy set above; SHAs in `DATA_MANIFEST.yaml` alongside; also mirrored on h17 under `/data/research/astrophysics/frbs/chime-dsa-codetections/upchan_codetections/` (not needed for P3).
- **Partial results:** P2's `g2_S1.json`/`g2_S2.json` null-amplitude sets are directly reusable as the seed of the `N(τ)` measurement (same construction, more realizations needed).
- **In-flight jobs:** none. All background agents from this session have completed.

## Verification State / Known-Broken

- **Faber2026 main:** all green — PRs #50–#53, #59–#63, #65 merged; control-system live `--check` PASSED after the F3 lane reconciliation in this handoff's PR. Board deployed.
- **FLITS main `1085de0`:** P2 record + P1 record indexed; CI green on #179/#180.
- **This handoff's own PR carries:** the F3 lane closure (status `in_progress` → `done`; PR #64/issue #57 were already merged/closed by the Devin session — the live drift-check caught it).
- **Untracked separate lanes (preserved, not mine to land):** `docs/rse/specs/research/research-chime-scint-instrumental-common-mode.md` (codex; needs its stale "Origin" section amended when landed), `.devin/` (Devin workspace state), pipeline submodule checkout on `scint/c1-allpairs-crossgp` [ahead 8] with modified b4 figures (pre-existing; unresolved).
- **Unverified:** P2's S3 statistic implemented + unit-tested but never run on data (complex voltages not staged anywhere; regenerating them from baseband was declared out of P2 scope). P3 does not need it.

## Learnings (non-obvious, will bite you otherwise)

1. **The common mode is beaten — don't re-fight it.** P2's G2 proves the on/off ratio cancels it algebraically (0.586 → ≲0.006). The remaining enemy is radiometer noise at `s_eff ≈ 0.008`. Any P3 effort spent on more common-mode mitigation is wasted.
2. **The lag-space ACF fit pins at 20–45 kHz on pure noise.** Never interpret a fitted width near the instrumental scale as signal; P3's null calibration must characterize the noise-pinning distribution of `argmax_Δν â/σ_â`.
3. **G2's literal window spec was ill-posed** (24 disjoint 100-sample windows don't fit in 267 off samples). P2 substituted seeded permutation splits — carry that construction into P3's record explicitly so no mid-implementation deviation is needed.
4. **Blinding is structural, not procedural:** `check_blinding()` in `routeb_voltage.py` raises on any on-pulse read without `allow_unblind=True`. The implementing agent must never pass that flag; unblinding is a separate orchestrator step after gate review.
5. **`gh pr create` in the FLITS clone resolves the base repo to the org `upstream` remote** and fails with "Head sha can't be blank"; always pass `--repo jakobtfaber/dsa110-FLITS`. Git ops there also spew harmless `[entire] ...` checkpoint warnings — ignore them.
6. **The control system's live `--check` treats a merged PR on a non-terminal lane as a contradiction** — set `pr = 0` on continuing lanes (provenance goes in `next_action`/comments), keep the landing PR number only on terminal lanes.
7. **Owner constraints in force:** no external data requests (CHIME calibrator ask declined); every route change needs a predeclared record with frozen gates before burst data; figures for every substantive result (visual vetting); journal every ≤10 min of active work (`scripts/journal-append.sh`), board via `program-state.toml` + `sync_state.py` only.

## Next Steps (priority order)

1. **Owner sanction for P3.** The owner has seen the P2 result and the optimal-estimator concept but has NOT yet said "build P3." Present this handoff's plan; get an explicit yes (the pending question in-session was "build P3 or stop here").
2. **Gate 0b forecast** (hours): measured-noise SNR ceiling from P2's null data. If <3σ at 213 kHz → report DOCUMENTED-FAIL-BY-FORECAST to the owner; stop.
3. **Write `experiment-chime-scint-p3-optimal-estimator.md`** (predeclaration; copy P2's structure; freeze everything in "Gate structure" above), PR to Faber2026.
4. **Implement + test (T1–T6) + run G1″/G2″** on the FLITS branch; open FLITS PR; do not merge without review; never unblind.
5. **Gate review → one-shot unblinding decision** (orchestrator + owner), then FLITS merge, pin bump, lane/board closeout, manuscript integration of whichever verdict.

**Recommended next skill:** `ai-research-workflows:implementing-plans` against this handoff's "The P3 plan" section (after step 1's owner sanction; use `ai-research-workflows:iterating-plans` first if the owner amends the plan).
