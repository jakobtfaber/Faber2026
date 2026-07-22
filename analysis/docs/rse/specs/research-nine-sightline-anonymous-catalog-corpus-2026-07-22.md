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
Exact unrounded spherical separations admit rows through 15 arcminutes. Rows in
the 15.0--15.1-arcminute guard ring are separate evidence: never canonical,
matched, or included in admitted totals.

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
The producer streamed all 49,745,965 native rows. It froze 88,687 admitted
per-sightline canonical rows and 1,215 separate guard-only rows. Admitted counts
are Casey 8,875; Chromatica 10,642; Hamilton 11,498; Isha 12,601; Oran 9,593;
Phineas 7,383; Whitney 8,416; Wilhelm 9,496; and Zach 10,183. The 4.65 GB source
shard is not in this repository: its size and SHA-256 were verified during
extraction, while the repository freezes and validates the derived per-sightline
canonical bytes.

## Frozen result

The completed manifest is
[`corpus-manifest.json`](evidence/nine-sightline-anonymous-catalog-corpus-2026-07-22/corpus-manifest.json)
(SHA-256 `d6c9847979ffbc5ee4b431ef657b0193d26ac0ffb2b294b4b4ae30f18ad9f13e`).
It binds 135 cells and 109,117 admitted records plus 1,474 separate guard-only
records: 37 cells are `matched`, 41
are `unmatched`, and 57 are `outside_footprint`. None is ambiguous,
access-denied, query-error, truncated, or overflowed.

All 552 byte-evidence members are stored without alteration in deterministic
`evidence-bundle.tar.gz`, SHA-256
`7db3e8b2ba5d85cb3ef7e8a9bd31864e7c1e5241ee5e520f29526546d71ece8d`.
The validator reads each manifest path directly from that bundle and checks its
member hash, while the top-level manifest also checks the bundle hash.

The corpus contains 975 DESI DR1 rows, 18,608 Gaia DR3 rows, 701 LoTSS DR3
rows, 142 VLASS rows, 88,687 PS1--STRM rows, and four Swift rows. SDSS DR19 and
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

The exact admission repair is complete. Ticket 14 remains open until official
exposure pixels or footprint polygons replace the Legacy DR10 and X-ray
pointing proxies. Ticket 16 remains the separate producer-independent replay
gate.

## Coverage repair routes

Live official-service checks identified the required replacements. XMM-Newton
public observations expose exact `footprint_fov` polygons through XSA TAP.
Chandra Source Catalog stacks expose chip-shaped `s_region` polygon unions
through CSC TAP. Legacy DR10 publishes native-WCS per-brick NEXP images, whose
positive pixels define actual included exposure. Swift publishes XRT exposure
maps per dataset but no anonymous bulk polygon query; until those maps are
downloaded and evaluated, Swift coverage remains unknown rather than inferred
from a pointing center.
