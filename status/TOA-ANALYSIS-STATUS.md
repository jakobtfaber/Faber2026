# CHIME–DSA time-of-arrival status and DSA trigger-time verification

Last updated: July 27, 2026.

This document consolidates the project timing status, the DSA-110 trigger-time
reconstruction, and the direct checks that resolved the possible 10 ms
serialization error. It is a working technical record, not manuscript text or
a scientific approval record.

## Read this first

- **CHIME/FRB:** the Canadian Hydrogen Intensity Mapping Experiment Fast Radio
  Burst project.
- **DSA-110:** the Deep Synoptic Array 110.
- **HDF5:** Hierarchical Data Format 5, the file format used for the CHIME
  single-beam recordings.
- **Time of arrival (TOA):** a fitted estimate of when the burst reached a
  chosen reference frequency.
- **Modified Julian Date (MJD):** the continuous day count used for the
  timestamp.
- **Dispersion measure (DM):** the electron-column measurement used to refer
  arrival times between radio frequencies.
- **Internal time coordinate:** where a sample lies according to the
  telescope's own clock.
- **Absolute clock accuracy:** how closely that telescope clock follows
  Coordinated Universal Time (UTC).

For a quick status check, read **Current conclusion** and **Requirements for a
paper-ready CHIME–DSA comparison**. The intervening sections contain the
reproducible DSA arithmetic and detailed validation.

These are three separate timing questions:

1. **Where is the recorded data in the telescope's time coordinate?**
2. **What arrival time does a fitted burst model measure?**
3. **How accurately is the telescope clock tied to UTC?**

The DSA trigger reconstruction answers the first question. It does not supply
a fitted burst TOA or quantify the DSA clock's absolute UTC error.

## Current conclusion

| Data set | Internal time coordinate | What is verified | What remains unknown |
| --- | --- | --- | --- |
| DSA-110 filterbanks | Display samples are 32.768 microseconds apart. The trigger search used 262.144 microseconds per search sample, equal to four 65.536-microsecond counter ticks. | All twelve trigger MJDs were reconstructed to about one microsecond of numerical precision using the production trigger arithmetic. The arithmetic matches all 150,627 surviving raw trigger rows. Records from zach's and whitney's own observing runs directly confirm their values. | The statistical uncertainty of each fitted burst TOA and the DSA station clock's absolute offset from UTC. |
| CHIME/FRB single-beam HDF5 files | Samples are 2.56 microseconds apart. Each file defines a precise coordinate on the UTC scale maintained by the CHIME station clock. | The file metadata and imported `baseband-analysis` code agree on the conversion from sample number to the file's time coordinate. | The statistical uncertainty of each fitted burst TOA and the CHIME station clock's absolute offset from UTC. The original CANFAR acquisition and timing record has not been recovered. |

Therefore:

- Use the recovered DSA trigger MJDs below instead of the rounded archived
  values.
- Do not describe either telescope as having a fully quantified absolute UTC
  uncertainty.
- Do not treat native sample spacing as an absolute clock uncertainty.
- Do not infer timing precision from the number of decimal places printed in a
  JSON file, filterbank header, or HDF5 attribute.

## DSA-110 trigger-time reconstruction

### Why reconstruction was needed

The DSA correlator records an exact integer spectrum counter named `specnum`.
One counter tick is 65.536 microseconds. The trigger system also wrote elapsed
time as a single-precision floating-point value formatted with six significant
digits. At hour-scale elapsed times, that text representation changes in
10 ms steps. The archived MJD can therefore differ from the counter-derived
value by up to approximately 5 ms even though it prints many decimal places.

### Reproducible arithmetic

Inputs for each burst are the archived `mjds` value and integer `specnum`:

```text
itime        = specnum // 4 + 1907
elapsed_true = itime * 262.144e-6 seconds

dt_f32       = float32(float32(262.144) * 1e-6)
token        = "%.6g" % float32(float32(itime) * dt_f32)

trigger_mjd  = mjds + (elapsed_true - token) / 86400
```

`itime` is the Heimdall search-sample index. One search sample equals four
counter ticks, or 262.144 microseconds. The fixed offset is 1907 samples.

The `float32` operations reproduce the producer's single-precision arithmetic.
They are part of the timestamp convention: using a different numerical
precision can select a neighboring six-digit token and shift the result by
exactly 10 ms.

The recovered values remain on the UTC scale kept by the observatory's
Network Time Protocol disciplined station clock. The station clock's offset
from true UTC has not been independently quantified.

### Validation

The complete reconstruction was tested against 150,627 surviving raw trigger
rows from five cluster-output files spanning March 2022 through February 2024:

- producer token mismatches: **0**
- 10 ms token flips: **0**
- numerical floor from the archived 64-bit floating-point MJDs: approximately
  **1 microsecond**

An independent implementation repeated the key checks using a structure-based
32-bit floating-point round trip instead of NumPy. It recovered the same
`dt_f32` bit pattern, `0x39897060`, and the same zach and whitney segment
anchors.

