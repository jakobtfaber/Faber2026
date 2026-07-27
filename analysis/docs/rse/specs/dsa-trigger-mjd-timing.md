# DSA-110 trigger times: verified microsecond-precision MJDs for all 12 bursts

Date: 2026-07-27. Status: verified. Scope: the twelve DSA-110 bursts in the
Faber2026 sample. This note is the authoritative statement of how each burst's
absolute trigger time (Modified Julian Date, MJD) is defined, recovered, and
verified. It is written for the manuscript methods section; the durable
evidence records live at the paths in the last section.

## Result

Every burst's trigger MJD is recovered to a numerical precision of about one
microsecond. The recovered values, and the corrections they include relative
to the archived trigger records, are in the certification table below.

## What specnum is, in plain language

The DSA-110 correlator stamps every recorded spectrum with a running integer
counter. `specnum` is that counter value at the moment the search pipeline
triggered: it says "this burst arrived N ticks after the acquisition segment
started", with one tick equal to 65.536 microseconds of the hardware clock.
Because it is an integer written directly into the trigger record, it is exact
— it carries no rounding error. The recorded floating-point trigger time, by
contrast, passed through a text serialization that kept only six significant
digits of the elapsed time in seconds, which at hour-scale elapsed times means
a 0.01-second quantum. The recovery below undoes that rounding exactly, using
the exact counter.

## The timing arithmetic (sufficient to reproduce every value)

Definitions, per burst, from the archived trigger record (`mjds`, `specnum`):

```
itime        = specnum // 4 + 1907                    (heimdall sample index)
elapsed_true = itime * 262.144e-6 s                   (exact hardware clock)
dt_f32       = float32(float32(262.144) * 1e-6)       (IEEE-754 hex 0x39897060)
token        = "%.6g" % float32(float32(itime) * dt_f32)
                                                      (the six-digit elapsed-
                                                       seconds text the search
                                                       pipeline actually wrote)
T_trigger    = mjds + (elapsed_true - token) / 86400  (MJD)
```

Reading the formula: the archived `mjds` equals the acquisition-segment anchor
plus the rounded six-digit token; adding back the difference between the exact
elapsed time and that token removes the serialization rounding while leaving
the anchor untouched. One heimdall sample is four counter ticks
(262.144 microseconds); the constants 4 and 1907 are the search pipeline's
decimation factor and fixed sample offset. The float32 steps replicate the
producer's single-precision arithmetic bit-exactly; using any other precision
can select a neighbouring six-digit token and shift the result by exactly
10 ms, so the float32 sequence above is part of the convention, not an
implementation detail.

Timescale: the values are MJDs in the observatory system clock's UTC (NTP
disciplined). The tie between that clock and true UTC has not been
independently quantified; see the caveats.

## Validation basis (one statement)

The reconstruction, including the float32 serialization step, was tested
against every surviving raw trigger row from the operating era: 150,627 rows
across five retained cluster-output files spanning 2022-03 to 2024-02
reproduce the producer's written token with zero mismatches and zero 10-ms
token flips, and same-run trigger records for two bursts (zach: two sibling
triggers in its own acquisition segment; whitney: six rows spanning four
distinct tokens in its own cluster file) yield a single common segment anchor
to within measurement precision, while either 10-ms alternative displaces the
anchor by exactly ten milliseconds. The residual numerical floor is about one
microsecond, set by float64 storage of the archived `mjds`.

## Certification table

Corrections are (recovered − archived) in microseconds.

| Burst | Event | Trigger MJD (recovered) | Correction (µs) | Basis |
|---|---|---|---|---|
| zach | 220207aabh | 59617.80850364566 | +474.880 | in-run producer records |
| whitney | 220310aaam | 59648.24172075109 | +583.808 | in-run producer records |
| oran | 220506aabd | 59705.59701297033 | +4042.112 | era-validated arithmetic |
| isha | 221113aaao | 59896.386510967975 | −743.040 | era-bracketed arithmetic |
| wilhelm | 221203aaaa | 59916.00175095013 | +4689.536 | era-validated arithmetic |
| phineas | 230307aaao | 60010.37885773464 | +1393.920 | era-validated arithmetic |
| freya | 230325aaag | 60028.071690569974 | −221.568 | era-validated arithmetic |
| johndoeII | 230814aaas | 60170.3609267866 | +2681.984 | era-validated arithmetic |
| hamilton | 230913aaao | 60200.207158079196 | −329.216 | era-validated arithmetic |
| mahi | 240122aaag | 60331.10427998119 | −2726.400 | era-validated arithmetic |
| chromatica | 240203aacl | 60343.83182190782 | −3518.080 | era-validated arithmetic |
| casey | 240229aaad | 60369.37095221912 | −2065.408 | era-validated arithmetic |

"In-run producer records" means the burst's own acquisition run survives and
directly confirms its six-digit token. "Era-validated arithmetic" means the
burst's token follows deterministically from the bit-exact arithmetic proven
on the surviving-row corpus; "era-bracketed" additionally notes the burst date
lies inside the validated date range.

## Trigger-clock verification versus burst-fit TOA uncertainty

This note certifies the trigger clock only: when the search pipeline's clock
said the trigger occurred. It is a property of the recording system. The
time of arrival (TOA) used in any scattering or dispersion analysis carries,
on top of it, the uncertainty of fitting a model to the burst profile
(component choice, reference frequency, dispersion-measure convention). Those
fitting uncertainties are typically far larger than the microsecond trigger
floor and are quantified per analysis, not here.

## Current caveats

- isha (221113aaao): no records from its own acquisition run survive on any
  reachable archive, so its token rests on the era-bracketed bit-exact
  arithmetic rather than a direct in-run check. Its date sits inside the
  validated range and there is zero counter-evidence.
- The absolute tie of the observatory clock to UTC is not independently
  quantified here. A future CHIME–DSA arrival-time comparison serves as an
  independent end-to-end check of the whole chain; it is not used as an anchor
  for any value in this note.

## Source evidence and durable artifacts

All under `~/Data/Faber2026/review/dsa-origin-metadata-20260727/` unless noted:

- `trigger_mjd_microsecond_recovery_v3_FINAL.json` — the authoritative
  per-burst values reproduced in the table above.
- `SUMMARY.md` — capture provenance for the archived trigger records
  (dsa-storage `/mnt/data/dsa110/candidates/candidates/<event>/`, h17 header
  re-reads, h23 recovery of casey's trigger record).
- `token-ambiguity-inrun-resolution-20260727.md` — the in-run confirmations
  for zach (`/mnt/data/bckuph23data/dsa110/T3/2022_2_6_19_34_4/` on
  dsa-storage) and whitney
  (`/mnt/data/dsa110/T2/2022_3_10_1_19_25/cluster_output1646891314.cand`),
  with the sibling rows and anchor arithmetic quoted verbatim, and the
  exhaustive negative search for isha-era records.
- `adversarial-review-usec-recovery.log` — independent adversarial review of
  the reconstruction.
- `dsastorage_capture.json`, `dsastorage_capture_raw.json`, per-burst
  `<burst>.json` — verbatim archived trigger records and filterbank headers
  with checksums.
