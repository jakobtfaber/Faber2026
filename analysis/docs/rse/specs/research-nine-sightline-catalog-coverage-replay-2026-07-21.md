# Research: nine-sightline catalog coverage replay

Date: 2026-07-21 PDT / 2026-07-22 UTC

Parent commit: `4df872d532822eaf1657d982f0acd857428397b8`

Pipeline commit: `ab6af1f713496abd2ff2d71bf11edf4100871e94`
Disposition: **fail closed; stored-row arithmetic passes, expanded search coverage does not exist**

## Question and boundary

Can the 50 current registry rows with finite host redshifts, spanning nine
sightlines, be independently replayed against the required expanded survey set?

**Not completely.** The current candidate-redshift source rows, stored verdict
inputs, duplicate mappings, and budget flags replay. The repository does not
contain a nine-sightline search artifact for the required expanded surveys.
Most required services were checked only for Zach, and those checks are prose
summaries rather than frozen response bytes. Candidate selection and coverage
for the other eight sightlines therefore cannot be replayed.

This research did not change any adopted redshift, verdict, duplicate mapping,
budget flag, trust state, or Figure 3 artifact.

## Frozen inputs

| Input | SHA-256 |
|---|---|
| `pipeline/galaxies/foreground/data/intervening_census_registry.csv` | `8e1998fd41b42e982cb2cdf4967e69eb028df1037caa1cf061578bb6ec2cab97` |
| `pipeline/galaxies/foreground/data/candidate_redshift_provenance.csv` | `ccc8427786455d498bfd668c878ef0395fbb143a1f2f0939630e5fec68138803` |
| `pipeline/galaxies/foreground/data/frozen_census/bursts.csv` | `204fb79727ff71f15269f3d5564215e34d8f027aedbd82719dfda162bdcfb644` |
| `pipeline/galaxies/foreground/data/frozen_census/foreground.csv` | `38ed01ac7561eddcbd33500e2fabeeb4130c22c4fdca791967415656a4d0cd15` |
| `pipeline/galaxies/foreground/data/frozen_census/foreground_validated.csv` | `c18fa388cd421d6a90e65b77edceca00afe9c8a9e4cc7feb31a52f468c6e79d7` |
| `pipeline/galaxies/foreground/data/frozen_census/foreground_final.csv` | `ce14b474424efb5ff442c5206020609475ff7b0675aa370cb026a47cc8ff4766` |
| `pipeline/galaxies/foreground/data/frozen_census/ps1_strm_resolution.csv` | `f3dbb32e590f9d5b953919e6de2b9e9473b3ccda36492e7010ee0fd557daf8b7` |
| `pipeline/galaxies/foreground/data/frozen_census/strm_catalog_rows.csv` | `42e576a234ac9ab471b695e89b6f25c3ad6875e1914c8ccb3ee518739fd04870` |
| `pipeline/galaxies/foreground/data/census_extensions/v4_extension.csv` | `c3284c954040cfa0d9363944336118b30f33249ab30e81eeac010d7d7e3817ed` |
| `pipeline/galaxies/foreground/data/census_masses/census_duplicates.csv` | `336e4023dbf046762477c724e57365c29a3ecabb982f6978e635fb0d05d47e45` |

The 50-row scope excludes the two Freya rows because their host redshift is not
finite. The included sightlines are Casey, Chromatica, Hamilton, Isha, Oran,
Phineas, Whitney, Wilhelm, and Zach.

## Independent replay

### Diagnostic candidate source-row identity replay

This check is not independent: I called the live source adapters used by
`pipeline/galaxies/foreground/freeze_candidate_redshift_provenance.py` without
writing its output. I then compared the returned source family, release,
stable identifier, canonical source-row hash, complete query-response hash, and
measurement kind with the checked-in ledger.

- All 50 calls completed without an error.
- 44 rows have an adopted candidate redshift. All 44 reproduced the source
  family, release, stable identifier, canonical source-row SHA-256, and
  measurement kind.
- Six rows deliberately have no adopted candidate redshift. Their normalized
  `not_applicable` source state reproduced.
- 37 of the 44 adopted-redshift rows reproduced the complete response hash.
  Seven large-radius cluster queries returned a changed surrounding response
  while preserving the selected source identifier and selected-row hash:
  Whitney `J085808.2+731234, 1161367`; Phineas
  `J115128.2+713637, 1254415`, `J114944.0+714348, 1253496`,
  `J115400.9+713320, 1255773`, `J115436.9+713930, 1256077`, and
  `J114928.5+712526, 1253366`; Casey `J112235.5+705438, 1239515`.
  This is response-set drift, not selected-source drift. The repository does
  not retain the prior response bytes, so the added, removed, or reordered
  surrounding rows cannot be reconstructed.

### Verdict inputs and budget flags

The replay used a separate calculation path. It did not call the pipeline
verdict or budget functions.

- Secure redshift: foreground only when candidate redshift is below host.
- Photometric redshift: foreground when candidate redshift plus its error is
  below host; background when candidate redshift minus its error is above host;
  otherwise inconclusive.