### Recovered trigger times

Corrections are recovered MJD minus archived MJD.

| Burst | DSA event | Recovered trigger MJD | Correction (microseconds) | Evidence |
| --- | --- | ---: | ---: | --- |
| zach | 220207aabh | 59617.80850364566 | +474.880 | Direct records from the burst's observing run |
| whitney | 220310aaam | 59648.24172075109 | +583.808 | Direct records from the burst's observing run |
| oran | 220506aabd | 59705.59701297033 | +4042.112 | Arithmetic validated on surviving records from the same observing era |
| isha | 221113aaao | 59896.386510967975 | −743.040 | Arithmetic validated on records before and after the event; no same-run record survives |
| wilhelm | 221203aaaa | 59916.00175095013 | +4689.536 | Arithmetic validated on surviving records from the same observing era |
| phineas | 230307aaao | 60010.37885773464 | +1393.920 | Arithmetic validated on surviving records from the same observing era |
| freya | 230325aaag | 60028.071690569974 | −221.568 | Arithmetic validated on surviving records from the same observing era |
| johndoeII | 230814aaas | 60170.3609267866 | +2681.984 | Arithmetic validated on surviving records from the same observing era |
| hamilton | 230913aaao | 60200.207158079196 | −329.216 | Arithmetic validated on surviving records from the same observing era |
| mahi | 240122aaag | 60331.10427998119 | −2726.400 | Arithmetic validated on surviving records from the same observing era |
| chromatica | 240203aacl | 60343.83182190782 | −3518.080 | Arithmetic validated on surviving records from the same observing era |
| casey | 240229aaad | 60369.37095221912 | −2065.408 | Arithmetic validated on surviving records from the same observing era |

### Direct resolution of the possible 10 ms error

Three bursts initially needed special attention because the six-digit
serialization could have selected a neighboring token.

#### zach: direct same-run confirmation

Source on `dsa-storage.ant.pvt`:

```text
/mnt/data/bckuph23data/dsa110/T3/2022_2_6_19_34_4/
```

The directory is zach's own observing run and contains the event record,
correlator outputs, and sibling candidates. Three records from the same
acquisition segment give one identical segment anchor:

| Event | Producer-written MJD | `specnum` | Token (seconds) | Segment anchor |
| --- | ---: | ---: | ---: | ---: |
| 220207aabe | 59617.7832463485 | 73443696 | 4813.71 | 59617.72753211239 |
| 220207aabg | 59617.78757806146 | 79154528 | 5187.97 | 59617.72753211239 |
| 220207aabh | 59617.80850364017 | 106741952 | 6995.94 | 59617.72753211239 |

The anchors agree at the displayed precision. Tokens 6995.93 and 6995.95
would shift zach's anchor by +9999.820 and −9999.820 microseconds,
respectively. The producer's 6995.94 token is therefore directly confirmed.

#### whitney: direct same-run, multi-token confirmation

Source:

```text
/mnt/data/dsa110/T2/2022_3_10_1_19_25/cluster_output1646891314.cand
```

Six rows in whitney's own cluster file span four tokens and give one identical
segment anchor:

| `specnum` | Producer-written MJD | Token (seconds) | Segment anchor |
| ---: | ---: | ---: | ---: |
| 71488020 | 59648.24172062858 | 4685.54 | 59648.18748984155 |
| 71488172 | 59648.24172074433 | 4685.55 | 59648.18748984155 |
| 71488200 (whitney) | 59648.24172074433 | 4685.55 | 59648.18748984155 |
| 71488316 | 59648.24172086007 | 4685.56 | 59648.18748984155 |
| 71488400 | 59648.24172086007 | 4685.56 | 59648.18748984155 |
| 71488524 | 59648.241720975806 | 4685.57 | 59648.18748984155 |

Tokens 4685.54 and 4685.56 would shift whitney's anchor by +10000.449 and
−9999.820 microseconds, respectively. The producer's 4685.55 token is
therefore directly confirmed.

#### isha: same-era confirmation only

No records from isha's own observing run remain on the reachable archive:

- DSA `T2` date directories end in June 2022.
- DSA `T4` contains no November 2022 directory or event matching `221113`.
- The H23 backup contains localization measurement sets for `221113aaao`, but
  no trigger-time sibling records or November 2022 run directory.

Isha occurred on November 13, 2022, inside the March 2022–February 2024
validation range. Its 3900.17-second token is determined by the bit-exact
producer arithmetic verified on records before and after the event. The
recovered value is supported by same-era arithmetic, not by a direct record
from isha's own run.

## CHIME/FRB time coordinate

All twelve canonical CHIME/FRB single-beam HDF5 files on the H17 data server
were inspected. Their sample-time coordinate is:

```text
delta_time       = 2.56 microseconds
time_coordinate  = time0.ctime + time0.ctime_offset + sample_offset
sample_offset[n] = n * delta_time
```

