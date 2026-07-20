# Research: CHIME scintillation feature measurement / fitting — state and rerun requirements

**Date:** 2026-07-14
**Scope:** internal codebase only (campaign methodology and prior-art lineage were settled in the lane-B campaign; no new external sweep)
**Codebase state:** Faber2026 `main` @ `3e59e9a`, pipeline submodule (`dsa110-FLITS` fork) pinned at `91a5120` (2026-07-14)
**Related Documents:**
[plan-chime-scint-gamma-campaign.md](../plan/plan-chime-scint-gamma-campaign.md) ·
[report-chime-scintillation-inventory-2026-07-14.md](../notes/report-chime-scintillation-inventory-2026-07-14.md) ·
[plan-chime-scint-recipe-parity.md](../plan/plan-chime-scint-recipe-parity.md) ·
[implement-freya-scint-fit-quality.md](../implement/implement-freya-scint-fit-quality.md)

## Question / Scope

Where does CHIME scintillation-bandwidth measurement/fitting stand in this
repo, where does the code live, and what exactly would it take to revive a
qualified CHIME Δν_d measurement (the "corrected-products sample-wide rerun"
trigger recorded at campaign closeout)?

In scope: the scint estimation package and its gates, the corrected-product
builder and its validation, the 12-burst campaign runner and configs, the
2026-07-13 campaign outcome and 2026-07-14 qualification inventory, and the
concrete precondition chain for a rerun. Out of scope: DSA-110 measurements
(qualified separately), external prior art, any new estimator design (that is
planning work).

## Codebase Findings

### 1. Campaign outcome (authoritative record)

- Lane-B campaign terminal state 2026-07-13: **0/12 CHIME bursts certify
  Δν_d**; DOCUMENTED-FAIL sample-wide under fail-closed gates
  ([plan-chime-scint-gamma-campaign.md:89](../plan/plan-chime-scint-gamma-campaign.md)).
  Freya's 36–45 kHz fitted widths pin to the ~35 kHz instrumental scale under
  all six preprocessing×lag sweep variants; the γ anchor is unavailable.
- The manuscript already reports this: fail-closed gate description and
  per-burst failure table `tab:chime_scint_gates` at
  `sections/results.tex:215-271`.
- The hamilton/chromatica "threshold-marginal" reading (off/on width ratios
  1.72 and 1.94 vs the 2.0 boundary) was **falsified** by the
  uncertainty-aware null probe: on-pulse widths sit *inside* the off-pulse fit
  population (hamilton log-z = 0.41, chromatica 0.90), so a spread-aware
  boundary fails them more decisively, not less
  ([plan-chime-scint-gamma-campaign.md:91](../plan/plan-chime-scint-gamma-campaign.md);
  regression pinned to the hamilton numbers in dsa110/dsa110-FLITS#51,
  commit `9237e4c`).
- The 2026-07-14 qualification inventory consolidates the Freya
  corrected-product/estimator routes: H0 rank-1 smoke, A1 additive covariance,
  H2 rank-2 calibration, H3 stationary-kernel whitening, B3 polarization
  cross-ACF, B4 four-stream cross-ACF, recovered-notebook replay, and the A1
  trigger calibration **all failed, were falsified, or delivered zero
  detection power**. Canonical machine-readable index:
  `pipeline/analysis/chime-scintillation/INVENTORY.yaml`
  (`qualified_chime_measurements: 0`); human entry point
  `pipeline/analysis/chime-scintillation/README.md`; narrative summary
  [report-chime-scintillation-inventory-2026-07-14.md](../notes/report-chime-scintillation-inventory-2026-07-14.md).

### 2. Estimation / fitting package

All CHIME scint code lives in the pinned submodule under
`pipeline/scintillation/scint_analysis/` (flat package: modules at package
root, plus `reference_arc/` originals and `tests/`).

