# Research: independent foreground redshift and verdict audit

**Date:** 2026-07-20  
**Verdict:** **FAIL-CLOSED** — arithmetic reproduces, source-level verification does not  
**Faber2026 commit:** `0cff064e2c4278cd97aa97ce3fb878f375df8071`  
**Pinned pipeline commit:** `c6111390ce9c159483a844417f5fd9d187e13f5b`

## Question

Do the checked-in primary or frozen inputs independently support every adopted
host and candidate redshift, uncertainty, foreground verdict, duplicate
decision, and budget-eligibility flag in the 52-row foreground registry?

**Answer: no.** An independent calculation reproduces all 52 verdict labels and
all 52 row-level budget flags. The seven declared duplicate pairs also have
matching redshifts and verdicts. However, none of the 52 rows has a complete,
checked-in source chain for both the host redshift and intervening object. The
missing Verdi source table blocks every host-redshift check. Legacy Survey DR9
and DESI DR1 extracts also omit their stable catalog identifiers and query
metadata. Figure 3 therefore remains blocked under the ticket's acceptance
rule.

## Frozen inputs

All calculations used the files below without network access. SHA-256 hashes
identify their exact bytes.

| Input | SHA-256 | Role |
|---|---|---|
| `pipeline/galaxies/foreground/data/intervening_census_registry.csv` | `8e1998fd41b42e982cb2cdf4967e69eb028df1037caa1cf061578bb6ec2cab97` | 52 stored rows under audit |
| `pipeline/galaxies/foreground/data/frozen_census/bursts.csv` | `204fb79727ff71f15269f3d5564215e34d8f027aedbd82719dfda162bdcfb644` | adopted host redshifts |
| `pipeline/galaxies/foreground/data/frozen_census/foreground.csv` | `38ed01ac7561eddcbd33500e2fabeeb4130c22c4fdca791967415656a4d0cd15` | coordinates and cluster geometry |
| `pipeline/galaxies/foreground/data/frozen_census/foreground_validated.csv` | `c18fa388cd421d6a90e65b77edceca00afe9c8a9e4cc7feb31a52f468c6e79d7` | captured Legacy Survey, DESI, and NED results |
| `pipeline/galaxies/foreground/data/frozen_census/foreground_final.csv` | `ce14b474424efb5ff442c5206020609475ff7b0675aa370cb026a47cc8ff4766` | stored 49-row pre-extension adjudication |
| `pipeline/galaxies/foreground/data/frozen_census/ps1_strm_resolution.csv` | `f3dbb32e590f9d5b953919e6de2b9e9473b3ccda36492e7010ee0fd557daf8b7` | prior STRM resolution output; not used as expected values |
| `pipeline/galaxies/foreground/data/frozen_census/strm_catalog_rows.csv` | `42e576a234ac9ab471b695e89b6f25c3ad6875e1914c8ccb3ee518739fd04870` | nine captured PS1-STRM rows |
| `pipeline/galaxies/foreground/data/census_extensions/v4_extension.csv` | `c3284c954040cfa0d9363944336118b30f33249ab30e81eeac010d7d7e3817ed` | three manually appended systems |
| `pipeline/galaxies/foreground/data/census_masses/census_duplicates.csv` | `336e4023dbf046762477c724e57365c29a3ecabb982f6978e635fb0d05d47e45` | seven duplicate-to-canonical mappings |

The 49-row final file entered pipeline history at
`367345781caefc6836320be30e7a633896c9c86a`; the raw STRM rows at
`ef5d8d02a8cd508f44356e6c26110de1301bcb4d`; the extension and 52-row
registry at `a70b9c54817a94d2739eaa95860333e6e3f03c0a`; and the duplicate table at
`4e951c8acd6f0e221058d86ed97bb52b9d8c8597`.

## Independent method

I did not treat `final_verdict`, `budget_eligible`,
`ps1_strm_resolution.csv`, or `foreground_final.csv` as expected answers.

1. I joined each registry row to the frozen evidence by
   `(nickname, type, obj)`.
2. For a usable spectroscopic redshift, I classified the object as foreground
   only when `candidate_z < host_z`; otherwise it is background.
3. For a photometric redshift with uncertainty, I classified it as foreground
   when `candidate_z + uncertainty < host_z`, background when
   `candidate_z - uncertainty > host_z`, and inconclusive otherwise.
4. A PS1-STRM non-galaxy class, extrapolated photometric redshift, missing host
   redshift, or missing candidate redshift is inconclusive. These rules come
   from `pipeline/galaxies/foreground/adjudication/ps1_strm_adjudicate.py` and
   `pipeline/galaxies/foreground/adjudication/validate_foreground.py`.
