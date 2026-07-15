# Implementation Plan: CHIME scintillation revival — decision-aligned C1 sequence

---
**Date:** 2026-07-14 (v1.1 same day — reconciled with the owner C1 decision)
**Author:** AI Assistant (v1.0 ladder approved by owner 2026-07-14 morning; v1.1 restructure approved 2026-07-14 evening after the C1 decision doc surfaced)
**Status:** Draft
**Related Documents:**
- [Decision: Figure 1 + CHIME C1 route (OWNER, governs this plan)](decision-2026-07-14-figure1-and-chime-c1.md)
- [Handoff: C1 estimator + first diagnostic (in-flight lane)](../../../pipeline/docs/rse/specs/handoff-2026-07-14-22-09-c1-allpairs-crossgp.md)
- [Research: CHIME scint measurement state](research-chime-scint-measurement.md)
- [Plan: lane-B γ campaign (terminal)](plan-chime-scint-gamma-campaign.md)
- [Report: qualification inventory 2026-07-14](report-chime-scintillation-inventory-2026-07-14.md)

---

## Overview

The lane-B campaign closed 2026-07-13 with 0/12 CHIME Δν_d certified; the
2026-07-14 qualification inventory shows every corrected-product/estimator
route (H0/A1/H2/H3/B3/B4, trigger calibration, notebook replay) failed on the
qualification target (freya). The recorded revival trigger — "corrected
products landing sample-wide" — is necessary but not sufficient: the shipped
correction algorithms are the ones that failed, and the uniform-tier configs
cannot pass the provenance gate as shipped.

**v1.1 governance note:** the owner decision
[decision-2026-07-14-figure1-and-chime-c1.md](decision-2026-07-14-figure1-and-chime-c1.md)
(merged PR #43) selected **`c1-allpairs-crossgp`** — an all-pairs,
cross-fitted polarization/time-fold estimator on the *retained*
polarization-resolved upchannelized product — as the next qualification
route, with a predeclared blinded calibration matrix and go/no-go rule. Its
stop rule forbids further estimator tuning on the retained product after a
C1 failure: the successor route must change the *information content of the
input product*. v1.0's C2 (per-coarse-channel gain) and C3 (on-pulse
whitening) are estimator/correction tuning on the retained product and are
therefore **ruled out**; v1.0's windowed re-upchannelization survives as the
sanctioned successor route. C1 implementation is already in flight
(uncommitted, branch `scint/c1-allpairs-crossgp`; see the linked handoff).

This plan is now a **decision-aligned sequence**: (1) hygiene, (2) complete
C1 through its blinded calibration and go/no-go, (3) *conditional on C1
FAIL*: the product-regeneration route under a new experiment ID with a fresh
blinded campaign, (4) *conditional on a PASS* (from C1 or the successor):
sample-wide application, provenance-complete configs, 12-burst campaign
rerun, (5) manuscript integration. A documented failure at every rung is a
valid terminal state.

**Goal:** either (a) a qualified CHIME Δν_d route exists and the 12-burst
campaign has been rerun on it with gates re-adjudicated and the manuscript
updated, or (b) C1 and the product-regeneration successor both carry
documented, reproducible blinded-campaign failures indexed in
`pipeline/analysis/chime-scintillation/INVENTORY.yaml`, closing the revival
path on current data and current reduction methods.

**Motivation:** the manuscript currently reports a sample-wide
DOCUMENTED-FAIL (`sections/results.tex:215-271`). A validated correction
would either revive CHIME-band Δν_d (γ anchor, two-screen constraint) or
prove the failure is fundamental to the products — both are publishable
outcomes; silence about the untested upstream lever is not.

## Current State Analysis

**Existing Implementation:**
- `pipeline/scintillation/scint_analysis/chime_artifact_guards.py:49-54` —
  `CHIME_REQUIRED_MITIGATIONS`: `instrumental_background_correction`,
  `grid_regularization`, `bandpass_normalization`, `harmonic_mask`;
  `_enabled` (`:60-62`) requires a dict block with truthy `enable`.
- `chime_artifact_guards.py:128-185` — fail-closed provenance gate; `:185`
  off-pulse null; `:280` low-lag stability; `:418` modulation physicality;
  `:454` sub-band support; `:480` `finalize_measurement_status`.
- `pipeline/scintillation/scint_analysis/pipeline.py:386-472` — gate wiring
  into per-burst results; `:196-205,526` — `_apply_bandpass_normalization`
  (implemented, mostly not enabled in configs).
- `pipeline/scintillation/scint_analysis/chime_product.py:21-24` —
  `SUPPORTED_CORRECTION_ALGORITHMS = {1: robust_coarse_rank1_v1,
  2: robust_coarse_rank2_v1}`; both failed the freya battery. Builder emits
  paired corrected/raw npz + SHA256 manifests (`write_chime_products`,
  `verify_product_manifest`).
- `pipeline/analysis/chime-recovery-2026-07-12/validate_freya_h2.py` (25.9K),
  `validate_freya_additive_covariance.py`, `validate_freya_h3.py`,
  `run_freya_gate.py` — the existing battery implementations (injections,
  held-out checks, adjudication via
  `chime_correction_validation.py:21,47,54,104`).
- `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py`
  — coherent dedispersion + `_upchannel(fftsize=2U, downfreq=2)` PFB fine
  channelization, in `chimefrb/baseband-analysis:latest` docker on h17;
  CLI flags at `:364-395` (`--no-time-shift`, `--run-unresolvable`,
  `--save-polarizations`).
- `pipeline/scripts/run_chime_scint_campaign.py:25-28` — 12-burst uniform
  campaign runner; `patch_config` at `:31`.
