# Time-of-arrival analysis status

Last updated: July 27, 2026. This is a temporary working summary, not a
manuscript source or a scientific approval record.

## Bottom line

The DSA and CHIME time axes are now understood well enough to define fitted
arrival times consistently. Neither side should yet be described as having a
fully certified absolute timing uncertainty in the manuscript.

| Data set | Internal time coordinate | Absolute-time status | Current rule |
| --- | --- | --- | --- |
| DSA filterbanks | Native samples are 32.768 microseconds apart (display filterbanks); the trigger-search chain ran at 262.144 microseconds per search sample (65.536 microseconds per counter tick). | Verified: all twelve trigger MJDs are recovered to about one microsecond of numerical precision under the production trigger arithmetic, confirmed against every surviving raw trigger row (zero mismatches) and, for zach and whitney, against records from their own observing runs. | Use the recovered trigger MJDs (authoritative note: `analysis/docs/rse/specs/dsa-trigger-mjd-timing.md`). The archived catalog MJDs carry up to ±5 ms of serialization rounding; the currently pinned cross-match products still use those archived values. |
| CHIME single-beam H5 files | Native samples are 2.56 microseconds apart. | Incomplete: the H5 metadata gives a precise internal time coordinate on the station clock's UTC scale — not an independently calibrated absolute UTC epoch — and no recovered CHIME clock-accuracy guarantee. | Use the H5 time-coordinate conversion; do not quote a certified absolute UTC/MJD uncertainty until CANFAR acquisition/timing provenance is recovered. |

## DSA: what we know

The DSA trigger records retain an exact integer spectrum counter, `specnum`.
The trigger system also serialized an elapsed-time value at limited precision,
so the many decimal places in archived trigger MJDs can conceal a
millisecond-scale rounding error.

For the verified production trigger convention (empirically established from
the surviving raw trigger rows; the display-filterbank sample of 32.768
microseconds is a factor of two finer than the counter tick and must not be
used in the trigger arithmetic):

```text
counter tick (specnum unit)  = 65.536 microseconds
search-sample interval       = 4 ticks = 262.144 microseconds
itime                        = specnum // 4 + 1907
elapsed time (exact)         = itime * 262.144 microseconds
```

