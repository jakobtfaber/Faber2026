# Experiment: RFI preservation dynamic-spectrum prototype

**Date:** 2026-07-21
**Status:** Development only; owner decision pending
**Canonical run:** `run-8`
**Exact reproduction:** `run-9`

## Question

What does the tentative one-measurement-uncertainty preservation limit look
like when the current rejected radio-frequency-interference (RFI) cleaner is
applied to known synthetic burst truth on Zach's verified CHIME grid?

## Controls

- No observed Zach intensity and no sealed benchmark data.
- 65,536 nominal fine positions; 55,744 independently source-valid positions.
- Fixed seed `2026072101`; two-component dispersed and scattered synthetic burst.
- Persistent lines, a 64-row comb, a drifting line, and a broad time impulse.
- Exact package cleaner:
  `baseband_analysis.core.flagging.get_RFI_channels`, mean threshold 5,
  standard-deviation threshold 3.
- Exact rejected order: RFI → bandpass mean/scale → normalize → RFI.
- Container:
  `chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41`.

The saved development bandpass arrays contained 5,118 cleaner-induced missing
values. Run 1 incorrectly treated them as absent source channels and is
invalidated. Final runs interpolate only the synthetic bandpass shape across
those rows while retaining the independent 55,744-position source mask.

## Result

The cleaner retained 51,429 of 55,744 measured rows (92.26%). It recovered
73.99% of injected RFI pixels, but only 20.93% of all rejected pixels were
actually injected RFI. The broad impulse near 137 ms visibly survives.

For this one realization:

| Protected quantity | Cleaner-induced shift | Tentative single-case result |
|---|---:|---|
| Total normalized fluence proxy | 3.20 measurement uncertainties; +0.56% | Outside |
| Arrival time | 0.47; +0.01% | Within |
| Profile width | 0.54; +0.78% | Within |
| Component count | unchanged at 2 | Stable |
| Component separation | unchanged; bootstrap uncertainty zero | Not exercised |
| Dispersion-measure offset | 0.76; +3.93% | Within |
| Two-dimensional morphology correlation | 7.08; −0.02% | Outside |
| Tail-scale proxy | 0.57; +1.94% | Within |
| Spectral modulation | 0.04; −0.02% | Within |
| Frequency autocorrelation half-width | 0.10; +4.84% | Within |

The median and 95th-percentile limits cannot be evaluated with one realization.
This figure can support owner review of the proposed limits; it cannot validate
the cleaner.

## Reproducibility

Remote evidence root:
`/data/Faber2026/evidence/rfi-preservation-prototype-20260721/`.

Runs 8 and 9 produced byte-identical SVG, JSON, and script artifacts:

```text
e08cda8020ada0307431994904bd52460d5214cc59e36309fef558fe9bbc0187  rfi_preservation_review.svg
6fc04cbe69c60a454cf74b3e17e5146c9cf2c46a7fc3d6404610bec540553f6a  rfi_preservation_review.json
2516daee4159b85cb4c1eac80a890429688779e175158fe9ae65cb155cc14a80  prototype_rfi_preservation_review.py
```

Local review packet:
[rfi-preservation-prototype-20260721](../verify/rfi-preservation-prototype-20260721/).

## Run history

- Run 1: invalidated; bandpass missing values were wrongly treated as missing source rows.
- Runs 2–3: corrected source geometry; byte-identical; superseded mask rendering.
- Runs 4–5: corrected mask-density calculation; superseded clipped legend.
- Runs 6–7: correct rendering; superseded by repository whitespace normalization.
- Runs 8–9: final rendering; byte-identical; canonical review evidence.

## Decision gate

Owner must visually review the canonical SVG, then accept or revise the
tentative preservation limits. Until then, the acceptance-contract ticket stays
open and the cleaner stays rejected.
