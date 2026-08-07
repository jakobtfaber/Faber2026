# Anonymous nine-sightline catalog corpus

Date: 2026-07-22  
Scope: execution evidence for Wayfinder ticket 14  
Verdict: **producer-valid; corrected 135-cell corpus awaits independent review**

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
product/sightline cells. The corrected roster includes JohndoeII,
matching the authoritative Verdi and protected-corpus roster. It binds both the
burst-center input SHA-256
`204fb79727ff71f15269f3d5564215e34d8f027aedbd82719dfda162bdcfb644`
and protected-roster manifest SHA-256
`43af38cc4e996b7890ea0858ef5a760c124e877825dc8866bc4221d3d02b347f`.

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

- DESI Data Release 1 and Legacy Survey Data Release 10 photometric redshifts:
  NOIRLab Data Lab TAP. Exact northern imaging coverage uses official Legacy
  Survey Data Release 9 SIA g/r/z NEXP cutouts.
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
- XMM-Newton source metadata: HEASARC TAP; exact footprints: XSA TAP.
- Chandra source metadata: HEASARC TAP; exact polygons: CSC ObsCore TAP.
- Swift source metadata: HEASARC TAP. Exact coverage uses the official UKSSDC
  LSXPS API and native XRT exposure-map FITS files, queried with swifttools
  4.0.2 and API version 1.0.5.
- PS1--STRM v1: [official MAST bulk archive](https://archive.stsci.edu/hlsps/ps1-strm/)
  and [published column schema](https://archive.stsci.edu/hlsps/ps1-strm/hlsp_ps1-strm_ps1_gpc1_all_multi_v1_readme.txt).

## PS1--STRM bulk execution

The public high-declination shard is
`hlsp_ps1-strm_ps1_gpc1_p69-p77_multi_v1_cat.csv.gz`. Its exact size is
4,650,535,027 bytes; published and locally checked MD5 is
`4ffea9f3b1f71ee6a8945077bcf87eaa`; SHA-256 is
`9c25f992f0b99bbf0cc7962d2d01b9058f514313041059617dc92fe78c3a77a3`.
The producer streamed all 49,745,965 native rows. It froze 93,115 admitted
per-sightline canonical rows and 1,232 separate guard-only rows. Admitted counts
are Casey 8,875; Chromatica 10,642; Hamilton 11,498; Isha 12,601;
JohndoeII 13,924; Oran 9,593; Phineas 7,383; Whitney 8,416; and Zach 10,183.
The 4.65 GB source
shard is not in this repository: its size and SHA-256 were verified during
extraction, while the repository freezes and validates the derived per-sightline
canonical bytes.

## Frozen result

The current manifest is
[`corpus-manifest.json`](evidence/nine-sightline-anonymous-catalog-corpus-2026-07-22/corpus-manifest.json)
(SHA-256 `14321fb328e372b8df0537d9a445dec2ab1376c4b258dabaf92116152eb023a5`).
It binds 135 cells and 115,713 admitted records plus 1,516 separate guard-only
records: 37 `matched`, 31 `unmatched`, and 67 `outside_footprint`. No cell is
unresolved. Exact official coverage evidence is frozen wherever required.

All 618 byte-evidence members are stored without alteration in deterministic
`evidence-bundle.tar.gz`, SHA-256
`fed672e29c1d84ffd09f93de2487a1337fb722c02bd5dc718f7f97c1e593d32d`.
The validator reads each manifest path directly from that bundle and checks its
member hash, while the top-level manifest also checks the bundle hash.

The frozen admission evidence contains 975 DESI DR1 rows, 20,766 Gaia DR3 rows, 701 LoTSS DR3
rows, 152 VLASS rows, four Swift rows, and 93,115 PS1--STRM rows. SDSS DR19 and
LAMOST DR11 returned no rows. J-PLUS and miniJPAS are outside footprint for all
the nine positions. Official Legacy Survey DR9 northern g/r/z NEXP pixels put
six positions outside and Whitney, Phineas, and Casey inside, with no Data
Release 10 photo-redshift rows. Exact XMM-Newton and Chandra polygons put all
the nine positions outside. Swift exposure pixels put Whitney and Casey inside;
only Casey has source rows. JohndoeII and the other six positions are outside.
All nine positions are outside
the exact eROSITA-DE public half-sky for both eRASS1 products.

Every cell freezes query text, release, UTC retrieval time, coverage state,
native response bytes or a canonical PS1 subset, normalized rows, stable source
identifiers, exact separations, native flags and uncertainties, count or
pagination evidence, and SHA-256 hashes. XMM-Newton and Chandra source queries
ran only after exact polygon checks; outside cells retain
the skipped source query and coverage bytes.

The validator reads every canonical snapshot and checks cell
identity, row count, identifier, native record, exact spherical separation,
deterministic ordering, guard-ring count, status, release, count response,
coverage evidence, and hashes. Focused tests cover inclusive 15-arcminute and
5-proper-Mpc boundaries, Planck18 calculation, missing cluster redshift,
overflow, count mismatch, and byte tampering. Swift validation additionally
checks the raw API request and response inventory, the conservative image-size
envelope, every FITS hash, and native-WCS positive pixels within 15 arcminutes.

Exact admission and all coverage repairs pass the producer validator. Ticket 14
remains open for independent review; ticket 16 remains blocked until that review
accepts the corrected corpus.

## Coverage repair routes

Live official-service checks completed the reachable replacements. XMM-Newton
uses XSA `footprint_fov` polygons. Chandra uses CSC `s_region` polygon unions.
Legacy Survey uses reachable official Data Release 9 northern SIA g/r/z NEXP
cutouts, with every FITS byte frozen and replayed through its native world
coordinate system. Data Release 10 has no northern imaging products and no
i-band northern exposure map. Swift uses a 60-arcminute LSXPS dataset query and
an independently queried upper bound on individual image size. Twenty-nine
candidate exposure maps were frozen. Native-WCS replay finds positive pixels
within 15 arcminutes for Whitney and Casey only. Raw query and image
API request and response bytes, API endpoint and version, map URLs, and every
FITS byte and hash are in the evidence bundle.
