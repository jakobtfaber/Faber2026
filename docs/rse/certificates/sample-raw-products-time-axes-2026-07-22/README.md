# Sample raw products and coordinate audit

Status: **owner review pending for eleven events**. Zach remains the accepted
reference. This packet identifies preliminary source products and coordinate
conventions; it accepts no new dispersion-measure fit, radio-frequency
interference mask, or science result.

All 24 project-copy SHA-256 hashes were recomputed on `h17` and match the
source-migration manifest. Full paths, hashes, headers, dataset metadata, and
unresolved fields are in `metadata.json` and the four `events-*.json` files.

## Event summary

`DSA DM` gives optimized/applied then trigger values. `CHIME DM` is the value
stored on `tiedbeam_power`; it is **not** evidence for voltage dedispersion.

| Event | DSA / CHIME ID | DSA DM (pc cm⁻³) | DSA `tstart` (MJD) | CHIME retained channels × samples | CHIME power DM (pc cm⁻³) | FPGA clock epoch (UTC) | Current DSA candidate relation |
|---|---|---:|---:|---:|---:|---|---|
| Whitney | 220310aaam / 215063905 | 462.150 / 462.700 | 59648.241721 | 863 × 55,950 | 462.213692 | 2022-01-27T18:58:36.999999960 | byte-identical |
| Oran | 220506aabd / 224263996 | 396.930 / 396.700 | 59705.597013 | 851 × 72,837 | 397.174546 | 2022-04-19T21:54:44.999999960 | byte-identical |
| Isha | 221113aaao / 252069198 | 411.400 / 411.027 | 59896.3865109765 | 823 × 55,954 | 411.696685 | 2022-10-30T20:04:45.999999960 | byte-identical |
| Wilhelm | 221203aaaa / 253635173 | 602.250 / 602.700 | 59916.0017508958 | 811 × 55,954 | 602.385632 | 2022-11-16T19:47:55.999999960 | byte-identical |
| Phineas | 230307aaao / 274819243 | 610.150 / 608.900 | 60010.378858 | 907 × 72,845 | 610.577493 | 2023-02-28T23:03:21.999999960 | byte-identical |
| Freya | 230325aaag / 278720455 | 912.380 / 914.400 | 60028.071691 | 891 × 55,953 | 912.469851 | 2023-02-28T23:03:21.999999960 | byte-identical |
| John Doe II | 230814aaas / 311723353 | 696.350 / 696.200 | 60170.360927 | 767 × 72,813 | 696.545741 | 2023-06-25T01:27:47.999999960 | byte-identical |
| Hamilton | 230913aaao / 318353610 | 518.700 / 518.600 | 60200.20716 | 799 × 55,954 | 518.789552 | 2023-09-05T00:04:31.999999960 | byte-identical |
| Mahi | 240122aaag / 354049284 | 959.900 / 957.973 | 60331.10428 | 756 × 55,946 | 960.207020 | 2023-11-22T15:46:15.999999960 | **different bytes** |
| Chromatica | 240203aacl / 356959136 | 272.600 / 272.400 | 60343.83182 | 767 × 55,938 | 272.710163 | 2023-11-22T15:46:15.999999960 | **filterbank absent** |
| Casey | 240229aaad / 362593221 | 491.150 / 491.600 | 60369.37095 | 771 × 55,945 | 491.209924 | 2024-02-13T18:36:20.999999960 | **different bytes** |

## Shared native coordinates

- DSA-110: 20,480 time samples × 6,144 descending frequency channels;
  32.768 μs and 30.51757812 kHz sampling; channel centres 1498.75 through
  1311.28051760884 MHz; duration 0.67108864 s.
- DSA-110 files are incoherently dedispersed. The producer selects `dm_opt`
  and references delay to 1530 MHz. The final filterbank header records neither
  value; exact per-run command logs were not found.
- CHIME/FRB: complex voltage and power both retain two beams at 2.56 μs. Each
  event has a different subset of the nominal 1,024 descending 390.625 kHz
  coarse channels. Missing-channel counts are event-specific in the JSON.
- CHIME/FRB voltage records no dispersion measure. Power records a coherent
  dispersion measure. The producer's coherent time-shift default is 400 MHz;
  incoherent alignment defaults to the lowest retained frequency.
- Preserve native sample indices. Neither format proves edge-versus-centre
  sample timing. DSA also does not encode its time scale. CHIME absolute timing
  must be reconstructed per channel from `time0`, its FPGA count, and stored
  sample offsets; the listed epoch is the common FPGA **clock epoch**, not the
  burst time.

## Custody exceptions

- Whitney through Hamilton, plus Zach: current `dsastorage` Level-3
  filterbanks are byte-identical to the project copies on `h17`.
- Mahi and Casey: current `dsastorage` files are different reprocessings. Do
  not replace the hash-pinned `h17` project copies.
- Chromatica: no current Level-3 filterbank exists on `dsastorage`; only event
  metadata remains there.
- Older `filaxes.json` files are partial sidecars. Zach and Isha contain only
  5,120 time entries; the others found contain 20,480. Their final frequency
  differs from the SIGPROC header-derived final channel centre. Preserve them
  as provenance, not as universal coordinate authority.

## Implication for manual bad-channel maps

Manual maps must be keyed to the source-product SHA-256 and native frequency
identity. A nickname or channel number alone is insufficient. Existing
automatic exclusions and later manual exclusions must remain separate mask
layers and be combined only when producing analysis-ready data.

## Read-only reproduction

```bash
ssh h17 'find /data/Faber2026/data/{dsa-110,chime-frb} -type f -print0 | sort -z | xargs -0 sha256sum'

ssh h24 'sha256sum /home/ubuntu/msherman_nsfrb/DSA110-DSAPOL-PROJECT/dsapol_tables/DSA110-FRBs-PARSEC_TABLE.csv'

ssh dsastorage 'find /mnt/data/dsa110/candidates/candidates -path "*/Level3/*_dev_polcal_I.fil" -print'
```

CHIME clock epochs were recomputed with
`baseband_analysis.core.sampling.fpga_start_time` in the pinned container
`chimefrb/baseband-analysis@sha256:f510909d892d0d5224c982c590cbe80967a49a59b79c396ab72bb710105c4c41`.
The container was network-disabled and mounted the project data read-only.

## Review gate

For each event, confirm the source identity, DSA optimized/applied starting
dispersion measure, and explicit unknowns. Only then may its raw-coordinate
record become an accepted input to dispersion-measure fitting and manual-map
generation.