- PS1--STRM non-galaxy or extrapolated rows remain inconclusive.
- Budget eligibility: confirmed halo, or confirmed cluster with finite
  `b/R500 <= 1`.

Result: 50/50 verdicts reproduce, with 30 confirmed, 13 inconclusive, and 7
refuted. All 50 budget flags reproduce; 15 row-level flags are true.

### Duplicate handling and separations

I recomputed spherical separations directly with the haversine formula from
registry coordinates. All seven pairs have identical stored redshift and
verdict. Replayed separations agree with the rounded mapping values:

| Duplicate to canonical | Stored / replayed separation (arcsec) |
|---|---:|
| Casey `795` to `192821699728654764` | `0.04 / 0.038813` |
| Casey `824` to `192821700026167542` | `0.01 / 0.006689` |
| Casey `827` to `192831699797402822` | `0.01 / 0.012530` |
| Phineas `832` to `194021777634832653` | `0.01 / 0.014596` |
| Phineas `1153` to `194041777780157594` | `0.02 / 0.017802` |
| Phineas `1190` to `194051777813062524` | `0.01 / 0.012768` |
| Whitney `1472` to `196191347354360083` | `0.12 / 0.121292` |

This establishes arithmetic coherence, not independent duplicate discovery.
The duplicate file remains an owner-adjudication table and lacks the two
catalog source rows and cross-match response needed to reproduce selection.

### Existing four-catalog classification snapshots

The repaired GSC 2.4.2, ALLWISE, CatWISE2020, and unWISE artifact contains all
50 scoped rows and a snapshot hash for every row/catalog pair. Its SHA-256 is
`17ef142bc5d57f0f1f42d11a397c084de2b9763fbb7543ce82e90e1a6d6ef727`.
Scoped statuses are:

| Catalog | Matched | Ambiguous | Unmatched |
|---|---:|---:|---:|
| GSC 2.4.2 | 38 | 8 | 4 |
| ALLWISE | 45 | 0 | 5 |
| CatWISE2020 | 45 | 2 | 3 |
| unWISE | 35 | 11 | 4 |

These classification snapshots do not substitute for the ticket's new search
and redshift sources.

## Expanded coverage gap

| Required source | Evidence currently present | Nine-sightline replay status |
|---|---|---|
| DESI Data Release 1 | 22 selected candidate source rows; one Zach non-detection | No full-region search artifact |
| Legacy Survey photometric redshifts | 17 selected candidate source rows | No full-region search artifact |
| PS1--STRM | nine frozen historical rows; three adopted source rows | Not a uniform 50-row or full-region pass |
| WISE--PS1--STRM | two owner-exported Zach rows | Missing eight sightlines; Zach query and job identifier absent |
| Sloan Digital Sky Survey Data Release 19 | Zach non-detection in prose | Missing eight sightlines and response bytes |
| LAMOST Data Release 11 | Zach non-detection in prose | Missing eight sightlines and response bytes |
| J-PLUS and J-PAS | Zach outside-footprint results in prose | Missing eight sightlines and response bytes |
| UNIONS/CFIS | Zach `access_denied`; identity lacks `CFIS-read` | Not queryable; missing eight normalized coverage records |
| Gaia Data Release 3 | Zach non-detection in prose | Missing eight sightlines and response bytes |
| LoTSS Data Release 3, VLASS, eROSITA eRASS1 | Zach non-detections in prose | Missing eight sightlines and response bytes |
| XMM-Newton, Chandra, Swift | Zach catalog non-detections in prose | No exposure-first coverage artifact; missing eight sightlines |

No current artifact gives a release, query or cone, retrieval time, source
identifier, coordinates, separation, quality fields, coverage result,
normalized state, response bytes, and hash for these sources across all 50
rows. The required normalized state set therefore cannot be audited, and the
search catalogs cannot establish that the present registry is complete.

The original frozen discovery cone or aperture was never recorded. Therefore
the ticket phrase “full recorded sightline region” does not currently identify
an executable, uniform query contract. Selecting a radius now would be a new
search-policy decision, not a replay of a frozen region.

Host redshift provenance is also still blocked: `bursts.csv` freezes values but
not the authoritative source-bearing Verdi rows or citations.

## Reproducibility

Replay entry point:
`scripts/replay_nine_sightline_catalog_coverage.py`. Offline mode uses only the
Python standard library. It independently recomputes the 50-row scope,
verdicts, budget flags, and spherical duplicate separations, and recounts the
existing four-catalog statuses. It verifies every input against the SHA-256
values above. It can check only that 44 stable identifiers and row hashes are
present in the ledger; raw source responses were not frozen, so it cannot
independently verify those identities offline.

Live mode reuses
`pipeline/galaxies/foreground/freeze_candidate_redshift_provenance.py`. It is a
diagnostic identity check, **not independent validation** and not the ticket's
required full-region search path. It compares the current adapter-selected
source identifiers and hashes with the ledger. The earlier completed diagnostic
run made 50 calls, matched all 44 adopted stable identifiers and selected-row
hashes, and found the seven response-set drifts listed above. A later clean
Conda rerun was bounded at 120 seconds and stopped incomplete; it produced no
replacement result.

