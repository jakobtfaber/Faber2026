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

The recovered trigger MJD is not, by itself, the time of sample zero in a
derived SIGPROC filterbank. A fit-ready filterbank observation must additionally
bind the trigger to an exact sample index through a producer receipt or an
independently verified integer-sample construction. The rounded `tstart` header
must not be substituted for that mapping.

For Casey, the owner approved the second route on 2026-08-01. In the raw
filterbank already dedispersed to 491.211 pc cm⁻³, the replayed band-integrated
peak is sample 15259, or 0.500006912 s from sample zero. An unverified
alternative pretrigger convention places an anchor at sample 15256. No
immutable producer artifact validates that convention. Their three-sample
difference is a 98.304 µs mapping ambiguity. It remains separate from the
unchanged clock prior. The owner approved a discrete two-anchor sensitivity on
2026-08-02. Joint fitting remains blocked until both prepared arms are
hash-bound and reviewed. This is an empirical trigger-to-peak binding, not
recovery of the missing producer receipt.

The trigger epoch referral from 1530 MHz to the shared 400 MHz coordinate is an
owner-approved provisional modeling convention, not a recovered producer fact.
It requires a retained reference-frequency sensitivity. At
491.211 pc cm⁻³ the proposed cold-plasma referral is +11.866546044944464 s.
The geometry constraint remains part of the joint fit; it is not used to choose
the anchor.

## Current caveats

- isha (221113aaao): no records from its own acquisition run survive on any
  reachable archive, so its token rests on the era-bracketed bit-exact
  arithmetic rather than a direct in-run check. Its date sits inside the
  validated range and there is zero counter-evidence.
- The absolute tie of the observatory clock to UTC is not independently
  quantified here. A future CHIME–DSA arrival-time comparison serves as an
  independent end-to-end check of the whole chain; it is not used as an anchor
  for any value in this note.

## Casey downstream claim boundary

The value 491.27737153955155 pc cm⁻³ is a coherent-power and
relative-dispersion diagnostic. It does not depend on the absolute
CHIME/FRB–DSA-110 time origins and remains pending independent and owner review.
The value 491.27924166266934 pc cm⁻³ is only a conditional geometry-alignment
sensitivity under the assumption that the recovered trigger epoch is the
DSA-110 burst arrival time; it has no formal uncertainty and is not a formal
dispersion-measure result.

The sole executed Casey joint absolute-timing fit used the rounded filterbank
`tstart` plus crop as its DSA-110 origin, producing an approximately 11.5583 s
origin displacement; the fit diagnostic records a nominal window gap of
11.55608945970681 s. Its `fit-result.json` has SHA-256
`7e88c030152b5b967c28be4d0fc9a3a219b199fcf6438f3272e916c2716846a8`, status
`failed_prior_rail`, and model and timing failures. The associated resolution
packet inherits that origin and contains no fit. Raw-only and exact-time
diagnostic packets avoid the numeric displacement through analysis-derived
trigger-to-peak assignments, but lack the producer mapping and contain no
traceable fit result. The owner-approved Casey trigger-to-peak binding above
permits a new, separately hash-bound preparation run; it does not validate
those historical packets. The legacy fixed-DM crossmatch is unverified.

No existing Casey product supplies a formally quotable geometry-matching DM or
geocentric 400 MHz TOA. These failures do not invalidate the relative or
coherent-power diagnostic above.

## Source evidence and durable artifacts

The current trigger-time authority is
`~/Data/Faber2026/dsa110/trigger_mjd_microsecond_recovery.json`, SHA-256
`87852969eb41c2abfa4c6534557ad03ed4f3e16e64cf1b28bd9da35f4ff89a0e`.
The configured h17 shared-input copy has the same hash. This JSON supplies the
trigger MJD only; it does not supply the filterbank sample-zero mapping.

The current supporting captures are described by
`~/Data/Faber2026/dsa110/origin-metadata/README.md`. Its `bursts/`,
`dsastorage/`, and `h17/` subdirectories contain the retained per-burst trigger
records and filterbank-header captures.
