# Review the RFI preservation limits on a controlled dynamic spectrum

- Type: `wayfinder:prototype` (HITL)
- Status: closed
- Assignee: Codex
- Blocked by: [Build the verified Zach CHIME preprocessing baseline](16-build-verified-zach-chime-preprocessing-baseline.md)
- Map: [ApJ submission](../map-apj-submission.md)
- Authorization: owner request, 2026-07-21

## Question

Do the proposed signal-preservation limits look scientifically appropriate
when applied to a controlled Zach dynamic-spectrum example?

Build a development-only review artifact without opening any sealed test data.
Use a burst-like injection with known truth and synthetic interference, then
show:

1. the injected truth dynamic spectrum;
2. the same injection with synthetic interference;
3. the output of the current rejected cleaner, used only as an illustrative
   candidate;
4. the output-minus-truth residual and explicit mask; and
5. concise pass/fail annotations for every proposed preservation limit.

Include the time profile and fluence by broad frequency slice beside the
dynamic spectra where needed to make hidden redistribution visible. Bind the
source, injection, random seed, code, environment, and output hashes. The
artifact is diagnostic only: it cannot validate the cleaner or admit science.

Resolution requires owner review of the figure and either acceptance or
revision of the proposed preservation limits.

## Observed-event supplement — 2026-07-21

Owner requested the candidate cleaner applied to a real sample event. The
supplement uses Zach's observed CHIME/FRB Stokes-I product. The first version at
commit `bd149c00` is invalid: it used the 5.24-ms scintillation sub-window
`[232,248)` and treated array column number as a common time coordinate.

The replacement is coherently dedispersed at the source H5
`tiedbeam_power.DM_coherent` value, `262.4359033801 pc cm^-3`, then aligned
without wraparound from each coarse channel's `fpga_count`. The independent fit
of the H5 cutout-start schedule corresponds to `263.247551 pc cm^-3`; that is a
time-coordinate property, not the coherent filter or a manuscript dispersion
measure. The aligned review shows the 14.42-ms on-pulse interval `[229,273)`
inside the 35.39-ms display `[197,305)`, with 10.49 ms of off-pulse padding on
each side. It adds a time-integrated on-pulse spectrum for visual RFI review.

Only off-pulse training columns `[55,137)` and source-context columns
`[149,305)` are loaded as numerical samples. The public validation interval and
sealed test interval remain unopened.

- Figure: [real Zach method comparison](../../verify/rfi-real-event-review-20260721/real_zach_rfi_method_comparison.svg)
- Machine record: [JSON](../../verify/rfi-real-event-review-20260721/real_zach_rfi_method_comparison.json)
- Exact script: [`review_real_zach_rfi_cleaner.py`](../../../../scripts/review_real_zach_rfi_cleaner.py)
- Remote evidence:
  `/data/Faber2026/evidence/zach-chime-rfi-review-correction-20260721/`
- Reproduction: pinned, network-disabled `baseband-analysis` container runs
  `review-1` and `review-2` have byte-identical output manifests.

Result: the cleaner retains 50,250 of 55,744 measured frequency rows and drops
5,494 rows (9.86%). On retained rows, its values equal the bandpass-only result
exactly; the maximum absolute difference is `0.0`. The visible effect is thus
support removal. Because the observed event has no known truth, this supplement
does not establish whether the removed rows are interference or signal and does
not validate the cleaner. Absolute arrival time remains uncertified.

### Owner review outcome — 2026-07-21

Rejected for revision. The owner identified obvious residual RFI between
700–750 MHz. The strongest retained on-pulse spectral row is 738.876 MHz with a
time-integrated value of 206.22, 18.39 times the retained-band median-based
spread above its median. Twenty retained rows exceed 100 and lie between
737.405–739.200 MHz.

The current candidate is therefore insufficient. Do not tune a frequency cut or
threshold on Zach: the next method must be specified independently and tested
against known truth before returning to this observed-event review.

This ticket remains open for a revised candidate and repeat owner review.

## Pixel-6 replacement attempt — 2026-07-21

The independently specified replacement retained the package row masks and
added a fixed two-dimensional mask after normalization: every finite,
row-valid pixel with absolute standardized intensity at least `6.0` became
explicit missing data. Threshold and code were frozen before Zach application.

Known-truth recovery improved to 98.69% overall, 99.66% for the broadband
impulse, and 100% for the drifting line. The candidate nevertheless failed
three protected measurements: morphology by 17.70 measurement uncertainties,
normalized residual by 14.47, and spectral modulation by 1.33. It is rejected.