The recovery replaces the rounded serialized elapsed-time term with the exact
integer-counter value, replicating the producer's single-precision
serialization bit-exactly. It was validated against 150,627 surviving raw
trigger rows spanning 2022-03 to 2024-02 with zero mismatches, and confirmed
inside zach's and whitney's own observing runs. The former required check
(runtime sample-interval evidence) is satisfied; the authoritative statement is
`docs/rse/specs/dsa-trigger-mjd-timing.md` on the Faber2026-analysis `main`
branch (merged as pull request #154, commit `b34e16c`). Note the local
`analysis/` checkout currently sits on another work branch
(`h17-postreorg-inventory`), so that path is not materialized in the working
tree until the checkout or submodule pin advances; retrieve it meanwhile with
`git -C analysis show origin/main:docs/rse/specs/dsa-trigger-mjd-timing.md`,
or read the labeled exported copy at `status/dsa-trigger-mjd-timing.md`.
Evidence records (including the in-run token resolution
`token-ambiguity-inrun-resolution-20260727.md`) live under
`~/Data/Faber2026/review/dsa-origin-metadata-20260727/`; a labeled exported
copy of that record is at `status/token-ambiguity-inrun-resolution-20260727.md`.

**Interpretation:** the trigger-to-raw-data time mapping is accurate at
roughly the microsecond level (numerical floor about 1 microsecond). A fitted
DSA TOA still needs its own model-fit uncertainty and its own stated
reference-frequency/DM convention, and the absolute tie of the observatory
clock to UTC remains unquantified.

## CHIME: what we know

All twelve canonical single-beam H5 files on H17 were inspected. They contain:

```text
delta_time = 2.56 microseconds
time coordinate = time0.ctime + time0.ctime_offset + sample_offset
sample_offset[n] = n * delta_time
```

The imported `baseband-analysis` implementation reconstructs the same
coordinate and can form a TOA by adding the fitted pulse offset and applying a
dispersion correction to the selected 400 MHz reference convention. This
establishes a well-defined H5-relative/UTC coordinate. It does **not** by
itself establish CHIME's absolute clock uncertainty.

The raw H5 files are traceable to ARC VOSpace source paths through local
fixtures. The missing evidence is the original CANFAR notebook/acquisition
record and timing-system documentation that applies to the relevant event and
processing version. H17 does not currently have a working direct ARC listing
path, so this provenance has not yet been refreshed from CANFAR.

## What to report today

For either telescope, a paper-ready TOA needs all of the following stated
separately:

1. The fitted arrival-time definition and reference frequency.
2. The DM and propagation-model convention used to refer the time to that
   frequency.
3. The statistical uncertainty from the two-dimensional fit.
4. The time-axis/absolute-clock status from this document.

Do not use the number of printed decimal places in a trigger JSON, filterbank
header, or H5 attribute as evidence of absolute timing precision.

## Evidence locations

- DSA derivation and review evidence: `~/Data/Faber2026/review/specnum-epoch-recon/`.
- DSA raw-source metadata capture: `~/Data/Faber2026/review/dsa-origin-metadata-20260727/`.
- CHIME raw-data guide on H17:
  `/data/Faber2026/data/chime-frb/README-TIME-AXIS.md`.
- CHIME imported source on H17:
  `/data/research/astrophysics/frbs/chime-dsa-codetections/baseband-analysis-canfar-src/`.

## Next CHIME–DSA cross-match

Do not run or publish a new cross-match until every event has:

1. The CHIME H5 path, file checksum, and event identity.
2. The selected dispersion measure and its source.
3. The 400 MHz arrival-time convention.
4. A burst-model arrival time and statistical fit uncertainty for each band.
5. The recovered DSA trigger MJD and its provenance category.
6. Separate fields for the CHIME and DSA absolute-clock systematics. An
   unknown value must remain explicitly unquantified, not replaced by the
   native sample interval or by zero.

The cross-match output must report the geometric correction, dispersion
referral, model-fit uncertainty, trigger/frame reconstruction status, and
absolute-clock status separately. Until both observatory-clock ties are
quantified, or the relative inter-site clock contribution is independently
bounded, report the CHIME–DSA residual as a consistency diagnostic without a
fully numerical absolute uncertainty or formal significance.

Current implementation check:

| Requirement | Current state |
| --- | --- |
| CHIME H5 identity and checksum | All twelve canonical H17 paths, byte sizes, and SHA-256 checksums are frozen in `status/chime-dsa-crossmatch-input-readiness.csv`; the current code input schema does not yet carry a checksum. |
| Dispersion measure | `pipeline/crossmatching/chime_side_inputs.json` carries a DSA value for all twelve events and an independently constrained CHIME value for eight; the run must freeze the selected value and source explicitly. |
| 400 MHz convention | Implemented as the default in `pipeline/crossmatching/chime_singlebeam.py`. |
| Formal arrival-time fit uncertainty | Missing from the current CHIME extractor, which returns a smoothed peak sample and native sample interval rather than a model-fit uncertainty. |
| Recovered DSA trigger time | Verified for all twelve events, but the pinned cross-match inputs still carry the archived rounded values. |
| Absolute-clock status | The observatory-clock tie is unquantified for both CHIME and DSA and is not represented separately in the current cross-match input or output schema. |

Therefore the next safe work is schema and input-manifest preparation. Running
the current extractor would reproduce a peak-sample diagnostic, not the
paper-ready paired arrival-time measurement.

The readiness CSV is an input inventory, not a run file. Its shared DSA
dispersion measures are labeled as current candidates; every row remains
`ready_for_crossmatch=NO` until the dispersion-measure source is approved, both
model fits exist with statistical uncertainties, and the separate clock
systematics are carried.

## Remaining required checks

- **DSA trigger reconstruction (complete 2026-07-27):** the time-step convention is confirmed from the
  surviving raw trigger rows and in-run records; the microsecond trigger-MJD
  recovery is verified for all twelve bursts. Remaining DSA item: the pinned
  cross-match products still use the archived (uncorrected) trigger MJDs;
  re-pointing them at the recovered values is a separate analysis step.
- **CHIME event timing:** recover and match the CANFAR acquisition/timing
  provenance to the archived event and processing version.
- **Cross-observatory clock calibration:** neither observatory clock's tie to
  UTC is independently quantified here. Before quoting a fully numerical
  absolute cross-match uncertainty, quantify both ties or independently bound
  their relative contribution. Never substitute a native sample interval (or
  zero) for an unquantified clock systematic.
