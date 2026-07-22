# Anonymous nine-sightline catalog-corpus checkpoint

Date: 2026-07-22  
Scope: execution evidence for Wayfinder ticket 14  
Verdict: **open; completed-corpus gate closed**

## Authority boundary

This work does not change adopted redshifts, catalog identities, verdicts,
budget flags, trust state, or manuscript figures. It implements and tests the
owner-approved search contract from ticket 13.

## Rejected prior artifact

Local commit `8049634` was inspected but not cherry-picked. It used obsolete
5.1/20.1-arcminute cones and the wrong survey matrix, silently accepted 34
500-row responses, applied non-contract classification/admission rules, hashed
reserialized rows rather than preserved response bytes, and supplied neither
complete provenance nor an independent replay.

## Executable contract

`scripts/freeze_anonymous_nine_sightline_corpus.py` fixes the nine frozen burst
centers and the 14 required service releases, or 126 service/sightline cells.
It requires the burst-center input SHA-256
`204fb79727ff71f15269f3d5564215e34d8f027aedbd82719dfda162bdcfb644`.
Validation fails for any missing or duplicate cell, unresolved service state,
wrong release or endpoint, missing exact query/retrieval time/native columns,
incomplete pagination, overflow, server-count mismatch, missing raw/canonical
bytes, hash mismatch, or X-ray query without exposure evidence. Exact,
unrounded spherical separations admit rows at 15 arcminutes and retain a
15.0--15.1-arcminute guard ring.

## Anonymous route preflight

The frozen preflight under
`evidence/nine-sightline-anonymous-catalog-corpus-2026-07-22/` records exact
request URLs, methods, UTC times, HTTP status, raw response bytes, and SHA-256
hashes. Live probes reached 13 query services and the official PS1--STRM bulk
archive. The checker rejects TAP protocol errors embedded in HTTP 200
responses.

Primary service surfaces:

- DESI Data Release 1 and Legacy Survey Data Release 10: NOIRLab Data Lab TAP.
- Sloan Digital Sky Survey Data Release 19: SkyServer SQL search.
- LAMOST Data Release 11 and VLASS Quick Look Epoch 1: VizieR TAP mirrors.
- J-PLUS Data Release 3 and miniJPAS PDR201912: CEFCA TAP.
- Gaia Data Release 3: ESA Gaia TAP.
- LoTSS Data Release 3: ASTRON TAP.
- eROSITA eRASS1: MPE simple cone search.
- XMM-Newton, Chandra, and Swift exposure metadata: HEASARC TAP.
- PS1--STRM v1: [official MAST bulk archive](https://archive.stsci.edu/hlsps/ps1-strm/)
  and [published column schema](https://archive.stsci.edu/hlsps/ps1-strm/hlsp_ps1-strm_ps1_gpc1_all_multi_v1_readme.txt).

## PS1--STRM bulk execution

The required high-declination shard is publicly readable without credentials:

```text
https://archive.stsci.edu/hlsps/ps1-strm/hlsp_ps1-strm_ps1_gpc1_p69-p77_multi_v1_cat.csv.gz
```

The resumable command was:

```sh
curl --fail --location --continue-at - \
  --output /Users/jakobfaber/Data/Faber2026/cache/ps1-strm/hlsp_ps1-strm_ps1_gpc1_p69-p77_multi_v1_cat.csv.gz \
  https://archive.stsci.edu/hlsps/ps1-strm/hlsp_ps1-strm_ps1_gpc1_p69-p77_multi_v1_cat.csv.gz
```

The downloaded size is exactly 4,650,535,027 bytes. The official checksum list
publishes MD5 `4ffea9f3b1f71ee6a8945077bcf87eaa`; local MD5 verification is recorded
as the same value. The source SHA-256 is
`9c25f992f0b99bbf0cc7962d2d01b9058f514313041059617dc92fe78c3a77a3`.
The producer streamed all 49,745,965 headerless native rows using the official
19-column order, retained all native values and flags, and selected 89,902 rows
within the guard cones, including 1,215 guard-ring rows. Counts by sightline
are Casey 8,994; Chromatica 10,782; Hamilton 11,674; Isha 12,767; Oran 9,713;
Phineas 7,510; Whitney 8,524; Wilhelm 9,636; and Zach 10,302.

The deterministic gzip/JSON snapshot is 12,091,860 bytes with SHA-256
`05a2b825d28ac0a4ff54ab1e31afff807e42090db0010017dc08718a722f55e5`.
An independent Astropy calculation checked all 89,902 stored separations; the
largest absolute difference was `8.78e-13` arcminutes and every row was within
the inclusive 15.1-arcminute guard cone.

## Remaining closure gates

The service preflight is not a completed cone-query corpus. Ticket 14 remains
open until all 126 cells have full queries, coverage results, native response
rows, complete pagination evidence, and hashes; the X-ray cells additionally
need exposure-first source-query evidence. The PS1 bulk route means no owner
credential is required. Authenticated MAST CasJobs would only be an optional
faster route.

No element is intrinsically human-only. The remaining work is autonomous
acquisition and independent replay, not an owner decision.
