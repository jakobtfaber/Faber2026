# Implementation Plan: DM re-measurement campaign — uniform multi-method battery with injection validation

---
**Date:** 2026-07-09
**Author:** AI Assistant (Claude Code)
**Status:** Approved (owner, 2026-07-09) — In Progress
**Related Documents:**
- [Research: DM measurement methods](../research/research-dm-measurement-methods.md)

---

## Overview

Re-measure DM from scratch for all 12 co-detections with a **uniform,
injection-validated, visually-vetted multi-method battery**, replacing the
inherited DSA catalog DMs (placeholder ±0.1 errors) and settling whether the
earlier in-tree DM-power/DM_phase nulls were implementation artifacts.

Owner constraints (binding): same methodology for every burst — no per-burst
method cherry-picking; every estimator run ships per-burst diagnostic figures
+ contact sheets for owner inspection — numerical gates alone never
accept/reject a DM.

**Goal:** a per-burst DM provenance table (all methods × all 24 products) with
a sample-wide primary estimator chosen once, per-burst inter-method scatter as
systematic uncertainty, every estimator proven on known-DM injections, and
contact sheets for owner adjudication.

**Motivation:** every quoted DM is currently inherited, not measured
(research doc §1); DM freedom in the joint scattering fits makes DM errors an
α/τ bias channel (§4); the improved figure and the data release both need
defensible DMs.

## Current State Analysis

(Anchors in [research-dm-measurement-methods.md](../research/research-dm-measurement-methods.md).)

- Quoted DMs = frozen DSA catalog (`pipeline/configs/bursts.yaml:21-148`),
  `dm_err: 0.1` placeholder; V6 pins both instruments to it.
- CHIME arrival-regression estimator exists and constrains 8/12
  (`pipeline/dispersion/chime_dm.py:73,85,116`); never run on DSA.
- In-tree DM_phase/DM-power are unvalidated reimplementations/variants
  (`pipeline/dispersion/dmphasev2.py:43,103-135`;
  `dm_power_analysis.py:59-235`); published packages never run as-released.
- Diagnostic-figure machinery exists: `_plot_result` + PIL contact sheets
  (`dm_phase_analysis.py:329,413`); data-manifest IO
  (`dm_power_analysis.py:303-400`).
- Data: 24 local `_cntr_bpc.npy` (CHIME coherently dedispersed at
  underived stem DMs; DSA incoherently at catalog DM); CHIME singlebeam .h5
  on h17 (coherent path, docker-only); DSA voltage data does not exist.

## Desired End State

- `pipeline/dispersion/dm_campaign/` (new subpackage on the FLITS pin branch)
  with: injection harness, adapters for each estimator, uniform run configs,
  per-burst diagnostic-panel + contact-sheet emitters.
- `results/dm_campaign/`: per-method JSON (all 24 products), injection
  validation report, cross-method comparison table
  (`dm_campaign_provenance.csv`), contact sheets under `docs/rse/specs/`.
- Owner has visually adjudicated; a sample-wide primary is proposed with
  evidence; `bursts.yaml` adoption and manuscript integration explicitly
  deferred to a follow-up gated plan (V-ladder implications).

**Success looks like:** for any burst, one page shows every method's
metric-vs-DM curve, the waterfall at each candidate DM, sub-band arrival
overlays, and the injection-recovery record of the method that produced it.

## What We're NOT Doing

- [ ] No adoption into `bursts.yaml` / budget tables / V6 artifacts in this
      plan — measurement first; adoption is a separate owner-gated step
      (changing DM_obs ripples through TOA residuals and the DM budget).
- [ ] No per-burst method selection (owner constraint).
- [ ] No DSA coherent dedispersion (no voltage data exists — physical limit).
- [ ] No CHIME coherent re-extraction on h17 in this plan (Phase H sketched
      as follow-up: needs docker + h17 session; triggered if the battery
      leaves the 4 unconstrained CHIME bursts unconstrained).
