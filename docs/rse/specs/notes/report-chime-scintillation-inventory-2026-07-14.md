# CHIME scintillation qualification inventory

**Date:** 2026-07-14

**Pipeline pin:** `dsa110-FLITS` `91a5120ed702d04530b9c3aae32d53a3861e87bd` ([PR #174](https://github.com/jakobtfaber/dsa110-FLITS/pull/174))

**Scope:** CHIME data and CHIME-specific validation only; DSA-110 measurements are excluded.

**Result:** **zero qualified CHIME scintillation-bandwidth measurements.**

The canonical machine-readable inventory is
[`pipeline/analysis/chime-scintillation/INVENTORY.yaml`](../../../../pipeline/analysis/chime-scintillation/INVENTORY.yaml),
with external input provenance in
[`DATA_MANIFEST.yaml`](../../../../pipeline/analysis/chime-scintillation/DATA_MANIFEST.yaml).
The human entry point is the adjacent
[`README.md`](../../../../pipeline/analysis/chime-scintillation/README.md).

## Qualification results

| Route | Target/input | Outcome | Decisive evidence |
| --- | --- | --- | --- |
| H0 rank-1 smoke test | Freya retained CHIME product | exact reconstructed failure; diagnostic only | low-band on/off width ratio `1.658` fails; high band `2.218` passes |
| A1 additive covariance | Freya plus injections | documented failure; diagnostic only | low-band held-out covariance and width/coverage/modulation recovery fail |
| H2 rank-2 calibration | Freya plus injections | documented failure; diagnostic only | injection, window, time-split, comb, held-out-kernel, and manual-review gates fail |
| H3 stationary-kernel whitening | Freya plus injections | documented failure; diagnostic only | held-out kernel and injection recovery fail; whitening is not applied on-pulse |
| B3 polarization cross-ACF | Freya high band | documented failure; diagnostic only | 11/12 off-pulse controls retain coherent structure; every `m=0.3` injection cell fails |
| B4 four-stream cross-ACF | Freya high band | documented failure; diagnostic only | null passes, but `m=0.15–0.30` recovery fails; the real product has only `m≈0.15–0.17` |
| Recovered notebook replay | Freya surviving product | falsified | inherited window is off-pulse and 24 matched controls reproduce the fitted scale |
| A1 trigger calibration | 60 null + 8 two-component synthetic cells | campaign complete, trigger unusable | 1% threshold `Delta ln Z = 59699.69283336272`; all eight power cells have zero escalation probability |

The H2 fitted widths (`38.616 kHz` at `523.268 MHz` and `64.989 kHz` at
`723.076 MHz`) and the B4 on-pulse Lorentzian are retained as diagnostics, not
measurements. A precise fitted number does not override a failed qualification
gate.

There is no qualified Oran CHIME detection in the inventory. No Oran CHIME
measurement bundle exists to adjudicate, and none of the Freya-only diagnostic
successes can be transferred to another burst.

## Trigger-calibration figure

![A1 trigger detection power is zero throughout the tested alternative grid.](../../../../pipeline/analysis/chime-scintillation/experiments/trigger-calibration/figures/a1_power_curves.png)

At the calibrated 1% operating point, detection power is zero for every tested
width ratio and component-amplitude ratio. The campaign itself completed and
is reproducible; the scientific outcome is a failed trigger design, not a
successful detection.

## Artifact repair completed

- Preserved the complete 68-cell trigger campaign, aggregate report, three
  diagnostic figures, validation record, and SHA256 manifest.
- Reconstructed the exact H0 JSON from the retained rank-1 product at the
  historical analysis commit.
- Regenerated and visually reviewed all four missing H2 PNG diagnostics.
- Converted A1, H2, H3, B4, replay, and trigger artifacts to explicit relative
  paths with SHA256 provenance; the generators now emit portable manifests.
- Landed the complete B3 and B4 bundles plus the recovered-notebook replay and
  falsification evidence.
- Renamed the two A1 surfaces in the canonical index as `a1-covariance` and
  `a1-trigger-calibration`.

## Consequence for the manuscript program

The CHIME scintillation lane remains scientifically open even though its
artifact-repair and inventory work is complete. A qualified measurement now
requires a new or revised estimator/product route that passes real-background
nulls, low-modulation injection recovery, stability checks, and visual review.
The present artifacts can constrain that redesign, but they cannot support a
CHIME bandwidth, a CHIME two-screen inference, or an Oran detection claim.