- `pipeline/scintillation/configs/chime_products.yaml` — target registry;
  hamilton currently `candidate` with no caveat field.
- `pipeline/scintillation/scint_analysis/tests/test_chime_product.py:236` —
  existing eligibility assertion pattern.

**C1 in-flight state (branch `scint/c1-allpairs-crossgp`, uncommitted as of
2026-07-14 22:09):**
- `pipeline/scintillation/scint_analysis/cross_acf.py:363` —
  `all_pairs_cross_acf(..., exclude_same_time=True, normalizations=None)`;
  `fit_cross_lorentzian` at `:230` (returns `dnu_mhz`, `m`, errs, `redchi`,
  … — no `r_val`/`p_val`).
- `tests/test_cross_acf.py:157` — three C1 unit tests, all passing (8 passed
  suite-wide); seeds 20260717/20260718.
- `pipeline/analysis/chime-scintillation/experiments/c1-allpairs-crossgp/diagnose_freya_c1.py:55`
  — first freya diagnostic: off-pulse m=0.139, Δν=0.082 MHz, coherent ± lag
  structure (not pure noise); on-pulse after single-template removal
  m=0.211, Δν pinned at the 0.003 MHz lower bound, m_err=17.3 —
  unconstrained. One off-pulse template is insufficient; the decision doc's
  multi-block held-out rotation is mandatory.
- Known blocker: `all_pairs_cross_acf` delegates pair-by-pair to
  `blockwise_cross_acf_pairs` (~435 pairs ≈ 30 s per call at 23,064
  channels × 40 lags) — impractical for ≥128 trials/cell; vectorization
  required first.
- Separate dirty lane in the same tree: regenerated B4 outputs under
  `analysis/chime-recovery-2026-07-12/results/b4_fourstream/` — must be
  committed/reverted independently of C1 code (handoff instruction).
- Data: `~/Data/Faber2026/dsa110/upchan_codetections/crossacf-2026-07-14/`
  (freya pol0/pol1/intensity npy + freq + metadata). Pol-resolved products
  exist for freya only; the other 11 bursts would need an h17
  `--save-polarizations` pass if C1 goes sample-wide.

**Current Behavior:** uniform-tier campaign results are demoted to
`diagnostic_only` by construction (no `instrumental_background_correction`
block in any burst config; `bandpass_normalization` only in
`freya_chime_hi.yaml:65`).

**Current Limitations:**
- Both shipped correction algorithms fail off-pulse nulls (low band),
  injection recovery at realistic m≈0.15, and held-out/time-split stability.
- The failure pattern is consistent with non-stationary instrumental
  frequency structure at the ~35 kHz scale in the products themselves —
  post-hoc corrections have not removed it; the upstream fine-channelization
  response has never been varied.
- hamilton eligibility is encoded inconsistently across plan doc, registry,
  and DATA_PROVENANCE.

## Desired End State

**New Behavior:**
- A parameterized freya battery harness runs any candidate product/algorithm
  through the full predeclared gate set with one command.
- Three candidate routes implemented and adjudicated; verdicts + artifacts
  indexed in the inventory.
- If a candidate passes: all 12 bursts have manifest-bearing corrected
  products, configs enable all four mitigations, campaign rerun complete,
  gates re-adjudicated, manuscript updated via PR.
- hamilton/johndoeII carry an explicit `provenance_caveat: single_block`
  that propagates into campaign results JSON.

**Success Looks Like:**
- `pytest pipeline/scintillation/scint_analysis/tests/` green including new
  tests.
- `INVENTORY.yaml` gains one entry per candidate with
  `qualified_measurement: true|false` and decisive evidence links.
- Either a merged manuscript PR with revived CHIME numbers, or a closing
  inventory entry documenting that C1 and P1 both fail and the revival path on
  current data is exhausted.

## What We're NOT Doing

- [ ] No DSA-110 estimator or result changes (qualified separately).
- [ ] **No estimator/correction tuning on the retained product beyond C1** —
      the decision doc's stop rule. v1.0's C2 (per-coarse-channel gain,
      `robust_coarse_perchannel_v1`) and C3 (on-pulse whitening) are ruled
      out and removed from this plan's phases; they may only ever return as
      a *new owner decision*, not as engineering follow-ups.
- [ ] No gate-threshold changes — C1's gates and calibration matrix are
      predeclared in the decision doc; any changed threshold creates a new
      experiment ID and a fresh blinded campaign (decision doc, verbatim
      rule). No threshold may be relaxed after the real burst estimate is
      inspected.
- [ ] No unblinding of the real freya on-pulse C1 estimate before every
      prerequisite, null, and required `m=0.15`/`m=0.17` recovery cell
      passes (go/no-go rule).
- [ ] No Oran detection adjudication (no measurement bundle exists).
- [ ] No bulk re-upchannelization or pol-resolved regeneration of all 12
      bursts before a route passes on freya (h17 compute gated on the
      go/no-go verdict).
- [ ] No `pipeline/` gitlink bump as a side effect — C1 code, figure work,
      and any pin bump are separate focused branches/PRs (decision doc +
      repo CLAUDE.md).
- [ ] No changes to `results/dm_campaign` (stays on the h17 lane) or to the
      org-mirror sync discipline.
