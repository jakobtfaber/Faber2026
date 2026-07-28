<!-- LABELED LOCAL EXPORT derived from the named authority; the whole file is NOT byte-identical to it because of this header line. AUTHORITY: ~/Data/Faber2026/review/dsa-origin-metadata-20260727/token-ambiguity-inrun-resolution-20260727.md, sha256 7e15f42b48f9d13cba4bb3ddf539561a196d66e6ad1fe632a2a03069a4768dbb. BODY of this file (everything after this first line) has that same sha256 — verify: tail -n +2 <this file> | shasum -a 256. Do not edit this copy. -->
# In-run resolution of the ±10 ms serialization-token ambiguity (zach, whitney, isha)

Date: 2026-07-27. Author: Faber2026-claude-code session (read-only remote evidence
gathering; local arithmetic). Task: repowire ask-7e12e275 from the coordinator.

Objective: determine, from DSA-side evidence alone (no CHIME arbitration), which
±10 ms serialization-token alternative is correct for the three bursts marked
AT-RISK in `trigger_mjd_microsecond_recovery_v2.json`. Phase: verification.
Inputs frozen: `trigger_mjd_microsecond_recovery_v3_FINAL.json` values were not
modified; this receipt is additive.

## Arithmetic used (identical to v3)

- `dt_f32 = float32(float32(262.144) * 1e-6)` seconds per heimdall sample
- `itime = specnum // 4 + 1907`
- `token = "%.6g" % float32(float32(itime) * dt_f32)` (the producer's printed
  elapsed-seconds value)
- run anchor `A = mjds − token/86400`; within one acquisition segment A must be
  constant; a wrong token displaces A by exactly ±10 ms.

## zach (220207aabh) — token 6995.94 CONFIRMED in-run

Source (read-only ssh, alias `dsastorage`, host dsa-storage.ant.pvt):
`/mnt/data/bckuph23data/dsa110/T3/2022_2_6_19_34_4/` — zach's own run directory
(h23 backup), 80 files, including `220207aabh.json`, `220207aabh.png`,
`corrNN_220207aabh_{data.out,header.json}` and 25 sibling candidate JSONs.

Same-acquisition-segment siblings (counter re-arm occurred earlier in the run;
segment membership by monotonic specnum vs mjds):

| trigname | mjds (producer-written) | specnum | token | anchor |
|---|---|---|---|---|
| 220207aabe | 59617.7832463485   | 73443696  | 4813.71 | 59617.72753211239 |
| 220207aabg | 59617.78757806146  | 79154528  | 5187.97 | 59617.72753211239 |
| 220207aabh | 59617.80850364017  | 106741952 | 6995.94 | 59617.72753211239 |

All three anchors identical (Δ = 0.000 µs at 11-decimal print precision).
Alternatives 6995.93 / 6995.95 displace zach's anchor by +9999.820 / −9999.820 µs.
Consequence: the 6-week era-extrapolation caveat for zach is eliminated — the v3
arithmetic reproduces producer tokens bit-exactly inside his own run.

## whitney (220310aaam) — token 4685.55 CONFIRMED in-run

Source: `/mnt/data/dsa110/T2/2022_3_10_1_19_25/cluster_output1646891314.cand`
(whitney's run; 2169 cluster_output*.cand files span the day). Her actual
producer row: printed mjds `59648.24172074433` (equals her T2 `mjds` exactly),
specnum 71488200. Six same-cluster rows spanning four distinct tokens:

| specnum | mjds (printed) | token | anchor |
|---|---|---|---|
| 71488020 | 59648.24172062858  | 4685.54 | 59648.18748984155 |
| 71488172 | 59648.24172074433  | 4685.55 | 59648.18748984155 |
| 71488200 (whitney) | 59648.24172074433 | 4685.55 | 59648.18748984155 |
| 71488316 | 59648.24172086007  | 4685.56 | 59648.18748984155 |
| 71488400 | 59648.24172086007  | 4685.56 | 59648.18748984155 |
| 71488524 | 59648.241720975806 | 4685.57 | 59648.18748984155 |

All anchors identical; whitney's alternatives 4685.54 / 4685.56 displace her
anchor by +10000.449 / −9999.820 µs. The 9-day caveat is eliminated (in-run,
multi-token validation).

## isha (221113aaao) — no same-run records survive; era-bracketed verification

Exhaustive negative (read-only searches on dsastorage, 2026-07-27):
- `/mnt/data/dsa110/T2/` date dirs end 2022-06 (no 2022_11_*).
- `/mnt/data/dsa110/T4/` — no 2022_11 dirs, no `*221113*`.
- `/mnt/data/bckuph23data/` — only `localization_processing/221113aaao/`
  (measurement sets; no trigger-time sibling records), no 2022_11 run dirs.

Isha's date (2022-11-13) lies inside the v3 validation range (2022-03→2024-02,
150,627 rows, zero token mismatches) — interpolation, not extrapolation. With
producer arithmetic proven bit-exact across the bracketing era, her token
(3900.17) is deterministic. Status: VERIFIED by era-bracketed bit-exact
arithmetic; labeled inference (no per-event in-run check possible), zero
counter-evidence.

## Verification

Re-runnable: the anchor computations above reproduce with the 12-line python
block (numpy float32) recorded in the session transcript; inputs are the
producer-written (mjds, specnum) pairs quoted verbatim above from the two run
directories. Remote reads were `ssh -o BatchMode=yes dsastorage '…cat/ls/grep…'`
only; nothing on the remote hosts was modified. v1/v2/v3 JSONs and SUMMARY.md
were not modified by this task.

## Disposition

- zach: VERIFIED (direct in-run producer evidence).
- whitney: VERIFIED (direct in-run producer evidence, four-token anchor test).
- isha: VERIFIED (era-bracketed bit-exact arithmetic; inference, no in-run check).
- Absolute-clock systematics (station clock vs UTC) remain outside this
  verification's scope; CHIME–DSA comparison stays an independent end-to-end
  check, not an anchor.

## Independent recheck (2026-07-27, audit response — ask-b8cfe084)

Auditor challenge: v3 `_derivation` and the SUMMARY THIRD-correction section
call zach/whitney era-extrapolated. Resolution: those texts predate this
receipt's in-run work; the raw artifacts decide. Recheck performed with a
fresh remote fetch and an INDEPENDENT arithmetic implementation (struct-based
float32 round-trip, no numpy; dt_f32 bit pattern re-confirmed 0x39897060):

- zach segment (3 producer records, fetched fresh): anchor 59617.72753211239,
  max spread 0.000 µs; ±10 ms token alternatives displace ±9999.8 µs.
- whitney cluster (6 producer rows, fetched fresh): anchor 59648.18748984155,
  max spread 0.000 µs; alternatives +10000.4 / −9999.8 µs.

Identical to the original computation. A superseding addendum was appended to
`SUMMARY.md`; the v3 JSON's numerical values needed no change (its narrative
caveat text alone was stale). CHIME wording tightened in `sections/toa.tex`
and `status/TOA-ANALYSIS-STATUS.md`: the H5 internal coordinate is now
explicitly "on the UTC scale as kept by the station clock, not an
independently calibrated absolute UTC epoch."
