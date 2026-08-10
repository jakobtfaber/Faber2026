# Explain the load_band time-factor discrepancy

- Type: `wayfinder:task` (AFK)
- Status: open
- Assignee: —
- Blocked by: —
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: manuscript-owner request, 2026-07-30 (low priority; do not
  investigate ahead of the controlled reruns)

## What to build

Identify what `load_band`'s time-decimation path does beyond averaging adjacent
samples, and record it, so that anything reasoning about that path reasons about
what it actually computes.

## What is known

Producing the owner's 2026-07-30 sampling decision required running the same
archival Zach DSA-110 product through
`scripts/plot_codetection_gallery.load_band` at time factors 1 and 2 with every
other argument held identical. The coarse arm does **not** equal a literal
adjacent-pair mean of the native arm. It differs by a near-constant `0.0997`,
about 0.37 off-pulse standard deviations, with the maximum difference
approximately equal to the median difference — the signature of a constant
offset rather than a shape change.

The cause was identified incidentally while re-deriving the component count and
is recorded here so nobody re-investigates it: `load_band` subtracts a
per-channel baseline taken as the median over the **outer quartiles of the
already-decimated array** (`scripts/plot_codetection_gallery.py:227-232`). The
quartile boundaries and the resulting median differ between the two time
factors, so each arm subtracts a slightly different constant. The independent
re-derivation, which fixes one off-pulse baseline in native time and applies it
to both arms, shows no such offset.

This is intended behaviour, not a defect. What remains is the small
documentation task below.

## Why it is worth a ticket

The retracted 2026-07-29 sampling record asserted that the two arms agree to a
maximum absolute difference of `2.22e-15`, and treated that near-exact identity
as evidence about the decimation. Through the production loader they do not
agree to anything near that tolerance, so the retracted figure presumably came
from an independent averaging step rather than from the path the fits use. Any
other reasoning that assumes the loader performs bare pairwise averaging is
wrong for the same reason.

Nothing here suggests the loader is incorrect, and no result currently depends
on the difference: the sampling comparison counted components inside each arm
after normalising that arm by its own off-pulse statistics, so a constant offset
does not move its conclusion.

## Acceptance criteria

- [x] The step responsible for the offset is identified in the source, by file
      and line.
- [x] Whether the offset is intended behaviour is stated, with the reason.
- [ ] `load_band`'s docstring says that the baseline is recomputed per decimated
      array, so two time factors do not share a zero point.
- [ ] The comparison receipt's `averaging_identity_note` is updated to point at
      the explanation instead of describing the discrepancy.

## Evidence

- `docs/rse/verify/zach-dsa-resolution-comparison-20260730/zach_dsa_resolution_comparison.json`,
  fields `averaging_identity_max_abs_difference` and
  `averaging_identity_note`.
- `docs/rse/verify/zach-dsa-resolution-comparison-20260730/compare_resolution.py`,
  which regenerates the comparison from the archival product.
- [Retract the unsupported Zach sampling decision](unsupported-zach-sampling-decision.md),
  the source of the `2.22e-15` claim.