On Zach, the same frozen code lowered the 700–750 MHz outlier score from 18.39
to 6.36 and removed all integrated rows above 100. The review panel also shows
that it clips the burst: the rejected-pixel mask follows the burst and the time
profile peak falls materially. This is not acceptable RFI cleaning.

- [Synthetic known-truth review](../../verify/rfi-time-frequency-candidate-20260721/synthetic/rfi_preservation_review.svg)
- [Synthetic machine record](../../verify/rfi-time-frequency-candidate-20260721/synthetic/rfi_preservation_review.json)
- [Zach rejected-candidate review](../../verify/rfi-time-frequency-candidate-20260721/zach/real_zach_rfi_method_comparison.svg)
- [Zach machine record](../../verify/rfi-time-frequency-candidate-20260721/zach/real_zach_rfi_method_comparison.json)
- Remote evidence:
  `/data/Faber2026/evidence/rfi-time-frequency-candidate-20260721/`
- Exact final reruns: `synthetic-{1,2}` and `zach-{5,6}` have byte-identical
  manifests within each pair.

The ticket remains open. Owner review may confirm the rejection visually, but
cannot promote Pixel 6. A future candidate must be specified from known truth,
not tuned on Zach.

## Protected off-pulse seed-row revision — 2026-07-21

The first whole-row revision used off-pulse standard deviation and lag-one
correlation. Although it passed its near-threshold known-truth case, it selected
only seven Zach rows and left the strongest marked-band residuals unchanged.
It is not promoted.

The revised saturated-row component uses no on-pulse samples. An absolute
standardized-intensity seed of six is promoted to a whole-row veto only when at
least four distinct seed rows occur in the same 64-row CHIME coarse group.
Columns with seed occupancy above 1% are excluded from row learning as
broadband, time-local evidence.

Known truth: all 84 injected saturated rows were recovered on each of three
full-grid seeds; no saturated intensity survived; no clean-control rows were
added; added burst-support loss was 0.138–0.143%. The three broadband-impulse
columns were excluded on every seed. A fresh-container repeat was
byte-identical.

On Zach, the frozen component:

- removes 1,649 of the 50,250 package-retained fine rows (3.28%);
- removes 350 rows in 600–650 MHz and 274 in 700–750 MHz;
- lowers the strongest 600–650 MHz spectral value from 99.70 to 84.82;
- lowers the strongest 700–750 MHz value from 206.22 to 119.37;
- reduces rows above 100 in 700–750 MHz from 20 to 3;
- changes the on-pulse profile peak by −0.44%; and
- leaves retained values exactly unchanged.

- [Owner-review figure](../../verify/rfi-horizontal-row-candidate-20260721/real_zach_rfi_method_comparison.svg)
- [Machine record](../../verify/rfi-horizontal-row-candidate-20260721/real_zach_rfi_method_comparison.json)
- [Known-truth experiment](../../specs/experiment-rfi-offpulse-seed-promotion.md)
- Remote Zach evidence:
  `/data/Faber2026/evidence/rfi-horizontal-row-candidate-20260721/`
- Remote known-truth evidence:
  `/data/Faber2026/evidence/rfi-offpulse-seed-promotion-experiment-20260721/`
- Exact Zach runs: `zach-seed-1` and `zach-seed-2` have byte-identical
  manifests.

Owner outcome: rejected. The owner still saw missed horizontal RFI in
700–750 MHz. The exact seed-only outputs remain preserved as `zach-seed-1` and
`zach-seed-2`; they are not the current review artifact.

## Isolated strong rows plus protected raw-voltage tails — 2026-07-21

The bounded revision fixes two independently diagnosed misses without using a
frequency-specific rule or any protected burst sample:

- any isolated off-pulse row seed with absolute standardized intensity at
  least six is accepted after simultaneous broadband columns are excluded;
- a raw-H5 parent coarse channel is accepted when protected voltage-amplitude
  kurtosis exceeds 4.5 median-based-spread units after simultaneous broadband
  voltage times are excluded.

Known truth precedes the real application. The row component recovers 84/84
injected saturated rows on all three seeds, leaves no injected saturated
intensity, selects 0–1 clean-control row, and removes 0.52–0.53% of injected
burst support. The voltage component recovers 28/28 contaminated coarse
channels on all three seeds, selects no clean or broadband-control channel, and
is invariant to every protected value. Both seed-2026072101 repeats are
byte-identical.

On Zach, the frozen union:

- removes 3,516 of 50,250 package-retained fine rows;
- retains 46,734 of 55,744 source rows (83.84%);
- selects 531 rows in 600–650 MHz and 803 in 700–750 MHz;
- selects 33 raw-voltage parent coarse channels, including 739.0625 MHz;
- removes every 700–750 MHz integrated row above 100;
- changes the on-pulse profile peak by +0.21%; and
- leaves every retained value exactly unchanged.

- [Full owner-review figure](../../verify/rfi-horizontal-row-candidate-20260721/real_zach_rfi_method_comparison.svg)
- [700–750 MHz review](../../verify/rfi-horizontal-row-candidate-20260721/real_zach_rfi_700_750_mhz_review.svg)
- [Machine record](../../verify/rfi-horizontal-row-candidate-20260721/real_zach_rfi_method_comparison.json)
- [Strong-row known truth](../../specs/experiment-rfi-offpulse-seed-promotion.md)
- [Raw-voltage known truth](../../specs/experiment-rfi-protected-voltage-kurtosis.md)
- Exact Zach runs: `zach-voltage-7` and `zach-voltage-8`; manifest SHA-256
  `831fa5c4b9ed0df347f3a9b59e35ef281d11625a3fb6c34a9a8bcdea24a7dcd7`.

Owner outcome: rejected as far too aggressive. The composite removed broad
coarse-channel blocks, visibly erasing much of roughly 718–745 MHz. Runs
`zach-voltage-7` and `zach-voltage-8` remain preserved only as failed evidence.
Their figure is not the current review surface.

## Manual bad-channel authority — 2026-07-21

Owner decision: manually zap channels for every event, store the resulting bad-
channel maps, and use those maps downstream. Automated RFI diagnostics may
inform review but may not promote channels into science masks.

Implemented safeguards:

- all twelve events are indexed for both CHIME/FRB and DSA-110;
- each map is bound to an exact frequency-axis SHA-256 and row count;
- ranges are exact, half-open, sorted, non-overlapping row intervals with
  recorded frequency limits, reason, and evidence;
- only `owner_approved` maps with reviewer and review time may be consumed;
- approved rows become explicit missing data and retained values are unchanged;
- frequency-axis drift invalidates a map rather than silently remapping it.

The first Zach CHIME/FRB atlas is generated from bandpass-only measured support;
no package RFI row mask and no manual zap is applied. The earlier atlas that
started after package masking is invalid and preserved separately.

- [Manual-map policy and queue](../../../../analysis/rfi/manual-bad-channels/README.md)
- [Zach CHIME/FRB 700–750 MHz atlas](../../verify/manual-bad-channel-review-20260721/zach-chime/zach_chime_manual_zap_atlas_700_750.svg)
- [Atlas provenance](../../verify/manual-bad-channel-review-20260721/zach-chime/zach_chime_manual_zap_atlas_700_750.json)
- Map loader: [`manual_bad_channels.py`](../../../../scripts/manual_bad_channels.py)
- Atlas generator: [`manual_bad_channel_atlas.py`](../../../../scripts/manual_bad_channel_atlas.py)
- Remote evidence:
  `/data/Faber2026/evidence/manual-bad-channel-review-20260721/`

The atlas also exposes diagonal time-local RFI; a one-dimensional channel map
cannot remove that without zapping the full swept band, so that class remains
explicitly separate from channel-row authority.

## Resolution — owner-approved manual authority, 2026-07-22

The owner approved the regenerated before/after artifact and its five exact
Zach CHIME/FRB ranges: 490 manual rows. The approved effective mask is the exact
union of 9,792 source-unavailable rows and those manual rows, with zero overlap:
10,282 bad rows and 55,254 retained rows.

Authoritative h17 directory:
`/data/Faber2026/evidence/manual-bad-channel-review-20260721/zach-chime/approved/`

- approved map SHA-256:
  `d3acc570ac8342982579facadc5d9f90e00a2b9a0a7cd88fd2878662d5a9d62e`
- review SVG SHA-256:
  `d769c3a7191e8fb7fa3a50a59e1eb0294325ed769db7fd6fac58336dc3ff53e5`
- effective mask SHA-256:
  `5de1bd08ff2ea0a3aa8b3ea37f609e6c7530ae14869d4d5e5361609c9adb8038`
- provenance SHA-256:
  `6501fe1bb15a96629e80e6f60d8e206bc955adad144c0128f91b2237033087ee`

Automated candidates remain rejected. The owner-approved manual map is the
complete channel-row authority for Zach CHIME/FRB autocorrelation-function
work. Diagonal or time-local interference remains a separate problem.