- [ ] No re-litigation of the joint scattering fits (trust-reset §V lanes);
      joint-model `delta_dm` is consumed read-only as a diagnostic layer.
- [ ] No gallery figure edits (deferred behind this lane per owner).

## Implementation Approach

**Key decisions:**
1. **Uniformity model — "uniform battery, single sample-wide primary":** all
   estimators run on all 24 products with identical configs; the primary is
   chosen once for the whole sample after injection validation + owner visual
   vetting; inter-method scatter becomes the per-burst systematic. Rationale:
   avoids forking-paths bias of per-burst choice while keeping cross-method
   information. Per-instrument asymmetry (coherent CHIME vs incoherent DSA)
   is stated once, uniformly.
2. **Injection validation is the gate for every estimator** (including the
   published packages and our arrival regression): synthetic EMG pulses,
   dispersed at known ΔDM, injected into REAL off-pulse noise from our own
   products, spanning a bright/faint × narrow/scattered × single/multi test
   matrix. This directly adjudicates "incorrectly implemented" for the
   in-tree variants.
3. **Published packages run as-released**, vendored at pinned SHAs
   (`opensrc fetch` → `pipeline/external/`), thin adapters only — no
   reimplementation. In-tree variants stay, relabeled as variants, and run
   through the same injections so the discrepancy is diagnosed, not assumed.
4. **Wide, reference-independent searches:** coarse stage ±50 pc cm⁻³ around
   a band-collapsed S/N peak (as `chime_dm.py:73` does), fine stage on each
   method's native metric — no more ±2 windows centered on the answer.
5. **Repo routing:** all code on the FLITS pin branch via pipeline PR
   (pin-bump is its own reviewed step per repo rules); campaign docs/memos in
   Faber2026 `docs/rse/specs/`.
6. **Diagnostics contract (uniform, per product × method):** 4-panel PNG —
   (a) metric-vs-DM curve with bootstrap band; (b) waterfall dedispersed at
   candidate DM (±40 ms); (c) waterfall at reference DM (delta view); (d)
   sub-band arrival-time overlay with regression line where applicable —
   tiled into per-method contact sheets (PIL pattern of
   `dm_phase_analysis.py:413`).

## Implementation Phases

### Phase 0: Injection validation harness (pipeline/dispersion/dm_campaign/)

**Objective:** a reusable known-truth test bed every estimator must pass
before its verdicts count.

**Tasks:**
- [x] **Write failing tests** — `pipeline/tests/test_dm_injection.py` (new;
  as written it also gained `test_injected_scattering_tail_is_causal`, and
  `disperse_waterfall` delegates to `chime_dm._dedisperse(-dm)` so
  injection/dedispersion stay inverses by construction rather than a parallel
  roll implementation):

  ```python
  import numpy as np
  from dispersion.dm_campaign.injection import (
      disperse_waterfall, inject_pulse, make_noise_from_offpulse, InjectionSpec,
  )

  DSA = dict(f_lo_ghz=1.31125, f_hi_ghz=1.49875, nchan=6144, dt_ms=32.768e-3)

  def test_dispersion_shift_matches_kdm():
      wf = np.zeros((64, 4096)); wf[:, 2048] = 1.0
      freq = np.linspace(1.32, 1.49, 64)
      out = disperse_waterfall(wf, freq_ghz=freq, dm=1.0, dt_ms=32.768e-3)
      # K_DM * DM * (f^-2 - f_ref^-2), f_ref = top of band
      k = 4.148808  # ms GHz^2 / (pc cm^-3)
      lag_lo = k * 1.0 * (freq[0] ** -2 - freq[-1] ** -2)
      assert abs(np.argmax(out[0]) - 2048 - round(lag_lo / 32.768e-3)) <= 1
      assert np.argmax(out[-1]) == 2048

  def test_injection_recovers_specified_snr():
      rng = np.random.default_rng(1)
      noise = rng.normal(size=(128, 8192)).astype(np.float32)
      spec = InjectionSpec(dm_offset=0.4, snr=40.0, width_ms=0.5,
                           tau_1ghz_ms=0.0, t0_frac=0.5)
      wf, truth = inject_pulse(noise, freq_ghz=np.linspace(1.32, 1.49, 128),
                               dt_ms=32.768e-3, spec=spec, rng=rng)
      assert truth["dm_offset"] == 0.4
      prof = wf.sum(axis=0)
      snr = (prof.max() - np.median(prof)) / (1.4826 * np.median(np.abs(prof - np.median(prof))))
      assert snr > 10  # injected burst is detectable

  def test_offpulse_noise_preserves_channel_stats():
      rng = np.random.default_rng(2)
      wf = rng.normal(loc=np.arange(32)[:, None], size=(32, 4000)).astype(np.float32)
      noise = make_noise_from_offpulse(wf, on_frac=(0.4, 0.6), n_time=2000, rng=rng)
      assert noise.shape == (32, 2000)
      assert np.allclose(noise.mean(axis=1), np.arange(32), atol=0.2)
  ```