5. I independently applied the budget rule in
   `pipeline/galaxies/foreground/census_registry.py`: confirmed halos qualify;
   confirmed clusters qualify only with finite `b/R500 <= 1`.
6. I compared the recomputed result with stored columns only after completing
   the calculation. I then checked every mapping in
   `pipeline/galaxies/foreground/data/census_masses/census_duplicates.csv`
   against both registry members.

This is an internal replay, not an external catalog re-query. The PS1-STRM
catalog definition is documented by [Beck et al. (2021)](https://doi.org/10.1093/mnras/staa2587),
and the Legacy Survey photometric-redshift method by
[Zhou et al. (2021)](https://doi.org/10.1093/mnras/staa3764). Those papers do
not establish the identity or values of these individual frozen rows.

## Results

- Stored totals: 30 confirmed, 15 inconclusive, 7 refuted.
- Independent arithmetic: identical totals; **0 verdict discrepancies**.
- Stored budget total: 15 row-level eligible entries. Independent arithmetic:
  identical; **0 eligibility discrepancies**.
- Of the 16 confirmed clusters, one has `b/R500 <= 1`; the other 15 are
  correctly budget-ineligible.
- Seven declared duplicate rows reproduce the canonical member's redshift and
  verdict. Five of them carry a true row-level budget flag. Removing declared
  duplicates reduces 15 eligible catalog rows to 10 eligible physical rows,
  as implemented by `registry_to_matches()` in
  `pipeline/galaxies/foreground/census_registry.py`.
- The adopted host redshift in every registry row agrees with the corresponding
  value in `bursts.csv`; this is file-to-file consistency only. `freya` has no
  host redshift and is correctly inconclusive.
- **0 of 52 rows passes source-level verification.** All lack a checked-in
  primary citation or source row for the adopted host redshift. Candidate-side
  provenance has additional failures listed below.

In the table, “recomputed / stored” shows the independent result first. “LS”
means Legacy Survey; “STRM” is the Pan-STARRS1 source classification and
photometric-redshift catalog. A blocked disposition means the arithmetic may
match but the acceptance requirement is not met.

| # | Registry key | Host z | Candidate z ± error (kind) | Verdict: recomputed / stored | Budget: recomputed / stored | Duplicate | Source disposition |
|---:|---|---:|---|---|---|---|---|
| 1 | `zach/195373100910393540` | 0.043 | 0.469361 ± 0.0471 (STRM photometric, extrapolated) | inconclusive / inconclusive | false / false | — | Blocked: missing host citation and STRM retrieval/release metadata. |
| 2 | `whitney/1472` | 0.479 | 0.555055 ± 0.0455 (LS/Zhou photometric) | refuted / refuted | false / false | → `196191347354360083` | Blocked: missing host citation, LS identifier, and query metadata. |
| 3 | `whitney/1473` | 0.479 | 0.358473 ± 0.113 (LS/Zhou photometric) | confirmed / confirmed | true / true | — | Blocked: missing host citation, LS identifier, and query metadata. |
| 4 | `whitney/1582` | 0.479 | 0.471249 ± 0.190 (LS/Zhou photometric) | inconclusive / inconclusive | false / false | — | Blocked: missing host citation, LS identifier, and query metadata. |
| 5 | `whitney/196191347354360083` | 0.479 | 0.555055 ± 0.0455 (LS/Zhou photometric) | refuted / refuted | false / false | — | Blocked: missing host citation, LS identifier, and query metadata. |
| 6 | `whitney/J085546.0+732230, 1160094` | 0.479 | 0.127679 ± 0.0000141 (DESI spectrum) | confirmed / confirmed | false / false | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 7 | `whitney/J085531.9+732432, 1159975` | 0.479 | 0.402303 ± 0.000128 (DESI spectrum) | confirmed / confirmed | false / false | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 8 | `whitney/J085808.2+731234, 1161367` | 0.479 | 0.257159 ± 0.0000127 (DESI spectrum) | confirmed / confirmed | false / false | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 9 | `oran/195393180643665627` | 0.3005 | — (STRM unsure) | inconclusive / inconclusive | false / false | — | Blocked: missing host citation and STRM retrieval/release metadata. |
| 10 | `wilhelm/194453151328186646` | 0.510 | — (STRM unsure) | inconclusive / inconclusive | false / false | — | Blocked: missing host citation and STRM retrieval/release metadata. |
| 11 | `phineas/832` | 0.271 | 0.192491 ± 0.0284 (LS/Zhou photometric) | confirmed / confirmed | true / true | → `194021777634832653` | Blocked: missing host citation, LS identifier, and query metadata. |
| 12 | `phineas/953` | 0.271 | 0.199064 ± 0.00000495 (DESI spectrum) | confirmed / confirmed | true / true | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 13 | `phineas/983` | 0.271 | 0.164920 ± 0.0585 (LS/Zhou photometric) | confirmed / confirmed | true / true | — | Blocked: missing host citation, LS identifier, and query metadata. |
| 14 | `phineas/986` | 0.271 | 0.208180 ± 0.0667 (LS/Zhou photometric) | inconclusive / inconclusive | false / false | — | Blocked: missing host citation, LS identifier, and query metadata. |
| 15 | `phineas/1072` | 0.271 | 0.299571 ± 0.0793 (LS/Zhou photometric) | inconclusive / inconclusive | false / false | — | Blocked: missing host citation, LS identifier, and query metadata. |
| 16 | `phineas/1153` | 0.271 | 0.214620 ± 0.0000427 (DESI spectrum) | confirmed / confirmed | true / true | → `194041777780157594` | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 17 | `phineas/1190` | 0.271 | 0.109607 ± 0.0000429 (DESI spectrum) | confirmed / confirmed | true / true | → `194051777813062524` | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 18 | `phineas/194021777634832653` | 0.271 | 0.192491 ± 0.0284 (LS/Zhou photometric) | confirmed / confirmed | true / true | — | Blocked: missing host citation, LS identifier, and query metadata. |
| 19 | `phineas/194031778315722893` | 0.271 | 0.884052 ± 0.115 (LS/Zhou photometric) | refuted / refuted | false / false | — | Blocked: missing host citation, LS identifier, and query metadata. |
| 20 | `phineas/194041777780157594` | 0.271 | 0.214620 ± 0.0000427 (DESI spectrum) | confirmed / confirmed | true / true | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 21 | `phineas/194051777813062524` | 0.271 | 0.109607 ± 0.0000429 (DESI spectrum) | confirmed / confirmed | true / true | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 22 | `phineas/J115120.4+714435, 1254337` | 0.271 | 0.200030 ± 0.000101 (DESI spectrum) | confirmed / confirmed | true / true | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 23 | `phineas/J115128.2+713637, 1254415` | 0.271 | 0.191599 ± 0.0000764 (DESI spectrum) | confirmed / confirmed | false / false | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 24 | `phineas/J114944.0+714348, 1253496` | 0.271 | 0.244017 ± 0.0000416 (DESI spectrum) | confirmed / confirmed | false / false | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 25 | `phineas/J115140.5+712732, 1254506` | 0.271 | 0.175807 ± 0.0000672 (DESI spectrum) | confirmed / confirmed | false / false | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 26 | `phineas/J115400.9+713320, 1255773` | 0.271 | 0.154945 ± 0.0000277 (DESI spectrum) | confirmed / confirmed | false / false | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 27 | `phineas/J115031.4+715735, 1253898` | 0.271 | 0.269577 ± 0.0000794 (DESI spectrum) | confirmed / confirmed | false / false | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 28 | `phineas/J115436.9+713930, 1256077` | 0.271 | 0.262775 ± 0.0000542 (DESI spectrum) | confirmed / confirmed | false / false | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 29 | `phineas/J114928.5+712526, 1253366` | 0.271 | -0.000109 ± 0.00000340 (DESI spectrum) | confirmed / confirmed | false / false | — | Blocked: missing host citation, DESI target identifier, and query metadata; negative redshift needs source-level review. |
| 30 | `freya/197030881733398302` | unknown | 0.304726 ± 0.0680 (STRM photometric) | inconclusive / inconclusive | false / false | — | Blocked: host redshift absent and STRM retrieval/release metadata missing. |
| 31 | `freya/197040882212782495` | unknown | 0.617521 ± 0.126 (STRM photometric) | inconclusive / inconclusive | false / false | — | Blocked: host redshift absent and STRM retrieval/release metadata missing. |
| 32 | `hamilton/192943050854547067` | 0.3024 | — (STRM unsure) | inconclusive / inconclusive | false / false | — | Blocked: missing host citation and STRM retrieval/release metadata. |
| 33 | `hamilton/192963050359413614` | 0.3024 | 0.307861 ± 0.0727 (STRM photometric) | inconclusive / inconclusive | false / false | — | Blocked: missing host citation and STRM retrieval/release metadata. |
| 34 | `chromatica/196673126794497004` | 0.074 | — (STRM unsure) | inconclusive / inconclusive | false / false | — | Blocked: missing host citation and STRM retrieval/release metadata. |
| 35 | `chromatica/196723126173351736` | 0.074 | 0.475102 ± 0.0438 (STRM photometric, extrapolated) | inconclusive / inconclusive | false / false | — | Blocked: missing host citation and STRM retrieval/release metadata. |
| 36 | `chromatica/196733128040225775` | 0.074 | 0.054338 ± unknown (NED) | confirmed / confirmed | true / true | — | Blocked: missing host citation, candidate-redshift uncertainty, and query metadata. |
| 37 | `casey/192821699728654764` | 0.287 | 0.374674 ± 0.0491 (LS/Zhou photometric) | refuted / refuted | false / false | — | Blocked: missing host citation, LS identifier, and query metadata. |
| 38 | `casey/192821700026167542` | 0.287 | 0.202814 ± 0.0000521 (DESI spectrum) | confirmed / confirmed | true / true | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 39 | `casey/192831699797402822` | 0.287 | 0.239752 ± 0.0120 (LS/Zhou photometric) | confirmed / confirmed | true / true | — | Blocked: missing host citation, LS identifier, and query metadata. |
| 40 | `casey/660` | 0.287 | 0.372738 ± 0.0670 (LS/Zhou photometric) | refuted / refuted | false / false | — | Blocked: missing host citation, LS identifier, and query metadata. |
| 41 | `casey/795` | 0.287 | 0.374674 ± 0.0491 (LS/Zhou photometric) | refuted / refuted | false / false | → `192821699728654764` | Blocked: missing host citation, LS identifier, and query metadata. |
| 42 | `casey/796` | 0.287 | 0.421672 ± 0.0953 (LS/Zhou photometric) | refuted / refuted | false / false | — | Blocked: missing host citation, LS identifier, and query metadata. |
| 43 | `casey/827` | 0.287 | 0.239752 ± 0.0120 (LS/Zhou photometric) | confirmed / confirmed | true / true | → `192831699797402822` | Blocked: missing host citation, LS identifier, and query metadata. |
| 44 | `casey/824` | 0.287 | 0.202814 ± 0.0000521 (DESI spectrum) | confirmed / confirmed | true / true | → `192821700026167542` | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 45 | `casey/825` | 0.287 | 0.348295 ± 0.203 (LS/Zhou photometric) | inconclusive / inconclusive | false / false | — | Blocked: missing host citation, LS identifier, and query metadata. |
| 46 | `casey/J111929.5+705441, 1237905` | 0.287 | 0.216168 ± 0.0000746 (DESI spectrum) | confirmed / confirmed | false / false | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 47 | `casey/J112235.5+705438, 1239515` | 0.287 | 0.215844 ± 0.0000360 (DESI spectrum) | confirmed / confirmed | false / false | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 48 | `casey/J112350.9+704142, 1240175` | 0.287 | 0.213271 ± 0.0000425 (DESI spectrum) | confirmed / confirmed | false / false | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 49 | `casey/J111930.9+702041, 1237924` | 0.287 | 0.090733 ± 0.00000422 (DESI spectrum) | confirmed / confirmed | false / false | — | Blocked: missing host citation, DESI target identifier, and query metadata. |
| 50 | `isha/WISEA J044538.83+701843.3` | 0.2505 | — | inconclusive / inconclusive | false / false | — | Blocked: missing host citation and extension source row/query provenance. |
| 51 | `oran/WISEA J211150.32+724807.8` | 0.3005 | — | inconclusive / inconclusive | false / false | — | Blocked: missing host citation and extension source row/query provenance. |
| 52 | `phineas/WHL J115048.0+714428` | 0.271 | 0.1893 ± unknown (WHL12/NED) | confirmed / confirmed | false / false | — | Blocked: missing host citation and full WHL12/NED source row/query provenance. |

## Missing provenance

### Host redshifts: blocking all rows

The repository says the Verdi draft is the redshift standard, but the full
Verdi table is not checked in. `bursts.csv` contains values, not citations,
source identifiers, uncertainty, redshift kind, release, retrieval date, or a
content hash of the upstream table. Agreement between `bursts.csv`,
`foreground_final.csv`, and the registry therefore traces copies of the same
adopted value; it is not independent verification. This blocks 50 rows with a
numeric host redshift. The two `freya` rows have no host redshift and remain
inconclusive by construction.

Required repair: freeze the authoritative Verdi host table or a minimal
source-bearing extract with FRB identifier, host identifier, redshift,
uncertainty, spectroscopic/photometric kind, bibliographic source, upstream
row identifier, retrieval date, release, and content hash.

### Candidate redshifts

- **Legacy Survey/Zhou photometric redshifts (17 rows):**
  `foreground_validated.csv` stores position, morphology, redshift, uncertainty,
  and separation, but `q_lsdr9()` did not select or persist `ls_id`. It also
  stores no query, release snapshot, retrieval time, or response hash. A
  numerical replay is possible; an identity-level source audit is not.
- **DESI spectra (22 rows):** the frozen file stores fiber coordinates,
  redshift, uncertainty, spectral class, and separation, but the query omitted
  `targetid` and other stable spectrum identifiers. It stores no query/release
  snapshot, retrieval time, or response hash. The row with a small negative
  redshift (`phineas/J114928.5+712526, 1253366`) especially requires inspection
  of the source spectrum and quality metadata; `zwarn = 0` alone is not frozen.
- **PS1-STRM (9 rows):** `strm_catalog_rows.csv` retains `objID`, coordinates,
  class, class probability, redshift, uncertainty, and extrapolation flag. It
  is the strongest candidate-side frozen evidence. The extracting script says
  rows were streamed from declination strips and selected by identifier, but
  no release identifier, source URL, retrieval date, extraction command,
  parent-file hash, or response hash accompanies the extract.
- **NED (1 base row):** the frozen row identifies the object and gives a
  redshift, but no uncertainty, redshift reference, measurement kind,
  retrieval date, or query response is stored. The point-value rule reproduces
  “confirmed,” but the uncertainty-aware acceptance rule cannot be audited.
- **V4 extension (3 rows):** the extension contains manual prose provenance,
  not the cited catalog rows. The isha and oran candidates correctly retain no
  adopted redshift. WHL J115048.0+714428 has a point redshift but lacks the full
  WHL12/NED row, uncertainty, stable upstream identifier, retrieval metadata,
  and response hash. `docs/rse/specs/research-v4-census-gap-extension.md`
  explicitly records that its attempted live NED check timed out.

### Duplicate provenance

The seven mappings are arithmetically coherent: separations are 0.01–0.12
arcsec, and each duplicate/canonical pair has the same frozen redshift and
verdict. Nevertheless, `census_duplicates.csv` is an owner-adjudication table,
not an independently reproducible crossmatch artifact. It does not include
both catalog names, stable upstream identifiers for both members, coordinate
columns, matching method/version, or hashes of the source rows. Retain the
deduplication for current fail-closed calculations, but do not label it
independently source-verified until that evidence is frozen.

## Decision-ready conclusion

The decision ticket's question resolves **negatively**:

1. The verdict and budget algorithms are internally consistent with the frozen
   numeric inputs: 52/52 verdicts and 52/52 budget flags reproduce.
2. That consistency does not validate the redshift evidence. The repository
   cannot currently trace any row through both an authoritative host source and
   an authoritative candidate source.
3. Do not change the stored redshifts or verdicts from this audit; it found no
   arithmetic discrepancy. Label them **legacy-adjudicated, provenance
   incomplete**.
4. Keep Figure 3 and catalog promotion fail-closed. Unblock only after a
   source-bearing Verdi extract and stable LS/DESI/NED/STRM query evidence are
   frozen, hashed, and replayed. Any resulting numerical change requires the
   separate owner-approved adjudication record required by the Wayfinder
   ticket.

## Sources

- `pipeline/galaxies/foreground/adjudication/validate_foreground.py`
- `pipeline/galaxies/foreground/adjudication/ps1_strm_adjudicate.py`
- `pipeline/galaxies/foreground/census_registry.py`
- `pipeline/galaxies/foreground/data/frozen_census/`
- `pipeline/galaxies/foreground/data/census_extensions/v4_extension.csv`
- `pipeline/galaxies/foreground/data/census_masses/census_duplicates.csv`
- `docs/rse/specs/research-v4-census-gap-extension.md`
- [PS1-STRM catalog paper](https://doi.org/10.1093/mnras/staa2587)
- [Legacy Survey photometric-redshift paper](https://doi.org/10.1093/mnras/staa3764)
- [NOIRLab Data Lab TAP service used by the frozen validator](https://datalab.noirlab.edu/tap)
- [NASA/IPAC Extragalactic Database](https://ned.ipac.caltech.edu/)
