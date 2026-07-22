# Experiment: Time-frequency RFI candidate

**Date:** 2026-07-21
**Author:** Codex
**Status:** Complete; selected candidate failed integrated preservation checks
**Related Documents:**
[research](research-rfi-time-frequency-candidate.md),
[owner review ticket](../wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md)

## Experiment Goal

Choose between a fixed pixel threshold and connected threshold growth using only
the existing synthetic known-truth development case.

**Primary question:** Which candidate materially recovers intermittent RFI with
the smallest added false rejection beyond the package row-mask baseline?

## Hypothesis

A fixed absolute standardized-intensity threshold of 6 will recover the strong
time-local contaminants. Connected growth from 6 through adjacent pixels above
4 may recover weak edges, but risks growing into protected burst structure.

Success requires higher overall, broadband-impulse, and drifting-line recovery
than the row baseline without tuning on Zach. This experiment does not exercise
the distribution-level acceptance contract.

## Approaches

1. **Row only:** current package mask learned on off-pulse training.
2. **Pixel 6:** row mask plus every finite pixel with absolute standardized
   intensity at least 6.
3. **Connected 6-to-4:** row mask plus eight-connected growth from pixels at
   least 6 through pixels at least 4.

## Setup

- Exact 65,536-row known-truth generator and seed `2026072101`.
- 55,744 independently measured rows; missing positions remain `NaN`.
- Persistent lines, frequency comb, broadband impulse, and drifting line.
- Pinned, network-disabled `baseband-analysis` container.
- Throwaway code:
  `.experiments/rfi-time-frequency/candidate_experiment.py`.
- Remote evidence:
  `/data/Faber2026/evidence/rfi-time-frequency-candidate-20260721/`.

Execution:

```bash
python /work/candidate_experiment.py \
  --input-root /evidence \
  --prototype-script /work/prototype_rfi_preservation_review.py \
  --output /output/experiment.json
```

The first and repeat JSON files are byte-identical with SHA-256
`a178e05088af03c17c7a60afe78158438f598adf91edc8585ca0571475d5d2e7`.

## Results

| Measure | Row only | Pixel 6 | Connected 6-to-4 |
|---|---:|---:|---:|
| All RFI pixels recovered | 73.99% | 98.69% | 98.78% |
| Rejected pixels that are true RFI | 20.93% | 25.74% | 24.64% |
| Broadband impulse recovered | 7.74% | 99.66% | 100.00% |
| Drifting line recovered | 11.16% | 100.00% | 100.00% |
| Persistent lines recovered | 100.00% | 100.00% | 100.00% |
| Frequency comb recovered | 98.28% | 98.29% | 98.29% |
| False rejection on interference-free data | 6.21% | 6.33% | 6.72% |

The row mask accounts for most interference-free rejection. Pixel 6 adds 32,882
rejected clean pixels, about 0.12% of independently measured pixels. Connected
growth adds 145,285, about 0.51%.

On common finite support, Pixel 6 preserves component count and separation. Its
differences from synthetic truth are `+0.0041 ms` arrival time,
`+0.0046 ms` profile width, `+0.00079 pc cm^-3` dispersion-measure offset, and
`+0.0280` normalized-fluence proxy. These are one-realization diagnostics, not
distribution-level acceptance results.

## Initial Comparison and Selection

**Selected for full review: Pixel 6.** It recovers nearly all time-local injected
RFI and improves precision while adding only 0.12% false rejection beyond the
row baseline. Connected growth gains only 0.09 percentage points of recovery,
but rejects roughly four times as many additional clean pixels and lowers
precision.

The threshold is frozen at absolute standardized intensity `6.0` before any
Zach application. If Zach still fails visual review, do not adjust this threshold
on Zach; return to the later frozen benchmark and cleaner-comparison tickets.

## Integrated Review Outcome

The full synthetic review rejected Pixel 6 despite its strong RFI-pixel recall.
Three protected measurements exceeded the tentative one-measurement-uncertainty
limit:

| Protected measurement | Shift in measurement uncertainties | Result |
|---|---:|---|
| Morphology correlation | 17.70 | fail |
| Normalized residual | 14.47 | fail |
| Spectral modulation | 1.33 | fail |

Arrival time, width, fluence, dispersion-measure offset, tail proxy, and
frequency autocorrelation halfwidth stayed within the tentative limit. That
mixed result is still a rejection: a cleaner must preserve every protected
measurement.

The frozen code was then applied to Zach only as the already authorized
diagnostic. It reduced the 700–750 MHz maximum from `18.39` to `6.36`
median-based spread units and removed all rows above an integrated value of 100.
The dynamic mask and burst profile show the cost: bright burst pixels were also
removed and the profile peak fell materially. No threshold was changed after
viewing Zach. Pixel 6 is rejected and cannot advance.

The design error is a scale mismatch. Threshold six was initially compared to
the injected burst's pre-normalization maximum of 2.8, but the mask acts after
division by an off-pulse frequency-row scale. Normalized burst pixels exceed
six and are therefore removed by construction.

## References

- [Research](research-rfi-time-frequency-candidate.md)
- [Original controlled experiment](experiment-rfi-preservation-dynamic-spectrum-prototype.md)
- `.experiments/rfi-time-frequency/candidate_experiment.py`