- [x] **Run, watch fail** (`cd pipeline && uv run python -m pytest tests/test_dm_injection.py -v`).
  *(Executed with `conda run -n flits python -m pytest` — the repo's env is conda
  `flits`, not uv. Collection failed as expected: module missing.)*
- [x] **Implement** `pipeline/dispersion/dm_campaign/injection.py`:
  `disperse_waterfall` (per-channel integer+subsample roll by
  K_DM·DM·(ν⁻²−ν_ref⁻²)/dt, top-of-band reference matching
  `chime_dm.py` convention), `InjectionSpec` dataclass, `inject_pulse`
  (EMG kernel reusing `dispersion.chime_dm.exgauss` :32, per-channel
  amplitude from a γ spectral index, scattering tail τ(ν)=τ_1GHz·ν⁻⁴,
  additive into supplied noise, returns (waterfall, truth dict)),
  `make_noise_from_offpulse` (bootstrap-resample off-pulse time columns
  per channel).
- [x] **Run, watch pass; commit** on FLITS branch `dm-campaign-2026-07`
  (4/4 green; committed `1412591`).
- [x] **Test matrix runner + report:**
  `dm_campaign/run_injections.py` — matrix = {S/N 8, 25, 80} × {width 0.3,
  2 ms} × {τ_600MHz 0, 5, 20 ms} × {1, 2 components} × both instrument
  geometries × 5 noise seeds per cell; emits
  `results/dm_campaign/injections/<estimator>.json` (recovered−truth per
  cell) + a recovery-vs-truth diagnostic grid PNG per estimator + contact
  sheet. Pass criterion per estimator: |median bias| < σ_quoted and 68%
  coverage within [0.5, 1.5] on cells with S/N ≥ 25 — **plus owner visual
  review of the recovery grids** (constraint ii).
  *Deviations (documented):* truth range is per-instrument (DSA ±2.5,
  CHIME ±1.5 — the 82 ms CHIME cutout bounds the sweep; plan said ±3);
  search windows ±5 (DSA) / ±4 (CHIME) uniform across estimators; noise is
  synthetic Gaussian in the matrix (real off-pulse bootstrap exercised in
  Phase 1 on real products); workers pin BLAS to 1 thread (a 4-worker
  all-core-BLAS run froze the 12-core laptop). Quick mode (2 seeds,
  n_boot=20) ran locally in 338 s, committed `17821bd`; full mode (5 seeds,
  n_boot=100) ran on h17 (40 cores;
  `/data/research/astrophysics/frbs/chime-dsa-codetections/dm_campaign/`,
  provenance-pinned to commit `0a88d44`) in 5827 s — folded in at `e052329`
  (`results/dm_campaign/injections_full/`), **no verdict flips** vs quick
  (only dmpower/DSA σ_factor drifting into the calibrated band, moot since
  it stays inaccurate there). Quick-mode gate: arrival_regression
  PASS on DSA, accurate but ~2.5× overconfident σ on CHIME; dmphase variant
  accurate in median on both geometries but ±3–5 outliers on wide/2-component
  morphology even at S/N 80; dmpower variant PASS on CHIME, FAIL on DSA
  (bias +0.81, scatter uncorrelated with truth — partly intrinsic: the DSA
  full-band sweep is ~3.5 samples per DM unit at product resolution).

