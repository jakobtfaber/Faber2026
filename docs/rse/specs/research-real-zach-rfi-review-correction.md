# Research: Correct the real Zach RFI review

**Date:** 2026-07-21
**Scope:** Internal code, configuration, H5 metadata, and live h17 products
**Code state:** Parent `3eaa7e85`; pipeline `ab6af1f7`
**Related Documents:** [RFI review ticket](../wayfinder/tickets/rfi-validation-01a-review-preservation-dynamic-spectrum.md)

## Question / Scope

Why did the real-event RFI figure use the wrong dispersion measure and clip the
burst, and what exact transformation is required before rebuilding it with a
time-integrated spectrum?

## Codebase Findings

### The old crop was a scintillation sub-window

`pipeline/scintillation/configs/bursts/zach_chime.yaml:8-18` fixes
`manual_burst_window: [232,248]` with `padding_factor: 0.0`. That is a
scintillation extraction window, not a full morphology or review window. Its
duration is 5.24288 ms. The independently recorded Zach CHIME envelope is
14.21 ms before review padding (`docs/analysis/dm/window-sweep.md:145-152`).

### Three distinct dispersion measures were conflated

- The worker uses the DSA-110 reference value `262.368 pc cm^-3`
  (`pipeline/configs/bursts.yaml:140-148`; worker target at
  `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py:128-136`).
- The H5 `tiedbeam_power` dataset records coherent dedispersion at
  `262.4359033801 pc cm^-3`; the voltage dataset has no dispersion-measure
  attribute (`docs/rse/specs/validation-zach-chime-preprocessing-baseline.md:153-164`).
- A direct fit of H5 `time0.fpga_count` against the cold-plasma delay law gives
  `263.247551 pc cm^-3`, with 0.755 microsecond root-mean-square residual. This
  is the frequency-dependent cutout-start schedule, not the coherent filter.

The independently derived time-alignment sweep gives `262.4312 pc cm^-3`
(`docs/analysis/dm/window-sweep.md:145-152`), agreeing with the H5 detected-power
coherent value to 0.0047 pc cm^-3. The older CHIME arrival-regression value
`261.524` (`pipeline/crossmatching/dm_provenance.csv:2`) is not the H5 time-axis
or coherent-filter reference. A live differential run at 261.524 increased the
450–800 MHz peak separation to about 8.19 ms; it is retained only as a failed
hypothesis under
`/data/Faber2026/evidence/zach-chime-dm261.524-review-20260721/`.

### Column index is not a shared time coordinate

The worker calls `coherent_dedisp(..., time_shift=False)` and retains per-channel
`fpga_count` metadata
(`pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py:327-360`).
The old review plotted a common column index and ignored those channel start
times. It therefore did not have one physical time axis.

For coherent target DM `262.4359033801`, the correct non-wrapping coordinate is

`t = (fpga_count - fpga_ref) * 2.56 us - K_DM * DM * (nu^-2 - nu_ref^-2) + j * 0.32768 ms`.

The row offsets span 15.733 ms, or 48 output bins. After applying them, fixed
50-MHz peak locations span five bins (1.6384 ms), rather than 34 bins
(11.1411 ms), and the five-standard-deviation on-pulse envelope is bins
`[229,273)`. The review display `[197,305)` supplies 10.49 ms of padding on each
side.

## Synthesis

The old artifact is invalid for manual review. Rebuild from the original H5 at
the H5 coherent value, align every row from `fpga_count` without wraparound,
learn bandpass/RFI masks only from off-pulse training bins `[55,137)`, and show
the padded aligned interval `[197,305)`. Integrate the one-dimensional spectrum
only over `[229,273)`. Keep the result diagnostic-only: the alignment is now
defined, but the RFI method still lacks known truth.

## Owner review and residual-RFI diagnosis

The owner rejected the candidate after seeing residual RFI between 700 and
750 MHz in the corrected diagnostic. A deterministic read-only check of the
saved spectrum and final row mask gives:

- retained-band median `10.30` and median-based spread estimate `10.65`;
- maximum `206.22` at `738.876 MHz`, or `18.39` times that spread above the
  median;
- 20 retained rows above `100`, spanning `737.405–739.200 MHz`.

The same assertion failed identically on two runs. It is a diagnostic feedback
loop, not an acceptance limit: `10` times the median-based spread was used only
to make this already owner-observed failure machine-detectable.

The cleaner learns both masks only from the off-pulse training interval
(`scripts/review_real_zach_rfi_cleaner.py:171-209`). A time-resolved probe of
the retained rows found two behaviors. The 738.876-MHz row is strongly
on-pulse (`4.69` mean versus `0.17` off-pulse), while nearby retained rows also
have off-pulse maxima of `14–60`. The evidence therefore rules out a single
pure bandpass explanation: the whole-row training-only mask misses a mixture of
time-local and persistent narrow-frequency structure. The time-integrated panel
and row-decision panel expose that miss
(`scripts/review_real_zach_rfi_cleaner.py:379-428,516-532`).

Zach cannot determine whether every burst-coincident narrow feature is RFI or
astrophysical structure because it has no known truth. The next method must not
be tuned by simply cutting 700–750 MHz or adjusting thresholds on this event.
It needs an independently specified time-frequency detector and known-truth
signal-preservation validation before a new Zach review.

## References / Sources

- `pipeline/scintillation/configs/bursts/zach_chime.yaml:8-18`
- `pipeline/configs/bursts.yaml:140-148`
- `pipeline/analysis/scattering-refit-2026-06/baseband_recovery/upchannelize_chime.py:128-136,327-360`
- `pipeline/crossmatching/dm_provenance.csv:2`
- `docs/analysis/dm/window-sweep.md:145-152`
- `docs/rse/specs/validation-zach-chime-preprocessing-baseline.md:153-164`
- H5: `/data/Faber2026/data/chime-frb/zach/singlebeam_210456524.h5`
- Corrected product evidence: `/data/Faber2026/evidence/zach-chime-rfi-review-correction-20260721/`