The imported `baseband-analysis` implementation reconstructs the same
coordinate. It can form an arrival time by adding the fitted pulse offset and
applying the dispersion correction needed to refer the result to 400 MHz.

This establishes a precise coordinate relative to the station clock. It does
not establish that clock's absolute UTC accuracy.

The HDF5 files are traceable to ARC VOSpace source paths through local
fixtures. The missing evidence is the original Canadian Advanced Network for
Astronomical Research (CANFAR) acquisition record and timing documentation for
the relevant event and processing version. H17 currently has no working
direct ARC listing path, so that provenance has not been refreshed from
CANFAR.

## Requirements for a paper-ready CHIME–DSA comparison

Each event needs:

1. CHIME HDF5 path, byte size, checksum, and event identity.
2. Selected dispersion measure and source.
3. One shared 400 MHz reference-frequency convention.
4. A fitted burst arrival time and statistical uncertainty for each
   telescope.
5. Recovered DSA trigger MJD and its evidence category.
6. Separate CHIME and DSA station-clock uncertainties. Unknown values must
   remain explicitly unquantified.

The output must keep these contributions separate:

- geometric delay
- dispersion referral to 400 MHz
- statistical burst-fit uncertainty
- trigger and data-frame reconstruction
- each station clock's UTC status

Until both station-clock ties are quantified, or their relative contribution
is independently bounded, the CHIME–DSA residual is a consistency diagnostic.
It does not have a fully numerical absolute uncertainty or formal
significance.

### Current implementation

| Requirement | Current state |
| --- | --- |
| CHIME file identity and checksum | All twelve canonical H17 paths, byte sizes, and SHA-256 checksums are recorded in `status/chime-dsa-crossmatch-input-readiness.csv`. The current code input schema does not carry a checksum. |
| Dispersion measure | `pipeline/crossmatching/chime_side_inputs.json` contains a DSA value for all twelve events and an independently constrained CHIME value for eight. The selected value and source still need approval. |
| 400 MHz reference frequency | Implemented as the default in `pipeline/crossmatching/chime_singlebeam.py`. |
| Statistical arrival-time uncertainty | Missing. The current CHIME extractor returns a smoothed peak sample and native sample interval, not a model-fit uncertainty. |
| Recovered DSA trigger time | Verified for all twelve events. The pinned cross-match inputs still contain the archived rounded values. |
| Station-clock status | The UTC tie is unquantified for both CHIME and DSA. The current input and output schemas do not represent the two clock terms separately. |

Running the current extractor would produce a peak-sample diagnostic, not a
paper-ready paired arrival-time measurement.

The readiness CSV is an input inventory, not a run file. Every row remains
`ready_for_crossmatch=NO` until the dispersion-measure source is approved,
both model fits exist with statistical uncertainties, and both clock terms are
represented separately.

## Source records

### DSA authority

The source-of-record derivation is:

```text
Faber2026-analysis main
docs/rse/specs/dsa-trigger-mjd-timing.md
pull request #154
commit b34e16c
SHA-256 13bbbc5e48f8c41bd7bdf018e81be5284954264f2f6908db0f0e59f81078acab
```

The local `analysis/` checkout may be on another work branch. Read the
source-of-record version without changing that checkout:

```bash
git -C analysis show origin/main:docs/rse/specs/dsa-trigger-mjd-timing.md
```

### DSA evidence

Under `~/Data/Faber2026/review/dsa-origin-metadata-20260727/`:

- `trigger_mjd_microsecond_recovery_v3_FINAL.json`: per-burst recovered values.
- `SUMMARY.md`: archived-record capture and the superseding direct
  zach/whitney confirmation.
- `token-ambiguity-inrun-resolution-20260727.md`: detailed same-run checks for
  zach and whitney, plus the exhaustive negative search for isha.
- `adversarial-review-usec-recovery.log`: independent review of the
  reconstruction.
- `dsastorage_capture.json`, `dsastorage_capture_raw.json`, and per-burst JSON
  files: archived trigger records and filterbank headers with checksums.

The direct-check record has SHA-256 checksum:

```text
7e15f42b48f9d13cba4bb3ddf539561a196d66e6ad1fe632a2a03069a4768dbb
```

Additional reconstruction material:

```text
~/Data/Faber2026/review/specnum-epoch-recon/
```

### CHIME evidence

- H17 time-axis guide:
  `/data/Faber2026/data/chime-frb/README-TIME-AXIS.md`
- Imported CHIME source on H17:
  `/data/research/astrophysics/frbs/chime-dsa-codetections/baseband-analysis-canfar-src/`

## Remaining work

- Replace the rounded DSA trigger MJDs in the pinned cross-match inputs with
  the recovered values.
- Recover and match the CANFAR acquisition and timing provenance to each CHIME
  event and processing version.
- Produce model-fitted CHIME and DSA arrival times with statistical
  uncertainties.
- Add separate CHIME and DSA station-clock fields without substituting zero or
  native sample spacing for unknown uncertainties.