**Verification:**
- [x] `pytest tests/test_dm_injection.py -v` green (local conda `flits` and
      h17 venv, 4/4 both).
- [x] Injection report + contact sheet exist for at least the two in-tree
      variants (their pass/fail adjudicates the "incorrectly implemented"
      question with evidence). Grids visually reviewed
      (`results/dm_campaign/injections/figures.review.json`); **owner visual
      review of the recovery grids still pending** (manual gate before
      Phase 1 conclusions are read).

### Phase 1: Published DM_phase + DM-power, as released

**Objective:** the two packages the owner named, run exactly as published,
uniformly, injection-validated.

**Tasks:**
- [x] `opensrc fetch danielemichilli/DM_phase hsiuhsil/DM-power`; vendor into
  `pipeline/external/{DM_phase,DM-power}/` at pinned SHAs (record SHA +
  license in `pipeline/external/README.md`).
  *(DM_phase @ `b7cf5fd61436` GPL-3; DM-power @ `f7787355ca28`, no license
  published — internal reproduction only. One numpy≥2 vendor patch in
  DM_phase, marked in-file; mpi4py stub + placeholder-argv import shims for
  DM-power; np.random.seed(0) at the adapter boundary because the released
  DM-power bootstraps via the unseeded global RNG. All documented in
  `pipeline/external/README.md`.)*
- [x] **Adapter contract test first** — `pipeline/tests/test_dm_adapters.py`:
  every adapter implements
  `measure(waterfall, freq_ghz, dt_ms, dm_ref) -> DMResult(dm, sigma, curve, meta)`
  and must recover an S/N-80, width-0.5 ms, ΔDM=+0.7 injection within
  3σ on both instrument geometries:

  ```python
  import numpy as np
  import pytest
  from dispersion.dm_campaign.adapters import ADAPTERS  # {"dm_phase_published": ..., "dm_power_published": ..., "dmphase_variant_intree": ..., "dmpower_variant_intree": ..., "arrival_regression": ...}
  from dispersion.dm_campaign.injection import standard_bright_case

  @pytest.mark.parametrize("name", list(ADAPTERS))
  def test_adapter_recovers_bright_injection(name):
      wf, freq, dt, truth = standard_bright_case(instrument="dsa", seed=3)
      res = ADAPTERS[name].measure(wf, freq_ghz=freq, dt_ms=dt, dm_ref=truth["dm_ref"])
      assert res.sigma > 0
      assert abs(res.dm - truth["dm_true"]) < 3 * max(res.sigma, 0.01)
  ```