- [ ] No per-burst method cherry-picking — whichever route passes is applied
      uniformly to all 12 (owner's uniform-methods rule).
- [ ] No touching the dirty regenerated B4 outputs from the C1 branch's
      commits (separate lane; revert or commit independently).

**Rationale:** the campaign's credibility rests on fail-closed, predeclared,
uniform methodology; every exclusion above protects that.

## Implementation Approach

**Technical Strategy:** execute the owner-decided route order. C1's arbiter
is the decision doc's own predeclared gate set and 128-trial blinded
calibration matrix, implemented as `validate_freya_c1.py` mirroring B4's
`validate_freya_highband_crossacf.py` (the freshest fail-closed battery in
the tree). The successor route (only on C1 FAIL) changes input-product
information content via windowed/oversampled fine re-channelization from
the coherently dedispersed baseband.

**Key Architectural Decisions:**
1. **Decision:** C1's validation mirrors the B4 script family, not the H2
   battery (v1.0's H2-harness refactor is dropped).
   - **Rationale:** the decision doc carries B4's gates forward unchanged
     and adds C1-specific ones (family-wise FPP ≤ 0.01, scramble and
     phase-shift controls, fit-window/frequency-split/time-fold stability);
     `validate_freya_highband_crossacf.py:44` already implements the
     constants, `_remove_instrument_template`, `_offpulse_gate`,
     `_injection_gate` to inherit.
   - **Trade-offs:** none material; H2 refactor effort saved.
   - **Alternatives considered:** generic multi-candidate harness (v1.0) —
     obsolete now that there is exactly one active route at a time.
2. **Decision:** vectorize `all_pairs_cross_acf` *before* the calibration
   matrix, gated by a numerical-equivalence regression test against the
   current per-pair implementation.
   - **Rationale:** ~30 s/call × ≥128 trials × 24 cells × multiple windows
     is weeks of serial compute; the handoff names this the blocker.
   - **Trade-offs:** equivalence test must cover block means, errors,
     covariance, `block_acfs` — not just the mean ACF.
   - **Alternatives considered:** run the matrix on h17 unvectorized
     (rejected: still slow, and h17 adds no per-call speedup for a
     single-threaded Python loop).
3. **Decision:** successor route implements windowed fine channelization as
   a *local* `windowed_fine_channelize` rather than patching
   `baseband_analysis` (unchanged from v1.0).
   - **Rationale:** the docker image's package is pinned/broken in places
     (see `upchannelize_chime.py` docstring API note); a local windowed
     overlap-FFT on the coherently dedispersed baseband is self-contained
     and testable.
   - **Trade-offs:** slower than the package path; freya-only at first.
   - **Alternatives considered:** upstream package patch (rejected: not
     reproducible from this repo).
4. **Decision:** conditional phases execute only on a predeclared PASS; the
   fail branch at each rung is an inventory-closing task.
   - **Rationale:** mirrors the inventory's fail-closed vocabulary; avoids
     sunk-cost pressure to promote diagnostics.

**Patterns to Follow:**
- Paired corrected/raw products with SHA256 manifests —
  `chime_product.py` (`write_chime_products`).
- Experiment bundles under `pipeline/analysis/chime-scintillation/experiments/<id>/`
  with README + RESULT + manifest — see
  `experiments/h2-calibration/README.md`.
- Focused fork PRs to `jakobtfaber/dsa110-FLITS` main; Faber2026 pin bump as
  its own ancestor-checked PR (repo CLAUDE.md standing authorization).

## Implementation Phases

### Phase 1: Eligibility caveat hygiene

**Objective:** encode the approved hamilton resolution (orthogonal to the
C1 lane; safe to run in the main checkout or a small hygiene branch — never
on `scint/c1-allpairs-crossgp`).

**Tasks:**
- [x] **Failing test — caveat encoding.** Append to
  `pipeline/scintillation/scint_analysis/tests/test_chime_product.py` (after
  the `:236` eligibility assertion):

  ```python
  def test_single_block_provenance_caveats():
      registry = load_chime_target()  # full registry load, same helper as :236 test
      assert registry["hamilton"]["measurement_eligibility"] == "candidate"
      assert registry["hamilton"]["provenance_caveat"] == "single_block"
      assert registry["johndoeII"]["provenance_caveat"] == "single_block"
      assert "provenance_caveat" not in registry["freya"]
  ```

- [x] **Run it, watch it fail:**
  `pytest pipeline/scintillation/scint_analysis/tests/test_chime_product.py::test_single_block_provenance_caveats -v`
  → KeyError `provenance_caveat`.
- [x] **Implement:** in `pipeline/scintillation/configs/chime_products.yaml`
  add `provenance_caveat: single_block` to the `hamilton` and `johndoeII`
  entries (hamilton stays `measurement_eligibility: candidate`).
- [x] **Run it, watch it pass**, then commit
  `feat(scint): encode single-block provenance caveats`.
- [x] **Failing test — caveat propagation into results.** In
  `tests/test_chime_artifact_guards.py` add:

  ```python
  def test_finalize_measurement_status_carries_caveat():
      provenance = {"is_chime": True, "status": "measurement", "missing": []}
      status = finalize_measurement_status(
          provenance,
          off_pulse_null={"null_pass": True},
          low_lag_stability={"stable": True},
          modulation_index={"physical": True},
          subband_support={"sufficient": True},
          provenance_caveat="single_block",
      )
      assert status["provenance_caveat"] == "single_block"
      assert status["status"] == "measurement"
  ```
- [x] **Implement:** `chime_artifact_guards.py:480`
  `finalize_measurement_status(..., provenance_caveat: str | None = None)`
  → include `"provenance_caveat": provenance_caveat` in the returned dict
  when not None. Wire in `pipeline.py` at the `:434-441` call site from
  `self.config.get("provenance_caveat")`, and in
  `pipeline/scripts/run_chime_scint_campaign.py` `patch_config` (`:31`)
  inject the registry value:

  ```python
  registry = yaml.safe_load((pkg_root / "scintillation/configs/chime_products.yaml").read_text())
  caveat = registry["targets"].get(nick, {}).get("provenance_caveat")
  if caveat:
      cfg["provenance_caveat"] = caveat
  ```

- [x] **Run tests, commit** `feat(scint): propagate provenance caveat into gate record`.
- [x] **Correct the plan-doc lumping:** edit
  [plan-chime-scint-gamma-campaign.md](plan-chime-scint-gamma-campaign.md)
  goal paragraph ("isha/hamilton/johndoeII carry lower-confidence
  upper-bound status") to: isha + johndoeII = `upper_limit_only`; hamilton =
  `candidate` with `single_block` caveat (owner decision 2026-07-14).
**Dependencies:** none (local, no h17).

**Verification:**
- [x] `pytest pipeline/scintillation/scint_analysis/tests/ -q` → all pass
      including the two new caveat tests.

*(v1.0's generic H2-battery harness was dropped in v1.1: C1 carries its own
predeclared battery — decision doc + `validate_freya_c1.py` in Phase 2.)*

### Phase 2: Complete C1 (`c1-allpairs-crossgp`) through go/no-go

**Objective:** finish the in-flight owner-decided route: vectorize the
estimator, build the full validation script, run the blinded 24-cell
calibration matrix, evaluate every predeclared gate, then unblind or
document failure. All work on branch `scint/c1-allpairs-crossgp` (one agent
per worktree — pipeline CLAUDE.md rule; the dirty B4 regenerated outputs in
that tree are a separate lane, never swept into C1 commits).

**Tasks:**
- [x] **Pin a characterization reference BEFORE touching the estimator.**
  Using the existing synthetic inputs from
  `tests/test_cross_acf.py:157` (`test_all_pairs_cross_acf_recovers_low_modulation`,
  seed 20260717), run the *current* per-pair `all_pairs_cross_acf`
  (`cross_acf.py:363`) once and save every `CrossACF` field (block means,
  errors, covariance, `block_acfs`) to
  `tests/fixtures/all_pairs_reference_20260717.npz`. Add:

  ```python
  def test_all_pairs_cross_acf_matches_pinned_reference():
      acf = _reference_all_pairs_inputs_and_call()   # same builder the m=0.15 test uses
      ref = np.load(FIXTURES_DIR / "all_pairs_reference_20260717.npz")
      for key in ("acf", "block_acfs", "errors", "covariance"):
          np.testing.assert_allclose(_field(acf, key), ref[key], rtol=1e-10, atol=1e-12)
  ```

  Run → PASS against the current implementation (this is a
  characterization test: green before the rewrite, must stay green after).
- [x] **Vectorize.** Replace the per-pair delegation to
  `blockwise_cross_acf_pairs` with a matrix pair-sum over the fold axis
  (build the pair index set once with `np.triu_indices` excluding
  same-time/auto pairs per `exclude_same_time`; accumulate cross-products
  with einsum/FFT-based lag correlation). Re-run the pinned test + the
  three existing C1 tests → all green. Benchmark task:
  `python -m timeit`-style check in the experiment dir showing ≥50×
  speedup on the freya-sized shape (23,064 channels × 40 lags, 435 pairs);
  record the number in the experiment README.
- [x] **Commit** `feat(scint): vectorize all_pairs_cross_acf` (C1 files
  only; B4 outputs excluded).
- [x] **Build `validate_freya_c1.py`** in
  `analysis/chime-scintillation/experiments/c1-allpairs-crossgp/`,
  mirroring `analysis/chime-recovery-2026-07-12/validate_freya_highband_crossacf.py:44`
  (inherit `BAND_MHZ`, `OFF_PULSE`, `BURST_WINDOW`, `MAX_LAG_BINS`,
  `FIRST_LAG_BIN`, `CHANNELS_PER_COARSE`, `FIT_MAXIMA_MHZ`,
  `_offpulse_gate`, `_injection_gate`) with the decision-doc deltas:
  multiple held-out off-pulse blocks with rotated training/test folds for
  the nuisance basis (never train and test on the same block; the
  single-template shortcut in `diagnose_freya_c1.py:55` is diagnostic
  only), per-fold `normalizations` from the on-pulse envelope (handoff
  learning: off-pulse mean ≈ 0 after baseline subtraction), and
  frozen-before-unblinding window/mask/block-map/hyperparameters written to
  a `frozen_config.json` whose SHA256 is recorded in every downstream
  artifact.
- [x] **Run the blinded calibration matrix** (checkpoint-per-cell,
  idempotent rerun — trigger-calibration campaign pattern):

  ```bash
  cd pipeline && conda run -n flits python \
    analysis/chime-scintillation/experiments/c1-allpairs-crossgp/run_c1_calibration.py \
    --trials 128 --m 0.10 0.15 0.17 0.20 0.30 1.00 \
    --width-channels 3 6 10 16 --workers 4 \
    --outdir analysis/chime-scintillation/experiments/c1-allpairs-crossgp/calibration/
  ```

  Deterministic seeds per cell; untouched real off-pulse backgrounds with
  independent held-out placement. Offload to h17 if projected wall-clock
  exceeds ~2 days at 4 local workers.
- [x] **Evaluate every predeclared gate** (decision doc §Gates): the four
  B4 recovery gates per required cell (finite estimates; width bias <
  max(0.10·truth, 0.25·channel); 68% coverage ∈ [0.53, 0.83]; m bias <
  max(0.10·truth, 0.05)) plus family-wise FPP ≤ 0.01 across held-out and
  pairing-scramble nulls, time/pol-scramble and coarse-channel phase-shift
  controls, <20% width movement across predeclared fit windows,
  frequency-split and time-fold consistency, provenance, and visual review
  (figure-review Stop gate applies). Emit `validation.json` +
  `figures.manifest.json` + `figures.review.json`.
- [x] **Go/no-go.** PASS (every prerequisite, null, and every `m=0.15` and
  `m=0.17` cell) → unblind the real on-pulse fit, then run the
  post-unblind stability gates before any `qualified_measurement` claim →
  proceed to Phase 4. FAIL → write the `DOCUMENTED-FAIL` RESULT.md +
  `INVENTORY.yaml` entry (`id: c1-allpairs-crossgp`), update the inventory
  README's "Current scientific answer", and proceed to Phase 3. Either
  way: `docs/rse/specs/experiment-chime-scint-c1-calibration.md` records
  the cell × gate matrix.
- [x] **Commit + push the C1 lane** (branch PR to FLITS fork main per
  standing authorization); revert or separately commit the B4 regenerated
  outputs (`analysis/chime-recovery-2026-07-12/results/b4_fourstream/*`)
  with their own figure review.

**Dependencies:** none on Phase 1 (parallel-safe; disjoint files).

**Verification:**
- [x] `pytest scintillation/scint_analysis/tests/test_cross_acf.py -q` →
      ≥9 passed (8 existing + pinned-reference test).
- [x] 24 calibration cells × ≥128 trials present with finite values;
      aggregate report recomputes from checkpoints (trigger-calibration
      precedent).
- [x] `validation.json` gate verdicts complete; go/no-go recorded; no
      unblinding artifact exists unless the go rule passed.

### Phase 3 (conditional on C1 FAIL): product-regeneration route — windowed fine channelization (freya, h17)

**Objective:** change the input product's information content (the only
sanctioned move after a C1 failure): regenerate freya with a windowed,
oversampled fine channelization from the coherently dedispersed baseband.
Mint a new experiment ID (`p1-window-upchan`) with its own frozen config
and a fresh blinded campaign — same gate discipline as C1, new bytes.

**Tasks:**
- [ ] **Failing test — windowed upchannelizer core (local, synthetic).** New
  `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/test_windowed_upchan.py`:

  ```python
  import numpy as np
  from windowed_upchan import windowed_fine_channelize

  def test_flat_tone_response_across_fine_channels():
      # complex white noise through one synthetic coarse channel: the fine-channel
      # mean power must be flat (scallop suppressed) to <1% ripple with hann+4x
      rng = np.random.default_rng(20260714)
      x = rng.normal(size=2**18) + 1j * rng.normal(size=2**18)
      spec = windowed_fine_channelize(x, factor=64, window="hann", oversample=4)
      band = spec.mean(axis=-1)              # (fine_channels,) time-averaged power
      ripple = band.std() / band.mean()
      assert ripple < 0.01

  def test_white_noise_power_level():
      # with P = |F|^2 / sum(w^2), white noise of per-sample power sigma^2
      # has E[P] = sigma^2 per fine channel — the absolute calibration check
      rng = np.random.default_rng(1)
      x = rng.normal(size=2**16) + 1j * rng.normal(size=2**16)
      spec = windowed_fine_channelize(x, factor=16, window="hann", oversample=2)
      assert np.isclose(spec.mean(), np.mean(np.abs(x) ** 2), rtol=0.05)
  ```
- [ ] **Implement `windowed_upchan.py`** (same directory):

  ```python
  def windowed_fine_channelize(x, *, factor, window="hann", oversample=2):
      """Overlap-FFT fine channelization of one coherently-dedispersed coarse channel.

      factor: number of fine channels U; FFT length = factor * oversample,
      hop = FFT length // oversample (50% overlap at oversample=2).
      Returns (U, n_frames) power. Window normalized so white-noise expectation
      is flat (divide by sum(w**2)).
      """
      n = factor * oversample
      w = np.hanning(n) if window == "hann" else np.ones(n)
      hop = n // oversample
      frames = np.lib.stride_tricks.sliding_window_view(x, n)[::hop] * w
      F = np.fft.fft(frames, axis=-1)
      # keep every `oversample`-th bin -> U fine channels, critically sampled
      P = (np.abs(F[:, ::oversample]) ** 2) / np.sum(w ** 2)
      return P.T
  ```

  Finalize the Parseval test constant against this normalization; run both
  tests → PASS; commit `feat(scint): windowed oversampled fine channelization`.
- [ ] **Wire into the h17 worker:** `upchannelize_chime.py` — add
  `--fine-window {none,hann}` and `--fine-oversample {2,4}` flags beside
  `:371-381`, route `_waterfall`'s per-coarse-channel step through
  `windowed_fine_channelize` when `--fine-window != none`, and suffix output
  files `_{window}{oversample}` (e.g. `freya_chime_upchan_hann4.npy`).
- [ ] **Generate freya variants on h17** (inside the docker image, per the
  module docstring):

  ```bash
  ssh h17 'docker run --rm -v $COD:$COD chimefrb/baseband-analysis:latest \
    python upchannelize_chime.py freya --no-time-shift --fine-window hann --fine-oversample 4'
  # and the oversample=2 variant; pull products back to
  # ~/Data/Faber2026/dsa110/scintillation-data/ alongside the existing npz
  ```

- [ ] **Build paired products:** run
  `pipeline/scintillation/scripts/build_chime_product.py` on each variant
  (algorithm 1 for the paired-raw bookkeeping; this route's correction *is*
  the product) and `verify_product_manifest` them. Regenerate with
  `--save-polarizations` so the C1 estimator (now the validated battery's
  estimator of record) can run on the new product.
- [ ] **Blinded campaign on the new product:** freeze a `p1-window-upchan`
  config (window, oversample, masks, folds), then rerun the Phase-2
  calibration matrix + gates via `validate_freya_c1.py`/`run_c1_calibration.py`
  pointed at the regenerated pol-resolved product — no threshold changes
  (a changed threshold would mint yet another experiment ID, decision-doc
  rule). Go/no-go identical to Phase 2. FAIL → inventory-closing entry
  (`p1-window-upchan`) and terminal state (b). PASS → Phase 4.
- [ ] **Commit** (FLITS fork PR) `feat(scint): p1 windowed fine-channelization route`.

**Dependencies:** Phase 2 concluded with FAIL (this phase does not start
otherwise); Phase-2 vectorized estimator + validation script; h17 + docker
+ arc access (already verified per `upchannelize_chime.py` docstring).

**Verification:**
- [ ] `pytest .../test_windowed_upchan.py -v` → 2 passed.
- [ ] Two freya variant npz exist locally with verified manifests
      (`verify_product_manifest` exit 0), pol-resolved streams included.
- [ ] `p1-window-upchan` calibration bundle complete with gate verdicts and
      go/no-go recorded.

### Phase 4 (conditional on a Phase-2 or Phase-3 PASS): sample-wide products + campaign rerun

**Objective:** uniform application of the passing route to all 12 bursts;
provenance-complete configs; rerun; re-adjudication.

**Tasks:**
- [ ] Generate the passing route's inputs for all 12 bursts and verify all
  manifests:
  - C1 passed → h17 `--save-polarizations` pass for the 11 bursts lacking
    pol-resolved upchan products (freya already staged at
    `~/Data/Faber2026/dsa110/upchan_codetections/crossacf-2026-07-14/`),
    then per-burst frozen configs cloned from freya's
    `frozen_config.json` (window/mask/block-map re-proved per burst against
    the retained product, per the decision's freeze discipline).
  - P1 passed → h17 batch via the new `--fine-window/--fine-oversample`
    flags over `BURSTS` (`run_chime_scint_campaign.py:25-28`) +
    `build_chime_product.py` paired outputs.
- [ ] Wire the passing route's measurement path into the campaign: per-burst
  measurement comes from the validated experiment harness
  (`validate_freya_c1.py` generalized to `validate_burst_c1.py` with the
  burst name a parameter — same gates, same emitters), not from a parallel
  reimplementation inside `pipeline.py`; campaign runner invokes it per
  burst and collects `validation.json` verdicts alongside the existing
  artifact gates (`pipeline.py:419-472`).
- [ ] **Failing test — config provenance completeness.** New
  `tests/test_campaign_config_provenance.py`:

  ```python
  import yaml
  from pathlib import Path
  from scint_analysis.chime_artifact_guards import chime_provenance_status

  def test_all_uniform_tier_configs_pass_provenance_gate():
      cfg_dir = Path("pipeline/scintillation/configs/bursts")
      for cfg_path in sorted(cfg_dir.glob("*_chime.yaml")):
          cfg = yaml.safe_load(cfg_path.read_text())
          status = chime_provenance_status(cfg)
          assert status["status"] == "measurement", (cfg_path.name, status["missing"])
  ```

- [ ] **Implement:** in every `{nick}_chime.yaml` point `input_data_path` at
  the corrected npz and add:

  ```yaml
  analysis:
    instrumental_background_correction:
      enable: true
      algorithm: <passing route id>
      product_manifest: <relative manifest path>
    bandpass_normalization:
      enable: true            # parameters copied from freya_chime_hi.yaml:65 block
  ```

  Run test → PASS; commit `feat(scint): provenance-complete uniform-tier configs`.
- [ ] Rerun: `python pipeline/scripts/run_chime_scint_campaign.py --python <env>`
  (bounded workers); per-burst gates re-adjudicated by the pipeline
  (`pipeline.py:419-472`); figure review on every product.
- [ ] Also fix, in the same rerun lane, the three cosmetic closeout bugs
  (ΔBIC panel empty, johndoeII glyph dropout, y-tick overprints) in
  `plotting.py` — each with a pinned-figure regression test in
  `tests/` asserting the panel renders non-empty (matplotlib
  `fig.axes[n].has_data()`).
- [ ] Results table (burst × gates × Δν_d/γ/m verdicts) into the experiment
  doc; journal + board update.

**Dependencies:** Phase 2 PASS (or Phase 3 PASS); h17 for either sample-wide
generation path.

**Verification:**
- [ ] `pytest tests/test_campaign_config_provenance.py -q` → 12 passed
      paths.
- [ ] 12 campaign result JSONs with `measurement_status` ∈
      {measurement, diagnostic_only} and zero missing-mitigation demotions.

### Phase 5 (conditional): manuscript integration + landing

**Objective:** land code (fork PRs), pin bump, manuscript update.

**Tasks:**
- [ ] FLITS fork PRs per lane (Phase 1 caveat hygiene; Phase 2 C1 lane;
  Phase 3 route if run; Phase 4 configs+rerun artifacts), CI green, merge;
  B4 regenerated outputs land in their own separate commit/PR.
- [ ] Faber2026 pin bump as its own PR with merge-base ancestor check
  (repo CLAUDE.md guardrail).
- [ ] Update `sections/results.tex:215-271`: replace/extend
  `tab:chime_scint_gates` with post-rerun verdicts; if measurements
  certify, add Δν_d/γ values + method sentence naming the passing
  correction route; recompile clean; verifier pass (prose vs results
  JSONs) before merge — mirrors the merged PR #22 pattern.
- [ ] Update memories: scint campaign rerun outcome; retire the
  "corrected-products rerun" trigger in
  `scint-campaign-autonomy-grant.md`.

**Dependencies:** Phase 4.

**Verification:**
- [ ] Manuscript compiles (`latexmk -pdf` clean) and PR merges with
      verifier MERGE-CLEAR.

## Success Criteria

### Automated Verification
- [ ] `pytest pipeline/scintillation/scint_analysis/tests/ -q` green
      (existing + caveat tests + pinned characterization test for the
      vectorized `all_pairs_cross_acf`).
- [ ] Calibration completeness: 24 cells × ≥128 trials, all finite;
      aggregate recomputes from checkpoints.
- [ ] All decision-doc gates evaluated with recorded verdicts in
      `validation.json`; go/no-go entry present; no unblinded on-pulse
      artifact unless the go rule passed.
- [ ] `verify_product_manifest` exit 0 for every product this plan builds.
- [ ] `INVENTORY.yaml` parses and carries the `c1-allpairs-crossgp` entry
      (+ `p1-window-upchan` if Phase 3 runs).
- [ ] (Conditional) provenance-completeness test passes for all 12 configs;
      campaign rerun emits 12 result JSONs.

### Manual Verification
- [ ] Figure review per calibration campaign and (conditional) per burst —
      full diagnostic set inspected together, verdict recorded in
      `figures.review.json` (visual review cannot override a failed
      quantitative gate — decision doc).
- [ ] Owner sign-off on any certified Δν_d before manuscript claims (a
      first-ever qualified CHIME number is a science claim, not a mechanical
      landing).
- [ ] Blinding audit: confirm no on-pulse fit was produced or inspected
      before the calibration go rule passed, and no threshold changed after
      any real-burst inspection (would mint a new experiment ID).

### Reproducibility & Correctness
- [ ] Every product carries SHA256 manifests; battery runs record inputs by
      digest (existing emitters).
- [ ] All synthetic tests seeded (`default_rng(seed)` as written).
- [ ] C1 h17 commands + docker image tag logged in the experiment doc;
      variant npz reproducible from `$COD` inputs by re-running the logged
      command.

## Testing Strategy

**Unit (in-phase, test-first):** caveat encoding/propagation; pinned
characterization test gating the `all_pairs_cross_acf` vectorization;
windowed channelizer flatness + white-noise power level (Phase 3); config
provenance completeness; figure-render regressions.

**Integration:** the Phase-2 blinded calibration matrix is the integration
test (estimator → nuisance training → injection recovery → full gate chain
→ validation.json); Phase-4 campaign rerun end-to-end.

**Manual:** figure reviews (predeclared visual-vetting rule); blinding
audit.

**Test Data:** retained pol-resolved freya products at
`~/Data/Faber2026/dsa110/upchan_codetections/crossacf-2026-07-14/`; real
off-pulse background blocks from the same product (calibration inputs);
synthetic arrays generated in-test; freya baseband `singlebeam_*.h5`
already on h17 `$COD` (Phase 3 only).

## Migration Strategy

No behavior change to shipped defaults until Phase 4: algorithms 1–2 and
existing configs stay untouched; the vectorized estimator (behavior-pinned),
new upchannelizer flags, and the validation scripts are
additive. **Rollback:** conditional phases land via focused PRs — reverting
the config PR restores the diagnostic-only state; products are new files,
never overwrites. **Backward compatibility:** `finalize_measurement_status`
caveat kwarg defaults to `None` (existing callers unaffected).

## Risk Assessment

1. **Risk:** C1 fails its low-modulation calibration cells (B4 failed
   injection recovery on the same data; the first diagnostic's on-pulse fit
   was unconstrained).
   - **Likelihood:** Medium-High · **Impact:** Low (defined next rung)
   - **Mitigation:** the decision doc declares a C1 failure a valid
     conclusion (product is information-limited); Phase 3 is predefined;
     manuscript already carries the DOCUMENTED-FAIL story.
2. **Risk:** vectorization silently changes the estimator's numerics.
   - **Likelihood:** Medium · **Impact:** High
   - **Mitigation:** pinned characterization test over every `CrossACF`
     field (rtol 1e-10) written against the current implementation BEFORE
     the rewrite; the three existing behavioral tests stay green.
3. **Risk:** blinding integrity questioned — `diagnose_freya_c1.py` already
   ran one on-pulse fit (single-template, unconstrained) before any freeze.
   - **Likelihood:** Medium · **Impact:** High (a contested unblind voids
     the qualification claim)
   - **Mitigation:** record the diagnostic as pre-freeze exploratory in the
     experiment README; derive `frozen_config.json` exclusively from
     off-pulse/window-proving criteria with that provenance stated; the
     unconstrained diagnostic numbers must not inform any threshold,
     window, or hyperparameter; blinding audit is a manual success
     criterion.
4. **Risk:** Phase-3 windowed path too slow for U=512 targets (mahi,
   johndoeII) at Phase 4.
   - **Likelihood:** Medium · **Impact:** Medium
   - **Mitigation:** freya-first gating means sample-wide cost is only paid
     on a win; the mahi `fftsize=2U` slow-path precedent shows overnight
     h17 runs are acceptable; batch per target.
5. **Risk:** a route passes on freya but fails visually sample-wide.
   - **Likelihood:** Medium · **Impact:** Medium
   - **Mitigation:** per-burst figure review gate in Phase 4; DOCUMENTED-FAIL
     remains a valid per-burst exit; uniform-methods rule prevents rescue
     hacks.

## Edge Cases and Error Handling

1. **Case:** freya variant product has different fine-channel count than
   configs assume (oversample changes grid).
   - **Expected:** `grid_regularization` (`freya_chime.yaml`) handles
     uniform grids as no-op; builder writes the actual frequency axis into
     the npz — `run_analysis` reads it, no config change needed.
   - **Implementation:** assert grid uniformity in the Phase-3 build step
     (`np.allclose(np.diff(freq), df)`), abort the variant otherwise.
2. **Case:** calibration run crashes mid-matrix.
   - **Handling:** `run_c1_calibration.py` writes per-cell checkpoints
     (pattern: trigger-calibration campaign's 68-cell checkpoints) and is
     idempotent on rerun; partial `validation.json` never written
     (write-once at end, temp file + rename).
3. **Case:** upper-limit-only bursts (isha, johndoeII) certify gates in
   Phase 4.
   - **Handling:** `measurement_eligibility` caps their reported status at
     upper limits regardless of gate outcome; caveat field makes this
     visible in results JSON (Phase 1 wiring). No silent promotion.

## Performance Considerations

- Calibration matrix: 24 cells × 128 trials ≈ 3,072 estimator calls; at the
  current ~30 s/call that is ~26 CPU-days — hence vectorization first
  (target ≥50×, bringing the matrix to ≈ 0.5 day at 4 workers). Offload to
  h17 if the achieved speedup falls short.
- Phase-3 h17: ~1 GB h5 pull already cached per target; windowed path is
  python-loop-slow only for U≥256 targets (Phase 4 only, overnight).

## Documentation Updates

- [ ] `pipeline/analysis/chime-scintillation/README.md` + `INVENTORY.yaml`
      — candidate entries and (either branch) updated "Current scientific
      answer".
- [ ] `experiment-chime-scint-c1-calibration.md` (new, Phase 2; extended by
      Phase 3 if run).
- [ ] `docs/rse/ACTIVE_LANES.md` — "CHIME C1 qualification" lane status as
      phases complete.
- [ ] `plan-chime-scint-gamma-campaign.md` — eligibility correction
      (Phase 1).
- [ ] `DATA_PROVENANCE.md` §7c — note the caveat encoding now lives in the
      registry.
- [ ] Journal (≤10 min cadence during active work) + readiness board per
      standing rule.

## Timeline Estimate

- Phase 1: ~half a day · Phase 2: ~1 day code (vectorize, validate script)
  plus ~0.5–2 days matrix wall-clock · Phase 3 (conditional): ~2 days ·
  Phases 4–5 (conditional): ~2–3 days.

## Open Questions

*None.* (v1.0 approach + hamilton resolution: owner-approved 2026-07-14
morning. v1.1 restructure to the decision-aligned C1 sequence:
owner-approved 2026-07-14 evening. Upstream corrected-product source:
confirmed none expected — the revival path runs entirely through this
repo's own routes, per the decision doc and `DATA_PROVENANCE.md`.)

---

## References

**Research Documents:**
- [Research: CHIME scint measurement state](research-chime-scint-measurement.md)

**Governing Decision & In-Flight Lane:**
- [Decision: Figure 1 + CHIME C1 route](decision-2026-07-14-figure1-and-chime-c1.md)
- [Handoff: C1 estimator + first diagnostic](../../../pipeline/docs/rse/specs/handoff-2026-07-14-22-09-c1-allpairs-crossgp.md)
- `docs/rse/ACTIVE_LANES.md` — "CHIME C1 qualification" lane

**Files Analyzed:**
- `pipeline/scintillation/scint_analysis/cross_acf.py:230,363` ·
  `pipeline/scintillation/scint_analysis/tests/test_cross_acf.py:157`
- `pipeline/analysis/chime-recovery-2026-07-12/validate_freya_highband_crossacf.py:44`
- `pipeline/analysis/chime-scintillation/experiments/c1-allpairs-crossgp/diagnose_freya_c1.py:55`
- `pipeline/scintillation/scint_analysis/{chime_artifact_guards,chime_product,chime_correction_validation,pipeline,analysis}.py`
- `pipeline/analysis/chime-recovery-2026-07-12/{validate_freya_h2,validate_freya_h3,validate_freya_additive_covariance,run_freya_gate}.py`
- `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py`
- `pipeline/scripts/run_chime_scint_campaign.py`
- `pipeline/scintillation/configs/{chime_products.yaml,bursts/freya_chime.yaml,bursts/freya_chime_hi.yaml}`
- `pipeline/analysis/chime-scintillation/{README.md,INVENTORY.yaml}` + experiment bundles
- `pipeline/scintillation/DATA_PROVENANCE.md` · `sections/results.tex:215-271`

**External Documentation:**
- `chimefrb/baseband-analysis:latest` docker image (baseband_analysis 1.9.0) — usage constraints in `upchannelize_chime.py` docstring.

---

## Review History

### Version 1.0 — 2026-07-14
- Initial plan; experiment-gated ladder + hamilton candidate-with-caveat
  approved by owner via in-session question.

### Version 1.1 — 2026-07-14 (same day)
- Reconciled with the owner decision doc
  (`decision-2026-07-14-figure1-and-chime-c1.md`, merged PR #43) and the
  in-flight C1 handoff. C1 = `c1-allpairs-crossgp` promoted to the
  first-class Phase 2 (vectorize → `validate_freya_c1.py` → blinded 24-cell
  matrix → go/no-go). v1.0's C2/C3 removed per the decision's stop rule
  (estimator tuning on the retained product is forbidden after a C1 fail).
  Windowed re-upchannelization retained as the conditional Phase-3
  successor (`p1-window-upchan`). H2 battery harness dropped. Phases
  renumbered 6→4, 7→5. Restructure owner-approved in-session.
