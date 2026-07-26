# Experiment: Horizontal RFI structure capture

---
**Date:** 2026-07-21
**Author:** Codex
**Status:** Complete; robust component retained only for the near-threshold synthetic class
**Related Documents:**
- [Research](research-rfi-horizontal-structure-capture.md)
- [Owner review ticket](../wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md)
---

## Experiment Goal

Determine which off-pulse-only method captures stationary, intermittent,
near-threshold contaminated fine-frequency rows without using burst brightness.

**Primary question:** Can a row component fully capture horizontal contaminated
segments while adding no false rows on interference-free controls and losing
less than 0.2% of injected burst support?

This resolves one missing component. It does not select or validate a complete
RFI cleaner.

## Hypothesis

Off-pulse row variability and temporal correlation will detect intermittent
contaminated rows that the package mean/standard-deviation mask and simple
threshold recurrence miss.

Success requires, on every development seed:

- every intermittent contaminated row fully recovered;
- no surviving contaminated run;
- zero added rows on the interference-free control;
- added row-veto burst-support loss below 0.2%; and
- no on-pulse value used in detection.

## Approaches Tested

### Package row mask

Existing whole-row baseline. Low complexity; no new code. It does not represent
intermittent structure directly.

### Robust off-pulse row statistics

Existing repository method: per-row off-pulse standard deviation and lag-one
temporal correlation, iteratively compared across rows with a median-based
spread statistic at threshold five. Medium complexity. Decisions are learned
only from the frozen training window.

### Off-pulse recurrence count

Flag a row after at least two off-pulse values reach absolute normalized
intensity four. Low complexity and analytically interpretable, but it depends on
individual normalized peaks.

The union of robust statistics and recurrence counting was also executed. It
was byte-equivalent in decisions to robust statistics alone.

## Experiment Setup

Throwaway code:
`.experiments/rfi-horizontal-structure/candidate_experiment.py`.

The known-truth generator was extended inside the experiment with 51
fine-frequency rows containing five fixed-frequency segments spanning training,
pre-burst, burst, and post-burst regions. Segment amplitudes range from 3.4 to
4.6 on the standardized injection scale. Exact truth records every contaminated
pixel.

Three deterministic development seeds were run on the full 65,536-row by
512-time-bin grid: `2026072101`, `2026072102`, and `2026072103`. Each approach
was also run on an otherwise identical interference-free control.

## Results

| Method | Fully recovered rows per seed | Longest surviving run | Added clean rows | Burst support lost |
|---|---|---:|---:|---:|
| Package row mask | 16, 14, 18 of 51 | 51 bins | 0 | 0% |
| Robust row statistics | 51, 51, 51 of 51 | 0 bins | 0 | 0.143%, 0.178%, 0.138% |
| Recurrence count | 16, 14, 18 of 51 | 51 bins | 0 | 0% |
| Union | 51, 51, 51 of 51 | 0 bins | 0 | same as robust |

The robust method added 88, 114, and 86 row vetoes on contaminated cases. No
additional row was selected on any clean control. Some added rows belong to
other injected RFI classes, so the count exceeds the 35–37 intermittent rows
that survived the package baseline.

The full preprocessing chain still fails protected measurements because this
row component does not remove the separate broadband impulse and drifting-line
contamination. Maximum measurement shifts remain 17.07, 11.88, and 10.68
measurement uncertainties. These failures forbid calling the result a complete
cleaner; they do not negate the exact horizontal-row recovery result.

Compared with the package baseline, robust row selection increases some
individual shift magnitudes by at most 0.41 measurement uncertainty across the
three seeds. This is consistent with its small, explicitly measured loss of
frequency support and remains a required diagnostic on Zach.

## Comparison and Recommendation

**Recommendation for this near-threshold class: robust off-pulse row
statistics.** It is the only tested approach here that recovers every
intermittent row on every seed, leaves no contaminated run, and adds no
clean-control rows.

The later Zach application invalidated it as the response to the owner-marked
saturated rows: it selected only seven rows and left the strongest 600–650 and
700–750 MHz residuals unchanged. It is therefore not the revised Zach
candidate. The separate [protected off-pulse seed promotion experiment](experiment-rfi-offpulse-seed-promotion.md)
targets that different interference class.

- Do not add the recurrence counter; it contributes no decisions.
- Do not restore Pixel-6 or connected growth; they use burst-bearing pixels and
  already failed signal preservation.
- Do not describe the robust row component as a complete cleaner. It must later
  be combined with independently qualified time-local components.

The frozen diagnostic configuration is median-based spread threshold `5.0`, at
most six iterations, using only off-pulse standard deviation and lag-one
temporal correlation. No Zach frequency, spectrum, or mask was used to choose
these values; they are the existing repository defaults.

## Reproducibility

- Host: h17, 40 logical CPUs, Intel Xeon Silver 4210 at 2.20 GHz.
- Container:
  `chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41`.
- Container runtime: Python 3.11.15, NumPy 1.26.4, SciPy 1.16.0.
- Network disabled; CPU-only; each run limited to four CPUs and 5 GiB.
- Experiment code SHA-256:
  `5636fade41c9fb95cf8033fcb299fca89d313f0b8a399fa2b00ac94f7525d4a5`.
- Robust method source SHA-256:
  `dc85377ab98c99ecb563ba94c972f85349ac7e9df8cbe579e9c7babd413fdb45`.
- Prototype source SHA-256:
  `e283a66d089e738de0839e00660bcde3224efb98abb2e4c8e38dc318987a26cc`.
- Remote evidence:
  `/data/Faber2026/evidence/rfi-horizontal-structure-experiment-20260721/`.
- Input hashes are the existing Zach synthetic-geometry packet; frequency,
  support, bandpass mean, bandpass scale, and exact package audit hashes are
  `02c794...cba2`, `b183f4...a39e`, `472a58...b753`, `e30822...27c`, and
  `5df48f...0c83` respectively.

Exact execution pattern:

```bash
docker run --rm --network none --memory 5g --cpus 4 \
  -v /data/Faber2026/evidence/zach-chime-preprocessing-20260721:/evidence:ro \
  -v /data/Faber2026/evidence/rfi-horizontal-structure-experiment-20260721/code:/work:ro \
  -v /data/Faber2026/evidence/rfi-horizontal-structure-experiment-20260721/results:/output \
  chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41 \
  python /work/candidate_experiment-v2.py \
  --input-root /evidence \
  --prototype-script /work/prototype_rfi_preservation_review.py \
  --auto-rfi-script /work/auto_rfi_flag.py \
  --seed 2026072101 \
  --output /output/seed-2026072101-v2.json
```

An independent fresh-container repeat of seed `2026072101` is byte-identical:
both JSON files have SHA-256
`cce56b78a51d3c4d8a0bfc2dcd27f59d6ca11f1f8dbd170a0b38f6ee5cb878a9`.

## Outcome

The robust row component was implemented and failed the real Zach review. The
four-row seed gate also failed owner review. The current bounded revision and
its preserved evidence are documented in
[the implementation report](implementation-rfi-horizontal-row-component.md).
The Wayfinder ticket remains open for owner review; time-local contamination
also remains unresolved.

## References

- [Research](research-rfi-horizontal-structure-capture.md)
- `.experiments/rfi-horizontal-structure/candidate_experiment.py`
- `pipeline/scintillation/scint_analysis/auto_rfi_flag.py`
- `scripts/prototype_rfi_preservation_review.py`
