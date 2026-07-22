# Anonymous nine-sightline catalog corpus

Date: 2026-07-22  
Scope: execution evidence for Wayfinder ticket 14  
Verdict: **producer corpus complete; independent replay remains separate**

## Authority boundary

This work changes no adopted redshift, catalog identity, verdict, budget flag,
trust state, or manuscript figure. It executes the owner-approved ticket-13
search contract.

## Rejected prior artifact

Local commit `8049634` was inspected but not cherry-picked. It used obsolete
5.1/20.1-arcminute cones and the wrong survey matrix, silently accepted 34
500-row responses, applied non-contract admission rules, hashed reserialized
rows rather than preserved responses, and lacked complete provenance.

## Executable contract

[`freeze_anonymous_nine_sightline_corpus.py`](../../scripts/freeze_anonymous_nine_sightline_corpus.py)
fixes the nine frozen burst centers and 15 required public products, or 135
product/sightline cells. It binds the burst-center input SHA-256
`204fb79727ff71f15269f3d5564215e34d8f027aedbd82719dfda162bdcfb644`.

The validator fails for a missing or duplicate cell, unresolved service state,
wrong release or endpoint, missing exact query or retrieval time, incomplete
pagination, overflow, server-count mismatch, missing bytes, hash mismatch,
canonical/manifest disagreement, or X-ray query without coverage evidence.
Exact unrounded spherical separations admit rows at 15 arcminutes and retain a
15.0--15.1-arcminute guard ring.

The eRASS1 primary cluster product is separate from the main source catalogue.
Its complete official bulk catalogue is the completeness authority; candidate
geometry uses `theta * Planck18.angular_diameter_distance(z) <= 5` proper Mpc.
There is no finite angular fallback.

## Primary service surfaces

- DESI Data Release 1 and Legacy Survey Data Release 10: NOIRLab Data Lab TAP.
- Sloan Digital Sky Survey Data Release 19: SkyServer SQL search.
- LAMOST Data Release 11 and VLASS Quick Look Epoch 1: VizieR TAP mirrors.
- J-PLUS Data Release 3 and miniJPAS PDR201912: CEFCA TAP.
- Gaia Data Release 3: ESA Gaia TAP.
- LoTSS Data Release 3: ASTRON TAP.
- eROSITA eRASS1 main and primary cluster catalogues: MPE. The
  [official catalogue inventory](https://erosita.mpe.mpg.de/dr1/AllSkySurveyData_dr1/Catalogues_dr1/)
  identifies the 930,203-source main catalogue and 12,247-row primary cluster
  catalogue. The [DR1 data-rights page](https://erosita.mpe.mpg.de/dr1/)
  supplies the exact public western-hemisphere longitude boundary used here.
- XMM-Newton, Chandra, and Swift exposure and source metadata: HEASARC TAP.
- PS1--STRM v1: [official MAST bulk archive](https://archive.stsci.edu/hlsps/ps1-strm/)
  and [published column schema](https://archive.stsci.edu/hlsps/ps1-strm/hlsp_ps1-strm_ps1_gpc1_all_multi_v1_readme.txt).

## PS1--STRM bulk execution

The public high-declination shard is
`hlsp_ps1-strm_ps1_gpc1_p69-p77_multi_v1_cat.csv.gz`. Its exact size is
4,650,535,027 bytes; published and locally checked MD5 is
`4ffea9f3b1f71ee6a8945077bcf87eaa`; SHA-256 is
`9c25f992f0b99bbf0cc7962d2d01b9058f514313041059617dc92fe78c3a77a3`.
The producer streamed all 49,745,965 native rows and selected 89,902 rows,
including 1,215 guard-ring rows. Counts are Casey 8,994; Chromatica 10,782;
Hamilton 11,674; Isha 12,767; Oran 9,713; Phineas 7,510; Whitney 8,524;
Wilhelm 9,636; and Zach 10,302.

## Frozen result

The completed manifest is
[`corpus-manifest.json`](evidence/nine-sightline-anonymous-catalog-corpus-2026-07-22/corpus-manifest.json)
(SHA-256 `f4eb168580c92d858ba4bebf80146f4bd5ef67f924d9564f283027cb3e227839`).
It binds 135 cells and 110,591 normalized records: 37 cells are `matched`, 41
are `unmatched`, and 57 are `outside_footprint`. None is ambiguous,
access-denied, query-error, truncated, or overflowed.

The corpus contains 986 DESI DR1 rows, 18,851 Gaia DR3 rows, 705 LoTSS DR3
rows, 143 VLASS rows, 89,902 PS1--STRM rows, and four Swift rows. SDSS DR19 and
LAMOST DR11 returned no rows. J-PLUS and miniJPAS are outside footprint for all
nine positions. Legacy Survey DR10 coverage is outside for six positions and
inside with no photo-redshift rows for three. All nine positions are outside
the exact eROSITA-DE public half-sky for both eRASS1 products.

Every cell freezes exact query text, release, UTC retrieval time, coverage,
native response bytes or a canonical PS1 subset, normalized rows, stable source
identifiers, exact separations, native flags and uncertainties, count or
pagination evidence, and SHA-256 hashes. XMM-Newton, Chandra, and Swift source
queries ran only after separate exposure-pointing queries; outside cells retain
the skipped source query and coverage bytes.

The validator reads every canonical snapshot and independently checks cell
identity, row count, identifier, native record, exact spherical separation,
deterministic ordering, guard-ring count, status, release, count response,
coverage evidence, and hashes. Focused tests cover inclusive 15-arcminute and
5-proper-Mpc boundaries, Planck18 calculation, missing cluster redshift,
overflow, count mismatch, and byte tampering.

Ticket 14 is complete. Ticket 16 is the deliberately separate producer-
independent replay gate.