| Concern | Where |
| --- | --- |
| ACF Lorentzian + generalized-Lorentzian models | `pipeline/scintillation/scint_analysis/analysis.py:42-62` (`lorentzian_component`, gen-Lorentzian), model registry ~`:121-137` |
| Δν_d convention (HWHM γ vs FWHM) | `analysis.py:234-242` (`_bandwidth_fields`) |
| γ frequency-scaling fit (sub-band power law) | `analysis.py:781-784` (scaled initial guesses), `analysis.py:847` (`_interpret_scaling_index`), `analysis.py:950` (`joint_2d_gamma_scaling`) |
| 2-D joint time–frequency fitting | `fitting_2d.py` |
| Cross-ACF (polarization / four-stream routes) | `cross_acf.py` |
| ACF evidence / model comparison | `acf_evidence.py` |
| Modulation index m(t), m(ν) | campaign products retained as gated diagnostics; verdict logic in `chime_artifact_guards.py:418` |
| Orchestration per burst | `pipeline.py` (gate wiring at `pipeline.py:386-472`), CLI `run_analysis.py:29` |
| Reference (Nimmo-lineage) recipe originals | `reference_arc/` (rescued via dsa110-FLITS#162), parity test `tests/test_reference_arc_parity.py` |

### 3. Fail-closed qualification gates

`pipeline/scintillation/scint_analysis/chime_artifact_guards.py`:

- `CHIME_REQUIRED_MITIGATIONS` (`:49-54`): `instrumental_background_correction`,
  `grid_regularization`, `bandpass_normalization`, `harmonic_mask`.
- `chime_provenance_status` (`:128`) — fail-closed: any missing/disabled
  mitigation demotes a CHIME result to `diagnostic_only`. Non-CHIME telescopes
  exempt.
- `off_pulse_null_verdict` (`:185`) — off-pulse ACF fit population vs on-pulse
  width (hard off/on ≥ 2.0 ratio; non-gating `off_log_z` / `off_log_mad_sigma`
  spread statistics recorded alongside).
- `low_lag_stability_verdict` (`:280`) — two-sided stability under low-lag
  excision (config `low_lag_excision_bins`, wired at `pipeline.py:386`).
- `harmonic_mask_systematic` (`:380`) — coarse-channel comb systematic
  (0.390625 MHz spacing; dsa110-FLITS#130).
- `modulation_index_verdict` (`:418`) — physicality bound m ≤ 1.5.
- `subband_support_verdict` (`:454`) — ≥ 3 valid sub-bands for γ.
- `finalize_measurement_status` (`:480`) — combines the above; wired into
  per-burst results at `pipeline.py:419-472`.

### 4. Corrected-product builder and its validation

- `chime_product.py` — provenance-bearing paired corrected/raw CHIME npz
  builder. Correction is applied **before** frequency-dependent alignment
  (burst track masked, common instrumental time mode estimated from remaining
  samples; padded placement, never circular wrap — module docstring).
  `SUPPORTED_CORRECTION_ALGORITHMS` (`chime_product.py:21-24`):
  `robust_coarse_rank1_v1`, `robust_coarse_rank2_v1`. Emits SHA256 manifests
  (`write_chime_products`, `verify_product_manifest`) and off-pulse
  diagnostics.
- CLI: `pipeline/scintillation/scripts/build_chime_product.py`.
- Validation/adjudication: `chime_correction_validation.py`
  (`adjudicate_chime_result:21`, `combine_science_status:47`,
  `injection_recovery_summary:54`, `kernel_crosscheck:104`), tests in
  `tests/test_chime_correction_validation.py`. Gating of corrected products
  landed in the fork ("feat(scint): gate corrected CHIME products",
  e.g. `8146137`).
- **Critical status:** both supported correction algorithms already failed
  the freya qualification battery (H0 rank-1 exact reconstructed failure; H2
  rank-2 documented failure across injection/window/time-split/comb/held-out
  gates — inventory §Qualification results). The machinery is sound and
  reproducible; the *algorithms* do not qualify.

### 5. Campaign runner, configs, data

- Runner: `pipeline/scripts/run_chime_scint_campaign.py` — all 12 bursts
  (`BURSTS` list `:25-28`), uniform full-band tier from shipped
  `{nick}_chime.yaml`, supplementary `{nick}_hi` band-restricted tier where a
  `_hi` config exists, freya factor-isolation sweep; bounded local
  parallelism, per-job isolated output dir with results JSON + figures +
  `figures.manifest.json`.
- Configs: `pipeline/scintillation/configs/bursts/*_chime.yaml`; target
  registry `pipeline/scintillation/configs/chime_products.yaml`
  (`measurement_eligibility`: freya = `qualification`; isha, johndoeII =
  `upper_limit_only`; the other nine = `candidate`).
- **Config gap (mechanism of the sample-wide provenance failure):** no shipped
  burst config contains an `instrumental_background_correction` block, and
  only `freya_chime_hi.yaml:65` has `bandpass_normalization`. Two of the four
  required mitigations are therefore absent by construction →
  `chime_provenance_status` demotes every uniform-tier CHIME result to
  `diagnostic_only` (e.g. `freya_chime.yaml` has `grid_regularization` and
  `harmonic_mask` enabled, the other two missing).
- Data: 12 CHIME npz per `pipeline/scintillation/DATA_PROVENANCE.md` — h17
  upchan inputs at `$COD/upchan_codetections/`, local npz at
  `~/Data/Faber2026/dsa110/scintillation-data/` (symlinked so
  `${FLITS_ROOT}/scintillation/data/{nick}_chime.npz` resolves). External
  input hashes: `pipeline/analysis/chime-scintillation/DATA_MANIFEST.yaml`.

### 6. Stale-memory correction (verified this session)

Project memory `flits-fork-rewrite-2026-07-13.md` recorded the scint/DM lane
as dropped from the pin, re-land pending. Verified false at pin `91a5120`:
`pipeline/scintillation/scint_analysis/` is fully present (package + tests +
`reference_arc/`), the campaign landed (dsa110/dsa110-FLITS#50, #51), and the
qualification inventory (#174) sits on top. Memory updated 2026-07-14.

## Synthesis

The CHIME scint lane is **methodologically complete and scientifically
open**: estimator, gates, corrected-product builder, validation harness,
campaign runner, and manuscript integration all exist and are reproducible,
but zero measurements qualify.

The recorded rerun trigger — "corrected CHIME products landing sample-wide" —
is **necessary but not sufficient**. The precondition chain for any revival:

1. **A new or revised correction/estimator route.** The two shipped
   algorithms (`robust_coarse_rank1_v1`, `robust_coarse_rank2_v1`) and every
   estimator route built on them already failed the freya qualification
   battery. Re-running the existing code sample-wide would reproduce
   `diagnostic_only` outcomes by construction.
2. **Qualification on freya first.** Any candidate route must pass the
   predeclared battery on the qualification target: real-background off-pulse
   nulls, low-modulation injection recovery (the real product sits at
   m ≈ 0.15–0.17; B4 failed recovery at m = 0.15–0.30), two-sided low-lag
   stability, held-out checks, and visual review. The inventory's retained
   diagnostics (H2 fitted widths, B4 on-pulse Lorentzian, trigger-power
   surfaces) constrain that redesign.
3. **Sample-wide corrected products.** Build paired corrected/raw npz for all
   12 bursts via `build_chime_product.py` with SHA256 manifests.
4. **Config enablement.** Add `instrumental_background_correction` and
   `bandpass_normalization` blocks to the uniform-tier configs so
   `chime_provenance_status` can pass (uniform methodology across all 12 —
   owner's uniform-methods rule; no per-burst method cherry-picking).
5. **Campaign rerun + re-adjudication** via `run_chime_scint_campaign.py`,
   gates re-run per burst, figure review per the visual-vetting rule.

Candidate-revival expectations should stay calibrated: hamilton and
chromatica have the best morphology but their off-pulse null failures are
robust (log-z 0.41/0.90), not threshold-marginal; casey_hi/whitney-class were
named at closeout as possible beneficiaries of a valid correction. Note an
eligibility discrepancy worth resolving in planning: the campaign plan lists
isha/hamilton/johndoeII as lower-confidence upper-bound bursts
([plan-chime-scint-gamma-campaign.md:20-21](../plan/plan-chime-scint-gamma-campaign.md)),
while the shipped registry encodes only isha and johndoeII as
`upper_limit_only` and hamilton as `candidate`
(`pipeline/scintillation/configs/chime_products.yaml`). Neither class may be
silently promoted.

Open questions (for planning, not research):

- What correction family could plausibly pass where rank-1/rank-2 common-mode
  failed — e.g. per-channel time-dependent gain models, cross-ACF variants
  with better null behavior, or upstream re-upchannelization changes?
- Is there any upstream (CHIME-side) corrected-product source expected, or is
  "corrected products landing" entirely this repo's own build?
- Cosmetic figure bugs from closeout (ΔBIC panel empty, johndoeII glyph
  dropout, y-tick overprints) — fold into any rerun or fix separately?

## Addendum (2026-07-14, same day — supersedes parts of the Synthesis)

This document's internal pass scanned `research-*`/`plan-*` specs but missed
`decision-*.md`: the owner decision
[decision-2026-07-14-figure1-and-chime-c1.md](../decision/decision-2026-07-14-figure1-and-chime-c1.md)
(merged PR #43) had already selected **`c1-allpairs-crossgp`** — an
all-pairs, cross-fitted polarization/time-fold estimator on the retained
pol-resolved product — as the next qualification route, with a predeclared
blinded calibration matrix and a stop rule: after a C1 failure, no further
estimator tuning on the retained product; the successor must change
input-product information content. This resolves the Synthesis's first open
question (correction family) by owner decision, and narrows the sanctioned
successor to product regeneration (e.g. windowed/oversampled fine
re-channelization).

C1 is in flight: core estimator `all_pairs_cross_acf`
(`pipeline/scintillation/scint_analysis/cross_acf.py:363`) + tests + a
first freya diagnostic (marginal; single off-pulse template insufficient),
uncommitted on branch `scint/c1-allpairs-crossgp` — see
[handoff-2026-07-14-22-09-c1-allpairs-crossgp.md](../../../../pipeline/docs/rse/specs/handoff-2026-07-14-22-09-c1-allpairs-crossgp.md).
Execution now follows
[plan-chime-scint-corrected-products-revival.md](../plan/plan-chime-scint-corrected-products-revival.md)
v1.1 (decision-aligned sequence).

## References / Sources

- Code (pin `91a5120`):
  `pipeline/scintillation/scint_analysis/chime_artifact_guards.py:49,128,185,280,380,418,454,480` ·
  `pipeline/scintillation/scint_analysis/pipeline.py:386-472` ·
  `pipeline/scintillation/scint_analysis/analysis.py:42,234,781,847,950` ·
  `pipeline/scintillation/scint_analysis/chime_product.py:21-24` ·
  `pipeline/scintillation/scint_analysis/chime_correction_validation.py:21,47,54,104` ·
  `pipeline/scripts/run_chime_scint_campaign.py:25` ·
  `pipeline/scintillation/configs/bursts/freya_chime.yaml` ·
  `pipeline/scintillation/configs/chime_products.yaml` ·
  `sections/results.tex:215-271`
- Records: `pipeline/analysis/chime-scintillation/{README.md,INVENTORY.yaml,DATA_MANIFEST.yaml}` ·
  `pipeline/scintillation/DATA_PROVENANCE.md` ·
  [plan-chime-scint-gamma-campaign.md](../plan/plan-chime-scint-gamma-campaign.md) status log ·
  [report-chime-scintillation-inventory-2026-07-14.md](../notes/report-chime-scintillation-inventory-2026-07-14.md)
