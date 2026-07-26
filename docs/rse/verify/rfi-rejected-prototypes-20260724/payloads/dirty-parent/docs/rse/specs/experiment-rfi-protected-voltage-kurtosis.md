# Experiment: Protected raw-voltage amplitude tails

---
**Date:** 2026-07-21
**Author:** Codex
**Status:** Component experiment complete; full-coarse application rejected
**Related Documents:**
- [Implementation plan](plan-rfi-horizontal-row-component.md)
- [Strong-row experiment](experiment-rfi-offpulse-seed-promotion.md)
---

## Question

Can raw CHIME/FRB voltage amplitudes identify contaminated parent coarse
channels that the derived-intensity row rule misses, without reading the burst
or mistaking a simultaneous broadband event for a bad channel?

## Frozen rule

1. Coherently dedisperse the Zach raw H5 at its recorded
   `tiedbeam_power.DM_coherent` value, `262.4359033801 pc cm^-3`.
2. Permit only the existing training block `[55,137)` and source-context block
   `[149,305)`, expressed at native voltage cadence. Exclude the aligned
   on-pulse interval `[229,273)` independently for every coarse-channel shift.
3. Before measuring a channel, exclude allowed times where eight-standard-
   deviation voltage events occur simultaneously in more than 1% of valid
   coarse channels.
4. Measure Pearson kurtosis of voltage amplitude per coarse channel on the
   remaining support.
5. Iteratively select only the high tail above 4.5 median-based-spread units.
   Map a selected parent coarse channel to its matching fine-frequency rows.
6. Replace selected values with explicit missing data. Do not interpolate,
   zero-fill, or alter retained values.

## Known-truth setup and results

Each of three deterministic complex-voltage grids contained 871 coarse
channels, two polarizations, and 4,096 time samples. Twenty-eight evenly spaced
channels received independent impulsive contamination outside the protected
burst. A three-time-sample broadband event was added to every channel as a
control. Separate clean, broadband-only, and protected-value-mutated controls
were evaluated.

| Seed | Contaminated channels recovered | Additional channels | Clean control | Broadband-only control | Protected invariant |
|---|---:|---:|---:|---:|---:|
| 2026072101 | 28/28 | 0 | 0 | 0 | yes |
| 2026072102 | 28/28 | 0 | 0 | 0 | yes |
| 2026072103 | 28/28 | 0 | 0 | 0 | yes |

The selected known-truth support fraction is `28/871 = 3.215%`. A fresh
container repeat of seed 2026072101 is byte-identical; both JSON files have
SHA-256
`c032292d8e156640eb3d1e56e81635873474af09babd15963845e87f5ae74576`.

## Real-data probe

On Zach, coarse channel ID 156 at 739.0625 MHz has amplitude kurtosis `5.6364`
and a robust score of `12.81`; it is independently selected from training-only
and context-off-pulse-only support. Under the revised 4.5 cutoff, 33 coarse
channels are selected. The result is used only as one component of the
development review; Zach has no known RFI truth.

## Reproducibility

- Raw H5:
  `/data/Faber2026/data/chime-frb/zach/singlebeam_210456524.h5`
- Raw H5 SHA-256:
  `215079a689c18b50a4b2cd8003529e34d531a326be677a86187be02e47d0f1a9`
- Remote known-truth evidence:
  `/data/Faber2026/evidence/rfi-voltage-kurtosis-experiment-20260721/`
- Revised code and results: `code-v2/` and `results-v2/`.
- Remote raw-data probe:
  `/data/Faber2026/evidence/rfi-raw-voltage-kurtosis-probe-20260721/`
- Container:
  `chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41`
- Candidate module SHA-256:
  `f5751abd56410e7d28774d265c7cb576361adf070f2d676fd49b389a7b65194e`
- Experiment script SHA-256:
  `1ee821d70aa1e5fd00b31664657b71981d49a35dc2d2258dd2ead41b7638d471`

## Interpretation

This establishes only a protected coarse-channel amplitude-tail diagnostic. Its
real Zach application mapped each selected parent to every fine row and erased
broad frequency blocks; the owner rejected it as far too aggressive. It is not
a bad-channel authority and cannot justify manuscript measurements.