- [x] Implement thin adapters (call the vendored packages' public entry
  points; NO algorithm code of our own; window = coarse ±50 stage from
  `chime_dm._coarse_dm` :73 then the package's native fine search).
  *(As executed: coarse stage uses the per-instrument physical windows
  (±5/±4, documented Phase-0 deviation) rather than ±50; the two-stage
  coarse→fine flow applies to dm_phase_published — handing it the coarse
  grid directly crashes its half-max window logic when the phase peak is
  under-resolved. All 19 contract tests green on BOTH geometries, including
  dm_power_published on DSA where the in-tree variant failed Phase 0.
  Adapters emit a normalized curve contract: `curve["residual_dm"]` is
  always the physical residual axis regardless of native sign/offset.)*
- [x] Uniform batch runner `dm_campaign/run_battery.py` over
  `load_manifest_rows` (`dm_power_analysis.py:303`) — all 24 products × all
  adapters, one config file (`dm_campaign/configs/battery.yaml`), per-run
  4-panel diagnostics + per-method contact sheets to
  `docs/rse/decks/dm/dm-campaign-2026-07/dm-battery-<method>-contact-sheet.png` + memo.
  *(Executed: 112/120 constrained. The 7 arrival_regression unconstrained
  runs — mahi/chime + 6 DSA — fail its 8-subband S/N≥4 gate while their
  coarse curves are clearly peaked: config sensitivity, the Phase-2 entry
  point, not non-detections. dm_power_published casey/chime SVD failure is
  deterministic under seeded RNG. Known CHIME non-detections (mahi, oran,
  isha, phineas) self-flag via large σ across methods. All five contact
  sheets visually reviewed; run_panels/ 45M gitignored, regenerable via
  `--replot`.)*
- [x] Commit; pipeline PR to the pin branch. *(FLITS `b17395c` on
  `dm-campaign-2026-07`; PR #157 → `pin/faber2026`.)*

**Dependencies:** Phase 0 (adapters must pass injections before the battery
run is read).

**Verification:**
- [x] `uv run python -m pytest tests/test_dm_adapters.py -v` green. *(19/19,
  conda `flits`.)*
- [x] 24-product battery JSON + contact sheets for ≥4 adapters; memo lists
      per-product (dm, σ, gate flags) with NO promotion language. *(All 5
      adapters; `results/dm_campaign/battery/{battery_results.json,memo.md}`.)*

### Phase 2: Arrival regression on DSA + joint-model delta_dm layer

**Objective:** extend the strongest existing estimator to DSA uniformly;
surface the model-conditional DM layer.

**Tasks:**
- [ ] **Failing test:** `test_chime_dm_on_dsa_geometry` — run
  `dispersion.chime_dm.measure_dm` on a DSA-geometry injection
  (6144→sub-banded, 32.768 µs) and require 3σ recovery; expose any
  hard-coded CHIME assumptions (`chime_dm.py:6,29`).
- [ ] Parameterize `chime_dm.py` for instrument geometry (freq axis + dt
  arguments already exist; lift any hard-coded sub-band/TDS constants into
  the battery config, defaults unchanged for CHIME back-compat — existing
  `tests/test_chime_dm.py` must stay green).
- [ ] Add `arrival_regression` to the battery (it then runs on all 24 in
  Phase 1's runner rerun).
- [ ] `dm_campaign/extract_joint_delta_dm.py` — read-only sweep of the beta
  campaign fit JSONs (`analysis/beta_campaign/fits/*_joint_fit_*.json`:
  `delta_dm_C/D` + `dm_init`) into the comparison table, flagged
  `diagnostic_only=true` (trust-reset).
- [ ] Commit; extend the pipeline PR.

**Verification:**
- [ ] Existing `tests/test_chime_dm.py` + new geometry test green.
- [ ] Battery table now has ≥5 method columns × 24 products.

### Phase 3: Cross-method synthesis + owner adjudication

**Objective:** the deliverable table and the visual decision session.

**Tasks:**
- [ ] `dm_campaign/build_provenance_table.py` →
  `results/dm_campaign/dm_campaign_provenance.csv`: per product × method
  (dm, σ, injection-validated?, gate flags, diagnostic paths) + per-burst
  inter-method scatter column + comparison against catalog DM, `dm_chime`,
  file-stem DMs (the four-DM map from the research doc §1).
- [ ] Master contact sheet per burst (all methods side-by-side, both
  instruments) → `docs/rse/specs/dm/dm-campaign-burst-sheets/` + summary memo
  `docs/rse/specs/dm/dm-campaign-synthesis-memo.md` (includes chromatica
  272.368-vs-272.664 adjudication panel: DSA waterfall dedispersed at both,
  battery DMs overlaid).
- [ ] **Owner visual adjudication (manual gate):** owner reviews burst
  sheets + injection reports; outcome = sample-wide primary method +
  per-burst systematic convention; recorded in the memo.
- [ ] Journal + Faber2026 docs PR (research doc, this plan, memos, sheets).

**Dependencies:** Phases 0–2.

**Verification:**
- [ ] CSV has 24 rows × full method set; every cell's diagnostic PNG exists.
- [ ] Memo records the owner's primary-method decision (or the explicit
      blockers) — this plan is complete at that decision, adoption is next.

## Success Criteria

### Automated Verification
- [ ] `cd pipeline && uv run python -m pytest tests/test_dm_injection.py tests/test_dm_adapters.py tests/test_chime_dm.py -v` — green
- [ ] Battery run exits 0 over all 24 manifest products for every adapter
- [ ] `dm_campaign_provenance.csv` complete (no empty method cells without a
      recorded failure reason)
- [ ] Injection reports exist for every adapter, incl. both in-tree variants

### Manual Verification (owner)
- [ ] Injection recovery grids visually sane per estimator
- [ ] Per-burst master sheets reviewed; primary method chosen sample-wide
- [ ] chromatica adjudication panel reviewed
- [ ] In-tree-variant vs published-package injection comparison answers the
      "incorrectly implemented" question to the owner's satisfaction

### Reproducibility & Correctness
- [ ] Vendored package SHAs + battery config + seeds recorded;
      injection truth tables saved alongside results
- [ ] Every number in the provenance CSV regenerable by
      `uv run python -m dispersion.dm_campaign.run_battery --config configs/battery.yaml`

## Testing Strategy

Unit tests in-phase (injection physics, adapter contract, DSA geometry).
Integration = the injection matrix itself (known-truth end-to-end) and the
24-product battery. Manual = owner visual adjudication (constraint ii).
Test data: real off-pulse noise from local products; no external fixtures.

## Risk Assessment

1. **Published packages unmaintained/API drift** (DM_phase last-era scripts)
   — Medium/Medium — vendor at SHA, adapter isolates; injection test defines
   "works."
2. **Battery contradicts V6/catalog DMs at >1 pc cm⁻³ level** — Medium/High —
   this plan stops at measurement + memo; adoption plan handles ripple
   (TOA residuals, budget) with the V-ladder.
3. **Multi-component bursts (whitney) give method-dependent DMs** —
   High/Medium — expected; expressed as inter-method scatter, per the
   uniformity model; injection matrix includes 2-component cells so the
   scatter is calibrated, not anecdotal.
4. **h17/docker unavailability** — coherent re-extraction is out of scope;
   battery runs entirely on local products.

## Edge Cases and Error Handling

1. Adapter crash/timeout on a product → recorded as failed cell with reason
   in the CSV; runner continues (no silent gaps).
2. Estimator returns edge-of-window peak → flagged `edge=true`, never a DM.
3. Zero-variance/masked channels → injection noise builder and adapters share
   the `dead_channel_mask` convention (`scripts/plot_codetection_gallery.py`
   pattern, ported into dm_campaign.util).

## Open Questions

None blocking Phase 0–3 execution. (The primary-method choice and adoption
are deliberately owner decisions AT the Phase-3 gate, not pre-committed.)

---

## References

- [Research: DM measurement methods](../research/research-dm-measurement-methods.md)
- Code anchors: `pipeline/dispersion/chime_dm.py:32,73,85,116`;
  `pipeline/dispersion/dm_power_analysis.py:59,119,303,602`;
  `pipeline/dispersion/dmphasev2.py:43,103-135`;
  `pipeline/dispersion/dm_phase_analysis.py:80-90,329,413`;
  `pipeline/scattering/scat_analysis/burstfit_joint.py:83-96`;
  `pipeline/analysis/beta_campaign/fits/`.
- External: arXiv:2208.13677 (DM-power); ascl:1910.004 (DM_phase);
  arXiv:2311.05829 (fitburst); arXiv:2607.03877 (six-method cross-validation).

## Review History

### Version 1.0 — 2026-07-09
- Drafted after owner corrections (uniform battery, visual vetting,
  implementation-suspect reading of prior nulls). Awaiting owner approval.