Environment:

- Offline clean-room replay: macOS 27.0 build `26A5378n`, arm64, fresh `venv`,
  Python `3.13.9`; no third-party packages, accelerator, parallel workers, or
  random numbers.
- Live diagnostic environment: clean `conda run -n py312`, Python `3.12.13`.
  Repository environment declaration:
  `pipeline/environment.yml`, SHA-256
  `f4c5b36c9502f1386c7ca5d0a0cde3a8aea967068175698333fc7ab8d4762e6e`.
- Code revision is emitted by the replay itself as `code.head`; dirty paths are
  emitted as `code.dirty_paths`. The pipeline revision is pinned above.
- Inputs and hashes are emitted under `inputs_sha256`. No seeds or numerical
  tolerances apply. Duplicate mappings pass only when the independently
  recomputed separation rounds to the stored two-decimal value.

Exact offline clean-room commands, from the repository root:

```bash
repro_dir="$(mktemp -d)"
python3 -m venv "$repro_dir/venv"
"$repro_dir/venv/bin/python" \
  scripts/replay_nine_sightline_catalog_coverage.py \
  --mode offline \
  --output "$repro_dir/offline.json"
"$repro_dir/venv/bin/python" -m json.tool "$repro_dir/offline.json" >/dev/null
```

Observed: exit `0`; `ok=true`; 52 total rows, 50 finite-host rows on nine
sightlines; 44 adopted-redshift ledger rows and six no-redshift rows; zero
verdict mismatches; zero budget mismatches; seven duplicate checks pass; the
four catalog counts equal the tables above. The same offline JSON was produced
by the working interpreter and the fresh virtual environment.

Exact bounded live diagnostic command:

```bash
gtimeout 120s env -i \
  HOME="$HOME" \
  PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/bin:/bin" \
  /opt/anaconda3/bin/conda run -n py312 \
  python scripts/replay_nine_sightline_catalog_coverage.py \
  --mode live \
  --output /tmp/nine-sightline-live.json
```

Observed for the clean Conda rerun: timeout after 120 seconds; incomplete; no
JSON result. This does not replace the earlier completed diagnostic result.
Network response hashes may change later even when the selected source row is
unchanged; live output reports both current drifts and whether they equal the
seven observed here.

Additional checks:

```bash
ruff check scripts/replay_nine_sightline_catalog_coverage.py
python3 -m py_compile scripts/replay_nine_sightline_catalog_coverage.py
pytest -q tests/test_expanded_catalog_validation.py
python3 scripts/validate_expanded_foreground_catalog_gate.py
```

Observed: Ruff and byte-compilation passed; the focused tests reported `3
passed in 0.25s`. The final command exits nonzero because it targets the
intentionally failed, superseded top-level gate and lists its eight preserved
defects.

The unit tests validate the repaired offline artifact contract. They do not
validate the missing expanded nine-sightline queries. The top-level validator
still targets the intentionally failed superseded gate and must not be treated
as a contradictory pass/fail result for this research.

## Decision-ready conclusion

1. Preserve all current adopted values and fail-closed states. The independent
   arithmetic found no row-level reason to change them.
2. Treat the candidate source ledger as live-replayed for selected-row identity,
   with seven explicitly recorded surrounding-response drifts.
3. Do not claim uniform expanded catalog coverage, deterministic search
   candidate selection, or independent duplicate discovery. The required
   frozen query corpus has not been created.
4. Keep scientific trust and Figure 3 promotion closed. A later execution task
   must run the full-region survey matrix, freeze raw or canonical normalized
   responses and hashes, and route any conflict to owner-approved adjudication.

## Primary sources

- `pipeline/galaxies/foreground/freeze_candidate_redshift_provenance.py`
- `pipeline/galaxies/foreground/data/candidate_redshift_provenance.csv`
- `pipeline/galaxies/foreground/data/intervening_census_registry.csv`
- `pipeline/galaxies/foreground/data/frozen_census/`
- `pipeline/galaxies/foreground/data/census_masses/census_duplicates.csv`
- `pipeline/galaxies/foreground/data/expanded_catalog_cross_references.csv`
- `docs/rse/specs/research-zach-intercatalog-redshift-discrepancy-2026-07-21.md`
- [DESI Data Release 1 database documentation](https://data.desi.lbl.gov/doc/access/database/)
- [Sloan Digital Sky Survey Data Release 19 access](https://www.sdss.org/dr19/data_access/)
- [LAMOST Data Release 11 Virtual Observatory](https://www.lamost.org/dr11/v2.0/vo)
- [WISE--PS1--STRM official release](https://archive.stsci.edu/hlsp/wise-ps1-strm)
- [Gaia Data Release 3 archive](https://gea.esac.esa.int/archive/documentation/GDR3/)
- [UNIONS/CFIS query documentation](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/community/unions/querydoc.html)
