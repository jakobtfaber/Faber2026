# Experiment: C1 blinded calibration matrix (`c1-allpairs-crossgp`)

**Date:** 2026-07-14 · **Verdict: NO-GO (DOCUMENTED-FAIL)** · **Blinded:** yes —
no unblinded on-pulse fit exists.

Governing docs: [decision-2026-07-14-figure1-and-chime-c1.md](decision-2026-07-14-figure1-and-chime-c1.md)
(gates, stop rule) · [plan-chime-scint-corrected-products-revival.md](plan-chime-scint-corrected-products-revival.md)
Phase 2 · pipeline result bundle
`pipeline/analysis/chime-scintillation/experiments/c1-allpairs-crossgp/RESULT.md`
(PR jakobtfaber/dsa110-FLITS#176).

## Setup

- Estimator: symmetrized all-pairs distinct-(pol, time-fold) cross products on
  the retained pol-resolved upchannelized freya product (627–800 MHz), LTE
  notch 730–760 MHz, leave-one-out off-pulse template rotation over 12
  held-out windows. Vectorized `all_pairs_cross_acf` (behavior-pinned at
  rtol 1e-10; ~1164× speedup, 0.026 s vs ~30 s per call at freya scale).
- Frozen config sha256 `444652ec…` (window, masks, block map, seeds) written
  before any calibration cell ran; prerequisites all passed (producer parity,
  provenance, alignment peak bin 254 ∈ [253, 268), finite fraction 0.844).
- Matrix: m ∈ {0.10, 0.15, 0.17, 0.20, 0.30, 1.00} × width ∈ {3, 6, 10, 16}
  native channels × 128 seeded trials; deterministic per-cell seeds
  (base 20260714). Gated cells: m = 0.15 and 0.17 (all widths).
- Gates per cell (B4-inherited, unchanged): finite estimates; median |width
  bias| < max(0.10·truth, 0.25·channel); 68% coverage ∈ [0.53, 0.83]; median
  |m bias| < max(0.10·truth, 0.05). Nulls: family-wise max |z| ≤ 4.408
  (α = 0.01, N = 960) over held-out off-pulse + pairing-scramble realizations.

## Cell × gate matrix (128 finite trials in every cell)

Ratios are observed/limit (>1 = violated, **bold**). G = qualification-gated.

| m | width [ch] | width-bias ratio | m-bias ratio | coverage 68% | cell |
|---|---|---|---|---|---|
| 0.10 | 3 | **8.33** | **1.44** | 0.82 | FAIL |
| 0.10 | 6 | **9.17** | 0.94 | 0.83 | FAIL |
| 0.10 | 10 | **9.50** | 0.96 | 0.68 | FAIL |
| 0.10 | 16 | **9.69** | **1.10** | 0.67 | FAIL |
| 0.15 G | 3 | **8.33** | **1.48** | **0.95** | FAIL |
| 0.15 G | 6 | **5.81** | 0.62 | 0.79 | FAIL |
| 0.15 G | 10 | **5.67** | 0.56 | 0.78 | FAIL |
| 0.15 G | 16 | **7.17** | 0.56 | 0.76 | FAIL |
| 0.17 G | 3 | **8.33** | **1.20** | **0.98** | FAIL |
| 0.17 G | 6 | **4.94** | 0.54 | 0.71 | FAIL |
| 0.17 G | 10 | **4.63** | 0.48 | 0.75 | FAIL |
| 0.17 G | 16 | **5.31** | 0.56 | **0.84** | FAIL |
| 0.20 | 3 | **6.15** | 0.91 | **0.97** | FAIL |
| 0.20 | 6 | **3.49** | 0.44 | 0.72 | FAIL |
| 0.20 | 10 | **3.51** | 0.34 | 0.75 | FAIL |
| 0.20 | 16 | **3.66** | 0.45 | **0.84** | FAIL |
| 0.30 | 3 | **3.21** | 0.84 | 0.63 | FAIL |
| 0.30 | 6 | **1.66** | 0.35 | 0.62 | FAIL |
| 0.30 | 10 | **1.70** | 0.28 | 0.62 | FAIL |
| 0.30 | 16 | **1.93** | 0.40 | 0.70 | FAIL |
| 1.00 | 3 | 0.54 | 0.19 | 0.70 | PASS |
| 1.00 | 6 | 0.34 | 0.13 | 0.71 | PASS |
| 1.00 | 10 | 0.39 | 0.17 | 0.67 | PASS |
| 1.00 | 16 | 0.47 | 0.24 | 0.66 | PASS |

**Nulls: FAIL** — max |z| = 4.810 > 4.408 (4 of 24 realizations exceed, both
null kinds); one fail-closed fit-level detection (bound-clear control fit
with an invalid uncertainty estimate counts as a detection under the
hardened post-review rule).

## Interpretation

- 0/8 gated cells pass; the decisive gate is width bias everywhere, with
  coverage and m-bias adding failures in the narrow-width column. Recovery
  histograms show low-m fits collapsing bimodally onto the fit-window bounds
  (~0.003 and 0.25 MHz) — the same low-modulation collapse B4 documented; the
  ~2× pair-count gain from all-pairs products was not enough.
- The clean m = 1.00 row shows the harness (estimator, fit, intervals,
  blinding plumbing) is sound; the failure is regime-specific to
  m ≈ 0.10–0.30 on this product.
- Per the decision doc's stop rule this closes estimator work on the retained
  product: the successor must change input-product information content →
  `p1-window-upchan` (plan Phase 3), a new experiment ID with a fresh frozen
  config and unchanged thresholds.

## Artifacts

- Verdict: `pipeline/.../c1-allpairs-crossgp/calibration_verdict.json`;
  per-cell checkpoints + `nulls.json` under `calibration/`.
- Figures (reviewed, all `match`): `c1_calibration_matrix.png`,
  `c1_recovery_histograms.png`, `c1_nulls.png` + manifest + review.
- Harness: `validate_freya_c1.py` (unblind refuses without hash-bound GO),
  `run_c1_calibration.py`, `plot_c1_calibration.py`.
